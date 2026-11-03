"""Позначає прочитані рядки під час виконання незмінених модулів жнив.

AST додає спостерігача до операцій, але не вирішує, що є записом чи полем.
Походження доходить до фактичного виходу збирача разом зі значенням рядка.
"""
import ast
import builtins
from dataclasses import dataclass
import html
import importlib.abc
import importlib.util
import json
import operator
from pathlib import Path
import re
import sys


@dataclass(frozen=True)
class Джерело:
    """Місце виконаного читання й вузол, з якого воно взяло текст."""
    файл: str
    рядок: int
    вузол: str
    порушення: bool
    причина: str = ''


class Текст(str):
    """Рядок із походженням; значення, істинність і порівняння лишаються штатними."""

    def __new__(клас, значення, джерела=(), відрізки=None):
        """Додає незмінну множину виконаних читань до значення."""
        об = super().__new__(клас, значення)
        об.відрізки = tuple(відрізки) if відрізки is not None else ((0, len(об), frozenset(джерела)),) if об and джерела else ()
        об.джерела = frozenset().union(*(д for _, _, д in об.відрізки))
        return об


class HTML(Текст):
    """Сире тіло сторінки до першого читання парсером чи регулярним виразом."""


def виріз(текст, початок, кінець):
    """Залишає походження тільки символів, які входять до зрізу."""
    відрізки = [(max(а, початок) - початок, min(б, кінець) - початок, д)
                for а, б, д in getattr(текст, 'відрізки', ()) if а < кінець and б > початок]
    return Текст(str(текст)[початок:кінець], відрізки=відрізки)


def зєднати(частини, роздільник=''):
    """Конкатенує текст і зміщує його відрізки, не заражаючи сусідні частини."""
    вих, відрізки, зсув = [], [], 0
    for і, ч in enumerate(частини):
        for шматок in ([роздільник, ч] if і else [ч]):
            вих.append(str(шматок))
            відрізки.extend((а + зсув, б + зсув, д) for а, б, д in getattr(шматок, 'відрізки', ()))
            зсув += len(str(шматок))
    return Текст(''.join(вих), відрізки=відрізки)


def походження(значення):
    """Повертає мітки тільки самого значення, не сусідніх полів контейнера."""
    return значення.джерела if isinstance(значення, Текст) else frozenset()


def позначити(значення, джерела):
    """Переносить мітки на рядкові листки результату операції."""
    if isinstance(значення, str):
        return Текст(значення, джерела)
    if isinstance(значення, list):
        return [позначити(ч, джерела) for ч in значення]
    if isinstance(значення, tuple):
        return tuple(позначити(ч, джерела) for ч in значення)
    return значення


class Збіг:
    """Передає групі regex лише походження прочитаного входу."""

    def __init__(self, збіг, джерела):
        """Зберігає справжній Match і його джерело."""
        self.збіг, self.джерела = збіг, джерела

    def __getattr__(self, ключ):
        """Делегує службові атрибути справжньому Match."""
        return getattr(self.збіг, ключ)

    def __getitem__(self, ключ):
        """Підписує вибрану групу, не весь словник локальних змінних."""
        return self.group(ключ)

    def group(self, *ключі):
        """Підписує групи справжнього збігу."""
        if len(ключі) > 1:
            return tuple(self.group(к) for к in ключі)
        ключ = ключі[0] if ключі else 0
        зн = self.збіг.group(ключ)
        if isinstance(self.збіг.string, Текст) and not isinstance(self.збіг.string, HTML) and зн is not None:
            return виріз(self.збіг.string, *self.збіг.span(ключ))
        return позначити(зн, self.джерела)

    def groups(self, *арг):
        """Підписує кортеж груп справжнього збігу."""
        return позначити(self.збіг.groups(*арг), self.джерела)

    def groupdict(self, *арг):
        """Підписує значення іменованих груп."""
        return {к: позначити(з, self.джерела) for к, з in self.збіг.groupdict(*арг).items()}


class Спостерігач:
    """Спостерігає конкретні операції читання й поширення тексту."""

    def __init__(self, межа=None):
        """Створює окремий журнал для одного виконання сторінки."""
        self.вузли = {}
        self.живі = []
        self.читання = set()
        self.межа = межа

    def джерело(self, файл, рядок, вузол, порушення, причина=''):
        """Реєструє саме виконане читання, включно з невикористаними."""
        дж = Джерело(файл, рядок, вузол, порушення, причина)
        self.читання.add(дж)
        return frozenset((дж,))

    def дерево(self, суп):
        """Прив'язує вузли парсера до межі товару до руйнівних decompose жниварки."""
        self.живі.append(суп)
        блок = self.межа(суп) if self.межа else None
        свої = {id(блок), *(id(в) for в in блок.descendants)} if блок is not None else set()
        крихти = {id(в) for кр in суп.select('[class*="breadcrumb"], [id*="breadcrumb"], '
                                         '[itemtype$="/BreadcrumbList"], nav[aria-label*="rumb"]')
                  for в in [кр, *кр.descendants]}
        шляхи, порядки = {id(суп): '[document]'}, {}
        for в in [суп, *суп.descendants]:
            ім = getattr(в, 'name', None)
            if not ім:
                continue
            if в is not суп:
                ключ = (id(в.parent), ім)
                порядки[ключ] = порядки.get(ключ, 0) + 1
                шляхи[id(в)] = f'{шляхи[id(в.parent)]}/{ім}[{порядки[ключ]}]'
            виняток = 'крихти — розділ цього товару' if id(в) in крихти else ''
            self.вузли[id(в)] = (шляхи[id(в)], id(в) not in свої and not виняток, виняток)

    def від_вузла(self, файл, рядок, вузол):
        """Повертає походження вузла, відомого з виконаного розбору сторінки."""
        if id(вузол) not in self.вузли:
            return frozenset()
        шлях, порушення, причина = self.вузли[id(вузол)]
        return self.джерело(файл, рядок, шлях, порушення, причина)

    def атрибут(self, файл, рядок, об, ключ):
        """Позначає читання DOM .text/.string, залишає методи та службові атрибути."""
        зн = getattr(об, ключ)
        if ключ in ('text', 'string') and isinstance(зн, str):
            return позначити(зн, self.від_вузла(файл, рядок, об) or походження(об))
        return зн

    def індекс(self, файл, рядок, об, ключ):
        """Зберігає мітку при зрізі тексту чи читанні атрибута DOM."""
        зн = об[ключ]
        if isinstance(об, Текст):
            if isinstance(ключ, slice):
                а, б, крок = ключ.indices(len(об))
                if крок == 1:
                    return виріз(об, а, б)
            elif isinstance(ключ, int):
                а = ключ % len(об)
                return виріз(об, а, а + 1)
            return позначити(зн, походження(об))
        if type(об).__module__.startswith('bs4'):
            return позначити(зн, self.від_вузла(файл, рядок, об))
        return зн

    def бінарна(self, вид, ліве, праве):
        """Виконує оператор і передає походження його рядкових операндів."""
        зн = {'Add': operator.add, 'Mod': operator.mod, 'Mult': operator.mul}[вид](ліве, праве)
        if вид == 'Add' and isinstance(ліве, str) and isinstance(праве, str):
            return зєднати([ліве, праве])
        дж = походження(ліве) | походження(праве)
        if isinstance(праве, tuple) and вид == 'Mod':
            дж |= frozenset().union(*(походження(ч) for ч in праве))
        return позначити(зн, дж) if isinstance(зн, str) else зн

    def формат(self, зн, перетворення, формат_рядка):
        """Виконує одну частину f-рядка без повторного обчислення виразу."""
        в = {-1: lambda ч: ч, 115: str, 114: repr, 97: ascii}[перетворення](зн)
        return позначити(format(в, формат_рядка), походження(зн))

    def зєднати(self, частини):
        """Складає обчислений f-рядок із походженням його частин."""
        return зєднати(частини)

    def регулярний(self, файл, рядок, функція, арг, ключі):
        """Виконує regex; мітки з'являються лише на тексті, який він повернув."""
        власник = getattr(функція, '__self__', None)
        ім = функція.__name__
        шаблон = власник if isinstance(власник, re.Pattern) else re.compile(арг[0], ключі.get('flags', арг[2] if len(арг) > 2 else 0))
        вхід = арг[0] if isinstance(власник, re.Pattern) else арг[1]
        хвіст = арг[1:] if isinstance(власник, re.Pattern) else ()
        if not isinstance(вхід, (Текст, HTML)):
            return функція(*арг, **ключі)
        дж = походження(вхід)
        if isinstance(вхід, HTML):
            дж = self.джерело(файл, рядок, '[document] (HTML/regex)', True)
        if ім in ('search', 'match', 'fullmatch'):
            зн = функція(*арг, **ключі)
            return Збіг(зн, дж) if зн else None
        збіги = шаблон.finditer(вхід, *хвіст)
        if ім == 'finditer':
            return (Збіг(зн, дж) for зн in збіги)
        return [Збіг(зн, дж).group(0) if not шаблон.groups else
                (Збіг(зн, дж).group(1) or '' if шаблон.groups == 1 else tuple(Збіг(зн, дж).group(і) or '' for і in range(1, шаблон.groups + 1)))
                for зн in збіги]

    def заміна(self, функція, арг, ключі):
        """Переносить мітки тільки з незамінених частин і вставлених груп regex."""
        власник = getattr(функція, '__self__', None)
        if isinstance(власник, re.Pattern):
            шаблон, заміна, текст = власник, арг[0], арг[1]
            стеля = ключі.get('count', арг[2] if len(арг) > 2 else 0)
        else:
            шаблон = re.compile(арг[0], ключі.get('flags', арг[4] if len(арг) > 4 else 0))
            заміна, текст = арг[1:3]
            стеля = ключі.get('count', арг[3] if len(арг) > 3 else 0)
        частини, позиція, кількість = [], 0, 0
        for збіг in шаблон.finditer(текст):
            if стеля and кількість >= стеля:
                break
            частини.append(виріз(текст, позиція, збіг.start()))
            if callable(заміна):
                нове = заміна(Збіг(збіг, походження(текст)))
            else:
                нове = збіг.expand(заміна)
                дж = походження(заміна)
                for пос in re.finditer(r'\\g<([^>]+)>|\\([1-9][0-9]?)', заміна):
                    ключ = пос.group(1) or пос.group(2)
                    ключ = int(ключ) if ключ.isdigit() else ключ
                    дж |= походження(виріз(текст, *збіг.span(ключ)))
                нове = позначити(нове, дж)
            частини.append(нове or '')
            позиція, кількість = збіг.end(), кількість + 1
        частини.append(виріз(текст, позиція, len(текст)))
        результат = зєднати(частини)
        return (результат, кількість) if функція.__name__ == 'subn' else результат

    def виклик(self, файл, рядок, функція, *арг, **ключі):
        """Виконує справжній виклик; позначає тільки примітиви перетворення тексту."""
        ім = getattr(функція, '__name__', '')
        власник = getattr(функція, '__self__', None)
        модуль = getattr(функція, '__module__', '') or ''
        if (isinstance(власник, re.Pattern) or модуль == 're') and ім in ('search', 'match', 'fullmatch', 'findall', 'finditer'):
            return self.регулярний(файл, рядок, функція, арг, ключі)
        if (isinstance(власник, re.Pattern) or модуль == 're') and ім in ('sub', 'subn'):
            індекс = 1 if isinstance(власник, re.Pattern) else 2
            if len(арг) > індекс and isinstance(арг[індекс], Текст) and not isinstance(арг[індекс], HTML):
                return self.заміна(функція, арг, ключі)
        if ім == 'join' and isinstance(власник, str):
            частини = list(арг[0])
            return зєднати(частини, власник)
        зн = функція(*арг, **ключі)
        if ім == 'BeautifulSoup' and арг and isinstance(арг[0], HTML):
            self.дерево(зн)
        if ім in ('get_text', 'get', '__getitem__') and id(власник) in self.вузли:
            # Клас, id та стилі — будова сторінки; слова — текст, title, content, value, alt.
            if ім == 'get_text' or (арг and арг[0] not in ('class', 'id', 'style', 'itemtype', 'itemprop')):
                return позначити(зн, self.від_вузла(файл, рядок, власник))
        if функція is json.loads and арг and походження(арг[0]):
            return self.json_листки(зн, походження(арг[0]))
        if ім in ('мета_теги', 'ог') and isinstance(зн, dict):
            for к in ('og:type', 'product:price:currency', 'og:price:currency', 'product:availability', 'og:availability'):
                if к in зн:
                    зн[к] = str(зн[к])
        if функція is str and арг:
            return позначити(зн, походження(арг[0]))
        if isinstance(власник, str) and ім not in ('__contains__', 'find', 'index', 'count', 'startswith', 'endswith'):
            if ім == 'replace' and isinstance(власник, Текст) and арг[0]:
                частини, позиція = [], 0
                стеля = арг[2] if len(арг) > 2 else -1
                while стеля:
                    початок = str(власник).find(арг[0], позиція)
                    if початок < 0:
                        break
                    частини.extend((виріз(власник, позиція, початок), арг[1]))
                    позиція = початок + len(арг[0])
                    стеля -= 1
                частини.append(виріз(власник, позиція, len(власник)))
                return зєднати(частини)
            if ім in ('strip', 'lstrip', 'rstrip') and isinstance(власник, Текст):
                а = (len(власник) - len(власник.lstrip(*арг))) if ім != 'rstrip' else 0
                return виріз(власник, а, а + len(зн))
            if ім in ('split', 'rsplit', 'splitlines', 'partition', 'rpartition') and isinstance(власник, Текст):
                частини, початок = [], 0
                for ч in зн:
                    а = str(власник).find(ч, початок)
                    частини.append(виріз(власник, а, а + len(ч)))
                    початок = а + len(ч)
                return tuple(частини) if isinstance(зн, tuple) else частини
            дж = походження(власник)
            # replace не повинен втратити джерело вставленого тексту.
            if ім in ('replace', 'format', 'format_map'):
                дж |= frozenset().union(*(походження(ч) for ч in арг))
            return позначити(зн, дж)
        if функція is html.unescape and арг:
            return позначити(зн, походження(арг[0]))
        if (isinstance(власник, re.Pattern) or модуль == 're') and ім in ('sub', 'subn', 'split'):
            індекс = (1 if ім == 'split' else 2) - int(isinstance(власник, re.Pattern))
            if len(арг) > індекс:
                дж = походження(арг[індекс])
                return позначити(зн, дж)
        return зн

    def json_листки(self, зн, дж, ключ=''):
        """Позначає слова JSON, виключає коди відкритого стандарту за їх джерелом."""
        if isinstance(зн, dict):
            тип = зн.get('@type')
            if тип == 'BreadcrumbList' or (isinstance(тип, list) and 'BreadcrumbList' in тип):
                дж = frozenset(Джерело(д.файл, д.рядок, д.вузол, False, 'крихти — розділ цього товару') for д in дж)
            return {к: self.json_листки(з, дж, к) for к, з in зн.items()}
        if isinstance(зн, list):
            return [self.json_листки(з, дж, ключ) for з in зн]
        if ключ in ('@type', '@context', 'availability', 'priceCurrency', 'currency', 'unitCode',
                    'image', 'url', '@id', 'contentUrl', 'thumbnailUrl'):
            return зн
        if isinstance(зн, str) and re.fullmatch(r'[-+\d.,\s]+', зн):
            return зн
        return позначити(зн, дж)


class Позначки(ast.NodeTransformer):
    """Додає до виразів спостерігача зі збереженням вихідних номерів рядків."""

    def __init__(self, файл):
        """Запам'ятовує шлях модуля від кореня репозиторію."""
        self.файл = файл

    def обгорнути(self, вузол, метод, арг, адреса=True):
        """Будує виклик спостерігача й переносить координати початкового виразу."""
        початок = [ast.Constant(self.файл), ast.Constant(вузол.lineno)] if адреса else []
        виклик = ast.Call(ast.Attribute(ast.Name('__походження__', ast.Load()), метод, ast.Load()), початок + арг, [])
        return ast.copy_location(виклик, вузол)

    def visit_Call(self, вузол):
        """Обгортає виклик, залишає аргументи й ключі з їхнім порядком."""
        self.generic_visit(вузол)
        if isinstance(вузол.func, ast.Name) and вузол.func.id in ('super', 'locals', 'globals', 'eval', 'exec', 'vars'):
            # Ці вбудовані функції читають кадр свого безпосереднього викликача.
            return вузол
        вих = self.обгорнути(вузол, 'виклик', [вузол.func, *вузол.args])
        вих.keywords = вузол.keywords
        return вих

    def visit_Attribute(self, вузол):
        """Обгортає читання атрибута, не ціль присвоєння."""
        self.generic_visit(вузол)
        return self.обгорнути(вузол, 'атрибут', [вузол.value, ast.Constant(вузол.attr)]) if isinstance(вузол.ctx, ast.Load) else вузол

    def visit_Subscript(self, вузол):
        """Обгортає читання індексу та перетворює AST зрізу на звичайний slice."""
        self.generic_visit(вузол)
        if not isinstance(вузол.ctx, ast.Load):
            return вузол
        зріз = вузол.slice
        if isinstance(зріз, ast.Slice):
            зріз = ast.Call(ast.Name('slice', ast.Load()), [зріз.lower or ast.Constant(None), зріз.upper or ast.Constant(None), зріз.step or ast.Constant(None)], [])
        return self.обгорнути(вузол, 'індекс', [вузол.value, зріз])

    def visit_BinOp(self, вузол):
        """Зберігає походження конкатенації, повторення й відсоткового форматування."""
        self.generic_visit(вузол)
        return self.обгорнути(вузол, 'бінарна', [ast.Constant(type(вузол.op).__name__), вузол.left, вузол.right], False) if isinstance(вузол.op, (ast.Add, ast.Mod, ast.Mult)) else вузол

    def visit_JoinedStr(self, вузол):
        """Виконує кожен підвираз f-рядка один раз і зберігає мітки."""
        частини = []
        for ч in вузол.values:
            if isinstance(ч, ast.FormattedValue):
                частини.append(self.обгорнути(вузол, 'формат', [self.visit(ч.value), ast.Constant(ч.conversion), self.visit(ч.format_spec) if ч.format_spec else ast.Constant('')], False))
            else:
                частини.append(ч)
        return self.обгорнути(вузол, 'зєднати', [ast.List(частини, ast.Load())], False)


class Модулі(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Завантажує модулі жнив із диска з позначками лише в пам'яті."""

    def __init__(self, корінь, спостерігач):
        """Обмежує перехоплення модулями на шляху розбору до каталогу."""
        self.корінь, self.спостерігач = Path(корінь), спостерігач
        self.імена = {'жниварка', 'виконавець', 'жнива_каталог', 'складальник', 'ricamare_сторінка'}

    def find_spec(self, fullname, path=None, target=None):
        """Знаходить модуль у поточному дереві храповика, не в дереві приладу."""
        if fullname.split('.')[0] in ('requests', 'curl_cffi', 'lxml'):
            # Це необов'язкові транспорти та альтернативний парсер, не
            # залежності повтору збережених HTML. Самі жнива мають fallback.
            raise ModuleNotFoundError('безмережевий повтор: ' + fullname)
        if fullname in self.імена:
            return importlib.util.spec_from_file_location(fullname, self.корінь / 'zhnyvarka' / (fullname + '.py'), loader=self)
        return None

    def create_module(self, spec):
        """Доручає створення модуля штатному importlib."""
        return None

    def exec_module(self, module):
        """Компілює чинний вихідний код зі спостерігачем і виконує його імпорт."""
        шлях = Path(module.__spec__.origin)
        файл = шлях.relative_to(self.корінь).as_posix()
        дерево = Позначки(файл).visit(ast.parse(шлях.read_text(encoding='utf-8-sig'), filename=файл))
        module.__dict__['__походження__'] = self.спостерігач
        exec(compile(ast.fix_missing_locations(дерево), файл, 'exec'), module.__dict__)
