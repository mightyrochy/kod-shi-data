"""Лічить п.4 кореня від виконання жнив на збереженій вибірці 30.10.

Запуск з кореня: python джерела/прилади/корінь_річ_запис_речі.py [--звіт файл.json]
Без мережі, npm ci, браузера й установлених пакетів: залежності лежать поруч.
Місце — виконане читання поза блоком товару, чий текст дійшов до запису каталогу.
"""
import argparse
import ast
from collections import defaultdict
import gzip
import gc
import hashlib
import importlib
import json
from pathlib import Path
import re
import subprocess
import sys
import types
import time

ТЕКА = Path(__file__).resolve().parent
for колесо in sorted((ТЕКА / 'річ_запис_дані').glob('*.whl')):
    sys.path.insert(0, str(колесо))
sys.path.insert(0, str(ТЕКА))
from bs4 import BeautifulSoup
from річ_запис_походження import HTML, Текст, Спостерігач, Модулі, Джерело, походження

КОРІНЬ = Path.cwd()
ВИБІРКА = Path('аудит/проби/річ_запис_каталог_2026_10_30')


def звірити_входи(корінь):
    """Не дозволяє зміненій чи неповній вибірці непомітно дати менше місць."""
    маніфест = json.loads((ТЕКА / 'річ_запис_дані/відбитки.json').read_text(encoding='utf-8'))
    for файл, відбиток in маніфест['файли'].items():
        if hashlib.sha256((корінь / файл).read_bytes()).hexdigest() != відбиток:
            raise ValueError(f'змінений вхід приладу: {файл}')


def межа_товару(суп, селектори=None):
    """Визначає вузол за рецептом/мікророзміткою, інакше межею виміру 30.10.

    Запасна межа — метод «блок_товару» з PR #2514, не вгадування поля чи
    запису за кодом. Корінь body/html документом товару не стає.
    """
    from річ_запис_межа import блок_товару
    сел = (селектори or {}).get('блок')
    товари = суп.select(сел or '[itemtype$="/Product"], [itemtype$="/Product/"]')
    заголовок = суп.find('h1')
    предки = {id(в) for в in заголовок.parents} if заголовок else None
    товари = [в for в in товари if в.name not in ('body', 'html', '[document]') and
              (id(в) in предки if предки is not None else len(товари) == 1)]
    if товари:
        return товари[-1]
    блок, _ = блок_товару(суп, set())
    return блок if блок is not None and блок.name not in ('body', 'html', '[document]') else None


def листки(зн, шлях=''):
    """Перебирає довільні поля фактичного запису, включно з вкладеними."""
    if isinstance(зн, dict):
        for к, з in зн.items():
            yield from листки(з, f'{шлях}.{к}' if шлях else str(к))
    elif isinstance(зн, (list, tuple)):
        for і, з in enumerate(зн):
            yield from листки(з, f'{шлях}[{і}]')
    elif isinstance(зн, str):
        yield шлях, зн


def звичайні(зн):
    """Знімає мітки для звірки значень і передавання в Node."""
    if isinstance(зн, str):
        return str(зн)
    if isinstance(зн, dict):
        return {str(к): звичайні(з) for к, з in зн.items()}
    if isinstance(зн, (list, tuple)):
        return [звичайні(з) for з in зн]
    return зн


def підсумувати(запис, читання, журнал=True):
    """Залишає виконані читання, що несуть слова у вихідний запис, а не діагностику."""
    поля = defaultdict(set)
    усі = defaultdict(set)
    for поле, зн in листки(запис):
        # URL/кадр — адреса, а не слова; колір має власні корені паспорта.
        if str(зн).startswith(('http://', 'https://', '//', 'data:')):
            continue
        if any(ч in поле.lower() for ч in ('колір', 'color', 'кольор', 'свотч')):
            continue
        for дж in походження(зн):
            усі[дж].add(поле)
            if дж.порушення:
                поля[дж].add(поле)
    return поля, [{'файл': дж.файл, 'рядок': дж.рядок, 'вузол': дж.вузол,
                   'порушення': дж.порушення, 'поля': sorted(усі[дж]),
                   'причина': дж.причина or ('у записі' if усі[дж] else 'текст не дійшов до поля запису')}
                  for дж in sorted(читання, key=lambda ч: (ч.файл, ч.рядок, ч.вузол))] if журнал else []


class Прогін:
    """Завантажує жнива поточного дерева й повторює HTML → запис без транспорту."""

    def __init__(self, корінь):
        """Під'єднує спостерігач до коду дерева голови чи бази храповика."""
        self.корінь = Path(корінь).resolve()
        self.спостерігач = Спостерігач()
        self.завантажувач = Модулі(self.корінь, self.спостерігач)
        sys.path.insert(0, str(self.корінь / 'zhnyvarka'))
        sys.path.insert(0, str(self.корінь / 'джерела'))
        sys.meta_path.insert(0, self.завантажувач)
        self.модулі = {ім: importlib.import_module(ім) for ім in ('жниварка', 'виконавець', 'складальник', 'ricamare_сторінка')}
        # Єдиний парсер на обох деревах: наявність lxml у машині не міняє числа.
        self.модулі['жниварка'].ПАРСЕР_HTML = 'html.parser'
        self.звичайні = {}
        for ім in ('жниварка', 'виконавець', 'ricamare_сторінка'):
            шлях = self.корінь / 'zhnyvarka' / (ім + '.py')
            мод = types.ModuleType('_без_міток_' + ім)
            мод.__file__ = str(шлях)
            exec(compile(шлях.read_text(encoding='utf-8-sig'), str(шлях), 'exec'), мод.__dict__)
            self.звичайні[ім] = мод
        self.звичайні['жниварка'].ПАРСЕР_HTML = 'html.parser'
        дерево = ast.parse((self.корінь / 'zhnyvarka/виконавець.py').read_text(encoding='utf-8-sig'))
        self.рядок_js = next(в.value.lineno for в in дерево.body if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == 'ЗЛІПОК_DOM' for ц in в.targets))
        self.код_js = self.модулі['виконавець'].ЗЛІПОК_DOM
        self.селектори_js = self.node(dict(код=self.код_js, лише_селектори=True))

    def закрити(self):
        """Прибирає перехоплювач після прогону чи тесту."""
        sys.meta_path.remove(self.завантажувач)
        for ім in self.завантажувач.імена:
            sys.modules.pop(ім, None)
        for тека in (self.корінь / 'zhnyvarka', self.корінь / 'джерела'):
            sys.path.remove(str(тека))

    def node(self, вхід):
        """Виконує JS допоміжним процесом на передньому плані, без мережі."""
        вих = subprocess.run(['node', str(ТЕКА / 'річ_запис_dom.cjs')], input=json.dumps(вхід, ensure_ascii=False),
                             capture_output=True, text=True, encoding='utf-8', timeout=30)
        if вих.returncode:
            raise RuntimeError(вих.stderr)
        return json.loads(вих.stdout)

    def dom(self, тіло, url, селектори):
        """Будує структурний DOM і виконує чинний JS зліпка з позначками."""
        суп = BeautifulSoup(тіло, 'html.parser')
        сп = Спостерігач(lambda с: межа_товару(с, селектори))
        сп.дерево(суп)
        вузли = [суп, *суп.find_all(True)]
        ід = {id(в): і for і, в in enumerate(вузли)}
        сел = {}
        for с in set(self.селектори_js) | {'body', 'title'}:
            try:
                сел[с] = [ід[id(в)] for в in суп.select(с)]
            except Exception:
                # Не кожен рядковий літерал JS — CSS; запит невідомого
                # селектора всередині виконання завершиться помилкою.
                continue

        def серіалізувати(в):
            """Передає структуру й атрибути вузла, не виконує скриптів сторінки."""
            from bs4 import Comment, Doctype
            шлях, порушення, причина = сп.вузли[id(в)]
            return dict(ід=ід[id(в)], тег=в.name, атр={к: ' '.join(з) if isinstance(з, list) else з for к, з in в.attrs.items()},
                        шлях=шлях, порушення=порушення, причина=причина,
                        діти=[серіалізувати(ч) if getattr(ч, 'name', None) else str(ч)
                              for ч in в.children if not isinstance(ч, (Comment, Doctype))])

        вих = self.node(dict(код=self.код_js, рядок=self.рядок_js, url=url, дерево=серіалізувати(суп), селектори=сел))
        for запис in вих['походження']:
            об = вих['dom']
            for ключ in запис['шлях'][:-1]:
                об = об[ключ]
            ключ = запис['шлях'][-1]
            джерела = [Джерело(**д) for д in запис['джерела']]
            об[ключ] = Текст(об[ключ], джерела)
        return вих['dom'], {Джерело(**д) for д in вих['читання']}

    def сторінка(self, рядок, тіло, браузер=True):
        """Виконує обидва збирачі HTML й повертає лише їхні записи каталогу."""
        ж = self.модулі['жниварка']
        селектори = ж.рецепт_селекторів(рядок['крамниця'])
        сп = self.спостерігач
        сп.вузли.clear()
        сп.живі.clear()
        сп.читання.clear()
        self.відмови = []
        сп.межа = lambda суп: межа_товару(суп, селектори)
        ф = ж.факти_з_картки(HTML(тіло), рядок['url'], селектори)
        if ф.get('dom_помилка'):
            raise RuntimeError(f'{рядок["url"]}: {ф["dom_помилка"]}')
        ф['url'] = рядок['url']
        з = ж.канонічний_запис(ф, {'домен': рядок['крамниця'], 'стать_типово': 'жіноче'}, 'html') if ф['є_товар'] else None
        зв = self.звичайні['жниварка']
        ф_без = зв.факти_з_картки(тіло, рядок['url'], селектори)
        ф_без['url'] = рядок['url']
        з_без = зв.канонічний_запис(ф_без, {'домен': рядок['крамниця'], 'стать_типово': 'жіноче'}, 'html') if ф_без['є_товар'] else None
        if звичайні(ф) != звичайні(ф_без) or звичайні(з) != звичайні(з_без):
            raise AssertionError(f'{рядок["url"]}: позначки змінили факти чи запис HTML')
        # Пропускаємо через справжній записувач XML у пам'яті, щоб сирі поля,
        # які він не серіалізує, не створювали місць.
        # ElementTree тримає позначені значення до write; перехоплюємо саме
        # створене дерево через його конструктор, не шукаємо збігів слів.
        if з is not None:
            з['id'] = рядок['id']
            записи = self.xml_запис(ж, з)
        else:
            записи = {}
            self.відмови.append('HTML: штатні жнива не визнали сторінку товаром; запис не створюється')
        if браузер:
            dom, js_читання = self.dom(тіло, рядок['url'], селектори)
            к = self.парний_виклик('офер браузера',
                lambda: self.звичайні['виконавець'].картка_з_dom(рядок['url'], тіло, звичайні(dom)),
                lambda: self.модулі['виконавець'].картка_з_dom(рядок['url'], HTML(тіло), dom))
            # Це офер жнив, який завершити повертає як «картка» журналу.
            # Не весь зліпок dom: document.title/довжини кандидатів тут зникнуть.
            if к is not None:
                записи['браузер'] = {поле: зн for поле, зн in к.items() if поле not in ('ld', 'og', 'текст')}
            сп.читання.update(js_читання)
        if рядок['крамниця'] == 'ricamare.com.ua':
            старий = dict(схема='v1', ід=рядок['id'], адреса=рядок['url'], параметри=[])
            знімок = dict(url=рядок['url'], html=тіло, знято='2026-10-30', sha256=hashlib.sha256(тіло.encode()).hexdigest())
            мод = self.модулі['ricamare_сторінка']
            нал = мод.рецепт()
            новий = self.парний_виклик('адаптер ricamare',
                lambda: self.звичайні['ricamare_сторінка'].розібрати(старий, знімок, нал),
                lambda: мод.розібрати(старий, dict(знімок, html=HTML(тіло)), нал))
            if новий is not None:
                записи['ricamare'] = новий
        return записи, set(сп.читання)

    def парний_виклик(self, назва, звичайний, позначений):
        """Звіряє виходи або однакову штатну відмову обох виконань."""
        результати = []
        for виклик in (звичайний, позначений):
            try:
                результати.append((виклик(), None))
            except (ValueError, TypeError, KeyError, IndexError) as помилка:
                результати.append((None, (type(помилка).__name__, str(помилка))))
        if звичайні(результати[0]) != звичайні(результати[1]):
            raise AssertionError(f'{назва}: позначки змінили вихід чи відмову: {результати[0][1]} / {результати[1][1]}')
        if результати[0][1]:
            self.відмови.append(f'{назва}: штатна відмова {результати[0][1]} — поля не створено')
        return результати[1][0]

    def xml_запис(self, ж, запис):
        """Зчитує мітки зі справжнього дерева XML до перетворення на байти."""
        import io
        дерева = []
        оригінал = ж.ET.ElementTree

        class дерево(оригінал):
            """Зберігає дерево, не міняючи перевірку типу в ET.indent."""

            def __init__(self, корінь):
                """Запам'ятовує корінь і викликає штатний конструктор."""
                дерева.append(корінь)
                super().__init__(корінь)

        ж.ET.ElementTree = дерево
        try:
            ж.записати_каталог([запис], io.BytesIO(), 'прилад')
        finally:
            ж.ET.ElementTree = оригінал
        вих = {}
        for і, ел in enumerate(дерева[0].iter()):
            if ел.text:
                вих.setdefault(f'{ел.tag}:{ел.get("name", "")}', []).append(ел.text)
        return {'html': вих}


def main(argv=None):
    """Виконує вибірку й друкує місця з часткою сторінок; помилка не дає нуль."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--звіт', type=Path)
    парсер.add_argument('--стеля', type=int, help='лише для налагодження; не число храповика')
    парсер.add_argument('--поступ', action='store_true', help='показувати виконані сторінки у stderr')
    арг = парсер.parse_args(argv)
    звірити_входи(КОРІНЬ)
    тека = КОРІНЬ / ВИБІРКА
    вибірка = json.loads((тека / 'вибірка_п3.json').read_text(encoding='utf-8'))
    if len(вибірка) != 144 or len({р['url'] for р in вибірка}) != 144:
        raise ValueError('очікується незмінна вибірка PR #2514: 144 унікальні сторінки')
    if арг.стеля:
        вибірка = вибірка[:арг.стеля]
    прогін = Прогін(КОРІНЬ)
    місця, сторінки = defaultdict(lambda: defaultdict(set)), []
    try:
        for і, рядок in enumerate(вибірка, 1):
            початок = time.monotonic()
            if арг.поступ:
                print(f'{і}/{len(вибірка)} {рядок["url"]}', file=sys.stderr, flush=True)
            шлях = тека / рядок['файл']
            тіло = gzip.decompress(шлях.read_bytes()).decode('utf-8')
            запис, читання = прогін.сторінка(рядок, тіло)
            поля, журнал = підсумувати(запис, читання, журнал=bool(арг.звіт))
            for дж, імена in поля.items():
                for поле in імена:
                    місця[(дж.файл, дж.рядок)][re.sub(r'\[\d+\]', '[]', поле)].add(рядок['url'])
            if арг.звіт:
                сторінки.append(dict(url=рядок['url'], sha256=hashlib.sha256(шлях.read_bytes()).hexdigest(), читання=журнал, відмови=прогін.відмови))
            if арг.поступ:
                print(f'  {time.monotonic() - початок:.2f} с', file=sys.stderr, flush=True)
            # DOM має циклічні parent/children; не тримаємо попередні великі
            # сторінки до випадкового спрацювання збирача сміття Python.
            gc.collect()
    finally:
        прогін.закрити()
    результат = []
    for (файл, рядок), поля in sorted(місця.items()):
        деталі = {поле: sorted(адреси) for поле, адреси in sorted(поля.items())}
        результат.append(dict(файл=файл, рядок=рядок, поля=деталі))
        for поле, адреси in деталі.items():
            print(f'{файл}:{рядок}\t{поле}\t{len(адреси)}/{len(вибірка)} ({len(адреси) / len(вибірка):.1%})')
    if арг.звіт:
        арг.звіт.write_text(json.dumps(dict(сторінок=len(вибірка), місця=результат, сторінки=сторінки), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'місць: {len(місця)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
