#!/usr/bin/env python3
"""Лічить точки отримання даних без власника-варіанта за паспортом кореня.

Це незавершений статичний інвентар, а не доказ власності з назв
змінних. Два обходи AST звіряють координати отримань усередині операторів;
їхній збіг не доводить повноти шляху від джерела до споживача. База зберігає
рішення для переглянутих виразів, включно з відхиленими кандидатами та причинами.
Новий вираз не успадковує винятку за іменем файла/функції: він рахується
окремо як непереглянутий. Координати беруться з дерева, не з бази.

Одиниця лічби — оператор отримання даних у Python, рядок отримання у JS;
повторні читання всередині нього не множать місце. Пункти класу можуть
перетинатися: загальна кількість — об'єднання місць, не сума підсумків.
Непереглянуті кандидати консервативно збільшують число, але це ще не
число порушень класу паспорта. Проби, тести й лабораторія теж скануються.
Згенерований index.html,
сторонній open-source-stylist і архів аудит/ не є вихідним кодом системи.
Нічого не імпортує з продукту, не звертається до мережі, не виконує вимірів.
"""
import argparse
import ast
import collections
import hashlib
import json
from pathlib import Path
import re
import sys
import warnings
from корінь_річ_кадр_маршрути import Граф, огляд


ПОЛЯ = {
    1: frozenset(('фото', 'фото_сирі', 'фото_усі', 'фото_опису', 'picture',
                  'images', 'image', 'og:image', 'кадр_виміру', 'кадри', 'галерея', 'файл')),
    2: frozenset(('колір_сирий', 'колір_назва', 'колір', 'color', 'colour',
                  'available', 'availability', 'наявність', 'is_in_stock',
                  'stock_quantity', 'розміри_в_наявності', 'колір_основний',
                  'колір_hex_фото', 'колір_назва_крамниці')),
}
ВИМІРИ = frozenset(('колір_з_фото', 'палітра_принту', 'виміряти_фото',
                    'поверхня_фото', 'поверхня_кадрів', 'виміряти_колір',
                    'виміряти_поверхню', 'спитати'))
МЕТОДИ = frozenset(('get', 'find', 'findtext', 'findall', 'iter', 'pop', 'setdefault'))
ДЖЕРЕЛА_КАДРУ = frozenset(('кадри_речі', 'фото_речі', 'адреса_кадру',
                          'адреси_зі_сторінки', 'фото_зі_сторінки', 'взяти_фото'))
ДЖЕРЕЛА_КОЛЬОРУ = frozenset(('колір_збагачення', 'lab_збагачення'))
ТУТ = Path(__file__).resolve()
БАЗА = ТУТ.with_suffix('.json')
ЧИТАННЯ_JS = re.compile(
    r'(?:\?\.|\.)(фото_усі|фото_сирі|фото_опису|фото|кадр_виміру|кадри|файл|'
    r'images|image|picture|колір_сирий|колір_назва|колір|color|colour|'
    r'available|availability|наявність|is_in_stock)\b|'
    r'\[\s*[\'\"](фото|фото_усі|images|image|color|available)[\'\"]\s*\]')


def відбиток(текст):
    """Стабільний ключ виразу без залежності від зсуву рядків."""
    return hashlib.sha256(текст.encode('utf-8')).hexdigest()[:24]


def назва_виклику(вузол):
    """Кінцева назва функції без домислів про її виконання."""
    return (вузол.func.attr if isinstance(вузол.func, ast.Attribute) else
            вузол.func.id if isinstance(вузол.func, ast.Name) else '')


def узгодити_ast(дерево):
    """Робить порожні параметри типів однаковими в AST Python 3.11 і 3.12.

    CI й ноутбук мають давати однакові відбитки: у 3.11 цього порожнього
    поля ще немає, а dump 3.12 його друкує також у вкладених означеннях.
    """
    for вузол in ast.walk(дерево):
        if (isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                and 'type_params' not in вузол._fields):
            вузол._fields = вузол._fields + ('type_params',)
            вузол.type_params = []
    return дерево


def сталий_dump(вузол):
    """Серіалізує AST з явними порожніми полями на Python 3.11–3.13.

    Python 3.13 приховує порожні списки у звичайному ast.dump. Тут формат
    визначає прилад, а не версія стандартної бібліотеки.
    """
    параметри = {'include_attributes': False}
    if sys.version_info >= (3, 13):
        параметри['show_empty'] = True
    return ast.dump(вузол, **параметри)


def походження(дерево):
    """Знаходить зовнішні DOM/regex-входи незалежно від назви вихідного поля.

    Селектори, читання DOM-атрибутів і витяг регулярним виразом стають
    кандидатами. Чи це кадр/колір/наявність на шляху продукту, визначає
    база оцінок; новий атрибут або інший regex не успадковує винятку.
    """
    зовнішні = {}
    методи = {'select', 'select_one', 'find_all', 'get_attribute', 'getAttribute',
              'get_text', 'xpath', 'cssselect', 'search', 'match', 'fullmatch',
              'finditer', 'findall', 'group', 'groups'}
    dom = set()
    оператори = list(ast.walk(дерево))
    for вузол in оператори:
        if isinstance(вузол, (ast.Assign, ast.For, ast.comprehension)):
            значення = вузол.value if isinstance(вузол, ast.Assign) else вузол.iter
            if any(isinstance(ч, ast.Call) and назва_виклику(ч) in
                   {'select', 'select_one', 'find_all', 'xpath', 'cssselect'}
                   for ч in ast.walk(значення)):
                цілі = вузол.targets if isinstance(вузол, ast.Assign) else [вузол.target]
                dom.update(ч.id for ц in цілі for ч in ast.walk(ц) if isinstance(ч, ast.Name))
    for вузол in оператори:
        if not isinstance(вузол, ast.Call):
            continue
        ім = назва_виклику(вузол)
        приймач = вузол.func.value if isinstance(вузол.func, ast.Attribute) else None
        аргумент = вузол.args[0] if вузол.args else None
        атрибут = аргумент.value if isinstance(аргумент, ast.Constant) else None
        if ім in методи or (ім in {'get', 'find', 'findtext', 'iter'} and (
                (isinstance(приймач, ast.Name) and приймач.id in dom)
                or (isinstance(атрибут, str) and (
                    атрибут.startswith('data-') or атрибут in {'src', 'srcset', 'style', 'href'}))
                or (ім == 'get' and isinstance(аргумент, ast.Name)))):
            # Навіть непрямий атрибут ел.get(атр) і група м.group(2)
            # є входом. Тут немає словника назв полів речі.
            зовнішні[вузол] = {1, 2}
    граф = Граф({'<вхід>.py': дерево})
    прямий = граф.від_джерел(граф.входи | {к for к, в in граф.точки.items() if в in зовнішні})
    # Вхід усередині допоміжної функції має дійти до її виклику.
    # Самої присутності входу в тілі недостатньо: потрібен шлях через return.
    for точка, ціль in граф.звязані_виклики.items():
        повернення = (*ціль, 'повернення')
        if повернення in прямий:
            зовнішні[граф.точки[точка]] = {1, 2}
    return зовнішні


def ознаки(вузол, власники=()):
    """Пункти-кандидати для вузла отримання даних, ключа чи виміру."""
    поле = None
    if isinstance(вузол, ast.Call):
        ім = назва_виклику(вузол)
        if ім in власники:
            return {1}
        if ім in МЕТОДИ and вузол.args and isinstance(вузол.args[0], ast.Constant):
            поле = вузол.args[0].value
        if ім in ВИМІРИ:
            return {4}
        if ім.lstrip('_') in ДЖЕРЕЛА_КАДРУ:
            return {1}
        if ім.lstrip('_') in ДЖЕРЕЛА_КОЛЬОРУ:
            return {2}
        if ім in ('urlparse', 'urlsplit', 'urlunparse', 'urlunsplit'):
            return {3}
    if (isinstance(вузол, ast.Subscript) and isinstance(вузол.ctx, ast.Load)
            and isinstance(вузол.slice, ast.Constant)):
        поле = вузол.slice.value
    if isinstance(вузол, ast.keyword):
        поле = вузол.arg
    if isinstance(вузол, ast.Subscript) and isinstance(вузол.ctx, ast.Store):
        if isinstance(вузол.slice, ast.Constant):
            поле = вузол.slice.value
    поле = поле.lower().lstrip('~') if isinstance(поле, str) else поле
    пункти = {п for п, поля in ПОЛЯ.items() if isinstance(поле, str) and поле in поля}
    if isinstance(поле, str):
        if re.search(r'кол[іь]р|кольор|colou?r|свотч|swatch|наявн|stock|avail', поле, re.I):
            пункти.add(2)
        if re.search(r'фото|кадр|галере|image|picture|photo', поле, re.I):
            пункти.add(1)
    if поле == 'фото_ключ':
        пункти.add(3)
    # Ключ запису/двійника: перевіряється структура присвоєння, не номер рядка.
    if isinstance(вузол, (ast.Assign, ast.AnnAssign)):
        цілі = вузол.targets if isinstance(вузол, ast.Assign) else [вузол.target]
        імена = {ч.id for ц in цілі for ч in ast.walk(ц) if isinstance(ч, ast.Name)}
        if any('ключ' in ім or ім in ('хто', 'за_файлом') for ім in імена):
            значення = ast.unparse(вузол.value) if вузол.value else ''
            if any(сл in значення for сл in ('фото', 'кадр', 'url', 'адр', 'group_id', 'назва', 'файл')):
                пункти.add(3)
    if isinstance(вузол, ast.Call):
        if any(к.arg == 'варіант' or (к.arg == 'стан' and isinstance(к.value, ast.Constant)
                                      and к.value.value == 'свій') for к in вузол.keywords):
            пункти.add(1)
        if назва_виклику(вузол) == 'next':
            пункти.update((1, 2))
    if (isinstance(вузол, ast.Subscript) and isinstance(вузол.slice, ast.Constant)
            and вузол.slice.value == 0):
        пункти.update((1, 2))
    return пункти


def розібрати_python(текст):
    """Звіряє координати кандидатів обходами від читань і від операторів."""
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', SyntaxWarning)
        дерево = узгодити_ast(ast.parse(текст))
    входи = походження(дерево)
    батьки, області = {}, {}

    def розмітити(вузол, область='<модуль>'):
        """Запам'ятовує лексичну область і батьків вузлів."""
        if isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            область = область + '.' + вузол.name
        області[вузол] = область
        for дитина in ast.iter_child_nodes(вузол):
            батьки[дитина] = вузол
            розмітити(дитина, область)

    розмітити(дерево)
    власники = {псевдо.asname or псевдо.name for імпорт in ast.walk(дерево)
                if isinstance(імпорт, ast.ImportFrom) and імпорт.module == 'фід_власник_кадру'
                for псевдо in імпорт.names if псевдо.name == 'запис'}

    def оператор(вузол):
        """Найближчий оператор отримання, без охоплення всього циклу/функції."""
        while not isinstance(вузол, ast.stmt):
            вузол = батьки[вузол]
        return вузол

    відбитки = {}

    def запис(вузол, пункт):
        """Канонічна координата оператора й пункту."""
        if вузол in відбитки:
            return (області[вузол], вузол.lineno, пункт, відбитки[вузол])
        норм = сталий_dump(вузол)
        # Для if/for/with беремо лише заголовок: тіло є іншими операторами.
        if isinstance(вузол, (ast.If, ast.While)):
            норм = сталий_dump(вузол.test)
        elif isinstance(вузол, (ast.For, ast.AsyncFor)):
            норм = сталий_dump(вузол.iter)
        відбитки[вузол] = відбиток(норм)
        return (області[вузол], вузол.lineno, пункт, відбитки[вузол])

    вперед = set()
    for вузол in ast.walk(дерево):
        for пункт in ознаки(вузол, власники) | входи.get(вузол, set()):
            вперед.add(запис(оператор(вузол), пункт))
    назад = set()

    def читання_оператора(вузол):
        """Від оператора спускається до його читань, не заходить у вкладені оператори."""
        yield вузол
        for дитина in ast.iter_child_nodes(вузол):
            if not isinstance(дитина, ast.stmt):
                yield from читання_оператора(дитина)

    for споживач in ast.walk(дерево):
        if isinstance(споживач, ast.stmt):
            for вузол in читання_оператора(споживач):
                for пункт in ознаки(вузол, власники) | входи.get(вузол, set()):
                    назад.add(запис(споживач, пункт))
    return вперед, назад


def код_js(текст):
    """Маскує коментарі й текстові літерали, лишаючи індекси та інтерполяції."""
    вихід = list(текст)

    def стерти(початок, кінець):
        """Зберігає координати рядків при маскуванні."""
        for і in range(початок, кінець):
            if вихід[і] != '\n':
                вихід[і] = ' '

    def код(і, вкладено=False):
        """Сканує код до кінця або закривальної дужки інтерполяції."""
        глибина = 0
        while і < len(текст):
            ч = текст[і]
            if вкладено and ч == '}' and глибина == 0:
                return і
            if ч == '{':
                глибина += 1
            elif ч == '}':
                глибина -= 1
            if текст.startswith('/*', і):
                кінець = текст.find('*/', і + 2)
                кінець = len(текст) if кінець < 0 else кінець + 2
                стерти(і, кінець)
                і = кінець
                continue
            if текст.startswith('//', і) and (і == 0 or текст[і - 1] != '\\'):
                кінець = текст.find('\n', і)
                кінець = len(текст) if кінець < 0 else кінець
                стерти(і, кінець)
                і = кінець
                continue
            попереднє = текст[:і].rstrip() if ч == '/' else ''
            if ч == '/' and (not попереднє or попереднє[-1] in '([{:;,=!?&|>'
                              or re.search(r'\b(?:return|case|yield)\s*$', попереднє)):
                початок, клас = і, False
                і += 1
                while і < len(текст):
                    if текст[і] == '\\':
                        і += 2
                        continue
                    if текст[і] == '[':
                        клас = True
                    elif текст[і] == ']':
                        клас = False
                    elif текст[і] == '/' and not клас:
                        і += 1
                        break
                    і += 1
                стерти(початок, і)
                continue
            if ч in ('\"', "'", '`'):
                початок, лапка = і, ч
                і += 1
                while і < len(текст):
                    if текст[і] == '\\':
                        і += 2
                    elif текст[і] == лапка:
                        і += 1
                        break
                    elif лапка == '`' and текст.startswith('${', і):
                        стерти(початок, і + 2)
                        і = код(і + 2, True) + 1
                        початок = і
                    else:
                        і += 1
                # Індексне читання o['фото'] зберігаємо, звичайну прозу — ні.
                if not (лапка != '`' and текст[:початок].rstrip().endswith('[')
                        and текст[і:].lstrip().startswith(']')):
                    стерти(початок, і)
                continue
            і += 1
        return і

    код(0)
    return ''.join(вихід)


def розібрати_js(текст):
    """Перевіряє отримання полів у JS; HTML обмежує тегами script."""
    if '<script' in текст:
        шматки = []
        for зб in re.finditer(r'<script\b[^>]*>([\s\S]*?)</script>', текст, re.I):
            початок = текст.count('\n', 0, зб.start(1))
            шматки.append((початок, зб.group(1)))
    else:
        шматки = [(0, текст)]
    вперед, назад = set(), set()
    for зсув, шматок in шматки:
        чистий = код_js(шматок)
        рядки = чистий.splitlines()
        # Походження з браузера не залежить від назви поля результату.
        джерела = re.compile(r'\.(?:querySelectorAll|querySelector|getAttribute|'
                            r'match|matchAll|exec)\s*\(|\.dataset\b')
        for номер, рядок in enumerate(рядки, зсув + 1):
            if джерела.search(рядок):
                норм = re.sub(r'\s+', ' ', рядок).strip()
                for пункт in (1, 2):
                    точка = ('<js>', номер, пункт, відбиток(норм))
                    вперед.add(точка)
                    назад.add(точка)
        for зб in ЧИТАННЯ_JS.finditer(чистий):
            номер = чистий.count('\n', 0, зб.start())
            поле = зб.group(1) or зб.group(2)
            пункт = next(п for п, поля in ПОЛЯ.items() if поле in поля)
            норм = re.sub(r'\s+', ' ', рядки[номер]).strip()
            вперед.add(('<js>', номер + зсув + 1, пункт, відбиток(норм)))
        for номер, рядок in enumerate(рядки, зсув + 1):
            for зб in ЧИТАННЯ_JS.finditer(рядок):
                поле = зб.group(1) or зб.group(2)
                пункт = next(п for п, поля in ПОЛЯ.items() if поле in поля)
                норм = re.sub(r'\s+', ' ', рядок).strip()
                назад.add(('<js>', номер, пункт, відбиток(норм)))
    return вперед, назад


def кандидати(корінь):
    """Сканує всі вихідні Python/JS/HTML у двох деревах системи, без списку прикладів."""
    вперед, назад = {}, {}
    файлів = 0
    for тека in ('джерела', 'zhnyvarka'):
        if not (корінь / тека).is_dir():
            raise ValueError(f'нема дерева вихідного коду: {корінь / тека}')
        for шлях in sorted((корінь / тека).rglob('*')):
            if not шлях.is_file() or шлях.suffix not in ('.py', '.js', '.html'):
                continue
            if any(ч in ('node_modules', '__pycache__', '.venv') for ч in шлях.parts):
                continue
            відносний = шлях.relative_to(корінь).as_posix()
            if відносний.startswith('джерела/прилади/корінь_річ_кадр_'):
                continue  # власний сканер не є споживачем каталогу
            текст = шлях.read_text(encoding='utf-8-sig')
            а, б = розібрати_python(текст) if шлях.suffix == '.py' else розібрати_js(текст)
            # Скрипти Playwright живуть також у рядках Python; не губимо їх.
            if шлях.suffix == '.py':
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', SyntaxWarning)
                    дерево = ast.parse(текст)
                for вузол in ast.walk(дерево):
                    if (isinstance(вузол, ast.Constant) and isinstance(вузол.value, str)
                            and 'document.' in вузол.value):
                        в, г = розібрати_js(вузол.value)
                        for знайдене, вихід in ((в, а), (г, б)):
                            for область, рядок, пункт, хеш in знайдене:
                                вихід.add(('<вбудований_js>', вузол.lineno + рядок - 1, пункт, хеш))
            файлів += 1
            for перелік, вихід in ((а, вперед), (б, назад)):
                повтори = collections.Counter()
                for область, рядок, пункт, хеш in sorted(перелік):
                    основа = f'{відносний}|{область}|{пункт}|{хеш}'
                    повтори[основа] += 1
                    ключ = основа + '|' + str(повтори[основа])
                    вихід.setdefault(ключ, {'файл': відносний, 'область': область,
                                           'рядок': рядок, 'пункт': пункт, 'вираз': хеш})
    return вперед, назад, файлів


def обєднати_місця(точки):
    """Оператор з кількома порушеннями рахує раз, зберігаючи всі пункти."""
    групи = {}
    for точка in точки:
        ключ = (точка['файл'], точка['область'], точка['рядок'], точка['вираз'])
        if ключ not in групи:
            групи[ключ] = dict(точка, пункти=[], причини={})
        місце = групи[ключ]
        пункт = точка['пункт']
        місце['пункти'].append(пункт)
        місце['причини'][str(пункт)] = точка['чому']
    for місце in групи.values():
        місце['пункти'] = sorted(set(місце['пункти']))
        місце['чому'] = '; '.join(f'{п}: {місце["причини"][str(п)]}' for п in місце['пункти'])
    return sorted(групи.values(), key=lambda т: (т['файл'], т['рядок'], т['вираз']))


def main():
    """Друкує місця й підсумки у форматі храповика; збої не маскує нулем."""
    ап = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ап.add_argument('--корінь', type=Path, default=ТУТ.parents[2])
    ап.add_argument('--база', type=Path, default=БАЗА)
    ап.add_argument('--json', action='store_true', help='машинний інвентар і непереглянуті кандидати')
    ап.add_argument('--маршрути', action='store_true', help='JSON доказів залежностей Python; не число порушень')
    арг = ап.parse_args()
    if арг.маршрути:
        print(json.dumps(огляд(арг.корінь.resolve()), ensure_ascii=False, indent=2))
        return
    вперед, назад, файлів = кандидати(арг.корінь.resolve())
    база = json.loads(арг.база.read_text(encoding='utf-8'))
    рішення = база['рішення']
    місця, нові = [], []
    for ключ, точка in sorted((вперед | назад).items()):
        оцінка = рішення.get(ключ)
        if оцінка is None:
            нові.append(ключ)
            місця.append(dict(точка, чому='НЕ ПЕРЕГЛЯНУТО: новий вираз отримання даних; потрібна незалежна звірка'))
        elif оцінка['порушення']:
            місця.append(dict(точка, чому=оцінка['чому']))
    розбіжності = sorted(вперед.keys() ^ назад.keys())
    підсумки = {п: sum(т['пункт'] == п for т in місця) for п in range(1, 5)}
    місця = обєднати_місця(місця)
    if арг.json:
        print(json.dumps(dict(місця=місця, підсумки=підсумки, нові=нові,
                              розбіжності=розбіжності, файлів=файлів,
                              кандидатів=len(вперед | назад), інвентар=вперед | назад),
                         ensure_ascii=False, indent=2))
        return
    for точка in місця:
        пункти = ','.join(map(str, точка['пункти']))
        print(f"{точка['файл']}:{точка['рядок']} · {пункти} · {точка['чому']}")
    print(f'файлів: {файлів}; кандидатів: {len(вперед | назад)}; непереглянутих: {len(нові)}')
    print(f'шляхи: джерела {len(вперед)}; споживачі {len(назад)}; розбіжностей {len(розбіжності)}')
    for пункт, число in підсумки.items():
        print(f'пункт {пункт}: {число}')
    print(f'місць: {len(місця)}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, SyntaxError, KeyError) as помилка:
        print(f'ПОМИЛКА приладу: {помилка}', file=sys.stderr)
        sys.exit(1)
