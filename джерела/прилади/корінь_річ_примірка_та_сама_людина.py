# -*- coding: utf-8 -*-
"""Лічить корінь «Річ-примірка-та-сама-людина» від споживачів значень.

Обхід рекурсивний: усі .py/.js/.html у джерела, крім тестів, проб, приладів,
стендів, лабораторії, залежностей і породженого вантажу. Python — ast, JS і
скрипти HTML — наявний Acorn (Node, без npm). Непрочитане — код 1.

Граф значень: лексичні імена, поля об'єктів, елементи масивів, аргументи,
повернення, callback, JSON-копія, IndexedDB, DOM. Замикання до нерухомої точки;
ключі полів розділені (картинка не забруднює фото/портрет того самого запису).
Умови й індекси консервативно об'єднуються; імена файлів та номери рядків
місць не є правилами приладу. Кожний споживач друкується з --докладно.

(а) Входи суду/виміру й мультимодальної моделі, до яких доходять пікселі
генератора. (б) Видимі src/srcset, HTML з img, canvas, до яких доходить кадр
генератора. Прихований Image для декодування та журнал — не показ жінці.
Вимір розміру кадру не є виміром її рис. Сам промпт — не суд і не показ.

Розпізнані джерела: відповідь модельП_блоки, inlineData/inline_data у відповіді
генератора, типові image-generation API Python/JS. Прозорі перетворення
фото зберігають походження на кожному виклику, не змішують виклики.
Тіла обгорток аналізуються; зовнішні API мають явні схеми перенесення байтів.
Оголошена функція з кількома місцями прямого виклику копіюється на кожне місце
(свої параметри, повернення й об'єкти): спільний декодер фото й генерації не
переносить походження генератора на фото.

Назва «маска» чи «повернути» та промпт не доводять повернення пікселів.
Пікселі генератора, скопійовані в результат, знімають місце лише з доведеним
контрактом повернення (клас Контракт): за структурою запису результату, де
маска ввімкнена — пікселі розкодованого кадру не з генератора, генератор —
лише поза нею чи в суміші з фото (шов). Семантики класів маски, вирівнювання
індексів і ширини шва прилад не доводить; недоведений контракт — місце.
Вкладені зображення визначаються схемами ПІКСЕЛІ; службові поля запису не
перетворюються на фото. Довільні прочитані поля все одно переносять значення.

Запуск: python джерела/прилади/корінь_річ_примірка_та_сама_людина.py
  [--корінь ШЛЯХ] [--докладно] [--json ФАЙЛ]
Останній рядок stdout — місць: N (різні файл:рядок), успіх — код 0.
"""
import argparse
import ast
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import subprocess
import sys

import обсяг_приладу as ОБСЯГ

НЕ_ТЕКИ = {'прилади', 'проби', 'лабораторія', 'node_modules', '__pycache__', '.git'}
НЕ_ПРЕФІКСИ = ('тест_', 'test_', 'стенд_', 'проба', 'build_', 'гейт', 'audit_', 'зібрано', 'показ_ПОВНИЙ')
НЕ_ІМЕНА = {'показ_зонд.html', 'досяжність.py', 'склад.py', 'таблиця_каталогу.py'}
ДЖЕРЕЛА = {'модельП_блоки', 'generate_image', 'generate_images', 'generateImage',
           'generateImages', 'text_to_image', 'image_to_image'}
ПРОЗОРІ = {'блобВБазу', '_блобВБазуЯкЄ', 'фотоДоСторониП', 'фотоДляЗапитуП',
           'урлФотоП', 'блокФотоП', 'пікселіРечіП', 'кадрРечіУрлП', 'зменшенаКопіяП',
           'розкодуватиФотоП', 'кадрФотоП', 'String', 'str', 'bytes', 'bytearray',
           'b64decode', 'b64encode', 'decode', 'encode', 'createObjectURL', 'createImageBitmap',
           'fetch', 'blob', 'arrayBuffer', 'stringify', 'parse', 'loads', 'dumps',
           'replace', 'replaceAll', 'slice', 'substring', 'trim', 'split', 'join', 'toString'}
# Декодування й кодування зображення: base64, байти, Blob, ImageData. Пікселі
# проходять крізь них, тож походження переноситься (чи байти — масив, масив
# масивів, чи значення напряму); ці місця самі нічого не знімають.
БАЙТИ_ТИПИ = {'Uint8Array', 'Uint8ClampedArray', 'Int8Array', 'Uint16Array', 'Int16Array', 'Uint32Array',
              'Int32Array', 'Float32Array', 'Float64Array', 'ArrayBuffer', 'DataView'}
КОНТЕЙНЕРИ = БАЙТИ_ТИПИ | {'Blob', 'File', 'ImageData'}
СКАЛЯРИ_З_АРГУМЕНТІВ = {'atob', 'btoa', 'fromCharCode', 'fromCodePoint', 'urlsafe_b64decode', 'urlsafe_b64encode'}
СКАЛЯРИ_З_ОДЕРЖУВАЧА = {'charCodeAt', 'codePointAt', 'getvalue'}
СУД = re.compile(r'суд|оцін|контраст|шкір|фігур|силует|облич|judge|assess|skin|figure|face|contrast', re.I)
НЕ_СУД = {'розмір_картинки', 'малюватиФотоОцінкиП', 'кінецьОцінкиП', 'збійОцінкиП',
          'оцінкаЗРозмовиП', 'оновитиРядокП', 'викликОцінкиП'}
ЧИСЛОВІ = {'width', 'height', 'length', 'size', 'ширина', 'висота', 'type', 'тип',
           'media_type', 'mime_type', 'ід', 'id', 'byteLength'}
# Мітки походження пікселів: кадр генератора, розкодований кадр, кадр після повернення.
МІТКИ = ('генератор:', 'пікселі:', 'повернено:')
ПІКСЕЛІ = {'*', 'data', 'дані', 'source', 'src', 'image', 'image_url', 'picture', 'photo',
           'картинка', 'фото', 'портрет', 'пікселі', 'пікселі_фото', 'rgb', 'rgba', 'pixels',
           'inlineData', 'inline_data', '@пікселі'}


def нащадки(в):
    """Без службових полів обходить безпосередні вузли ESTree."""
    if not isinstance(в, dict):
        return
    for к, з in в.items():
        if к == 'loc':
            continue
        for д in з if isinstance(з, list) else [з]:
            if isinstance(д, dict) and 'type' in д:
                yield д


def імʼя(в):
    """Ім'я виклику або ланцюжка атрибутів, без евристики за рядком коду."""
    if not isinstance(в, dict):
        return ''
    if в['type'] == 'Identifier':
        return в['name']
    if в['type'] == 'MemberExpression':
        return імʼя(в['object']) + '.' + str(ключ(в))
    return ''


def ключ(в):
    """Статичний ключ поля, невідомий індекс — *."""
    п = в['property']
    if not в.get('computed'):
        return п.get('name', '*')
    if п.get('type') == 'Literal':
        з = п.get('value')
        return '*' if isinstance(з, int) else str(з)
    return '*'


def вузол(тип, рядок=1, **поля):
    """Спільна форма вузла для Python та ESTree."""
    return dict(type=тип, loc={'start': {'line': рядок}}, **поля)


def пітон(в):
    """Перетворює AST Python у спільні операції потоку значень."""
    if в is None:
        return вузол('Literal', value=None)
    if isinstance(в, list):
        return [пітон(д) for д in в]
    н = getattr(в, 'lineno', 1)
    т = lambda тип, **п: вузол(тип, н, **п)
    if isinstance(в, ast.Module):
        return т('Program', body=пітон(в.body))
    if isinstance(в, ast.Name):
        return т('Identifier', name=в.id)
    if isinstance(в, ast.Constant):
        return т('Literal', value=в.value if isinstance(в.value, (str, int, float, bool, type(None))) else None)
    if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        тіло = пітон(в.body) if isinstance(в, ast.Lambda) else т('BlockStatement', body=пітон(в.body))
        return т('FunctionExpression' if isinstance(в, ast.Lambda) else 'FunctionDeclaration',
                 id=None if isinstance(в, ast.Lambda) else т('Identifier', name=в.name),
                 params=[т('Identifier', name=а.arg) for а in в.args.posonlyargs + в.args.args + в.args.kwonlyargs],
                 kwargs=в.args.kwarg.arg if в.args.kwarg else None,
                 body=тіло)
    if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)):
        цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
        return т('SequenceExpression', expressions=[т('VariableDeclarator', id=пітон(ц), init=пітон(в.value))
                 if isinstance(ц, ast.Name) else т('AssignmentExpression', left=пітон(ц), right=пітон(в.value)) for ц in цілі])
    if isinstance(в, ast.Attribute):
        return т('MemberExpression', object=пітон(в.value), property=т('Identifier', name=в.attr), computed=False)
    if isinstance(в, ast.Subscript):
        return т('MemberExpression', object=пітон(в.value), property=пітон(в.slice), computed=True)
    if isinstance(в, ast.Call):
        return т('CallExpression', callee=пітон(в.func), arguments=пітон(в.args),
                 keywords=[т('Property', key=т('Literal', value=к.arg), value=пітон(к.value)) for к in в.keywords])
    if isinstance(в, ast.Dict):
        return т('ObjectExpression', properties=[т('SpreadElement', argument=пітон(з)) if к is None else
                 т('Property', key=пітон(к), value=пітон(з), computed=False) for к, з in zip(в.keys, в.values)])
    if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
        return т('ArrayExpression', elements=пітон(в.elts))
    if isinstance(в, (ast.For, ast.AsyncFor, ast.comprehension)):
        return т('ForOfStatement', left=пітон(в.target), right=пітон(в.iter), body=т('BlockStatement', body=пітон(getattr(в, 'body', []))))
    if isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
        генератори = [пітон(г) for г in в.generators]
        значення = пітон(в.value if isinstance(в, ast.DictComp) else в.elt)
        return т('Comprehension', generators=генератори, value=значення)
    if isinstance(в, ast.Return):
        return т('ReturnStatement', argument=пітон(в.value))
    if isinstance(в, ast.Import):
        return т('Program', body=[т('ImportBinding', local=а.asname or а.name.split('.')[0], module=а.name.split('.')[0], imported=None) for а in в.names])
    if isinstance(в, ast.ImportFrom):
        return т('Program', body=[т('ImportBinding', local=а.asname or а.name, module=в.module or '', imported=а.name) for а in в.names])
    if isinstance(в, ast.IfExp):
        return т('ConditionalExpression', test=пітон(в.test), consequent=пітон(в.body), alternate=пітон(в.orelse))
    if isinstance(в, (ast.BinOp, ast.BoolOp, ast.JoinedStr, ast.FormattedValue)):
        return т('SequenceExpression', expressions=[пітон(д) for д in ast.iter_child_nodes(в)])
    # Умови не передають пікселів у значення; їхні вкладені виклики все ж обходимо.
    return т('Other', children=[пітон(д) for д in ast.iter_child_nodes(в)])


@dataclass
class Вхід:
    """Одна точка суду або можливого показу, незалежно від походження кадру."""
    файл: str
    рядок: int
    умова: str
    значення: tuple
    опис: str
    обʼєкт: int = 0


class Розмітка(HTMLParser):
    """Обліковує статичні img/canvas та їхні id окремо від JS-рядків."""

    def __init__(self):
        super().__init__()
        self.зображення, self.полотна, self.входи = set(), set(), []
        self.елементи = []

    def handle_starttag(self, tag, attrs):
        """Називає кожний статичний вхід показу у вихідному HTML."""
        а = dict(attrs)
        if tag in {'img', 'canvas'}:
            self.елементи.append((tag, а))
            if а.get('id'):
                (self.зображення if tag == 'img' else self.полотна).add(а['id'])
            self.входи.append((self.getpos()[0], tag))


def відповідає_селектору(селектор, тег, атрибути):
    """Консервативно зіставляє ціль селектора з елементом HTML."""
    def розкодувати(збіг):
        код = збіг.group(1)
        if re.fullmatch(r'[0-9a-fA-F]{1,6}\s?', код):
            число = int(код.strip(), 16)
            return chr(число) if 0 < число <= 0x10ffff else '\ufffd'
        return код
    селектор = re.sub(r'\\([0-9a-fA-F]{1,6}\s?|[^\n\r\f0-9a-fA-F])', розкодувати, селектор)
    for частина in селектор.split(','):
        частини, буфер, глибина = [], '', 0
        for знак in частина:
            if знак in '[(':
                глибина += 1
            elif знак in '])':
                глибина = max(0, глибина - 1)
            if not глибина and (знак.isspace() or знак in '>+~'):
                if буфер:
                    частини.append(буфер)
                    буфер = ''
            else:
                буфер += знак
        if буфер:
            частини.append(буфер)
        if not частини:
            continue
        кінцева = re.sub(r':[\w-]+(?:\([^)]*\))?', '', частини[-1])
        тип = re.match(r'^([\w-]+|\*)', кінцева)
        if тип and тип.group(1).lower() not in {'*', тег}:
            continue
        без_атрибутів = re.sub(r'\[[^]]*\]', '', кінцева)
        ід = re.findall(r'#([\w-]+)', без_атрибутів)
        класи = re.findall(r'\.([\w-]+)', без_атрибутів)
        if any(атрибути.get('id') != з for з in ід):
            continue
        if any(з not in (атрибути.get('class') or '').split() for з in класи):
            continue
        if any(назва not in атрибути for назва in re.findall(r'\[\s*([\w-]+)', кінцева)):
            continue
        return True
    return False


class Граф:
    """Скінченний граф включень з полями й викликами до нерухомої точки."""

    def __init__(self):
        self.знач = [set()]
        self.поля = defaultdict(set)
        self.ребра, self.читання, self.записи, self.виклики = set(), set(), set(), []
        self.функції, self.оточення, self.батьки = {}, [dict()], [None]
        self.входи, self.видимі, self.зображення, self.полотна = [], set(), set(), set()
        self.дом, self.сховища, self.резолвери = self.нове(True), {}, {}
        self.модулі = {}
        self.файл = ''
        self.кроків = 0
        self.кеш_вузлів = {}
        self.дерева = []
        self.елементи_викликів = {}
        self.символічні = {}
        self.символічні_поля = {}
        self.вибір_типу = {}
        self.ід_зображень, self.ід_полотен = set(), set()
        self.html_елементи = []
        self.розпаковані_поля = {}
        self.означення = {}
        self.застосування = set()
        self.імена_параметрів = {}
        self.kwargs_параметри = {}
        self.kwargs_викликів = {}
        self.іменовані_виклики = {}
        self.скалярні = set()
        self.джерела_функцій = set()
        self.адреси_викликів = {}
        self.адреси_вузлів = {}
        self.передачі = {}
        self.обробляється = None
        self.види = {}
        self.читання_кешу = defaultdict(list)
        self.копії = set()
        # Копія оголошеної функції на кожне місце прямого виклику: спільний
        # декодер для фото й для генерації не зливає їхніх пікселів (13426).
        self.декларації, self.клони, self.тексти_клонів = {}, {}, []
        self.викликів_імені = Counter()
        # Контракт повернення: вузли кожної операції AST у всіх копіях функції;
        # доведені записи результату (id присвоєння → мітка) — з першого проходу.
        self.вузли_ast = defaultdict(set)
        self.доведені = {}

    def лічити_виклики(self, дерево):
        """Скільки прямих викликів має кожне ім'я: функцію з одним місцем не копіюємо."""
        край = [дерево]
        while край:
            д = край.pop()
            if д.get('type') in {'CallExpression', 'NewExpression'} and д['callee'].get('type') == 'Identifier':
                self.викликів_імені[д['callee']['name']] += 1
            край.extend(нащадки(д))

    def нове(self, обʼєкт=False):
        """Виділяє вузол; об'єкт має власну ідентичність для записів у поля."""
        н = len(self.знач)
        self.знач.append({н} if обʼєкт else set())
        return н

    def звʼязати(self, з, до):
        """Додає спрямований потік значення."""
        if з and до and з != до:
            self.ребра.add((з, до))

    def змінна(self, назва, с, оголосити=False):
        """Лексичне ім'я; window.x відповідає глобальному x."""
        де = с
        if not оголосити:
            while назва not in self.оточення[де] and self.батьки[де] is not None:
                де = self.батьки[де]
        if назва not in self.оточення[де]:
            self.оточення[де][назва] = self.нове(self.батьки[де] is None)
            if self.батьки[де] is None:
                в = self.оточення[де][назва]
                self.символічні[в] = в
                if назва in ДЖЕРЕЛА - {'модельП_блоки'}:
                    self.джерела_функцій.add(в)
        return self.оточення[де][назва]

    def поле(self, обʼєкт, к):
        """Додає читання поля; * означає невідомий індекс масиву/словника."""
        вих = self.нове(False)
        if обʼєкт in self.символічні:
            о = self.символічні[обʼєкт]
            адреса = (о, '*' if isinstance(к, tuple) else к)
            if адреса not in self.символічні_поля:
                self.символічні_поля[адреса] = self.нове(True)
            дитина = self.символічні_поля[адреса]
            self.поля[адреса].add(дитина)
            self.символічні[вих] = дитина
        self.читання.add((вих, обʼєкт, к))
        return вих

    def запис(self, обʼєкт, к, значення):
        """Додає запис конкретного поля, не забруднює сусідні поля."""
        self.записи.add((обʼєкт, к, значення))

    def ключ_вузла(self, в, с):
        """Ключ з масиву імен має дочекатися значення індексу, зокрема порожнього callback."""
        if в.get('computed') and в['property']['type'] != 'Literal':
            return ('ключ', self.вираз(в['property'], с))
        return ключ(в)

    def звʼязати_ціль(self, в, с, з):
        """Присвоює ім'я, поле або деструктурований шаблон."""
        if not в:
            return
        т = в['type']
        if т == 'Identifier':
            self.звʼязати(з, self.змінна(в['name'], с))
        elif т == 'MemberExpression':
            if імʼя(в['object']) in {'window', 'globalThis'}:
                self.звʼязати(з, self.змінна(ключ(в), 0))
            else:
                б = self.вираз(в['object'], с)
                self.запис(б, self.ключ_вузла(в, с), з)
                if ключ(в) in {'src', 'srcset', 'innerHTML', 'outerHTML'}:
                    self.входи.append(Вхід(self.файл, в['loc']['start']['line'], 'б', (з,), 'запис ' + ключ(в), б))
        elif т in {'ArrayPattern', 'ArrayExpression'}:
            for д in в.get('elements', []):
                self.звʼязати_ціль(д, с, self.поле(з, '*'))
        elif т in {'ObjectPattern', 'ObjectExpression'}:
            for п in в.get('properties', []):
                к = п.get('key', {})
                self.звʼязати_ціль(п.get('value', п.get('argument')), с,
                                  self.поле(з, str(к.get('name', к.get('value', '*')))))
        elif т in {'RestElement', 'AssignmentPattern'}:
            self.звʼязати_ціль(в.get('argument', в.get('left')), с, з)

    def оголосити(self, в, с):
        """Завчасно оголошує локальні імена, не входячи в дочірню функцію."""
        т = в['type']
        if т in {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}:
            if т == 'FunctionDeclaration' and в.get('id'):
                self.декларації[self.змінна(в['id']['name'], с, True)] = (в, с, self.файл)
            return
        if т == 'VariableDeclarator':
            def імена(п):
                if not п:
                    return
                if п['type'] == 'Identifier':
                    self.змінна(п['name'], с, True)
                else:
                    for д in нащадки(п):
                        імена(д.get('value', д) if д['type'] == 'Property' else д)
            імена(в['id'])
        if т == 'ImportBinding':
            self.змінна(в['local'], с, True)
        for д in нащадки(в):
            self.оголосити(д, с)

    def вираз(self, в, с=0, повернення=0):
        """Кожна операція AST потрапляє в граф один раз на лексичне оточення."""
        if not isinstance(в, dict):
            return 0
        к = (id(в), с, повернення)
        if к not in self.кеш_вузлів:
            self.кеш_вузлів[к] = self._вираз(в, с, повернення)
            р = self.кеш_вузлів[к]
            self.вузли_ast[id(в)].add(р)
            if р:
                self.адреси_вузлів.setdefault(р, f"{self.файл}:{в.get('loc', {}).get('start', {}).get('line', 1)} {в['type']} {в.get('name', '')}")
        return self.кеш_вузлів[к]

    def _вираз(self, в, с=0, повернення=0):
        """Будує потоки ESTree, включно з усіма тілами й альтернативами."""
        if not isinstance(в, dict):
            return 0
        т = в['type']
        н = в.get('loc', {}).get('start', {}).get('line', 1)
        if т == 'Identifier':
            return self.змінна(в['name'], с)
        if т == 'Literal':
            р = self.нове(False)
            з = в.get('value')
            if isinstance(з, str):
                if len(з) < 180:
                    self.знач[р].add('рядок:' + з)
                if re.search(r'<(?:img|canvas)\b', з, re.I):
                    self.знач[р].add('розмітка:зображення')
            elif isinstance(з, (int, float, bool)):
                self.знач[р].add('число:' + str(з))
            return р
        if т in {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}:
            return self.функція(в, с)
        if т == 'VariableDeclarator':
            з = self.вираз(в.get('init'), с)
            self.звʼязати_ціль(в['id'], с, з)
            return з
        return self._вираз_далі(в, с, повернення, т, н)

    def клон(self, змінна, виклик):
        """Копія оголошеної функції для одного місця виклику (1-CFA): свої параметри,
        повернення й виділення об'єктів; рекурсія повертає вже початий клон."""
        к = (id(виклик), змінна)
        if к not in self.клони:
            оголошення, с, файл = self.декларації[змінна]
            # Тіло копії належить файлу оголошення, не файлу виклику.
            було, self.файл = self.файл, файл
            self.функція(оголошення, с, к)
            self.файл = було
        return self.клони[к]

    def функція(self, в, с, клон=None):
        """Значення функції; клон не прив'язується до імені оголошення."""
        т = в['type']
        р = self.нове(True)
        if клон is not None:
            self.клони[клон] = р
        нов = len(self.оточення)
        self.оточення.append({})
        self.батьки.append(с)
        параметри = []
        for п in в.get('params', []):
            пв = self.нове()
            # Оголошення параметрів потрібне до зв'язування, інакше це глобальне ім'я.
            def локальні(д):
                if д['type'] == 'Identifier':
                    self.змінна(д['name'], нов, True)
                else:
                    for ч in нащадки(д):
                        локальні(ч.get('value', ч) if ч['type'] == 'Property' else ч)
            локальні(п)
            self.звʼязати_ціль(п, нов, пв)
            параметри.append(пв)
        пов = self.нове()
        self.функції[р] = (параметри, пов)
        self.імена_параметрів[р] = {п['name']: пв for п, пв in zip(в.get('params', []), параметри) if п['type'] == 'Identifier'}
        if в.get('kwargs'):
            self.kwargs_параметри[р] = self.змінна(в['kwargs'], нов, True)
        self.оголосити(в['body'], нов)
        з = self.вираз(в['body'], нов, пов)
        if в['body']['type'] != 'BlockStatement':
            self.звʼязати(з, пов)
        if т == 'FunctionDeclaration' and в.get('id') and клон is None:
            self.звʼязати(р, self.змінна(в['id']['name'], с))
            self.означення[в['id']['name']] = в['body']
        return р

    def _вираз_далі(self, в, с, повернення, т, н):
        """Решта операцій ESTree після функцій і оголошень."""
        if т == 'AssignmentExpression':
            з = self.вираз(в['right'], с)
            if id(в) in self.доведені:
                # Запис результату, для якого перший прохід довів контракт повернення:
                # у результат іде мітка повернення, а не пікселі генератора (див. Контракт).
                з = self.нове()
                self.знач[з].add('повернено:' + self.доведені[id(в)])
            self.звʼязати_ціль(в['left'], с, з)
            return з
        if т == 'MemberExpression':
            if імʼя(в['object']) in {'window', 'globalThis'}:
                return self.змінна(ключ(в), 0)
            б = self.вираз(в['object'], с)
            if ключ(в) in {'inlineData', 'inline_data'}:
                # Це двійковий блок відповіді; запит inline_data сам не є генератором.
                р = self.поле(б, ключ(в))
                return р
            return self.поле(б, self.ключ_вузла(в, с))
        if т in {'ObjectExpression', 'ArrayExpression'}:
            р = self.нове(True)
            if т == 'ArrayExpression':
                for д in в.get('elements', []):
                    if д:
                        self.запис(р, '*', self.вираз(д, с))
            else:
                for п in в.get('properties', []):
                    if п['type'] == 'SpreadElement':
                        self.копії.add((self.вираз(п['argument'], с), р))
                    else:
                        к = п['key']
                        к = '*' if п.get('computed') else str(к.get('name', к.get('value', '*')))
                        self.запис(р, к, self.вираз(п['value'], с))
            return р
        if т in {'CallExpression', 'NewExpression'}:
            назва = імʼя(в['callee'])
            ім = назва.rsplit('.', 1)[-1]
            б = self.вираз(в['callee']['object'], с) if в['callee']['type'] == 'MemberExpression' else 0
            функ = 0
            if в['callee']['type'] == 'Identifier' and self.викликів_імені[назва] > 1:
                змінна = self.змінна(назва, с)
                if змінна in self.декларації:
                    функ = self.клон(змінна, в)
            функ = функ or self.вираз(в['callee'], с)
            арг = tuple(self.вираз(а, с) for а in в.get('arguments', []))
            р = self.нове(ім in {'ел', 'createElement', '$', 'querySelector', 'querySelectorAll', 'getElementById',
                                  'Image', 'Promise', 'Map', 'Set', 'map', 'flatMap', 'getAll', 'get', 'json', 'містП', 'модельП_блоки'} | БАЙТИ_ТИПИ)
            if ім in {'find', 'filter'} and в.get('arguments'):
                край = [в['arguments'][0]]
                while край:
                    д = край.pop()
                    if д.get('type') == 'BinaryExpression' and д.get('operator') in {'===', '=='}:
                        л, п = д['left'], д['right']
                        if л.get('type') == 'MemberExpression' and ключ(л) == 'type' and п.get('value') in {'image', 'text'}:
                            self.вибір_типу[р] = п['value']
                    край.extend(нащадки(д))
            self.виклики.append((р, функ, б, ім, назва, арг, self.файл, н))
            self.адреси_викликів[р] = f'{self.файл}:{н}'
            self.іменовані_виклики[р] = tuple((к['key']['value'], self.вираз(к['value'], с)) for к in в.get('keywords', []))
            if ім == 'setAttribute' and б and len(арг) >= 2:
                ключ_атрибута = в['arguments'][0].get('value')
                if isinstance(ключ_атрибута, str):
                    self.запис(б, ключ_атрибута, арг[1])
            if (ім in {'add', 'toggle', 'replace'} and арг and
                    в['callee']['type'] == 'MemberExpression' and
                    в['callee']['object']['type'] == 'MemberExpression' and
                    ключ(в['callee']['object']) == 'classList'):
                елемент = self.вираз(в['callee']['object']['object'], с)
                for а in арг:
                    self.запис(елемент, 'className', а)
            if self.іменовані_виклики[р]:
                словник = self.нове(True)
                self.kwargs_викликів[р] = словник
                for назва_аргументу, а in self.іменовані_виклики[р]:
                    if назва_аргументу is None:
                        self.копії.add((а, словник))
                    else:
                        self.запис(словник, назва_аргументу, а)
            if ім in {'модельП', 'викликОцінкиП'}:
                кадри = арг[1:2] if ім == 'модельП' else арг[2:3]
                self.входи.append(Вхід(self.файл, н, 'а', кадри, 'фото в ' + ім))
            elif (СУД.search(ім) and ім not in НЕ_СУД and not ім.startswith(('малювати', 'записати', 'показати'))):
                self.входи.append(Вхід(self.файл, н, 'а', арг + tuple(з for _, з in self.іменовані_виклики[р]), 'вхід ' + назва))
            elif ім == 'містП' and в.get('arguments'):
                е = в['arguments'][0].get('value')
                if е in {'оцінка', 'річ_фото', 'палітра', 'силует'}:
                    self.входи.append(Вхід(self.файл, н, 'а', арг[1:], 'міст ' + е))
            if ім in {'розміткаЖінціП', 'insertAdjacentHTML', 'write'}:
                self.входи.append(Вхід(self.файл, н, 'б', арг[1:] if ім != 'write' else арг, 'HTML зображення'))
            if ім in {'drawImage', 'putImageData'}:
                self.входи.append(Вхід(self.файл, н, 'б', арг[:1], 'canvas ' + ім, б))
            if ім == 'setAttribute' and в.get('arguments', [{}])[0].get('value') in {'src', 'srcset'}:
                self.входи.append(Вхід(self.файл, н, 'б', арг[1:2], 'атрибут src', б))
            return р
        if т in {'ReturnStatement', 'YieldExpression'}:
            р = self.вираз(в.get('argument'), с)
            self.звʼязати(р, повернення)
            return р
        if т in {'ForOfStatement', 'ForInStatement'}:
            з = self.поле(self.вираз(в['right'], с), '*')
            л = в['left']
            if л['type'] == 'VariableDeclaration':
                л = л['declarations'][0]['id']
            self.звʼязати_ціль(л, с, з)
            return self.вираз(в['body'], с, повернення)
        if т == 'Comprehension':
            for г in в['generators']:
                self.вираз(г, с)
            р = self.нове(True)
            self.запис(р, '*', self.вираз(в['value'], с))
            return р
        if т == 'ImportBinding':
            м = self.модулі.setdefault(в['module'], self.нове(True))
            з = self.поле(м, в['imported']) if в['imported'] else м
            self.звʼязати(з, self.змінна(в['local'], с))
            return з
        if т in {'BinaryExpression', 'LogicalExpression', 'ConditionalExpression', 'SequenceExpression', 'TemplateLiteral', 'AwaitExpression', 'ChainExpression', 'SpreadElement', 'AssignmentPattern'}:
            р = self.нове(False)
            if т in {'BinaryExpression', 'TemplateLiteral'}:
                self.знач[р].add('ключ:невідомий')
            for к, д in ((к, д) for к, з in в.items() for д in (з if isinstance(з, list) else [з]) if isinstance(д, dict) and 'type' in д):
                з = self.вираз(д, с, повернення)
                if к != 'test' and в.get('operator') not in {'===', '!==', '==', '!=', '<', '>', '<=', '>='}:
                    self.звʼязати(з, р)
            return р
        # Конструкції керування не зливають значення умови з результатом.
        for д in нащадки(в):
            self.вираз(д, с, повернення)
        return 0

    def до_функції(self, функ, арг, вих, умова=0, іменовані=()):
        """Параметри й повернення для можливих адресатів виклику."""
        self.застосування.add((функ, tuple(арг), вих, умова, іменовані))
        if умова:
            return
        for ф in tuple(self.знач[функ]):
            if ф in self.функції:
                параметри, пов = self.функції[ф]
                for а, п in zip(арг, параметри):
                    self.звʼязати(а, п)
                for ім, а in іменовані:
                    if ім in self.імена_параметрів[ф]:
                        self.звʼязати(а, self.імена_параметрів[ф][ім])
                    elif ім is None:
                        for назва, п in self.імена_параметрів[ф].items():
                            self.звʼязати(self.розпаковані_поля[а, назва], п)
                if ф in self.kwargs_параметри and вих in self.kwargs_викликів:
                    self.звʼязати(self.kwargs_викликів[вих], self.kwargs_параметри[ф])
                self.звʼязати(пов, вих)
            if ф in self.резолвери and арг:
                self.звʼязати(арг[0], self.резолвери[ф])

    def замкнути(self):
        """Замикає присвоєння, поля, виклики й відомі транспортні API."""
        # Прозорий транспорт, який став генератором (навіть через обгортку),
        # втрачає транспортний контракт: аналізуємо його справжнє повернення.
        генерують = set(ДЖЕРЕЛА)
        звʼязки = {}
        for назва, тіло in self.означення.items():
            край, виклики = [тіло], set()
            while край:
                д = край.pop()
                if д.get('type') == 'CallExpression':
                    виклики.add(імʼя(д['callee']).rsplit('.', 1)[-1])
                край.extend(нащадки(д))
            звʼязки[назва] = виклики
        було = -1
        while було != len(генерують):
            було = len(генерують)
            генерують.update(ім for ім, вв in звʼязки.items() if вв & генерують)
        прозорі = ПРОЗОРІ - генерують
        # Читання **kwargs створюємо до індексу й розв'язання викликів.
        назви = {н for мапа in self.імена_параметрів.values() for н in мапа}
        for пари in self.іменовані_виклики.values():
            for ім, об in пари:
                if ім is None:
                    for назва in назви:
                        self.розпаковані_поля[об, назва] = self.поле(об, назва)
        попередники = defaultdict(set)
        for з, до in self.ребра:
            попередники[до].add(з)

        def сталі_рядки(вузол):
            """Знаходить сталі через присвоєння до замикання графа."""
            черга, бачені, рядки = [вузол], set(), set()
            while черга:
                н = черга.pop()
                if н in бачені:
                    continue
                бачені.add(н)
                рядки.update(з[6:] for з in self.знач[н] if isinstance(з, str) and з.startswith('рядок:'))
                черга.extend(попередники[н] - бачені)
            return рядки
        # Розклад сталих native-операцій будуємо лише раз.
        for р, функ, б, ім, назва, арг, файл, н in self.виклики:
            if ім == 'Map':
                self.види[р] = 'мапа'
            if ім == 'модельП_блоки':
                блок, дані = self.нове(True), self.нове(True)
                self.поля[р, '*'].add(блок)
                self.поля[блок, 'type'].add('рядок:image')
                self.поля[блок, 'source'].add(дані)
                self.поля[дані, 'data'].add(f'генератор:{файл}:{н}')
                текст = self.нове(True)
                self.поля[р, '*'].add(текст)
                self.поля[текст, 'type'].add('рядок:text')
            elif ім in ДЖЕРЕЛА or назва.endswith(('images.generate', 'images.edit')):
                self.знач[р].add(f'генератор:{файл}:{н}')
            elif ім in {'блобВБазу', '_блобВБазуЯкЄ', 'зменшенаКопіяП'} and арг and ім in прозорі:
                # FileReader читає байти Blob/URL, не поле «картинка» довільного
                # службового запису, який нечутливий до ключів IndexedDB граф
                # міг приєднати до того самого читача.
                self.знач[р].add(р)
                байти = self.нове()
                self.скалярні.add((арг[0], байти))
                self.запис(р, 'дані', байти)
            elif ім in {'фотоДоСторониП', 'пікселіРечіП', 'урлФотоП', 'кадрРечіУрлП', 'блокФотоП', 'фотоДляЗапитуП'} and арг and ім in прозорі:
                вхід = self.поле(арг[0], '*') if ім == 'фотоДляЗапитуП' else арг[0]
                байти = self.поле(вхід, 'дані')
                if ім in {'урлФотоП', 'кадрРечіУрлП'}:
                    self.звʼязати(байти, р)
                else:
                    self.знач[р].add(р)
                    if ім == 'фотоДляЗапитуП':
                        фото = self.нове(True)
                        self.запис(р, '*', фото)
                        self.запис(фото, 'дані', байти)
                    elif ім == 'блокФотоП':
                        дж = self.нове(True)
                        self.запис(р, 'source', дж)
                        self.запис(дж, 'data', байти)
                    else:
                        self.запис(р, 'дані', байти)
            elif ім in {'String', 'str', 'toString', 'createObjectURL'}:
                if б and ім == 'toString':
                    self.скалярні.add((б, р))
                elif арг:
                    self.скалярні.add((арг[0], р))
            elif ім in КОНТЕЙНЕРИ and арг:
                # Байти — масив, масив масивів чи значення напряму (`[байти]`, `new Blob(частини)`).
                перший = арг[0]
                шар = self.поле(перший, '*')
                self.звʼязати(перший, р)
                self.звʼязати(шар, р)
                self.звʼязати(self.поле(шар, '*'), р)
                if ім in БАЙТИ_ТИПИ:
                    self.запис(р, '*', перший)
                    self.запис(р, '*', шар)
            elif ім in СКАЛЯРИ_З_АРГУМЕНТІВ:
                for а in арг:
                    self.звʼязати(а, р)
            elif ім in СКАЛЯРИ_З_ОДЕРЖУВАЧА and б:
                self.звʼязати(б, р)
            elif ім in прозорі:
                for з in ((б,) if б and ім in {'replace', 'replaceAll', 'slice', 'substring', 'trim', 'split', 'join', 'toString', 'blob', 'arrayBuffer', 'decode', 'encode'} else арг[:1]):
                    self.звʼязати(з, р)
            elif ім in {'ел', 'createElement', '$', 'querySelector', 'querySelectorAll', 'getElementById', 'Image'}:
                if ім == 'Image':
                    self.зображення.add(р)
                elif арг:
                    текст = сталі_рядки(арг[0])
                    селектори = ім in {'$', 'querySelector', 'querySelectorAll'}
                    теги = {тег for селектор in текст for тег, атрибути in self.html_елементи
                            if селектори and відповідає_селектору(селектор, тег, атрибути)}
                    if текст & {'img', 'IMG'} or текст & self.ід_зображень or 'img' in теги:
                        self.зображення.add(р)
                    if текст & {'canvas', 'CANVAS'} or текст & self.ід_полотен or 'canvas' in теги:
                        self.полотна.add(р)
                    if ім == 'querySelectorAll':
                        self.запис(р, '*', р)
                if ім in {'$', 'querySelector', 'querySelectorAll', 'getElementById'}:
                    self.видимі.add(р)
                    if р in self.зображення:
                        self.звʼязати(self.дом, р)
            elif ім in {'розміткаЖінціП', 'insertAdjacentHTML'} and len(арг) > 1:
                self.запис(self.дом, 'src', арг[1])
            elif ім == 'getContext' and б:
                self.звʼязати(б, р)
            elif ім == 'Promise' and арг:
                рез = self.нове(True)
                self.резолвери[рез] = р
                self.до_функції(арг[0], (рез,), 0)
            elif ім == 'assign' and арг:
                self.звʼязати(арг[0], р)
                for з in арг[1:]:
                    self.копії.add((з, арг[0]))
            elif ім in {'getImageData', 'toDataURL', 'toBlob'} and б:
                self.звʼязати(self.поле(б, '@пікселі'), р)
                if ім == 'getImageData':
                    # Розкодовані пікселі зображення: доказ, що джерело — кадр, а не стала.
                    self.знач[р].add(f'пікселі:{файл}:{н}')
            elif ім in {'drawImage', 'putImageData'} and б and арг:
                self.запис(б, '@пікселі', арг[0])
            elif ім == 'objectStore' and арг:
                к = tuple(sorted(str(з) for з in self.знач[арг[0]] if isinstance(з, str)))
                сх = self.сховища.setdefault(к, self.нове(True))
                self.види[сх] = 'сховище'
                self.звʼязати(сх, р)
            elif ім == 'tx' and len(арг) >= 4:
                к = tuple(sorted(str(з) for з in self.знач[арг[1]] if isinstance(з, str)))
                сх = self.сховища.setdefault(к, self.нове(True))
                self.види[сх] = 'сховище'
                self.до_функції(арг[3], (сх,), р)
            elif ім == 'get' and б:
                кк = {з[6:] for з in self.знач[арг[0]] if isinstance(з, str) and з.startswith('рядок:')} if арг else set()
                self.читання_кешу[б].append((р, кк))
            elif ім == 'getAll' and б:
                збережене = self.поле(б, '@збережене')
                масив = self.нове(True)
                self.запис(масив, '*', збережене)
                self.запис(р, 'result', масив)
            elif ім in {'put', 'set'} and б and арг:
                self.запис(б, '@збережене', арг[-1] if ім == 'set' else арг[0])
                if ім == 'set' and len(арг) >= 2:
                    пара = self.нове(True)
                    for а in арг[:2]:
                        self.запис(пара, '*', а)
                    self.запис(б, '*', пара)
            elif ім == 'setAttribute' and б and len(арг) >= 2:
                if 'рядок:src' in self.знач[арг[0]]:
                    self.запис(б, 'src', арг[1])

        фільтри = defaultdict(list)
        for р, функ, б, ім, назва, арг, файл, н in self.виклики:
            if ім in {'appendChild', 'append', 'prepend', 'replaceChild', 'replaceChildren'}:
                for а in арг[:1]:
                    self.видимі.update(з for з in self.знач[а] if isinstance(з, int))
            if ім in {'push', 'append', 'extend', 'unshift'} and б:
                for а in арг:
                    self.запис(б, '*', а)
            elif ім in {'map', 'flatMap', 'forEach', 'filter', 'find', 'some', 'every'} and б and арг:
                # Одна адреса операції читання на виклик, не нова на кожне коло.
                if р not in self.елементи_викликів:
                    self.елементи_викликів[р] = (self.поле(б, '*'), self.нове(), self.нове())
                всі, повернене, ел = self.елементи_викликів[р]
                індекс = self.нове()
                self.знач[індекс].add('число:0')
                if р in self.вибір_типу:
                    фільтри[всі].append((ел, self.вибір_типу[р]))
                else:
                    self.звʼязати(всі, ел)
                if ім in {'map', 'flatMap'}:
                    self.до_функції(арг[0], (ел, індекс), повернене, ел)
                    self.запис(р, '*', повернене)
                else:
                    self.до_функції(арг[0], (ел, індекс), 0, ел)
                    if ім == 'find':
                        self.звʼязати(ел, р)
                    elif ім == 'filter':
                        self.знач[р].add(р)
                        self.запис(р, '*', ел)
            elif ім == 'concat' and б:
                self.звʼязати(б, р)
                for а in арг:
                    self.звʼязати(а, р)
            elif ім == 'then' and б and арг:
                self.до_функції(арг[0], (б,), р)
            elif ім not in ДЖЕРЕЛА | прозорі | {'модельП', 'викликОцінкиП', 'блокиВТекст', 'розміткаЖінціП', 'ел', 'createElement', '$', 'querySelector', 'getElementById', 'getContext', 'Promise', 'assign', 'objectStore', 'tx'}:
                self.до_функції(функ, арг, р, іменовані=self.іменовані_виклики[р])
        додавання = defaultdict(list)
        for _, _, _, ім, _, арг, _, _ in self.виклики:
            if ім in {'appendChild', 'append', 'prepend', 'replaceChild', 'replaceChildren'} and арг:
                додавання[арг[0]].append(True)
        читачі, писачі, викличі = defaultdict(list), defaultdict(list), defaultdict(list)
        скалярні = defaultdict(list)
        for з, до in self.скалярні:
            скалярні[з].append(до)
        for вих, б, к in self.читання:
            читачі[б].append((вих, к))
        for б, к, з in self.записи:
            писачі[б].append((к, з))
        ключові, умовні = defaultdict(list), defaultdict(list)
        for вих, б, к in self.читання:
            if isinstance(к, tuple):
                ключові[к[1]].append(('читати', вих, б))
        for б, к, значення in self.записи:
            if isinstance(к, tuple):
                ключові[к[1]].append(('писати', значення, б))
        for ф, арг, вих, умова, іменовані in self.застосування:
            викличі[ф].append((арг, вих, умова, іменовані))
            if умова:
                умовні[умова].append((ф, арг, вих, іменовані))
        наступні = defaultdict(set)
        for з, до in self.ребра:
            наступні[з].add(до)
        черга, очікує = deque(), defaultdict(set)
        def додати(до, значення, звідки=None):
            нові = set(значення) - self.знач[до]
            if нові:
                for з in нові:
                    if isinstance(з, str) and з.startswith('генератор:'):
                        self.передачі[до, з] = звідки if звідки is not None else self.обробляється
                self.знач[до].update(нові)
                if not очікує[до]:
                    черга.append(до)
                очікує[до].update(нові)
        def ребро(з, до):
            if з and до and з != до and до not in наступні[з]:
                наступні[з].add(до)
                додати(до, self.знач[з], з)
        адреси, поля_обʼєкта, усі_читачі = {}, defaultdict(set), defaultdict(set)
        копії_обʼєктів, ключі_обʼєктів = defaultdict(set), defaultdict(set)
        копії_джерела, копії_цілі = defaultdict(set), defaultdict(set)
        for з, до in self.копії:
            копії_джерела[з].add(до)
            копії_цілі[до].add(з)
        def поле(о, к):
            адреса = (о, к)
            if адреса not in адреси:
                в = self.нове()
                адреси[адреса] = в
                ключі_обʼєктів[о].add(к)
                self.адреси_вузлів[в] = self.адреси_вузлів.get(о, str(о)) + ' поле ' + к
                поля_обʼєкта[о].add(в)
                for вих in усі_читачі[о]:
                    ребро(в, вих)
                for до in tuple(копії_обʼєктів[о]):
                    ребро(в, поле(до, к))
            return адреси[адреса]
        def копіювати(джерела, цілі):
            for з in джерела:
                for до in цілі:
                    if isinstance(з, int) and isinstance(до, int) and з != до and до not in копії_обʼєктів[з]:
                        копії_обʼєктів[з].add(до)
                        for к in tuple(ключі_обʼєктів[з]):
                            ребро(поле(з, к), поле(до, к))
        for (о, к), значення in tuple(self.поля.items()):
            додати(поле(о, к), значення)
        for з, значення in enumerate(self.знач):
            if значення:
                if not очікує[з]:
                    черга.append(з)
                очікує[з].update(значення)
        for о in self.видимі & self.зображення:
            ребро(поле(о, 'src'), поле(self.дом, 'src'))
        def імена_ключа(к):
            if not isinstance(к, tuple):
                return {к}
            значення = self.знач[к[1]]
            if any(isinstance(з, str) and (з.startswith('число:') or з == 'ключ:невідомий') for з in значення):
                return {'*'}
            return {з[6:] for з in значення if isinstance(з, str) and з.startswith('рядок:')}
        def читати(вих, обʼєкти, ключі):
            for к in ключі:
                for о in обʼєкти:
                    if isinstance(о, str):
                        if о.startswith(МІТКИ) and к not in ЧИСЛОВІ:
                            додати(вих, [о])
                    elif к == '*':
                        усі_читачі[о].add(вих)
                        for в in tuple(поля_обʼєкта[о]):
                            ребро(в, вих)
                    else:
                        ребро(поле(о, к), вих)
        def писати(значення, обʼєкти, ключі):
            for к in ключі:
                for о in обʼєкти:
                    if isinstance(о, int):
                        ребро(значення, поле(о, к))
        def викликати(функції, арг, вих, іменовані):
            for ф in функції:
                if ф in self.джерела_функцій and вих:
                    додати(вих, ['генератор:' + self.адреси_викликів[вих]])
                if ф in self.функції:
                    параметри, пов = self.функції[ф]
                    for а, п in zip(арг, параметри):
                        ребро(а, п)
                    for ім, а in іменовані:
                        if ім in self.імена_параметрів[ф]:
                            ребро(а, self.імена_параметрів[ф][ім])
                        elif ім is None:
                            for назва, п in self.імена_параметрів[ф].items():
                                ребро(self.розпаковані_поля[а, назва], п)
                    if ф in self.kwargs_параметри and вих in self.kwargs_викликів:
                        ребро(self.kwargs_викликів[вих], self.kwargs_параметри[ф])
                    ребро(пов, вих)
                if ф in self.резолвери and арг:
                    ребро(арг[0], self.резолвери[ф])
        while черга:
            з = черга.popleft()
            self.обробляється = з
            нові = очікує.pop(з)
            self.кроків += 1
            for до in tuple(наступні[з]):
                додати(до, нові)
            for до in скалярні[з]:
                додати(до, (в for в in нові if isinstance(в, str)))
            for до in копії_джерела[з]:
                копіювати(нові, self.знач[до])
            for дж in копії_цілі[з]:
                копіювати(self.знач[дж], нові)
            for вих, ключі in self.читання_кешу[з]:
                for о in нові:
                    if not isinstance(о, int):
                        continue
                    if self.види.get(о) == 'сховище':
                        ребро(поле(о, '@збережене'), поле(вих, 'result'))
                    elif self.види.get(о) == 'мапа':
                        ребро(поле(о, '@збережене'), вих)
                    else:
                        for к in ключі:
                            ребро(поле(о, к), вих)
            for вих, к in читачі[з]:
                читати(вих, нові, імена_ключа(к))
            for к, значення in писачі[з]:
                писати(значення, нові, імена_ключа(к))
            for вид, значення, б in ключові[з]:
                (читати if вид == 'читати' else писати)(значення, self.знач[б], імена_ключа(('ключ', з)))
            for арг, вих, умова, іменовані in викличі[з]:
                if not умова or self.знач[умова]:
                    викликати(нові, арг, вих, іменовані)
            for ф, арг, вих, іменовані in умовні[з]:
                викликати(self.знач[ф], арг, вих, іменовані)
            for вих, тип in фільтри[з]:
                for о in нові:
                    типи = self.поля.get((о, 'type'), set())
                    if not типи or 'рядок:' + тип in типи:
                        додати(вих, [о])
            if з in додавання:
                for о in нові:
                    if isinstance(о, int):
                        self.видимі.add(о)
                        if о in self.зображення:
                            ребро(поле(о, 'src'), поле(self.дом, 'src'))
        self.поля = {адреса: self.знач[в] for адреса, в in адреси.items()}
        self.номери_полів = адреси
        # Селектор може повернути функція або прочитати поле, тому його
        # остаточний тип визначаємо також після поширення значень графом.
        динамічні = []
        for тег, вузли in (('img', self.зображення), ('canvas', self.полотна)):
            for об in вузли:
                атрибути = {}
                for поле, назва in (('id', 'id'), ('className', 'class'), ('class', 'class')):
                    значення = self.поля.get((об, поле), set())
                    рядки = [з[6:] for з in значення if isinstance(з, str) and з.startswith('рядок:')]
                    if рядки:
                        атрибути[назва] = ' '.join(рядки)
                динамічні.append((тег, атрибути))
        for р, _, _, ім, _, арг, _, _ in self.виклики:
            if ім not in {'$', 'querySelector', 'querySelectorAll'} or not арг:
                continue
            селектори = {з[6:] for з in self.знач[арг[0]] if isinstance(з, str) and з.startswith('рядок:')}
            теги = {тег for селектор in селектори for тег, атрибути in self.html_елементи + динамічні
                    if відповідає_селектору(селектор, тег, атрибути)}
            if 'img' in теги or селектори & {'img', 'IMG'}:
                self.зображення.add(р)
            if 'canvas' in теги or селектори & {'canvas', 'CANVAS'}:
                self.полотна.add(р)

    def походження(self, входи, мітка='генератор:'):
        """Простежує споживача назад через значення і вкладені поля до міток одного роду."""
        if not hasattr(self, '_походження'):
            self._походження = {}
        if мітка not in self._походження:
            зворотні, знайдені = defaultdict(set), defaultdict(set)
            def ребро(б, з):
                if isinstance(з, int):
                    if б != з:
                        зворотні[з].add(б)
                elif з.startswith(мітка):
                    знайдені[б].add(з.removeprefix(мітка))
            for б, зн in enumerate(self.знач):
                for з in зн:
                    ребро(б, з)
            for (б, к), зн in self.поля.items():
                if к in ПІКСЕЛІ:
                    for з in зн:
                        ребро(б, з)
            черга = deque(знайдені)
            while черга:
                з = черга.popleft()
                for б in зворотні[з]:
                    if not знайдені[з] <= знайдені[б]:
                        знайдені[б].update(знайдені[з])
                        черга.append(б)
            self._походження[мітка] = знайдені
        return sorted(set().union(*(self._походження[мітка][в] for в in входи)))

    def результат(self):
        """Класифікує всі входи; місце — лише доведений шлях генератора."""
        рядки = []
        вид = set(self.видимі)
        for в in self.входи:
            дж = self.походження(в.значення)
            показ = True
            if в.умова == 'б' and в.обʼєкт:
                адреси = self.знач[в.обʼєкт]
                показ = bool(адреси & вид) and bool(адреси & (self.зображення | self.полотна | {self.дом}))
                if в.опис.startswith('запис inner') or в.опис.startswith('запис outer'):
                    показ = any('розмітка:зображення' in self.знач[з] for з in в.значення)
            elif в.умова == 'б':
                показ = any('розмітка:зображення' in self.знач[з] for з in в.значення)
            є = bool(дж) and показ
            повернено = [] if є or not показ else self.походження(в.значення, 'повернено:')
            чому = ('генератор ' + ', '.join(дж) + '; повернення пікселів оригіналу не доведене') if є else (
                'декодування/поза видимим DOM, не показ' if not показ else
                ('кадр генератора пройшов повернення з доведеним контрактом: ' + ', '.join(повернено)) if повернено else
                'у графі нема автоматичного шляху від генератора; зовнішній вхід/дані/метадані')
            рядки.append(dict(файл=в.файл, рядок=в.рядок, умова=в.умова, місце=є, чому=чому, вхід=в.опис))
        # Тіло функції будується в кожній її копії: той самий вхід — місце, якщо хоч в одній копії.
        унік = {}
        for р in рядки:
            к = (р['файл'], р['рядок'], р['умова'], р['вхід'])
            if к not in унік or (р['місце'] and not унік[к]['місце']):
                унік[к] = р
        return sorted(унік.values(), key=lambda р: (р['файл'], р['рядок'], р['умова'], р['вхід']))

    def слід(self, файл, рядок):
        """Найкоротший структурний шлях конкретного входу до генератора для звірки."""
        входи = [в for в in self.входи if в.файл == файл and в.рядок == рядок]
        край = deque((з, []) for в in входи for з in в.значення)
        бачені, поля = set(), defaultdict(list)
        імена = {з: f'оточення {с}: {ім}' for с, о in enumerate(self.оточення) for ім, з in о.items()}
        for (б, к), зн in self.поля.items():
            if к in ПІКСЕЛІ:
                поля[б].extend((з, к) for з in зн)
        while край:
            з, шлях = край.popleft()
            if з in бачені:
                continue
            бачені.add(з)
            if isinstance(з, str):
                if з.startswith('генератор:'):
                    return шлях + [з]
                continue
            де = self.адреси_вузлів.get(з, імена.get(з, f'вузол {з}'))
            for д in self.знач[з]:
                if д != з:
                    if isinstance(д, str) and д.startswith('генератор:'):
                        предки, був, п = [], set(), з
                        while п is not None and п not in був:
                            був.add(п)
                            предки.append(self.адреси_вузлів.get(п, імена.get(п, str(п))))
                            п = self.передачі.get((п, д))
                        край.append((д, шлях + предки))
                    else:
                        край.append((д, шлях + [де]))
            for д, к in поля[з]:
                предки, був, п = [], set(), self.номери_полів.get((з, к))
                if isinstance(д, str) and д.startswith('генератор:'):
                    while п is not None and п not in був:
                        був.add(п)
                        предки.append(self.адреси_вузлів.get(п, імена.get(п, str(п))))
                        п = self.передачі.get((п, д))
                край.append((д, шлях + [де + ' → поле ' + к] + предки))
        return []


def обсяг(корінь):
    """Читає все дерево мов класу; кожне виключення має названу причину."""
    файли, виключені = {}, {}
    дж = Path(корінь) / 'джерела'
    if not дж.is_dir():
        raise ValueError('немає теки джерела')
    for ф in sorted(дж.rglob('*')):
        if not ф.is_file() or ф.suffix not in {'.py', '.js', '.html'}:
            continue
        шлях = ф.relative_to(корінь).as_posix()
        if set(ф.relative_to(дж).parts[:-1]) & НЕ_ТЕКИ or ф.name.startswith(НЕ_ПРЕФІКСИ) or ф.name in НЕ_ІМЕНА:
            виключені[шлях] = 'тест/проба/прилад/стенд/збірка/залежність/лабораторія'
            continue
        try:
            файли[шлях] = ф.read_text(encoding='utf-8-sig')
        except (OSError, UnicodeError) as е:
            ОБСЯГ.непрочитано(шлях, е)
    return файли, виключені


class Складно(Exception):
    """Перебір умов запису вийшов за межу: контракт не доведено."""


НЕВІДОМЕ = 'невідоме'
ПОРІВНЯННЯ = {'===', '==', '!==', '!=', '<', '>', '<=', '>='}
ФУНКЦІЇ = {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}
МЕЖА_ТЕРМІВ = 512


def записи_елементів(дерево):
    """Присвоєння елементу масиву `N[і] = …` з найближчою функцією й умовами if над ним у ній."""
    записи, край = [], [(дерево, None, ())]
    while край:
        в, ф, умови = край.pop()
        т = в.get('type')
        if т in ФУНКЦІЇ:
            край.extend((д, в, ()) for д in нащадки(в))
            continue
        if т == 'IfStatement':
            край.append((в['test'], ф, умови))
            край.append((в['consequent'], ф, умови + ((в['test'], True),)))
            if в.get('alternate'):
                край.append((в['alternate'], ф, умови + ((в['test'], False),)))
            continue
        л = в.get('left') if т == 'AssignmentExpression' else None
        if (ф is not None and л and л.get('type') == 'MemberExpression' and л.get('computed')
                and л['object'].get('type') == 'Identifier'):
            записи.append((ф, в, умови))
        край.extend((д, ф, умови) for д in нащадки(в))
    return записи


def імена_шаблону(п):
    """Імена, які оголошує шаблон параметра чи деструктуризації."""
    if not isinstance(п, dict):
        return set()
    if п.get('type') == 'Identifier':
        return {п['name']}
    return set().union(set(), *(імена_шаблону(д.get('value', д) if д.get('type') == 'Property' else д) for д in нащадки(п)))


class Локальні:
    """Локальні означення однієї функції: які імена можна підставити, які масиви — її власні.

    Ім'я підставляється, лише коли воно означене в ній один раз і більше не присвоюється
    (ні в ній, ні у вкладених функціях); решта — непрозорий лист, його походження дає граф."""

    def __init__(self, ф):
        self.означення, self.змінні, self.елементи = defaultdict(list), set(), defaultdict(list)
        for п in ф.get('params', []):
            self.змінні |= імена_шаблону(п)
        край = [(ф['body'], False)]
        while край:
            в, вкладена = край.pop()
            if not isinstance(в, dict):
                continue
            т = в.get('type')
            if т in ФУНКЦІЇ:
                if т == 'FunctionDeclaration' and в.get('id') and not вкладена:
                    self.змінні.add(в['id']['name'])
                край.extend((д, True) for д in нащадки(в))
                continue
            if т == 'VariableDeclarator' and not вкладена:
                if в['id'].get('type') == 'Identifier':
                    self.означення[в['id']['name']].append(в.get('init'))
                else:
                    self.змінні |= імена_шаблону(в['id'])
            ціль = в.get('left') if т == 'AssignmentExpression' else в.get('argument') if т == 'UpdateExpression' else None
            if ціль:
                if ціль.get('type') == 'Identifier':
                    self.змінні.add(ціль['name'])
                elif ціль.get('type') == 'MemberExpression' and ціль['object'].get('type') == 'Identifier':
                    # Запис невідомого поля чи запис із вкладеної функції — невідоме значення елемента.
                    сталий = т == 'AssignmentExpression' and в['operator'] == '=' and not вкладена and ціль.get('computed')
                    self.елементи[ціль['object']['name']].append(в['right'] if сталий else None)
                else:
                    self.змінні |= імена_шаблону(ціль)
            if т in {'ForOfStatement', 'ForInStatement'}:
                л = в['left']
                for д in (л.get('declarations', []) if л.get('type') == 'VariableDeclaration' else [{'id': л}]):
                    self.змінні |= імена_шаблону(д['id'])
            край.extend((д, вкладена) for д in нащадки(в))

    def підстановка(self, ім):
        """Вираз означення, якщо ім'я незмінне; інакше None."""
        оо = self.означення.get(ім, [])
        if len(оо) == 1 and оо[0] is not None and ім not in self.змінні:
            return оо[0]
        return None

    def власний_типізований(self, ім):
        """Масив створено в ній як типізований: до запису елементи — нулі."""
        в = self.підстановка(ім)
        return bool(в and в.get('type') == 'NewExpression' and в['callee'].get('type') == 'Identifier'
                    and в['callee']['name'] in БАЙТИ_ТИПИ - {'ArrayBuffer', 'DataView'})


class Контракт:
    """Перевіряє контракт повернення за структурою коду, без назв функцій, масок чи промпту.

    Результат — масив, у який функція пише пікселі генератора (`R[і] = вираз`). Для кожного
    запису в нього вираз розкладається на терми з умовами: умова — значення елемента власного
    масиву функції (маски) в тому самому пікселі, `if` над записом і порівняння, які
    згортаються, коли відомі обидві сторони (маска, де записано лише 0, вмикатись не може).
    Лист терма — операція, яку не підставлено; її рід дає граф: «генератор» (пікселі кадру
    генератора), «фото» (розкодовані пікселі кадру не з генератора), «інше».

    Контракт доведено, коли для якоїсь маски M і її стану p:
    1) кожен терм із пікселями генератора — або там, де M у стані не-p (поза областю
       повернення: нова річ), або змішаний із пікселями фото там, де M = p (шов);
    2) є терм, де M = p, а всі листи — пікселі фото (досяжна область, де піксель — з фото).
    Терм генератора без умови маски — порушення. Семантики класів маски (які саме частини
    людини вона повертає), вирівнювання індексів і ширини шва прилад не доводить."""

    def __init__(self, граф):
        self.г = граф
        self.кеш_масивів = {}

    def рід(self, листи):
        """Рід листів за графом першого проходу."""
        вузли = {в for л in листи for в in self.г.вузли_ast.get(л, ()) if в}
        if self.г.походження(вузли):
            return 'генератор'
        if вузли and self.г.походження(вузли, 'пікселі:'):
            return 'фото'
        return 'інше'

    @staticmethod
    def злити(*умови):
        """Об'єднання умов; суперечність (маска і ввімкнена, і вимкнена) — None."""
        р = frozenset().union(*умови)
        стан = {}
        for м, б in р:
            if стан.setdefault(м, б) != б:
                return None
        return р

    def значення_масиву(self, лок, ім):
        """Значення елементів власного масиву: записані сталі, нуль типізованого; інакше невідоме."""
        к = (id(лок), ім)
        if к not in self.кеш_масивів:
            self.кеш_масивів[к] = {НЕВІДОМЕ}
            вс = {0} if лок.власний_типізований(ім) else {НЕВІДОМЕ}
            for праве in лок.елементи.get(ім, []):
                if праве is None:
                    вс.add(НЕВІДОМЕ)
                    continue
                for _, з, листи in self.терми(лок, праве, frozenset(), 0):
                    вс.add(НЕВІДОМЕ if листи else з)
            self.кеш_масивів[к] = вс
        return self.кеш_масивів[к]

    def масив(self, лок, в):
        """Ім'я власного масиву, якщо `в` — читання його елемента."""
        if (в.get('type') == 'MemberExpression' and в.get('computed') and в['object'].get('type') == 'Identifier'
                and (в['object']['name'] in лок.елементи or лок.власний_типізований(в['object']['name']))):
            return в['object']['name']
        return None

    def терми(self, лок, в, умова, гл):
        """Розклад виразу: [(умова, стале значення чи НЕВІДОМЕ, листи)]."""
        if гл > 60:
            raise Складно('глибина')
        т = в.get('type')
        if т == 'Literal' and isinstance(в.get('value'), (int, float, bool, str, type(None))) and 'regex' not in в:
            return [(умова, в.get('value'), frozenset())]
        if т == 'Identifier':
            ініц = лок.підстановка(в['name'])
            if ініц is not None:
                return self.терми(лок, ініц, умова, гл + 1)
            return [(умова, НЕВІДОМЕ, frozenset({id(в)}))]
        ім = self.масив(лок, в)
        if ім:
            вс = self.значення_масиву(лок, ім)
            if НЕВІДОМЕ in вс:
                return [(умова, НЕВІДОМЕ, frozenset({id(в)}))]
            вихід = []
            for з in вс:
                у = self.злити(умова, {(ім, bool(з))})
                if у is not None:
                    вихід.append((у, з, frozenset()))
            return вихід
        if т == 'ConditionalExpression':
            вихід = []
            for у, так in self.умови(лок, в['test'], умова, гл + 1):
                вихід += self.терми(лок, в['consequent' if так else 'alternate'], у, гл + 1)
            return self.межа(вихід)
        if т in {'BinaryExpression', 'LogicalExpression'}:
            вихід = []
            for ул, зл, лл in self.терми(лок, в['left'], умова, гл + 1):
                for уп, зп, лп in self.терми(лок, в['right'], ул, гл + 1):
                    у = self.злити(ул, уп)
                    if у is not None:
                        вихід.append((у, згорнути(в['operator'], зл, зп), лл | лп))
            return self.межа(вихід)
        if т == 'UnaryExpression':
            return [(у, згорнути(в['operator'], з), л) for у, з, л in self.терми(лок, в['argument'], умова, гл + 1)]
        return [(умова, НЕВІДОМЕ, frozenset({id(в)}))]

    def умови(self, лок, в, умова, гл):
        """Розклад умови: [(умова, істина)] — гілки, досяжні за відомих значень."""
        т = в.get('type')
        if т == 'Identifier' and лок.підстановка(в['name']) is not None:
            return self.умови(лок, лок.підстановка(в['name']), умова, гл + 1)
        if т == 'UnaryExpression' and в['operator'] == '!':
            return [(у, not б) for у, б in self.умови(лок, в['argument'], умова, гл + 1)]
        if т == 'LogicalExpression':
            вихід = []
            for у, б in self.умови(лок, в['left'], умова, гл + 1):
                if б == (в['operator'] == '||') or в['operator'] not in {'&&', '||'}:
                    вихід.append((у, б))
                else:
                    вихід += self.умови(лок, в['right'], у, гл + 1)
            return self.межа(вихід)
        вихід = []
        for у, з, _ in self.терми(лок, в, умова, гл + 1):
            вихід += [(у, б) for б in ((істинне(з),) if з is not НЕВІДОМЕ else (True, False))]
        return self.межа(вихід)

    @staticmethod
    def межа(вихід):
        """Без повторів; забагато гілок — контракт не доводиться."""
        вихід = list(dict.fromkeys(вихід))
        if len(вихід) > МЕЖА_ТЕРМІВ:
            raise Складно('гілок понад %d' % МЕЖА_ТЕРМІВ)
        return вихід

    def перевірити(self, файл_дерев):
        """Перевіряє кожен масив-результат, у який функція пише пікселі генератора."""
        групи = defaultdict(list)
        for файл, дд in файл_дерев:
            for д in дд:
                for ф, запис, умови in записи_елементів(д):
                    групи[(id(ф), запис['left']['object']['name'])].append((файл, ф, запис, умови))
        звіти = []
        for (_, ім), записи in групи.items():
            if not any(self.г.походження(self.г.вузли_ast.get(id(з['right']), ())) for _, _, з, _ in записи):
                continue
            файл, ф = записи[0][0], записи[0][1]
            рядки = sorted({з['loc']['start']['line'] for _, _, з, _ in записи})
            звіт = dict(файл=файл, рядки=рядки, масив=ім, доведено=False, маска=None,
                        записи=[id(з) for _, _, з, _ in записи])
            лок = Локальні(ф)
            try:
                терми = []
                for _, _, з, умови in записи:
                    початок = [frozenset()]
                    for тест, гілка in умови:
                        початок = [у for п in початок for у, б in self.умови(лок, тест, п, 0) if б == гілка]
                    for п in початок:
                        терми += [(у, {self.рід([л]) for л in листи}) for у, _, листи in self.терми(лок, з['right'], п, 0)]
            except Складно as е:
                звіт['чому'] = 'не доведено: ' + str(е)
                звіти.append(звіт)
                continue
            маски = sorted({м for у, _ in терми for м, _ in у})
            for м in маски:
                for стан in (True, False):
                    порушення = [у for у, роди in терми if 'генератор' in роди
                                 and (м, not стан) not in у and not ((м, стан) in у and 'фото' in роди)]
                    фото = any((м, стан) in у and роди == {'фото'} for у, роди in терми)
                    if not порушення and фото:
                        звіт.update(доведено=True, маска=f'{м}[…] {"увімкнена" if стан else "вимкнена"}')
                        break
                if звіт['доведено']:
                    break
            if звіт['доведено']:
                звіт['чому'] = (f'де маска {звіт["маска"]} — пікселі фото (шов — суміш із фото), '
                                'поза нею — кадр генератора')
            elif not маски:
                звіт['чому'] = 'не доведено: пікселі генератора пишуться без умови маски'
            else:
                звіт['чому'] = ('не доведено: нема маски, з якою пікселі генератора лишались би поза її областю, '
                                'а досяжна область давала б лише пікселі фото')
            звіти.append(звіт)
        return звіти


def істинне(з):
    """Істинність сталого значення за правилами JS."""
    return bool(з) and з != ''


def згорнути(оп, *зз):
    """Згортає операцію над сталими; невідоме — НЕВІДОМЕ."""
    if any(з is НЕВІДОМЕ for з in зз):
        return НЕВІДОМЕ
    try:
        if len(зз) == 1:
            з, = зз
            return {'-': lambda: -з, '+': lambda: +з, '!': lambda: not істинне(з)}[оп]()
        а, б = зз
        if оп in {'===', '=='}:
            return а == б
        if оп in {'!==', '!='}:
            return а != б
        return {'+': lambda: а + б, '-': lambda: а - б, '*': lambda: а * б, '/': lambda: а / б,
                '<': lambda: а < б, '>': lambda: а > б, '<=': lambda: а <= б, '>=': lambda: а >= б,
                '&&': lambda: б if істинне(а) else а, '||': lambda: а if істинне(а) else б}[оп]()
    except (KeyError, TypeError, ZeroDivisionError):
        return НЕВІДОМЕ


def побудувати(файли, дерева, python_дерева, перетворені, доведені):
    """Граф усього обсягу; `доведені` — записи результату з доведеним контрактом повернення."""
    г = Граф()
    г.доведені = доведені
    for ф, текст in файли.items():
        if ф.endswith('.html'):
            html = Розмітка()
            html.feed(текст)
            г.html_елементи.extend(html.елементи)
            г.ід_зображень.update(html.зображення)
            г.ід_полотен.update(html.полотна)
            for н, тег in html.входи:
                г.входи.append(Вхід(ф, н, 'б', (), 'статичний ' + тег))
    # Спільний глобальний JS показу; Python має окреме оточення на модуль.
    for ф, дд in дерева.items():
        г.файл = ф
        for д in дд:
            г.лічити_виклики(д)
            г.оголосити(д, 0)
    for ф, дд in дерева.items():
        г.файл = ф
        for д in дд:
            г.вираз(д)
    for ф, д in python_дерева.items():
        if ф not in перетворені:
            # Доведена відсутність джерела в усій Python-частині. Входи з JS
            # перевіряються на межі містП, до серіалізації; слова профілю й
            # числа не стають зображенням під час арифметики Python.
            for в in ast.walk(д):
                if isinstance(в, ast.Call):
                    назва = ast.unparse(в.func)
                    if СУД.search(назва):
                        г.входи.append(Вхід(ф, в.lineno, 'а', (), 'Python: ' + назва))
            continue
        дерево = перетворені[ф]
        г.дерева.append(дерево)
        г.файл = ф
        с = len(г.оточення)
        г.оточення.append({})
        г.батьки.append(None)
        м = г.модулі.setdefault(Path(ф).stem, г.нове(True))
        г.лічити_виклики(дерево)
        г.оголосити(дерево, с)
        г.вираз(дерево, с)
        for ім, з in г.оточення[с].items():
            г.запис(м, ім, з)
    г.замкнути()
    return г


def лічба(корінь, слід=None):
    """Будує граф всього обсягу, перевіряє контракти повернення й повертає відтворюваний звіт.

    Два проходи: перший граф дає походження листів для перевірки контракту; другий
    будується з доведеними записами результату (у них — мітка повернення, не пікселі
    генератора). Недоведений контракт нічого не змінює: місце лишається."""
    файли, виключені = обсяг(Path(корінь))
    js = {ф: т for ф, т in файли.items() if not ф.endswith('.py')}
    парсер = Path(__file__).with_name('примірка_ast.cjs')
    прогін = subprocess.run(['node', str(парсер)], input=json.dumps(js, ensure_ascii=False),
                           encoding='utf-8', capture_output=True, check=False)
    if прогін.returncode:
        raise ValueError(прогін.stderr.strip())
    дерева = json.loads(прогін.stdout)
    python_дерева = {}
    є_генератор = False
    for ф, текст in файли.items():
        if not ф.endswith('.py'):
            continue
        д = ОБСЯГ.розібрати(текст, ф)
        if д is None:
            continue
        python_дерева[ф] = д
        for в in ast.walk(д):
            if isinstance(в, ast.Call):
                назва = ast.unparse(в.func)
                if назва.rsplit('.', 1)[-1] in ДЖЕРЕЛА or назва.endswith(('images.generate', 'images.edit')):
                    є_генератор = True
    перетворені = {ф: пітон(д) for ф, д in python_дерева.items()} if є_генератор else {}
    г = побудувати(файли, дерева, python_дерева, перетворені, {})
    контракти = Контракт(г).перевірити(
        [(ф, дд) for ф, дд in дерева.items()] + [(ф, [д]) for ф, д in перетворені.items()])
    доведені = {з: f"{к['файл']}:{','.join(map(str, к['рядки']))}"
                for к in контракти if к['доведено'] for з in к['записи']}
    if доведені:
        г = побудувати(файли, дерева, python_дерева, перетворені, доведені)
    рядки = г.результат()
    звіт = dict(файли=dict(Counter(Path(ф).suffix for ф in файли)), обсяг=sorted(файли),
                виключені=виключені, кроків=г.кроків, входи=рядки,
                контракти=[{к: з for к, з in к.items() if к != 'записи'} for к in контракти],
                місць=len({(р['файл'], р['рядок']) for р in рядки if р['місце']}))
    if слід:
        ф, н = слід.rsplit(':', 1)
        звіт['слід'] = г.слід(ф, int(н))
    return звіт


def main():
    """Друкує місця, обсяг, а за потреби всі відкинуті входи та JSON."""
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument('--корінь', default='.')
    ап.add_argument('--докладно', action='store_true')
    ап.add_argument('--json')
    ап.add_argument('--слід')
    а = ап.parse_args()
    try:
        звіт = лічба(а.корінь, а.слід)
    except (OSError, ValueError, subprocess.SubprocessError) as е:
        print(f'непрочитано: {е}', file=sys.stderr)
        return 1
    if а.json:
        Path(а.json).write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if а.слід:
        print('слід: ' + ' → '.join(звіт['слід']))
    for к in звіт['контракти']:
        if not (к['доведено'] or а.докладно):
            continue
        print(f"контракт повернення · {к['файл']}:{','.join(map(str, к['рядки']))} · масив {к['масив']} · "
              f"{'доведено' if к['доведено'] else 'не доведено'} · {к['чому']}")
    for р in звіт['входи']:
        if р['місце'] or а.докладно:
            print(f"{'місце' if р['місце'] else 'не місце'} · {р['файл']}:{р['рядок']} · ({р['умова']}) {р['вхід']} · {р['чому']}")
    print('обсяг: ' + ', '.join(f'{к} {з}' for к, з in звіт['файли'].items()) +
          f"; входів {len(звіт['входи'])}; оновлень графа {звіт['кроків']}")
    print(f"місць: {звіт['місць']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
