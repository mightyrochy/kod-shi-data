#!/usr/bin/env python3
"""Будує граф походження Python без виконання коду продукту.

Ребро означає залежність значення, а не лише сусідство вузлів AST.
Аргументи з'єднано з параметрами, повернення — з викликами; псевдоніми
імпортів розв'язуються за модулем. Прямий пошук починається на зовнішніх
входах, зворотний — на явно заданих споживачах. Це статичне наближення:
гілки не виконуються, динамічні виклики лишаються нерозв'язаними.
"""
import ast
from collections import defaultdict, deque
from pathlib import Path
import warnings
import re


class Граф:
    """Зберігає залежності операторів, змінних, параметрів і повернень."""

    def __init__(self, тексти):
        """Розбирає модулі, спершу оголошуючи всі функції та імпорти."""
        self.ребра = defaultdict(set)
        self.зворотні = defaultdict(set)
        self.точки = {}
        self.функції = {}
        self.імпорти = {}
        self.привязки = defaultdict(set)
        self.глобальні = defaultdict(set)
        self.області = {}
        self.модулі = {}
        self.дерева = {}
        self.входи = set()
        self.нерозвязані = set()
        self.звязані_виклики = {}
        self.готові_вирази = set()
        for файл, текст in sorted(тексти.items()):
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', SyntaxWarning)
                дерево = текст if isinstance(текст, ast.AST) else ast.parse(текст)
            self.дерева[файл] = дерево
            self.модулі[файл] = str(Path(файл).with_suffix('')).replace('\\', '/').replace('/', '.')
        self.за_модулем = {м: ф for ф, м in self.модулі.items()}
        for файл, дерево in self.дерева.items():
            self._оголосити(файл, дерево, '<модуль>')
        for файл, дерево in self.дерева.items():
            self._тіло(файл, дерево.body, '<модуль>')

    def ребро(self, звідки, куди):
        """Додає напрям залежності та окремий індекс її обернення."""
        if звідки != куди:
            self.ребра[звідки].add(куди)
            self.зворотні[куди].add(звідки)

    def _оголосити(self, файл, вузол, область):
        """Збирає означення й лексичні імпорти до аналізу викликів."""
        if isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            область += '.' + вузол.name
            if not isinstance(вузол, ast.ClassDef):
                self.функції[файл, область] = вузол
        self.області[вузол] = область
        if isinstance(вузол, ast.Name) and isinstance(вузол.ctx, ast.Store):
            self.привязки[файл, область].add(вузол.id)
        elif isinstance(вузол, ast.arg):
            self.привязки[файл, область].add(вузол.arg)
        elif isinstance(вузол, ast.Global):
            self.глобальні[файл, область].update(вузол.names)
        if isinstance(вузол, ast.ImportFrom):
            for пс in вузол.names:
                self.імпорти[файл, область, пс.asname or пс.name] = (вузол.module or '', пс.name)
        elif isinstance(вузол, ast.Import):
            for пс in вузол.names:
                self.імпорти[файл, область, пс.asname or пс.name.split('.')[0]] = (пс.name, '')
        for ч in ast.iter_child_nodes(вузол):
            self._оголосити(файл, ч, область)

    def _змінна(self, файл, область, ім):
        """Ключ змінної розділяє однойменні локальні області."""
        if ім in self.глобальні[файл, область]:
            область = '<модуль>'
        else:
            while '.' in область and ім not in self.привязки[файл, область]:
                область = область.rpartition('.')[0]
        return (файл, область, 'змінна', ім)

    def _точка(self, файл, область, вузол):
        """Стабільна координата вузла, незалежна від версії ast.dump."""
        ключ = (файл, область, вузол.lineno, вузол.col_offset, type(вузол).__name__)
        self.точки[ключ] = вузол
        return ключ

    def _імпорт(self, файл, область, ім):
        """Шукає імпорт у поточній та батьківських областях."""
        while область:
            знайдене = self.імпорти.get((файл, область, ім))
            if знайдене:
                return знайдене
            область = область.rpartition('.')[0]
        return None

    def _модуль(self, файл, модуль):
        """Віддає локальний модуль з урахуванням двох коренів sys.path."""
        for назва in (модуль, self.модулі[файл].rpartition('.')[0] + '.' + модуль,
                      'джерела.' + модуль, 'zhnyvarka.' + модуль):
            if назва in self.за_модулем:
                return self.за_модулем[назва]
        return None

    def _розвязати(self, файл, область, функція, бачені=None):
        """Розв'язує локальний/імпортований виклик, також реекспорт фасаду."""
        бачені = set() if бачені is None else бачені
        ключ = (файл, область, ast.dump(функція))
        if ключ in бачені:
            return None
        бачені.add(ключ)
        if isinstance(функція, ast.Name):
            пошук = область
            while пошук:
                к = (файл, пошук + '.' + функція.id)
                if к in self.функції:
                    return к
                пошук = пошук.rpartition('.')[0]
            імпорт = self._імпорт(файл, область, функція.id)
            if імпорт and імпорт[1] != '*':
                інший = self._модуль(файл, імпорт[0])
                if інший:
                    return self._розвязати(інший, '<модуль>', ast.Name(id=імпорт[1]), бачені)
        elif isinstance(функція, ast.Attribute) and isinstance(функція.value, ast.Name):
            імпорт = self._імпорт(файл, область, функція.value.id)
            if імпорт:
                інший = self._модуль(файл, імпорт[0])
                if інший:
                    return self._розвязати(інший, '<модуль>', ast.Name(id=функція.attr), бачені)
        return None

    def _вираз(self, файл, область, вузол):
        """З'єднує вхідні значення виразу з його результатом."""
        if вузол is None:
            return None
        к = self._точка(файл, область, вузол)
        if к in self.готові_вирази:
            return к
        self.готові_вирази.add(к)
        if isinstance(вузол, ast.Name):
            self.ребро(self._змінна(файл, область, вузол.id), к)
            return к
        if isinstance(вузол, ast.Lambda):
            # Тіло lambda виконується лише викликом. Не домішуємо його до означення.
            return к
        ціль_виклику = self._розвязати(файл, область, вузол.func) if isinstance(вузол, ast.Call) else None
        аргументи = set(вузол.args) | set(вузол.keywords) if isinstance(вузол, ast.Call) else set()
        for ч in ast.iter_child_nodes(вузол):
            if ціль_виклику and ч in аргументи:
                # Параметр впливає на результат тільки через тіло функції.
                continue
            if isinstance(ч, ast.expr):
                self.ребро(self._вираз(файл, область, ч), к)
            elif isinstance(ч, ast.keyword):
                self.ребро(self._вираз(файл, область, ч.value), к)
            elif isinstance(ч, ast.comprehension):
                вхід = self._вираз(файл, область, ч.iter)
                self._ціль(файл, область, ч.target, вхід)
                self.ребро(вхід, к)
                for умова in ч.ifs:
                    self.ребро(self._вираз(файл, область, умова), к)
        if isinstance(вузол, ast.NamedExpr):
            self._ціль(файл, область, вузол.target, к)
        if isinstance(вузол, ast.Call):
            ім = вузол.func.attr if isinstance(вузол.func, ast.Attribute) else getattr(вузол.func, 'id', '')
            if ім in {'select', 'select_one', 'find_all', 'findtext', 'xpath', 'cssselect',
                      'get_attribute', 'getAttribute', 'search', 'match', 'finditer', 'findall', 'group', 'groups'}:
                self.входи.add(к)
            if ім == 'get' and вузол.args and isinstance(вузол.args[0], ast.Constant):
                атр = вузол.args[0].value
                if isinstance(атр, str) and (атр.startswith('data-') or атр in {'src', 'srcset', 'style'}):
                    self.входи.add(к)
            ціль = ціль_виклику
            if ціль:
                self.звязані_виклики[к] = ціль
                self.ребро((*ціль, 'повернення'), к)
                опис = self.функції[ціль]
                параметри = опис.args.posonlyargs + опис.args.args
                for арг, пар in zip(вузол.args, параметри):
                    self.ребро(self._вираз(файл, область, арг), self._змінна(*ціль, пар.arg))
                for арг in вузол.keywords:
                    if арг.arg:
                        self.ребро(self._вираз(файл, область, арг.value), self._змінна(*ціль, арг.arg))
            elif isinstance(вузол.func, ast.Name) and ім not in {'dict', 'list', 'set', 'tuple', 'str', 'int', 'float', 'len', 'bool', 'max', 'min', 'next', 'sorted', 'enumerate', 'zip', 'range', 'any', 'all', 'print', 'isinstance', 'getattr', 'open', 'sum'}:
                self.нерозвязані.add(к)
            # append/update змінюють контейнер; це ребро потрібне для повернення списку.
            if isinstance(вузол.func, ast.Attribute) and ім in {'append', 'extend', 'update', 'add', 'setdefault'}:
                self._ціль(файл, область, вузол.func.value, к)
        return к

    def _ціль(self, файл, область, ціль, значення):
        """З'єднує запис із локальною змінною чи зміненим контейнером."""
        if isinstance(ціль, ast.Name):
            self.ребро(значення, self._змінна(файл, область, ціль.id))
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            for ч in ціль.elts:
                self._ціль(файл, область, ч, значення)
        elif isinstance(ціль, (ast.Subscript, ast.Attribute)):
            self._ціль(файл, область, ціль.value, значення)

    def _тіло(self, файл, тіло, область):
        """Будує залежності операторів без змішування вкладених функцій."""
        for оп in тіло:
            к = self._точка(файл, область, оп)
            if isinstance(оп, (ast.FunctionDef, ast.AsyncFunctionDef)):
                нова = область + '.' + оп.name
                параметри = оп.args.posonlyargs + оп.args.args
                for пар, значення in zip(параметри[len(параметри) - len(оп.args.defaults):], оп.args.defaults):
                    self.ребро(self._вираз(файл, область, значення), self._змінна(файл, нова, пар.arg))
                for пар, значення in zip(оп.args.kwonlyargs, оп.args.kw_defaults):
                    if значення is not None:
                        self.ребро(self._вираз(файл, область, значення), self._змінна(файл, нова, пар.arg))
                self._тіло(файл, оп.body, область + '.' + оп.name)
                continue
            if isinstance(оп, ast.ClassDef):
                self._тіло(файл, оп.body, область + '.' + оп.name)
                continue
            if isinstance(оп, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                if оп.value is not None:
                    self.ребро(self._вираз(файл, область, оп.value), к)
                    for ціль in оп.targets if isinstance(оп, ast.Assign) else [оп.target]:
                        self._ціль(файл, область, ціль, к)
            elif isinstance(оп, ast.Return):
                if оп.value is not None:
                    self.ребро(self._вираз(файл, область, оп.value), к)
                    self.ребро(к, (файл, область, 'повернення'))
            elif isinstance(оп, (ast.For, ast.AsyncFor)):
                self.ребро(self._вираз(файл, область, оп.iter), к)
                self._ціль(файл, область, оп.target, к)
            elif isinstance(оп, (ast.With, ast.AsyncWith)):
                for пункт in оп.items:
                    вхід = self._вираз(файл, область, пункт.context_expr)
                    self.ребро(вхід, к)
                    if пункт.optional_vars:
                        self._ціль(файл, область, пункт.optional_vars, вхід)
            else:
                for ч in ast.iter_child_nodes(оп):
                    if isinstance(ч, ast.expr):
                        self.ребро(self._вираз(файл, область, ч), к)
            for поле in ('body', 'orelse', 'finalbody'):
                вкладене = getattr(оп, поле, None)
                if isinstance(вкладене, list):
                    self._тіло(файл, вкладене, область)
            for обробник in getattr(оп, 'handlers', ()):
                self._тіло(файл, обробник.body, область)

    def від_джерел(self, джерела=None):
        """Поширює значення від джерел по прямих ребрах до нерухомої точки."""
        слід = {к: None for к in (self.входи if джерела is None else джерела)}
        черга = deque(sorted(слід, key=str))
        while черга:
            к = черга.popleft()
            for наступний in sorted(self.ребра.get(к, ()), key=str):
                if наступний not in слід:
                    слід[наступний] = к
                    черга.append(наступний)
        return слід

    def від_споживачів(self, споживачі):
        """Шукає залежності назад від споживачів, не використовуючи прямого обходу."""
        слід = {к: None for к in споживачі}
        черга = list(sorted(слід, key=str))
        while черга:
            к = черга.pop()
            for попередній in sorted(self.зворотні.get(к, ()), key=str):
                if попередній not in слід:
                    слід[попередній] = к
                    черга.append(попередній)
        return слід

    def маршрут(self, слід, к):
        """Відновлює один скінченний доказ до початку відповідного пошуку."""
        шлях = []
        while к in слід:
            шлях.append(к)
            к = слід[к]
        return шлях

    def споживачі(self):
        """Незалежно від входів знаходить записи полів кадру, кольору й наявності.

        Це кінці пошуку, а не готові порушення: поле готової речі може
        копіюватись без нового входу. Пункт 4 позначає виклик виміру.
        """
        вихід = defaultdict(set)

        def роль(поле):
            """Визначає роль записуваного поля, не імена локальних змінних."""
            п = set()
            if re.search(r'фото|кадр|галере|image|picture|photo', поле, re.I):
                п.add(1)
            if re.search(r'кол[іь]р|кольор|colou?r|свотч|swatch|наявн|stock|avail|^lab$|^hex$', поле, re.I):
                п.add(2)
            return п

        for к, в in self.точки.items():
            поля = []
            if isinstance(в, ast.Call):
                ім = в.func.attr if isinstance(в.func, ast.Attribute) else getattr(в.func, 'id', '')
                if ім in {'dict', 'update', 'setdefault'}:
                    поля.extend(п.arg for п in в.keywords if п.arg)
                    if ім == 'setdefault' and в.args and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
                        поля.append(в.args[0].value)
                if re.search(r'виміряти_(?:фото|колір|поверхню)|колір_з_фото|поверхня_кадрів|палітра_принту', ім):
                    вихід[4].add(к)
            elif isinstance(в, ast.Dict):
                поля.extend(п.value for п in в.keys if isinstance(п, ast.Constant) and isinstance(п.value, str))
            elif isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                for ц in цілі:
                    if isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant) and isinstance(ц.slice.value, str):
                        поля.append(ц.slice.value)
                    elif isinstance(ц, ast.Attribute):
                        поля.append(ц.attr)
            for поле in поля:
                for пункт in роль(поле):
                    вихід[пункт].add(к)
        return вихід


def огляд(корінь):
    """Звіряє реальні залежності від входів і від записів/вимірів всього Python."""
    тексти = {}
    for тека in ('джерела', 'zhnyvarka'):
        for шлях in sorted((корінь / тека).rglob('*.py')):
            if any(ч in ('node_modules', '__pycache__', '.venv') for ч in шлях.parts):
                continue
            файл = шлях.relative_to(корінь).as_posix()
            if файл.startswith('джерела/прилади/корінь_річ_кадр_'):
                continue
            тексти[файл] = шлях.read_text(encoding='utf-8-sig')
    граф = Граф(тексти)
    прямий = граф.від_джерел()
    кінці = граф.споживачі()
    підсумки, докази = {}, []
    for пункт, усі in sorted(кінці.items()):
        зворотний = граф.від_споживачів(усі)
        досягнуті = усі & прямий.keys()
        входи = граф.входи & зворотний.keys()
        підсумки[пункт] = dict(споживачів=len(усі), з_походженням=len(досягнуті),
                              входів_до_споживачів=len(входи),
                              без_походження=len(усі - прямий.keys()))
        for к in sorted(досягнуті, key=str)[:20]:
            докази.append(dict(пункт=пункт, споживач=к, від_джерела=граф.маршрут(прямий, к)))
        for к in sorted(входи, key=str)[:20]:
            докази.append(dict(пункт=пункт, джерело=к, до_споживача=граф.маршрут(зворотний, к)))
    return dict(файлів=len(тексти), вузлів=len(граф.точки),
                звязаних_викликів=len(граф.звязані_виклики),
                нерозвязаних_викликів=sorted(граф.нерозвязані, key=str),
                підсумки=підсумки, докази=докази)
