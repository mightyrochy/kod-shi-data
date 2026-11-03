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
Невідоме перетворення не очищає походження. Назва «маска» чи «повернути»
та промпт не доводять повернення пікселів. Копіювання пікселів перевіряється
окремо: прилад поки консервативно залишає такий шлях місцем, доки немає
верифікованого контракту повернення. Це обмеження називається у переліку.

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
СУД = re.compile(r'суд|оцін|контраст|шкір|фігур|силует|облич|judge|assess|skin|figure|face|contrast', re.I)
НЕ_СУД = {'розмір_картинки', 'малюватиФотоОцінкиП', 'кінецьОцінкиП', 'збійОцінкиП',
          'оцінкаЗРозмовиП', 'оновитиРядокП', 'викликОцінкиП'}
ЧИСЛОВІ = {'width', 'height', 'length', 'size', 'ширина', 'висота', 'type', 'тип',
           'media_type', 'mime_type', 'ід', 'id', 'byteLength'}
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
        арг = пітон(в.args)
        if в.keywords:
            арг.append(т('ObjectExpression', properties=[т('Property', key=т('Literal', value=к.arg), value=пітон(к.value), computed=False) for к in в.keywords]))
        return т('CallExpression', callee=пітон(в.func), arguments=арг)
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

    def handle_starttag(self, tag, attrs):
        """Називає кожний статичний вхід показу у вихідному HTML."""
        а = dict(attrs)
        if tag in {'img', 'canvas'}:
            if а.get('id'):
                (self.зображення if tag == 'img' else self.полотна).add(а['id'])
            self.входи.append((self.getpos()[0], tag))


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
        self.означення = {}
        self.застосування = set()
        self.скалярні = set()
        self.джерела_функцій = set()
        self.адреси_викликів = {}

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
            адреса = (о, к)
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
                self.запис(б, ключ(в), з)
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
                self.змінна(в['id']['name'], с, True)
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
            return р
        if т in {'FunctionDeclaration', 'FunctionExpression', 'ArrowFunctionExpression'}:
            р = self.нове(True)
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
            self.оголосити(в['body'], нов)
            з = self.вираз(в['body'], нов, пов)
            if в['body']['type'] != 'BlockStatement':
                self.звʼязати(з, пов)
            if т == 'FunctionDeclaration' and в.get('id'):
                self.звʼязати(р, self.змінна(в['id']['name'], с))
                self.означення[в['id']['name']] = в['body']
            return р
        if т == 'VariableDeclarator':
            з = self.вираз(в.get('init'), с)
            self.звʼязати_ціль(в['id'], с, з)
            return з
        if т == 'AssignmentExpression':
            з = self.вираз(в['right'], с)
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
            return self.поле(б, ключ(в))
        if т in {'ObjectExpression', 'ArrayExpression'}:
            р = self.нове(True)
            if т == 'ArrayExpression':
                for д in в.get('elements', []):
                    if д:
                        self.запис(р, '*', self.вираз(д, с))
            else:
                for п in в.get('properties', []):
                    if п['type'] == 'SpreadElement':
                        self.звʼязати(self.вираз(п['argument'], с), р)
                    else:
                        к = п['key']
                        к = '*' if п.get('computed') else str(к.get('name', к.get('value', '*')))
                        self.запис(р, к, self.вираз(п['value'], с))
            return р
        if т in {'CallExpression', 'NewExpression'}:
            назва = імʼя(в['callee'])
            ім = назва.rsplit('.', 1)[-1]
            б = self.вираз(в['callee']['object'], с) if в['callee']['type'] == 'MemberExpression' else 0
            функ = self.вираз(в['callee'], с)
            арг = tuple(self.вираз(а, с) for а in в.get('arguments', []))
            р = self.нове(ім in {'ел', 'createElement', '$', 'querySelector', 'querySelectorAll', 'getElementById',
                                  'Image', 'Promise', 'Map', 'Set', 'map', 'flatMap', 'getAll', 'get', 'json', 'містП', 'модельП_блоки'})
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
            if ім in {'модельП', 'викликОцінкиП'}:
                кадри = арг[1:2] if ім == 'модельП' else арг[2:3]
                self.входи.append(Вхід(self.файл, н, 'а', кадри, 'фото в ' + ім))
            elif (СУД.search(ім) and ім not in НЕ_СУД and not ім.startswith(('малювати', 'записати', 'показати'))):
                self.входи.append(Вхід(self.файл, н, 'а', арг, 'вхід ' + назва))
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
            for к, д in ((к, д) for к, з in в.items() for д in (з if isinstance(з, list) else [з]) if isinstance(д, dict) and 'type' in д):
                з = self.вираз(д, с, повернення)
                if к != 'test' and в.get('operator') not in {'===', '!==', '==', '!=', '<', '>', '<=', '>='}:
                    self.звʼязати(з, р)
            return р
        # Конструкції керування не зливають значення умови з результатом.
        for д in нащадки(в):
            self.вираз(д, с, повернення)
        return 0

    def до_функції(self, функ, арг, вих):
        """Параметри й повернення для можливих адресатів виклику."""
        self.застосування.add((функ, tuple(арг), вих))
        for ф in tuple(self.знач[функ]):
            if ф in self.функції:
                параметри, пов = self.функції[ф]
                for а, п in zip(арг, параметри):
                    self.звʼязати(а, п)
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
        # Розклад сталих native-операцій будуємо лише раз.
        for р, функ, б, ім, назва, арг, файл, н in self.виклики:
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
            elif ім in прозорі:
                for з in ((б,) if б and ім in {'replace', 'replaceAll', 'slice', 'substring', 'trim', 'split', 'join', 'toString', 'blob', 'arrayBuffer', 'decode', 'encode'} else арг[:1]):
                    self.звʼязати(з, р)
            elif ім in {'ел', 'createElement', '$', 'querySelector', 'querySelectorAll', 'getElementById', 'Image'}:
                if ім == 'Image':
                    self.зображення.add(р)
                elif арг:
                    текст = {з[6:] for з in self.знач[арг[0]] if isinstance(з, str) and з.startswith('рядок:')}
                    if текст & {'img', 'IMG'} or текст & self.ід_зображень or any(re.search(r'(?:^|\s|>)img\b', з) for з in текст):
                        self.зображення.add(р)
                    if текст & {'canvas', 'CANVAS'} or текст & self.ід_полотен:
                        self.полотна.add(р)
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
                for з in арг:
                    self.звʼязати(з, р)
                for з in арг[1:]:
                    self.звʼязати(з, арг[0])
            elif ім in {'getImageData', 'toDataURL', 'toBlob'} and б:
                self.звʼязати(self.поле(б, '@пікселі'), р)
            elif ім in {'drawImage', 'putImageData'} and б and арг:
                self.запис(б, '@пікселі', арг[0])
            elif ім == 'objectStore' and арг:
                к = tuple(sorted(str(з) for з in self.знач[арг[0]] if isinstance(з, str)))
                сх = self.сховища.setdefault(к, self.нове(True))
                self.звʼязати(сх, р)
            elif ім == 'tx' and len(арг) >= 4:
                к = tuple(sorted(str(з) for з in self.знач[арг[1]] if isinstance(з, str)))
                сх = self.сховища.setdefault(к, self.нове(True))
                self.до_функції(арг[3], (сх,), р)
            elif ім in {'getAll', 'get'} and б:
                збережене = self.поле(б, '@збережене')
                if ім == 'getAll':
                    масив = self.нове(True)
                    self.запис(масив, '*', збережене)
                    self.запис(р, 'result', масив)
                else:
                    self.звʼязати(збережене, р)
                    self.запис(р, 'result', збережене)
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
                if р in self.вибір_типу:
                    фільтри[всі].append((ел, self.вибір_типу[р]))
                else:
                    self.звʼязати(всі, ел)
                if ім in {'map', 'flatMap'}:
                    self.до_функції(арг[0], (ел,), повернене)
                    self.запис(р, '*', повернене)
                else:
                    self.до_функції(арг[0], (ел,), 0)
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
            elif ім not in ДЖЕРЕЛА | прозорі | {'модельП', 'викликОцінкиП', 'блокиВТекст', 'ел', 'createElement', '$', 'querySelector', 'getElementById', 'getContext', 'Promise', 'assign', 'objectStore', 'tx'}:
                self.до_функції(функ, арг, р)
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
        for ф, арг, вих in self.застосування:
            викличі[ф].append((арг, вих))
        наступні = defaultdict(set)
        for з, до in self.ребра:
            наступні[з].add(до)
        черга, очікує = deque(), defaultdict(set)
        def додати(до, значення):
            нові = set(значення) - self.знач[до]
            if нові:
                self.знач[до].update(нові)
                if not очікує[до]:
                    черга.append(до)
                очікує[до].update(нові)
        def ребро(з, до):
            if з and до and з != до and до not in наступні[з]:
                наступні[з].add(до)
                додати(до, self.знач[з])
        адреси, поля_обʼєкта, усі_читачі = {}, defaultdict(set), defaultdict(set)
        def поле(о, к):
            адреса = (о, к)
            if адреса not in адреси:
                в = self.нове()
                адреси[адреса] = в
                поля_обʼєкта[о].add(в)
                for вих in усі_читачі[о]:
                    ребро(в, вих)
            return адреси[адреса]
        for (о, к), значення in tuple(self.поля.items()):
            додати(поле(о, к), значення)
        for з, значення in enumerate(self.знач):
            if значення:
                if not очікує[з]:
                    черга.append(з)
                очікує[з].update(значення)
        for о in self.видимі & self.зображення:
            ребро(поле(о, 'src'), поле(self.дом, 'src'))
        while черга:
            з = черга.popleft()
            нові = очікує.pop(з)
            self.кроків += 1
            for до in tuple(наступні[з]):
                додати(до, нові)
            for до in скалярні[з]:
                додати(до, (в for в in нові if isinstance(в, str)))
            for вих, к in читачі[з]:
                for о in нові:
                    if isinstance(о, str):
                        if о.startswith('генератор:') and к not in ЧИСЛОВІ:
                            додати(вих, [о])
                    elif к == '*':
                        усі_читачі[о].add(вих)
                        for в in tuple(поля_обʼєкта[о]):
                            ребро(в, вих)
                    else:
                        ребро(поле(о, к), вих)
            for к, значення in писачі[з]:
                for о in нові:
                    if isinstance(о, int):
                        ребро(значення, поле(о, к))
            for арг, вих in викличі[з]:
                for ф in нові:
                    if ф in self.джерела_функцій and вих:
                        додати(вих, ['генератор:' + self.адреси_викликів[вих]])
                    if ф in self.функції:
                        параметри, пов = self.функції[ф]
                        for а, п in zip(арг, параметри):
                            ребро(а, п)
                        ребро(пов, вих)
                    if ф in self.резолвери and арг:
                        ребро(арг[0], self.резолвери[ф])
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

    def походження(self, входи):
        """Простежує споживача назад через значення і вкладені поля."""
        if not hasattr(self, '_походження'):
            зворотні, знайдені = defaultdict(set), defaultdict(set)
            def ребро(б, з):
                if isinstance(з, int):
                    if б != з:
                        зворотні[з].add(б)
                elif з.startswith('генератор:'):
                    знайдені[б].add(з.removeprefix('генератор:'))
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
            self._походження = знайдені
        return sorted(set().union(*(self._походження[в] for в in входи)))

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
            чому = ('генератор ' + ', '.join(дж) + '; повернення пікселів оригіналу не доведене') if є else (
                'декодування/поза видимим DOM, не показ' if not показ else
                'у графі нема автоматичного шляху від генератора; зовнішній вхід/дані/метадані')
            рядки.append(dict(файл=в.файл, рядок=в.рядок, умова=в.умова, місце=є, чому=чому, вхід=в.опис))
        унік = {(р['файл'], р['рядок'], р['умова'], р['вхід']): р for р in рядки}
        return sorted(унік.values(), key=lambda р: (р['файл'], р['рядок'], р['умова'], р['вхід']))


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


def лічба(корінь):
    """Будує граф всього обсягу й повертає відтворюваний звіт."""
    файли, виключені = обсяг(Path(корінь))
    js = {ф: т for ф, т in файли.items() if not ф.endswith('.py')}
    парсер = Path(__file__).with_name('примірка_ast.cjs')
    прогін = subprocess.run(['node', str(парсер)], input=json.dumps(js, ensure_ascii=False),
                           encoding='utf-8', capture_output=True, check=False)
    if прогін.returncode:
        raise ValueError(прогін.stderr.strip())
    дерева = json.loads(прогін.stdout)
    г = Граф()
    for ф, текст in файли.items():
        if ф.endswith('.html'):
            html = Розмітка()
            html.feed(текст)
            г.ід_зображень.update(html.зображення)
            г.ід_полотен.update(html.полотна)
            for н, тег in html.входи:
                г.входи.append(Вхід(ф, н, 'б', (), 'статичний ' + тег))
    # Спільний глобальний JS показу; Python має окреме оточення на модуль.
    for ф, дд in дерева.items():
        for д in дд:
            г.оголосити(д, 0)
    for ф, дд in дерева.items():
        г.файл = ф
        for д in дд:
            г.вираз(д)
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
    for ф, д in python_дерева.items():
        if not є_генератор:
            # Доведена відсутність джерела в усій Python-частині. Входи з JS
            # перевіряються на межі містП, до серіалізації; слова профілю й
            # числа не стають зображенням під час арифметики Python.
            for в in ast.walk(д):
                if isinstance(в, ast.Call):
                    назва = ast.unparse(в.func)
                    if СУД.search(назва):
                        г.входи.append(Вхід(ф, в.lineno, 'а', (), 'Python: ' + назва))
            continue
        дерево = пітон(д)
        г.дерева.append(дерево)
        г.файл = ф
        с = len(г.оточення)
        г.оточення.append({})
        г.батьки.append(None)
        м = г.модулі.setdefault(Path(ф).stem, г.нове(True))
        г.оголосити(дерево, с)
        г.вираз(дерево, с)
        for ім, з in г.оточення[с].items():
            г.запис(м, ім, з)
    г.замкнути()
    рядки = г.результат()
    return dict(файли=dict(Counter(Path(ф).suffix for ф in файли)), обсяг=sorted(файли),
                виключені=виключені, кроків=г.кроків, входи=рядки,
                місць=len({(р['файл'], р['рядок']) for р in рядки if р['місце']}))


def main():
    """Друкує місця, обсяг, а за потреби всі відкинуті входи та JSON."""
    ап = argparse.ArgumentParser(description=__doc__)
    ап.add_argument('--корінь', default='.')
    ап.add_argument('--докладно', action='store_true')
    ап.add_argument('--json')
    а = ап.parse_args()
    try:
        звіт = лічба(а.корінь)
    except (OSError, ValueError, subprocess.SubprocessError) as е:
        print(f'непрочитано: {е}', file=sys.stderr)
        return 1
    if а.json:
        Path(а.json).write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for р in звіт['входи']:
        if р['місце'] or а.докладно:
            print(f"{'місце' if р['місце'] else 'не місце'} · {р['файл']}:{р['рядок']} · ({р['умова']}) {р['вхід']} · {р['чому']}")
    print('обсяг: ' + ', '.join(f'{к} {з}' for к, з in звіт['файли'].items()) +
          f"; входів {len(звіт['входи'])}; оновлень графа {звіт['кроків']}")
    print(f"місць: {звіт['місць']}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
