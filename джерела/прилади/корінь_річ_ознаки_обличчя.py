# -*- coding: utf-8 -*-
"""прилади/корінь_річ_ознаки_обличчя.py — прилад кореня Річ-ознаки-обличчя: ознака її колориту як вимір коду.

Клас — `аудит/корені/Річ-ознаки-обличчя.md` («Клас місць», «Стан і що лишилось»). Місце — точка коду продукту, де
значення про її колорит, якого код не міряв (hex моделі зору з портрета і все, що з нього пораховано), стає числом чи
класом для дальшого рахунку або йде моделі чи жінці як вимір. Пункти:
  1  hex моделі стає рисою з довірою знімку без позначки оцінки (читання полів відповіді, риса з `from_photo`, риса в
     запис із довірою `AXIS_RELIABILITY`), або код порівнює з порогом пораховане з нього (рівень, щілина, сім'я, b*,
     echo/set_off, «її чорний», смуга світлоти);
  2  незнання стає значенням: гілка «невідомо» (`is None`, `is False`, `not x`) ставить клас чи число; запасне число
     (`x or 0`, `.get(k, 0)`);
  3  причина «чому — її <ознака>» проходить за наявністю запису, а не його значенням (таблиця звірки причин);
  4  опис поля для моделі зве значення з цього джерела виміром коду («measured»).

ВІД ЗНАЧЕННЯ, НЕ ВІД ІМЕН. Зерно — оголошення збирача, чий скелет відповіді несе `<hex>` (читання її портрета): його
hex-поля й читач форми з `схеми_розбору`. Потік (Python, до нерухомої точки, контекстно-чутливо за мітками параметрів):
присвоєння, розпаковка, ключ dict і `dict(...)`, мутації (`append`, `update`, присвоєння за ключем), повернення,
аргументи → параметри (позиційні, іменовані, `*`/`**`), лямбди, таблиці функцій (`ТАБЛ[к](...)`), фабрики лямбд,
глобальні кеші модуля, замикання вкладених функцій. Межа Python/JS: поля відповіді читача → `КОЛІР` показу →
ключі входу моста (`показ/*.js`) → вхід ендпойнтів `bridge.виклик` (зі шва `показ/воркер_міст.js`). Ключ входу, що
несе hex, дає ознаку; інші ключі входу — лише «може містити профіль». Мітки: S — її колорит з моделі; P — вхід
показу; F — запис рис із `from_photo`; R — довіра з `AXIS_RELIABILITY`.

НЕ МІСЦЕ: її самозвіт і елісітація (власне джерело), `spectro`, освітлення портрета (`light_cast`, `light_correction`),
службові `_meta`, обраний макіяж (`_макіяж`, `макіяж_*`), кількість (`len`), рядкові порівняння коду протоколу.
Обсяг Python — `джерела/*.py` продукту без вимірників і фікстур (`батарея_*`, `gate_*`, `measure_*`, `стенд_*`,
`тест_*`, `audit_*`, `pair_test`, `run_outfit`, `status_перевірки`), лише код, досяжний зі шва показу; JS —
`джерела/показ/*.js` (межа й перевірка, що JS hex лише несе й показує).

ВИВІД: `файл:рядок · п.N · чому`, підсумки за пунктами, межа Python/JS, самоперевірка відомих місць паспорта (8 ід)
і не-місць, останній рядок `місць: <N>` (різні `файл:рядок`); код 0 (формат храповика, `аудит/КОД.md`).
Запуск: python3 -W ignore джерела/прилади/корінь_річ_ознаки_обличчя.py [--корінь <дерево>] [--стенд]"""
import argparse, ast, collections, glob, os, re, sys, warnings

ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)")
S, P, F, R, C = "S", "P", "F", "R", "C"
# C — дані з файлу (каталог крамниць, кеші фіду): число з її ознаки й такого запису разом — про річ, не про її колорит
ФАЙЛОВІ = frozenset(("open", "load", "parse", "fromstring", "iterparse", "read_text", "read_bytes", "urlopen",
                     "reader", "DictReader", "XML"))
ВМІСТИЩА = frozenset(("list", "tuple", "dict", "set", "frozenset", "sorted", "zip", "reversed", "enumerate", "filter",
                      "map", "iter", "next", "chain", "deepcopy", "copy", "OrderedDict", "defaultdict", "Counter"))


def _пара(*мітки):
    """Мітки числа з кількох операндів. Її значення (S) разом з іншим зовнішнім значенням без S — входу (P) чи запису
    з файлу (C): річ, нагода, лічба — число про пару, а не про її колорит, і S знімається; зі сталими й таблицями
    коду (без міток) чи з іншою її ознакою S лишається."""
    вих = E
    for м in мітки:
        вих = вих | м
    if S in вих and any(S not in м and (P in м or C in м) for м in мітки):
        вих = вих - {S}
    return вих
E = frozenset()
СЛУЖБОВІ = re.compile(r"^(_meta|_макіяж|макіяж_|protocol$|from_photo$|source$|photo_note$)")
НЕВІДОМЕ = re.compile(r"не стверджу|not_asserted|unknown|невідом|не визнач|н/д|^none$|не калібр|^free$|вільн|^—$|\bнема\b|не чита",
                      re.IGNORECASE)
ВИМІР = re.compile(r"(?<!not )(?<!un)(?<!не )\b(measured|measures|measure|виміря\w*|вимір\w*)", re.IGNORECASE)
HEX_РЕГ = re.compile(r"\[0-9a-fA-F\]\{6\}|\[0-9A-Fa-f\]\{6\}")
ПОРЯДОК = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)
БУЛЕВІ = frozenset(("len", "isinstance", "issubclass", "hasattr", "callable", "bool", "any", "all", "id", "type",
                    "print", "hash", "range"))
# методи, що повертають позицію, лічбу чи так/ні, а не значення
ПОЗИЦІЙНІ = frozenset(("find", "rfind", "index", "rindex", "count", "startswith", "endswith", "isdigit", "isalpha",
                       "isalnum", "isspace", "islower", "isupper", "isnumeric", "isdecimal", "isidentifier"))
МУТАЦІЇ = frozenset(("append", "extend", "add", "insert", "update", "setdefault", "appendleft", "extendleft", "feed"))
Місце = collections.namedtuple("Місце", "файл рядок пункт чому")


class Функція:
    def __init__(self, модуль, ім, вузол, батько):
        self.модуль, self.ім, self.вузол, self.батько = модуль, ім, вузол, батько
        а = вузол.args
        self.позиційні = [x.arg for x in а.posonlyargs + а.args]
        self.іменні = [x.arg for x in а.kwonlyargs]
        self.зірка = а.vararg.arg if а.vararg else None
        self.дві_зірки = а.kwarg.arg if а.kwarg else None
        типові = {}
        for x, д in zip(reversed(а.args), reversed(а.defaults)):
            типові[x.arg] = д
        for x, д in zip(а.kwonlyargs, а.kw_defaults):
            if д is not None:
                типові[x.arg] = д
        self.типові = типові

    @property
    def повне(self):
        return "%s.%s" % (self.модуль.ім, self.ім)


class Модуль:
    def __init__(self, ім, шлях, дерево):
        self.ім, self.шлях, self.дерево = ім, шлях, дерево
        self.імпорти, self.з_імпортів, self.зірки = {}, {}, []
        self.функції, self.присвоєння, self.лямбди = {}, {}, {}
        for n in ast.walk(дерево):
            if isinstance(n, ast.Import):
                for а in n.names:
                    self.імпорти[а.asname or а.name.split(".")[0]] = а.name
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for а in n.names:
                    if а.name == "*":
                        self.зірки.append(n.module)
                    else:
                        self.з_імпортів[а.asname or а.name] = (n.module, а.name)
        for n in дерево.body:
            if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
                self.присвоєння[n.targets[0].id] = n.value
            elif isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.value is not None:
                self.присвоєння[n.target.id] = n.value
        self._зібрати(дерево.body, "", None)

    def _зібрати(self, тіло, префікс, батько):
        for n in тіло:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                ім = префікс + n.name
                ф = Функція(self, ім, n, батько)
                self.функції[ім] = ф
                self._зібрати(n.body, ім + ".", ф)
                self._лямбди(n, ф)
            elif isinstance(n, ast.ClassDef):
                self._зібрати(n.body, префікс + n.name + ".", батько)
            elif батько is None:
                self._лямбди(n, None)

    def _лямбди(self, вузол, власник):
        стек = [вузол] if not isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef)) else list(вузол.body)
        while стек:
            n = стек.pop()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            if isinstance(n, ast.Lambda):
                ім = "λ%d:%d" % (n.lineno, n.col_offset)
                if ім not in self.функції:
                    self.функції[ім] = Функція(self, ім, n, власник)
                    self.лямбди[id(n)] = self.функції[ім]
            стек.extend(ast.iter_child_nodes(n))


def _імена(в):
    return {x.id for x in ast.walk(в) if isinstance(x, ast.Name)}


def _число(в):
    return isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool)


def _край_таблиці(в, т):
    """`T.get((15, h)) if L < 15 else None`: межа — край сітки таблиці (той самий вузол 15 у ключі пошуку), а не поріг
    рішення: за краєм функція бере крайній вузол замість екстраполяції."""
    гілки = [в.body, в.orelse]
    if not any(isinstance(г, ast.Constant) and г.value is None for г in гілки):
        return False
    межа = т.comparators[0].value
    for г in гілки:
        for n in ast.walk(г):
            ключ = n.slice if isinstance(n, ast.Subscript) else n.args[0] if isinstance(n, ast.Call) and \
                isinstance(n.func, ast.Attribute) and n.func.attr == "get" and n.args else None
            if isinstance(ключ, ast.Tuple) and any(_число(x) and x.value == межа for x in ключ.elts):
                return True
    return False


def _формульні(дерево):
    """Порівняння — шматок формули, а не поріг рішення: кусково задана функція тієї самої величини
    (`f(L) if L > 8.0 else g(L)`, `x / (a+b) if (a+b) > 0 else 0.0`) чи нормування кута
    (`if d > 180: d = 360 - d`). Межу ставить формула, а не код про неї."""
    вих = set()
    for в in ast.walk(дерево):
        if isinstance(в, ast.For) and isinstance(в.iter, ast.Call) and isinstance(в.iter.func, ast.Name) \
                and в.iter.func.id == "zip" and len(в.iter.args) == 2 and isinstance(в.iter.args[0], ast.Name) \
                and isinstance(в.iter.args[1], ast.Subscript) and isinstance(в.iter.args[1].slice, ast.Slice) \
                and isinstance(в.iter.args[1].value, ast.Name) and в.iter.args[1].value.id == в.iter.args[0].id:
            # `for (x0, y0), (x1, y1) in zip(якорі, якорі[1:]): if g <= x1: …` — відрізок кусково-лінійної
            # функції за таблицею якорів, а не поріг: межі ставить таблиця формули
            цілі = _імена(в.target)
            for і in в.body:
                т = getattr(і, "test", None)
                if isinstance(і, ast.If) and isinstance(т, ast.Compare) and len(т.ops) == 1 \
                        and _імена(т.comparators[0]) and _імена(т.comparators[0]) <= цілі:
                    вих.add(id(т))
        т = getattr(в, "test", None)
        if isinstance(в, ast.If) and not в.orelse and len(в.body) == 1 and isinstance(в.body[0], ast.AugAssign) \
                and isinstance(т, ast.Compare) and len(т.ops) == 1 and isinstance(в.body[0].target, ast.Name) \
                and _число(в.body[0].value) and abs(в.body[0].value.value) == 360 \
                and в.body[0].target.id in _імена(т):
            вих.add(id(т))   # `if b < a: b += 360` — розгортка дуги через 0°, а не поріг
            continue
        порівняння = т.values if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And) else [т]
        if not all(isinstance(x, ast.Compare) and len(x.ops) == 1 and _число(x.comparators[0]) for x in порівняння):
            continue
        if len(порівняння) > 1:   # `f(r) if σ > 0 and r > 0 else 0.0` — охорона ділення чи кореня всієї формули
            if isinstance(в, ast.IfExp) and isinstance(в.body, ast.BinOp) and _число(в.orelse) and в.orelse.value == 0 \
                    and set().union(*(_імена(x.left) for x in порівняння)) <= _імена(в.body):
                вих.update(id(x) for x in порівняння)
            continue
        ім = _імена(т.left)
        if not ім:
            continue
        if isinstance(в, ast.IfExp) and _край_таблиці(в, т):
            вих.add(id(т))
            continue
        if isinstance(в, ast.IfExp):
            if not isinstance(в.body, ast.BinOp) or not ім <= _імена(в.body):
                continue
            if ім <= _імена(в.orelse) and isinstance(в.orelse, (ast.BinOp, ast.Call, ast.Name)) \
                    or _число(в.orelse) and в.orelse.value == 0:
                вих.add(id(т))
        elif isinstance(в, ast.If) and not в.orelse and len(в.body) == 1 and isinstance(в.body[0], ast.Assign) \
                and isinstance(т.left, ast.Name) and isinstance(в.body[0].value, ast.BinOp) \
                and [ц.id for ц in в.body[0].targets if isinstance(ц, ast.Name)] == [т.left.id] \
                and т.left.id in _імена(в.body[0].value):
            вих.add(id(т))
    return вих


def _значення_полів(дерево):
    """Поле → рядкові значення, які йому дають літерали словників модуля (`{"поле": "довжина_см"}`,
    `dict(поле="верх_см")`): `р.get(сп["поле"])` читає лише ці ключі, а не всі ключі запису."""
    вих = collections.defaultdict(set)
    for в in ast.walk(дерево):
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if _рядок(к) and _рядок(з):
                    вих[к.value].add(з.value)
        elif isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
            for кв in в.keywords:
                if кв.arg and _рядок(кв.value):
                    вих[кв.arg].add(кв.value.value)
    return {к: frozenset(в) for к, в in вих.items()}


class Аналіз:
    def __init__(self, корінь):
        self.корінь = корінь
        self.модулі = {}
        self.синтетичні, self.тримати = {}, []   # `map(f, xs)` → виклик f(xs[і]); вузли тримаються, щоб id не мінявся
        self.формульні = set()
        self.значення_полів = {}   # модуль → поле → рядки, які літерали словників модуля кладуть у це поле
        for шлях in sorted(glob.glob(os.path.join(корінь, "джерела", "*.py"))):
            ім = os.path.basename(шлях)[:-3]
            if ВИКЛЮЧЕНО.match(ім):
                continue
            with open(шлях, encoding="utf-8") as ф:
                текст = ф.read()
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    дерево = ast.parse(текст)
                except SyntaxError:
                    continue
            self.модулі[ім] = Модуль(ім, os.path.relpath(шлях, корінь), дерево)
            self.формульні |= _формульні(дерево)
            self.значення_полів[ім] = _значення_полів(дерево)
        self.пам = {}             # (функція, контекст) → мітки повернення
        self.ключі_пов = collections.defaultdict(lambda: collections.defaultdict(frozenset))  # функція → ключ → мітки
        self.глоб = collections.defaultdict(frozenset)                                       # (модуль, ім) → мітки
        self.середовища = collections.defaultdict(dict)                                     # функція → останнє env
        self.місця = {}
        self.змінилось = False
        self.у_роботі = set()
        self.відвідано = set()
        self.зерно = None         # (модуль оголошення, ім оголошення, hex-ключі, форма, читач)
        self.функції_зерна = set()
        self.носії = set()        # ключі входу моста, що несуть hex (з JS)
        self.межа = {}
        self.оголошення = {}      # (модуль, ім) → {поле: (рядок, текст)}
        self.перевірки = {}
        self.звідки, self.поточний = {}, None
        self.кортежі, self.останній_кортеж = {}, None    # (функція, контекст) → мітки елементів повернутого кортежу
        self.ключі_пам, self.останні_ключі = {}, None    # (функція, контекст) → ключ повернутого dict → мітки

    # ── розв'язання імен ──────────────────────────────────────────────
    def у_модулі(self, мод, ім, глибина=0):
        м = self.модулі.get(мод)
        if not м or глибина > 6:
            return None
        if ім in м.функції and "." not in ім:
            return м.функції[ім]
        if ім in м.з_імпортів:
            return self.у_модулі(*м.з_імпортів[ім], глибина=глибина + 1)
        в = м.присвоєння.get(ім)
        if isinstance(в, (ast.Name, ast.Attribute)):
            return self.вираз_функції(м, в, None, глибина + 1)
        for з in м.зірки:
            ф = self.у_модулі(з, ім, глибина + 1)
            if ф:
                return ф
        return None

    def вираз_функції(self, м, в, ф, глибина=0):
        if глибина > 6:
            return None
        if isinstance(в, ast.Name):
            о = ф
            while о is not None:
                кандидат = м.функції.get(о.ім + "." + в.id)
                if кандидат:
                    return кандидат
                о = о.батько
            return self.у_модулі(м.ім, в.id, глибина)
        if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name):
            мод = м.імпорти.get(в.value.id)
            if мод is None and в.value.id in м.з_імпортів:
                мм, ім = м.з_імпортів[в.value.id]
                мод = мм + "." + ім if (мм + "." + ім) in self.модулі else (ім if ім in self.модулі else None)
            if мод:
                return self.у_модулі(мод.split(".")[-1], в.attr, глибина)
        return None

    def викликані(self, м, в, ф):
        """Вираз виклику → функції продукту (пряма, таблиця функцій, фабрика лямбди, лямбда)."""
        if isinstance(в, ast.Lambda):
            л = м.лямбди.get(id(в))
            return [л] if л else []
        if isinstance(в, ast.Subscript):
            табл = в.value
            if isinstance(табл, ast.Name) and табл.id in м.присвоєння:
                табл = м.присвоєння[табл.id]
            if isinstance(табл, ast.Dict):
                вих = []
                for з in табл.values:
                    вих.extend(self.значення_функції(м, з, ф))
                return вих
            return []
        ц = self.вираз_функції(м, в, ф)
        return [ц] if ц else []

    def значення_функції(self, м, в, ф):
        """Значення таблиці → функції: лямбда, ім'я функції, виклик фабрики (її повернені лямбди й функції)."""
        if isinstance(в, ast.Lambda):
            л = м.лямбди.get(id(в))
            return [л] if л else []
        if isinstance(в, (ast.Name, ast.Attribute)):
            ц = self.вираз_функції(м, в, ф)
            return [ц] if ц else []
        if isinstance(в, ast.Call):
            фабрика = self.вираз_функції(м, в.func, ф)
            if фабрика and isinstance(фабрика.вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
                вих = []
                for n in ast.walk(фабрика.вузол):
                    if isinstance(n, ast.Return) and n.value is not None:
                        вих.extend(self.значення_функції(фабрика.модуль, n.value, фабрика))
                return вих
        return []

    # ── місця ─────────────────────────────────────────────────────────
    def місце(self, м, вузол, пункт, чому):
        ключ = (м.шлях, вузол.lineno)
        self.місця.setdefault(ключ, set()).add((пункт, чому))

    # ── аналіз функції ────────────────────────────────────────────────
    def аналізувати(self, ф, контекст):
        ключ = (ф.повне, контекст)
        if ключ in self.у_роботі or ключ in self.відвідано:
            return self.пам.get(ключ, E)
        self.у_роботі.add(ключ)
        с = Стан(self, ф, контекст)
        попередній, self.поточний = self.поточний, ключ
        пов = с.виконати()
        self.поточний = попередній
        self.у_роботі.discard(ключ)
        self.відвідано.add(ключ)
        if с.кортеж:
            було = self.кортежі.get(ключ)
            нове = [_злити_ел(x, y) for x, y in zip(було, с.кортеж)] if було and len(було) == len(с.кортеж) else list(с.кортеж)
            if нове != було:
                self.кортежі[ключ] = нове
                self.змінилось = True
        кп = self.ключі_пам.setdefault(ключ, {})
        загальні = self.ключі_пов[ф.повне]
        for к, в in с.ключі_пов.items():
            if в - кп.get(к, E):
                кп[к] = кп.get(к, E) | в
                self.змінилось = True
            загальні[к] = загальні[к] | в
        старе = self.пам.get(ключ, E)
        if пов - старе:
            self.пам[ключ] = старе | пов
            self.змінилось = True
        стар_env = self.середовища[ф.повне]
        for к, в in с.env.items():
            if в - стар_env.get(к, E):
                стар_env[к] = стар_env.get(к, E) | в
                self.змінилось = True
        return self.пам.get(ключ, E)

    def виклик(self, ф, позиційні, іменні, зірка=E, дві_зірки=E):
        """Аргументи (мітки, ключі dict чи None) → контекст параметрів → (мітки повернення, ключі повернення)."""
        к, км = {}, {}

        def дати(п, значення):
            мітки, ключі = значення if isinstance(значення, tuple) else (значення, None)
            к[п] = к.get(п, E) | мітки
            if ключі:
                ц = км.setdefault(п, {})
                for кл, в in ключі.items():
                    ц[кл] = ц.get(кл, E) | в
        for i, з in enumerate(позиційні):
            if i < len(ф.позиційні):
                дати(ф.позиційні[i], з)
            elif ф.зірка:   # `*а` — ключі за номером, щоб `f(*а)` далі ліг на ті самі параметри
                дати(ф.зірка, з[0] | _усі(з[1]) if isinstance(з, tuple) else з)
                дати("%s#%d" % (ф.зірка, i - len(ф.позиційні)), з)
        for ім, з in іменні.items():
            if ім in ф.позиційні or ім in ф.іменні:
                дати(ім, з)
            elif ф.дві_зірки:   # `**к` — ключ за іменем аргументу
                дати(ф.дві_зірки, (E, {ім: з[0] | _усі(з[1]) if isinstance(з, tuple) else з}))
                дати("%s#%s" % (ф.дві_зірки, ім), з)
        if зірка:
            for п in ф.позиційні + ([ф.зірка] if ф.зірка else []):
                дати(п, зірка)
        if дві_зірки:
            for п in ф.позиційні + ф.іменні + ([ф.дві_зірки] if ф.дві_зірки else []):
                дати(п, дві_зірки)
        контекст = frozenset((п, frozenset(к.get(п, E)), frozenset((кл, frozenset(в)) for кл, в in км.get(п, {}).items()
                                                                  if в))
                             for п in set(к) | set(км) if к.get(п) or any(км.get(п, {}).values()))
        if контекст and (ф.повне, контекст) not in self.звідки:
            self.звідки[(ф.повне, контекст)] = self.поточний
        пов = self.аналізувати(ф, контекст)
        self.останній_кортеж = self.кортежі.get((ф.повне, контекст))
        self.останні_ключі = self.ключі_пам.get((ф.повне, контекст)) or None
        return пов

    # ── зерно й межа ──────────────────────────────────────────────────
    def знайти_зерно(self):
        """Оголошення, чий скелет відповіді несе `<hex>`, його hex-поля, форма й читач форми (`схеми_розбору`)."""
        for м in self.модулі.values():
            for ім, в in м.присвоєння.items():
                if not (isinstance(в, ast.Call) and _ім_виклику(в.func) == "Оголошення"):
                    continue
                кв = {к.arg: к.value for к in в.keywords}
                поля = {}
                for п in (кв.get("вхід").elts if isinstance(кв.get("вхід"), ast.Tuple) else []):
                    if isinstance(п, ast.Call) and п.args and isinstance(п.args[0], ast.Constant):
                        тексти = [а.value for а in п.args[1:] if isinstance(а, ast.Constant) and isinstance(а.value, str)]
                        тексти += [к.value.value for к in п.keywords if к.arg in ("що", "як") and
                                   isinstance(к.value, ast.Constant) and isinstance(к.value.value, str)]
                        поля[str(п.args[0].value).split(".")[0]] = (п.lineno, " ".join(тексти))
                self.оголошення[(м.ім, ім)] = поля
                скелет = кв.get("скелет")
                if not isinstance(скелет, ast.Dict):
                    continue
                hexи = [к.value for к, з in zip(скелет.keys, скелет.values) if isinstance(к, ast.Constant)
                        and "<hex>" in ast.unparse(з)]
                if hexи and isinstance(кв.get("вихід"), ast.Constant):
                    self.зерно = dict(модуль=м.ім, ім=ім, ключі=frozenset(hexи), форма=кв["вихід"].value,
                                      рядок=в.lineno)
        if not self.зерно:
            return
        for м in self.модулі.values():
            for n in ast.walk(м.дерево):
                if isinstance(n, ast.Dict):
                    for к, з in zip(n.keys, n.values):
                        if isinstance(к, ast.Constant) and к.value == self.зерно["форма"] and isinstance(з, ast.Call):
                            for кв in з.keywords:
                                if кв.arg == "розбір":
                                    ц = self.вираз_функції(м, кв.value, None)
                                    if ц:
                                        self.зерно["читач"] = ц
        читач = self.зерно.get("читач")
        if читач:
            черга = [читач]
            while черга:
                ф = черга.pop()
                if ф.повне in self.функції_зерна:
                    continue
                self.функції_зерна.add(ф.повне)
                for n in ast.walk(ф.вузол):
                    if isinstance(n, ast.Call):
                        ц = self.вираз_функції(ф.модуль, n.func, ф)
                        if ц and ц.модуль is ф.модуль:
                            черга.append(ц)

    def межа_js(self, поля_читача):
        """Поля відповіді читача → поля `КОЛІР` показу → ключі входу моста, що несуть hex."""
        тексти = {}
        for шлях in sorted(glob.glob(os.path.join(self.корінь, "джерела", "показ", "*.js"))):
            with open(шлях, encoding="utf-8") as ф:
                тексти[os.path.relpath(шлях, self.корінь)] = ф.read()
        поля = "|".join(sorted(re.escape(п) for п in поля_читача)) or "^$"
        поля_колір = set()
        for т in тексти.values():
            for м in re.finditer(r"\bКОЛІР\s*=\s*\{(.*?)\};", т, re.S):
                for к, з in _властивості(м.group(1)):
                    if re.search(r"\.(%s)\b" % поля, з):
                        поля_колір.add(к)
        пк = "|".join(sorted(re.escape(п) for п in поля_колір)) or "^$"
        носії, читачі, обчислення = set(), [], []
        for шлях, т in тексти.items():
            аліаси = set(re.findall(r"\b([\wа-яіїєґʼ']+)\s*=\s*[\wа-яіїєґʼ']+\.колір\s*(?:\|\|\s*\{\})?\s*[,;]", т))
            імена = ["КОЛІР"] + sorted(аліаси)
            шаблон = r"\b(?:%s)\.(?:точки\s*\|\|\s*\{\}\)\.)?(?:%s)\b" % ("|".join(map(re.escape, імена)), пк)
            for к, з in _властивості(т):
                if re.match(r"\s*\(?\s*" + шаблон, з):
                    носії.add(к)
            for н, рядок in enumerate(т.splitlines(), 1):
                if re.search(r"\bКОЛІР\.(?:%s)\b" % пк, рядок):
                    читачі.append((шлях, н))
                    без_стрілок = рядок.replace("=>", " ")
                    if re.search(r"\bКОЛІР\.(?:%s)\b[^;]*?(?<![=!<>])[<>](?!=?>)|[-+*/]\s*КОЛІР\.(?:%s)\b|\bКОЛІР\.(?:%s)"
                                 r"(?:\.\w+)?\s*[-+*/](?!/)" % (пк, пк, пк), без_стрілок):
                        обчислення.append((шлях, н, рядок.strip()[:90]))
        self.носії = носії | {п for п in поля_колір if п in носії}
        self.межа = dict(поля_читача=sorted(поля_читача), поля_колір=sorted(поля_колір), носії=sorted(self.носії),
                         читачі=читачі, обчислення=обчислення)
        return обчислення

    def входи_шва(self):
        """Ендпойнти, які кличе шов показу (`bridge.<ім>` у `показ/воркер_міст.js`), і таблиця `bridge.виклик`."""
        шлях = os.path.join(self.корінь, "джерела", "показ", "воркер_міст.js")
        імена = set()
        if os.path.isfile(шлях):
            with open(шлях, encoding="utf-8") as ф:
                імена = set(re.findall(r"\bbridge\.([\wа-яіїєґʼ']+)\s*\(", ф.read()))
        вих = []
        м = self.модулі.get("bridge")
        for ім in sorted(імена):
            ф = self.у_модулі("bridge", ім) if м else None
            if ф:
                вих.append(ф)
        return вих

    def таблиці_причин(self):
        """Таблиці звірки: dict модуля, значення якого — функції, і який кличуть за ключем (`ТАБЛ[к](...)`)."""
        self.перевірки = collections.defaultdict(list)     # функція → [(модуль, рядок рядка таблиці, ключ)]
        for м in self.модулі.values():
            кличуть = {n.func.value.id for n in ast.walk(м.дерево) if isinstance(n, ast.Call)
                       and isinstance(n.func, ast.Subscript) and isinstance(n.func.value, ast.Name)}
            for ім in кличуть:
                табл = м.присвоєння.get(ім)
                if not isinstance(табл, ast.Dict):
                    continue
                for к, з in zip(табл.keys, табл.values):
                    if not _рядок(к):
                        continue
                    for ц in self.значення_функції(м, з, None):
                        self.перевірки[ц.повне].append((м, к, к.value))

    def прогін(self):
        self.знайти_зерно()
        self.таблиці_причин()
        входи = self.входи_шва()
        for _ in range(12):
            self.змінилось = False
            self.відвідано = set()
            if self.зерно and self.зерно.get("читач"):
                ч = self.зерно["читач"]
                self.виклик(ч, [frozenset({P})] * len(ч.позиційні), {})
                поля = sorted({str(к).split("/")[0] for к, в in self.ключі_пов[ч.повне].items() if S in в})
                if not self.носії:
                    self.межа_js(поля)
            for ф in входи:
                self.виклик(ф, [frozenset({P})] * max(1, len(ф.позиційні)), {})
            if not self.змінилось:
                break


ТОКЕН = "#"   # токен коду заяви: мітка "#<код>" — заява цього коду; S з токенами — її значення в заявах цих кодів


def _токени(мітки):
    return frozenset(м for м in (мітки or ()) if isinstance(м, str) and м.startswith(ТОКЕН))


def _звузити(мітки, дозволені):
    """Мітки значення в гілці, що йде лише для кодів `дозволені`: значення заяв інших кодів її колориту не несуть."""
    т = _токени(мітки)
    if S in мітки and т and not (т & дозволені):
        return frozenset(мітки - {S} - т)
    return мітки


МАПА, МАПА_М = "{}", frozenset({"D"})
# Ключ-позначка МАПА: значення — словник за змінним ключем (`d[ід] = запис`, `{с: пул for …}`), його ключі — ключі
# елемента. Перебір (`for к in d`, `list(d)`, `sorted(d)`) дає ключі-рядки, а не записи; `d.values()` — записи.
# Мітка позначки — не мітка значення: у суму ключів (`_усі`, `читати`) не йде.


def _усі(ключі):
    вих = E
    for к, в in (ключі or {}).items():
        if к != МАПА:
            вих = вих | в
    return вих


def _без_мапи(ключі):
    """Ключі елемента словника-мапи чи списку: без позначки МАПА верхнього рівня."""
    return {к: в for к, в in (ключі or {}).items() if к != МАПА} or None


def _перебір(мітки, ключі):
    """Елемент перебору: мапа дає ключі-рядки (мітки поза ключами), список записів — запис із ключами."""
    if ключі and МАПА in ключі:
        return мітки, None
    return мітки, ключі


ГЛИБИНА = 3   # ключі запису за шляхом «ключ/під/…»: список записів ділить ключі з записом


def _під(ключі, ключ):
    """Ключі значення під `ключ` (шлях «ключ/під»)."""
    п = "%s/" % ключ
    return {к[len(п):]: в for к, в in (ключі or {}).items() if isinstance(к, str) and к.startswith(п)}


def _з_префіксом(ключ, ключі):
    """Ключі значення під `ключ`; глибше за ГЛИБИНУ — мітки найглибшого дозволеного предка (не губляться)."""
    вих = {}
    for к, в in (ключі or {}).items():
        if not в:
            continue
        шлях = "%s/%s" % (ключ, к)
        частини = шлях.split("/")
        if len(частини) > ГЛИБИНА:
            if частини[-1] == МАПА:
                continue
            шлях = "/".join(частини[:ГЛИБИНА])
        вих[шлях] = вих.get(шлях, E) | в
    return вих


def _без_першого(ключі):
    """Ключі елемента за змінним ключем: і ключі самого запису, і під будь-яким його ключем."""
    вих = {к: в for к, в in (ключі or {}).items() if к != МАПА}
    for к, в in (ключі or {}).items():
        if isinstance(к, str) and "/" in к:
            р = к.split("/", 1)[1]
            if р != МАПА:
                вих[р] = вих.get(р, E) | в
    return вих


def _злити_ключі(*набори):
    вих = {}
    for н in набори:
        for к, в in (н or {}).items():
            вих[к] = вих.get(к, E) | в
    return вих


def _ел(мітки, ключі=None):
    """Елемент повернутого кортежу: мітки поза ключами й ключі dict (сталий, порівнюваний вигляд)."""
    return frozenset(мітки), frozenset((к, frozenset(в)) for к, в in (ключі or {}).items() if в)


def _злити_ел(а, б):
    ключі = dict(а[1])
    for к, в in б[1]:
        ключі[к] = ключі.get(к, E) | в
    return _ел(а[0] | б[0], ключі)


def _ім_виклику(в):
    return в.id if isinstance(в, ast.Name) else в.attr if isinstance(в, ast.Attribute) else None


def _властивості(текст):
    """Пари `ключ: значення` об'єктних літералів JS (значення — до коми чи дужки на тому ж рівні, грубо)."""
    for м in re.finditer(r"(?<![\wа-яіїєґʼ'.])([\wа-яіїєґʼ']+)\s*:(?!:)\s*([^,{};\n]*(?:\([^()\n]*\)[^,{};\n]*)*)", текст):
        yield м.group(1), м.group(2)


def _корінь_імені(в):
    while isinstance(в, (ast.Subscript, ast.Attribute, ast.Starred)):
        в = в.value
    return в.id if isinstance(в, ast.Name) else None


def _рядок(в):
    return isinstance(в, ast.Constant) and isinstance(в.value, str)


def _шлях(в):
    """`d["а"]["б"][і]` → ("d", ["а", "б"], чи далі змінний ключ): сталий префікс шляху від імені."""
    ключі = []
    while isinstance(в, ast.Subscript):
        ключі.append(в.slice.value if _рядок(в.slice) else None)
        в = в.value
    if not isinstance(в, ast.Name):
        return None, [], False
    ключі.reverse()
    префікс = []
    for к in ключі:
        if к is None:
            break
        префікс.append(к)
    return в.id, префікс, len(префікс) < len(ключі)


class Стан:
    """Один аналіз функції в контексті: env імен → мітки, без порядку інструкцій (до нерухомої точки)."""

    def __init__(self, а, ф, контекст):
        self.а, self.ф, self.м = а, ф, ф.модуль
        self.env = {}
        self.ключі = collections.defaultdict(lambda: collections.defaultdict(frozenset))
        self.розгорнуті = collections.defaultdict(dict)   # `*а`/`**к` → номер чи ім'я → (мітки, ключі)
        for п, мітки, км in контекст:
            if "#" in п:
                осн, _, де = п.partition("#")
                self.розгорнуті[осн][int(де) if де.isdigit() else де] = (мітки, (dict(км) or None))
                continue
            if мітки:
                self.env[п] = мітки
            for кл, в in км:
                self.ключі[п][кл] = в
        self.ключі_пов = {}
        self.ключі_циклу = {}    # ім'я циклу над кортежем рядків → ці рядки (`kw.get(k)` читає лише їх)
        self.ключі_викликів = {}  # id(виклик) → (мітки поза ключами, ключі повернення)
        self.глобальні = set()
        self.псевдоніми = {}     # ім'я → мапа, елементом якої воно є (`е = d.setdefault(к, …)`)
        self.невідомо = {}       # ім'я → гілка «невідомо» ("так"/"ні"), коли ім'я — перевірка невідомого на S
        self.пов = E
        self.кортеж, self.кортеж_зламано = None, False
        self.кортежі_викликів = {}
        self.локальні = set(self.env) | set(self.ключі) | set(ф.позиційні) | set(ф.іменні) | {ф.зірка, ф.дві_зірки}
        вузли = ф.вузол.body if isinstance(ф.вузол.body, list) else []
        for n in self._обійти(вузли):
            if isinstance(n, (ast.Name,)) and isinstance(n.ctx, ast.Store):
                self.локальні.add(n.id)
            elif isinstance(n, ast.Global):
                self.глобальні.update(n.names)
        self.локальні -= self.глобальні
        # інструкції верхнього рівня тіла: тут присвоєння імені замінює попереднє значення (далі по тілу ім'я
        # несе лише нове); у гілці чи циклі — додає, бо інший шлях міг лишити старе
        self.верх = set() if isinstance(ф.вузол, ast.Lambda) else {id(і) for і in ф.вузол.body}
        self.зерно = ф.повне in а.функції_зерна

    def _обійти(self, тіло):
        стек = list(тіло)
        while стек:
            n = стек.pop()
            yield n
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                continue
            стек.extend(ast.iter_child_nodes(n))

    def виконати(self):
        в = self.ф.вузол
        for _ in range(8):
            до = (dict(self.env), self.пов)
            if isinstance(в, ast.Lambda):
                self.пов |= self.e(в.body)
            else:
                self.тіло(в.body)
            if (self.env, self.пов) == до:
                break
        return frozenset(x for x in self.пов)

    # ── імена ──
    def читати(self, ім):
        return self.читати_env(ім) | _усі(self.ключі.get(ім))

    def ключ_імені(self, ім, ключ, вузол, типове=None):
        """`ім["к"]` / `ім.get("к")`: значення ключа, записане тут, і правило індексу на решті міток імені."""
        км = self.ключі.get(ім, {})
        return км.get(ключ, E) | _усі(_під(км, ключ)) | self.індекс(self.читати_env(ім), ast.Constant(ключ), вузол,
                                                                типове)

    def читати_env(self, ім):
        if ім in self.env:
            return self.env[ім]
        if ім not in self.локальні:
            о = self.ф.батько
            while о is not None:
                в = self.а.середовища.get(о.повне, {}).get(ім)
                if в:
                    return в
                о = о.батько
            return self.а.глоб.get((self.м.ім, ім), E)
        return E

    def наступний(self, в):
        return isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "next" and bool(в.args) \
            and not self.а.викликані(self.м, в.func, self.ф)

    def можливі_ключі(self, в):
        """Рядки, якими може бути ключ-вираз: ім'я циклу над кортежем рядків чи поле запису, якому літерали
        модуля дають лише рядки (`сп["поле"]`, `сп.get("поле")`); інакше None."""
        if isinstance(в, ast.Name):
            return self.ключі_циклу.get(в.id)
        поле = None
        if isinstance(в, ast.Subscript) and _рядок(в.slice):
            поле = в.slice.value
        elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                and _рядок(в.args[0]):
            поле = в.args[0].value
        return self.а.значення_полів.get(self.м.ім, {}).get(поле) if поле else None

    def писати(self, ім, мітки, мутація=False):
        """Мутація контейнера модуля з функції (`КЕШ[к] = …`, `ЗАПИСИ.append(…)`) — кеш чи слід: його читання в
        іншому виклику не несе її значення далі (на шляху, що рахує, значення й так іде поверненням)."""
        if not мітки:
            return
        if мутація and ім not in self.локальні and ім not in self.глобальні:
            return
        if ім in self.локальні or ім not in self.м.присвоєння:
            self.env[ім] = self.env.get(ім, E) | мітки
        if ім in self.глобальні or (ім not in self.локальні and ім in self.м.присвоєння):
            к = (self.м.ім, ім)
            if мітки - self.а.глоб[к]:
                self.а.глоб[к] = self.а.глоб[к] | мітки
                self.а.змінилось = True

    def присвоїти(self, ціль, мітки, значення=None):
        if isinstance(ціль, ast.Name):
            сам = значення.value if isinstance(значення, (ast.Await, ast.YieldFrom)) else значення
            if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "setdefault" \
                    and isinstance(сам.func.value, ast.Name) and сам.func.value.id in self.локальні:
                self.псевдоніми[ціль.id] = сам.func.value.id
            if isinstance(сам, (ast.IfExp, ast.BoolOp)):
                мітки, кл = self.значення(сам)
                for к, в in (кл or {}).items():
                    self.ключі[ціль.id][к] = self.ключі[ціль.id][к] | в
            elif self.з_ключами(значення):
                мітки = self.без_ключів(значення)
            elif isinstance(сам, ast.Call) and id(сам) in self.ключі_викликів and self.ключі_викликів[id(сам)][1]:
                мітки = self.ключі_викликів[id(сам)][0]
            elif isinstance(сам, ast.Name) and any(self.ключі.get(сам.id, {}).values()):
                мітки = self.читати_env(сам.id)
            elif isinstance(сам, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.List, ast.Subscript, ast.BinOp,
                                  ast.DictComp, ast.Tuple)) or self.наступний(сам) or (
                    isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute)
                    and сам.func.attr in ("get", "pop", "values")):
                м, кл = self.значення(сам)
                if кл:
                    мітки = м
                    for к, в in кл.items():
                        self.ключі[ціль.id][к] = self.ключі[ціль.id][к] | в
            self.писати(ціль.id, мітки)
            if isinstance(значення, ast.Compare):
                г = self.гілка_невідомо(значення)
                if г:
                    self.невідомо[ціль.id] = г
            if значення is not None:
                self.ключі_з(ціль.id, значення)
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            к = self.кортежі_викликів.get(id(значення)) if isinstance(значення, (ast.Call, ast.Await, ast.YieldFrom)) else None
            if isinstance(значення, (ast.Tuple, ast.List)) and len(значення.elts) == len(ціль.elts):
                for ц, з in zip(ціль.elts, значення.elts):
                    self.присвоїти(ц, self.e(з), з)
            elif к and len(к) == len(ціль.elts) and not any(isinstance(ц, ast.Starred) for ц in ціль.elts):
                for ц, (мк, кл) in zip(ціль.elts, к):
                    if isinstance(ц, ast.Name) and кл:
                        self.писати(ц.id, мк)
                        for кк, вв in кл:
                            self.ключі[ц.id][кк] = self.ключі[ц.id][кк] | вв
                    elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) and кл \
                            and ц.value.id in self.локальні:
                        # `d[к], інше = f(…)`: запис позиції кортежу — як `d[к] = запис`, ключі окремо від міток
                        self.e(ц.slice)
                        км = self.ключі[ц.value.id]
                        if _рядок(ц.slice):
                            км[ц.slice.value] = км[ц.slice.value] | (мк - {F})
                            for кк, вв in _з_префіксом(ц.slice.value, dict(кл)).items():
                                км[кк] = км[кк] | вв
                        else:
                            for кк, вв in кл:
                                км[кк] = км[кк] | вв
                            км[МАПА] = МАПА_М
                            self.писати(ц.value.id, мк - {F}, мутація=True)
                    else:
                        self.присвоїти(ц, мк | _усі(dict(кл)))
            else:
                for ц in ціль.elts:
                    self.присвоїти(ц, мітки)
        elif isinstance(ціль, ast.Starred):
            self.присвоїти(ціль.value, мітки)
        elif isinstance(ціль, (ast.Subscript, ast.Attribute)):
            if isinstance(ціль, ast.Subscript):
                self.e(ціль.slice)
                вм, вк = self.значення(значення) if значення is not None else (мітки, None)
                if isinstance(ціль.value, ast.Name) and _рядок(ціль.slice):
                    for ім in (ціль.value.id, self.псевдоніми.get(ціль.value.id)):
                        if ім is None:
                            continue   # псевдонім елемента мапи (`е = d.setdefault(…)`): запис у е — запис в елемент d
                        к = self.ключі[ім]
                        к[ціль.slice.value] = к[ціль.slice.value] | вм
                        for кл, в in _з_префіксом(ціль.slice.value, вк).items():
                            к[кл] = к[кл] | в
                elif isinstance(ціль.value, ast.Subscript) and self.у_шлях(ціль, вм, вк):
                    return
                elif isinstance(ціль.value, ast.Subscript) and isinstance(ціль.value.value, ast.Name) \
                        and not _рядок(ціль.value.slice) and _рядок(ціль.slice) \
                        and ціль.value.value.id in self.локальні and ціль.value.value.id not in self.глобальні:
                    # `d[к]["поле"] = x`: поле елемента мапи d, а не мітка всієї d
                    self.e(ціль.value.slice)
                    км = self.ключі[ціль.value.value.id]
                    км[ціль.slice.value] = км[ціль.slice.value] | (вм - {F})
                    for кл, в in _з_префіксом(ціль.slice.value, вк).items():
                        км[кл] = км[кл] | в
                    км[МАПА] = МАПА_М
                    return
                elif isinstance(ціль.value, ast.Name) and вк and ціль.value.id in self.локальні:
                    # `d[ід] = запис`: ключі запису — ключі елемента d, d — мапа
                    к = self.ключі[ціль.value.id]
                    for кл, в in вк.items():
                        к[кл] = к[кл] | в
                    к[МАПА] = МАПА_М
                    self.писати(ціль.value.id, вм - {F}, мутація=True)
                    return
            корінь = _корінь_імені(ціль)
            ключем = isinstance(ціль, ast.Subscript) and isinstance(ціль.value, ast.Name) and _рядок(ціль.slice)
            if корінь and ключем and ціль.slice.value == "_meta":
                self.писати(корінь, frozenset({F}), мутація=True)
            elif корінь and not ключем:
                self.писати(корінь, мітки - {F}, мутація=True)

    def у_шлях(self, ціль, вм, вк):
        """Запис у `d["а"]["б"]…` (чи `.append` на ньому): мітки — ключу «а/б», ключі значення — під ним.
        Змінний ключ у кінці — як `d[ід] = запис`; змінний посередині — усе значення ключу префікса."""
        корінь, префікс, змінний = _шлях(ціль)
        if not корінь or not префікс or корінь not in self.локальні or корінь in self.глобальні:
            return False
        if len(префікс) > ГЛИБИНА:
            префікс, змінний = префікс[:ГЛИБИНА], True
            вм, вк = вм | _усі(вк), None
        шлях = "/".join(префікс)
        км = self.ключі[корінь]
        км[шлях] = км[шлях] | (вм - {F})
        for кл, в in _з_префіксом(шлях, вк).items():
            км[кл] = км[кл] | в
        return True

    def значення(self, в):
        """Вираз → (мітки поза сталими ключами, ключі dict чи None): ключі dict ідуть у виклик і з повернення окремо."""
        сам = в.value if isinstance(в, (ast.Await, ast.YieldFrom)) else в
        if isinstance(сам, (ast.IfExp, ast.BoolOp)):
            гілки = [сам.body, сам.orelse] if isinstance(сам, ast.IfExp) else list(сам.values)
            if isinstance(сам, ast.IfExp):
                self.e(сам.test)
            вих, ключі = E, {}
            for г in гілки:
                м, к = self.значення(г)
                вих |= м
                for кл, з in (к or {}).items():
                    ключі[кл] = ключі.get(кл, E) | з
            self.e(сам)   # місця гілки «невідомо» й запасного числа
            return вих, (ключі or None)
        if self.наступний(сам):
            # `next(р for р in речі if …)`: елемент послідовності — запис із її ключами, а не всі ключі разом
            м, к = self.значення(сам.args[0])
            if к:
                self.e(сам)
                к = dict(к)
                for д in сам.args[1:]:
                    мд, кд = self.значення(д)
                    м |= мд
                    for кл, з in (кд or {}).items():
                        к[кл] = к.get(кл, E) | з
                return м - {F}, к
        if isinstance(сам, ast.Subscript) and isinstance(сам.value, ast.Name) and self.ключі.get(сам.value.id):
            км = self.ключі[сам.value.id]
            self.e(сам)
            if _рядок(сам.slice):
                к = сам.slice.value
                return (км.get(к, E) | self.індекс(self.читати_env(сам.value.id), сам.slice, сам)), (_під(км, к) or None)
            if isinstance(сам.slice, ast.Constant) and type(сам.slice.value) is int and ("#%d" % сам.slice.value) in км:
                к = "#%d" % сам.slice.value
                return (км[к] | self.індекс(self.читати_env(сам.value.id), ast.Constant(к), сам)), (_під(км, к) or None)
            return self.індекс(self.читати_env(сам.value.id), сам.slice, сам), (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") and сам.args \
                and _рядок(сам.args[0]) and isinstance(сам.func.value, ast.Name) and self.ключі.get(сам.func.value.id) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            км = self.ключі[сам.func.value.id]
            к = сам.args[0].value
            self.e(сам)
            типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
            return (км.get(к, E) | типове | self.індекс(self.читати_env(сам.func.value.id), сам.args[0], сам)), \
                (_під(км, к) or None)
        if isinstance(сам, (ast.List, ast.Set)) or (isinstance(сам, ast.BinOp) and isinstance(сам.op, ast.Add)):
            частини = сам.elts if isinstance(сам, (ast.List, ast.Set)) else [сам.left, сам.right]
            вих, ключі = E, {}
            for ч in частини:
                м, к = self.значення(ч.value if isinstance(ч, ast.Starred) else ч)
                вих |= м
                ключі = _злити_ключі(ключі, к)
            return вих, (ключі or None)
        if isinstance(сам, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            self.e(сам)
            збережено = self.область(сам)
            try:
                м, к = self.значення(сам.elt)
            finally:
                self.відновити(збережено)
            return м - {F}, к
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and not _рядок(сам.args[0]) and isinstance(сам.func.value, ast.Name) \
                and self.ключі.get(сам.func.value.id) and not self.а.викликані(self.м, сам.func, self.ф) \
                and not self.можливі_ключі(сам.args[0]):
            # `d.get(змінний)`: елемент d за змінним ключем — як `d[змінний]`
            self.e(сам)
            км = self.ключі[сам.func.value.id]
            типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
            return (self.індекс(self.читати_env(сам.func.value.id), сам.args[0], сам) | типове) - {F}, \
                (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and not _рядок(сам.args[0]) and not isinstance(сам.func.value, ast.Name) \
                and not self.а.викликані(self.м, сам.func, self.ф) and not self.можливі_ключі(сам.args[0]):
            # `d["к"].get(змінний)`: елемент мапи під ключем — запис із ключами, а не сума всіх ключів
            мз, кз = self.значення(сам.func.value)
            if кз:
                self.e(сам)
                типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
                return (self.індекс(мз, сам.args[0], сам) | типове) - {F}, (_без_першого(кз) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr in ("get", "pop") \
                and сам.args and _рядок(сам.args[0]) and not isinstance(сам.func.value, ast.Name) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            мз, кз = self.значення(сам.func.value)
            к = сам.args[0].value
            if кз and (к in кз or _під(кз, к)):
                self.e(сам)
                типове = self.e(сам.args[1]) if len(сам.args) > 1 else E
                return (кз.get(к, E) | типове | self.індекс(мз, сам.args[0], сам)), (_під(кз, к) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "pop" \
                and isinstance(сам.func.value, ast.Name) and self.ключі.get(сам.func.value.id) \
                and (not сам.args or (isinstance(сам.args[0], ast.Constant) and type(сам.args[0].value) is int)) \
                and not self.а.викликані(self.м, сам.func, self.ф):
            # `список.pop(і)`: елемент списку записів — ключі запису, не їхня сума
            self.e(сам)
            км = self.ключі[сам.func.value.id]
            return self.індекс(self.читати_env(сам.func.value.id), ast.Constant(0), сам), (_без_першого(км) or None)
        if isinstance(сам, ast.Call) and isinstance(сам.func, ast.Attribute) and сам.func.attr == "values" \
                and not сам.args and not self.а.викликані(self.м, сам.func, self.ф):
            мз, кз = self.значення(сам.func.value)
            if кз and МАПА in кз:
                # `d.values()` мапи — її записи з ключами, а не сума всіх ключів
                self.e(сам)
                return мз - {F}, _без_мапи(кз)
        if isinstance(сам, ast.Subscript) and isinstance(сам.slice, ast.Slice):
            self.e(сам)
            return self.значення(сам.value)
        if isinstance(сам, ast.Subscript) and not isinstance(сам.value, ast.Name):
            мз, кз = self.значення(сам.value)
            if кз:
                self.e(сам)
                if _рядок(сам.slice):
                    к = сам.slice.value
                    return (кз.get(к, E) | self.індекс(мз, сам.slice, сам)), (_під(кз, к) or None)
                return self.індекс(мз, сам.slice, сам), (_без_першого(кз) or None)
        if isinstance(сам, ast.DictComp):
            self.e(сам)
            збережено = self.область(сам)
            try:
                мв, кв = self.значення(сам.value)
                мк = self.значення(сам.key)[0]
            finally:
                self.відновити(збережено)
            if кв:
                # ключ dict — рядок чи число, не запис: ключі запису, що їх несе ім'я ключа, у мітки не йдуть;
                # значення — запис чи список записів за змінним ключем: мапа
                return (мк | мв) - {F}, dict(_без_мапи(кв) or {}, **{МАПА: МАПА_М})
        if isinstance(сам, ast.Tuple) and сам.elts and not any(isinstance(x, ast.Starred) for x in сам.elts):
            ключі = {}
            for і, x in enumerate(сам.elts):
                м, к = self.значення(x)
                if м:
                    ключі["#%d" % і] = м
                ключі.update(_з_префіксом("#%d" % і, к))
            return E, (ключі or None)
        if isinstance(сам, ast.Name):
            к = self.ключі.get(сам.id)
            if к and any(к.values()):
                return self.читати_env(сам.id), dict(к)
            return self.читати(сам.id), None
        if self.з_ключами(сам):
            self.e(сам)
            return self.без_ключів(сам), (self.ключі_виразу(сам) or None)
        мітки = self.e(в)
        if isinstance(сам, ast.Call) and id(сам) in self.ключі_викликів:
            поза, ключі = self.ключі_викликів[id(сам)]
            return поза, (dict(ключі) or None)
        return мітки, None

    def область(self, в):
        """Генератори виразу-включення у власній області (Python 3): імена циклу не чіпають однойменних імен функції."""
        імена = {n.id for г in в.generators for n in ast.walk(г.target) if isinstance(n, ast.Name)}
        збережено = {ім: (self.env.get(ім), dict(self.ключі[ім]) if ім in self.ключі else None,
                          self.ключі_циклу.get(ім), self.невідомо.get(ім)) for ім in імена}
        for г in в.generators:
            self.ітерація(г.target, г.iter)
            for у in г.ifs:
                self.e(у)
        return збережено

    def відновити(self, збережено):
        for ім, (env, ключі, цикл, невідомо) in збережено.items():
            for сховище, значення in ((self.env, env), (self.ключі_циклу, цикл), (self.невідомо, невідомо)):
                if значення is None:
                    сховище.pop(ім, None)
                else:
                    сховище[ім] = значення
            self.ключі.pop(ім, None)
            if ключі is not None:
                self.ключі[ім].update(ключі)

    def ітерація(self, ціль, ітер):
        """`for ціль in ітер`: номер `enumerate` і ключ `.items()` — позиція й ім'я, не значення про колорит.
        Ім'я циклу щоразу прив'язане заново (сильне оновлення): два цикли з тим самим ім'ям не зливають елементів."""
        for n in ast.walk(ціль):
            if isinstance(n, ast.Name) and n.id in self.локальні and n.id not in self.глобальні:
                self.env.pop(n.id, None)
                self.ключі.pop(n.id, None)
        if isinstance(ціль, ast.Tuple) and len(ціль.elts) == 2 and isinstance(ітер, ast.Call) and \
                isinstance(ітер.func, ast.Name) and ітер.func.id == "enumerate" and ітер.args:
            self.e(ітер)
            self.присвоїти(ціль.elts[0], E)
            self.елемент(ціль.elts[1], *_перебір(*self.значення(ітер.args[0])))
            return
        if isinstance(ціль, ast.Tuple) and isinstance(ітер, ast.Call) and isinstance(ітер.func, ast.Name) and \
                ітер.func.id == "zip" and len(ітер.args) == len(ціль.elts) and not ітер.keywords and \
                not any(isinstance(x, ast.Starred) for x in ітер.args + ціль.elts):
            self.e(ітер)
            for ц, а in zip(ціль.elts, ітер.args):
                self.елемент(ц, *_перебір(*self.значення(а)))
            return
        if isinstance(ціль, ast.Tuple) and not any(isinstance(x, ast.Starred) for x in ціль.elts) and \
                not (isinstance(ітер, ast.Call) and _ім_виклику(ітер.func) in ("enumerate", "items")):
            м, кл = self.значення(ітер)
            if кл and any(isinstance(к, str) and к.startswith("#") for к in кл):
                self.e(ітер)
                for і, ц in enumerate(ціль.elts):
                    п = "#%d" % і
                    self.елемент(ц, (м | кл.get(п, E)) - {F}, _під(кл, п) or None)
                return
        мітки = self.e(ітер) - {F}
        if isinstance(ціль, ast.Tuple) and len(ціль.elts) == 2 and isinstance(ітер, ast.Call) and \
                isinstance(ітер.func, ast.Attribute) and ітер.func.attr == "items" and not ітер.args:
            self.присвоїти(ціль.elts[0], E)
            м, кл = self.значення(ітер.func.value)
            if кл:
                # значення dict за змінним ключем: мітки поза ключами й ключі елемента
                self.елемент(ціль.elts[1], м - {F}, _без_першого(кл))
            else:
                self.присвоїти(ціль.elts[1], мітки)
            return
        if isinstance(ціль, ast.Name):
            if isinstance(ітер, (ast.Tuple, ast.List, ast.Set)) and ітер.elts and all(_рядок(x) for x in ітер.elts):
                self.ключі_циклу[ціль.id] = self.ключі_циклу.get(ціль.id, frozenset()) | {x.value for x in ітер.elts}
            self.елемент(ціль, *_перебір(*self.значення(ітер)))
            return
        self.присвоїти(ціль, мітки)

    def елемент(self, ціль, мітки, ключі):
        """Елемент списку записів: мітки поза ключами й ключі запису."""
        if isinstance(ціль, ast.Name) and ключі:
            self.писати(ціль.id, мітки - {F})
            for кл, в in ключі.items():
                self.ключі[ціль.id][кл] = self.ключі[ціль.id][кл] | в
        else:
            self.присвоїти(ціль, (мітки | _усі(ключі)) - {F})

    def з_ключами(self, в):
        return isinstance(в, ast.Dict) or (isinstance(в, ast.Call) and _ім_виклику(в.func) == "dict"
                                           and isinstance(в.func, ast.Name))

    def без_ключів(self, в):
        """Мітки dict-літерала поза сталими ключами (розгортання, змінні ключі, позиційні аргументи `dict`)."""
        вих = E
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if к is None:
                    вих |= self.значення(з)[0]
                elif not _рядок(к):
                    вих |= self.e(з)
        else:
            for а in в.args:
                вих |= self.значення(а)[0]
            for к in в.keywords:
                if к.arg is None:
                    вих |= self.значення(к.value)[0]
        return вих

    def ключі_з(self, ім, в):
        """Ключі dict-літерала чи `dict(...)`, присвоєного імені (для повернення й опису полів)."""
        for к, з in self.ключі_виразу(в).items():
            self.ключі[ім][к] = self.ключі[ім][к] | з

    def ключі_виразу(self, в):
        вих = {}
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if _рядок(к):
                    м, кк = self.значення(з)
                    вих[к.value] = вих.get(к.value, E) | м
                    вих = _злити_ключі(вих, _з_префіксом(к.value, кк))
                elif к is None:
                    вих = _злити_ключі(вих, self.значення(з)[1])
        elif isinstance(в, ast.Call) and _ім_виклику(в.func) == "dict":
            for а in в.args:
                вих = _злити_ключі(вих, self.значення(а)[1])
            for к in в.keywords:
                if к.arg:
                    м, кк = self.значення(к.value)
                    вих[к.arg] = вих.get(к.arg, E) | м
                    вих = _злити_ключі(вих, _з_префіксом(к.arg, кк))
                else:
                    вих = _злити_ключі(вих, self.значення(к.value)[1])
        elif isinstance(в, (ast.Await, ast.YieldFrom)):
            вих.update(self.ключі_виразу(в.value))
        elif isinstance(в, ast.Call):
            вих.update(self.ключі_викликів.get(id(в), (E, {}))[1])
        elif isinstance(в, ast.Name):
            вих.update(self.ключі.get(в.id, {}))
        токени = _токени(вих.get("code"))
        if токени and self.з_ключами(в):
            for к in list(вих):
                if (к == "values" or к.startswith("values/")) and S in вих[к]:
                    вих[к] = вих[к] | токени
        return вих

    # ── інструкції ──
    def тіло(self, інструкції):
        for н, і in enumerate(інструкції):
            self.інструкція(і)
            if isinstance(і, ast.If) and not і.orelse and і.body \
                    and isinstance(і.body[-1], (ast.Return, ast.Raise, ast.Continue, ast.Break)):
                # `if код not in ТАБЛ: return` — решта тіла йде лише з кодів, що пройшли охорону
                self.у_звуженні(self.звуження(і.test)[1], інструкції[н + 1:])
                return

    def звуження(self, т):
        """Тест на код заяви → (дозволені токени в тілі, в гілці else) чи None. Код — вираз, що несе токени кодів
        (`код`, `з["code"]`); порівняння з рядком чи переліком сталих рядків (літерал чи таблиця модуля).
        Таблицю з включенням беремо з запасом (більше кодів): лише для тіла, для else потрібен точний перелік."""
        if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And):
            тіла = [x for x in (self.звуження(у)[0] for у in т.values) if x is not None]
            return (frozenset.intersection(*тіла) if тіла else None), None
        if not (isinstance(т, ast.Compare) and len(т.ops) == 1 and len(т.comparators) == 1):
            return None, None
        токени = _токени(self.e(т.left))
        if not токени:
            return None, None
        оп, право = т.ops[0], т.comparators[0]
        коди, точно = None, False
        if isinstance(оп, (ast.Eq, ast.NotEq)) and _рядок(право):
            коди, точно = {право.value}, True
        elif isinstance(оп, (ast.In, ast.NotIn)):
            вузол = право
            if isinstance(право, ast.Name) and право.id in self.м.присвоєння and право.id not in self.локальні:
                вузол = self.м.присвоєння[право.id]
            if isinstance(вузол, (ast.Tuple, ast.List, ast.Set)) and all(_рядок(x) for x in вузол.elts):
                коди, точно = {x.value for x in вузол.elts}, True
            elif isinstance(вузол, ast.Dict) and None not in вузол.keys and all(_рядок(x) for x in вузол.keys):
                коди, точно = {x.value for x in вузол.keys}, True
            elif isinstance(вузол, (ast.Dict, ast.Tuple, ast.List, ast.Set, ast.DictComp, ast.SetComp, ast.ListComp,
                                    ast.Call)):
                коди = {n.value for n in ast.walk(вузол) if _рядок(n)}
        if коди is None:
            return None, None
        в_наборі = frozenset(токени & {ТОКЕН + к for к in коди})
        поза = frozenset(токени - {ТОКЕН + к for к in коди}) if точно else None
        return (в_наборі, поза) if isinstance(оп, (ast.Eq, ast.In)) else (поза, в_наборі if точно else None)

    def у_звуженні(self, дозволені, інструкції):
        """Тіло гілки з кодами `дозволені`: мітка S лишається лише на значеннях, чий код серед них (токени без
        перетину з дозволеними знімають S). Без звуження — як є. Записане в гілці додається до незвуженого."""
        if not інструкції:
            return
        if дозволені is None:
            self.тіло(інструкції)
            return
        до_env = dict(self.env)
        до_ключі = {ім: dict(км) for ім, км in self.ключі.items()}
        self.env = {ім: _звузити(м, дозволені) for ім, м in до_env.items()}
        self.ключі = collections.defaultdict(lambda: collections.defaultdict(frozenset),
                                             {ім: collections.defaultdict(frozenset, {к: _звузити(м, дозволені)
                                                                                      for к, м in км.items()})
                                              for ім, км in до_ключі.items()})
        try:
            self.тіло(інструкції)
        finally:
            for ім, м in до_env.items():
                self.env[ім] = self.env.get(ім, E) | м
            for ім, км in до_ключі.items():
                for к, м in км.items():
                    self.ключі[ім][к] = self.ключі[ім][к] | м

    def інструкція(self, і):
        if isinstance(і, ast.Assign):
            мітки = self.e(і.value)
            ц = і.targets[0]
            if id(і) in self.верх and len(і.targets) == 1 and isinstance(ц, ast.Name) and ц.id in self.локальні \
                    and ц.id not in _імена(і.value):
                self.env.pop(ц.id, None); self.ключі.pop(ц.id, None); self.невідомо.pop(ц.id, None)
            for ц in і.targets:
                self.присвоїти(ц, мітки, і.value)
        elif isinstance(і, ast.AugAssign):
            мк = self.значення(і.value) if isinstance(і.target, ast.Name) and isinstance(і.op, ast.Add) else (E, None)
            if мк[1] and МАПА not in мк[1]:
                # `записи += інші_записи`: список записів росте записами — ключі ідуть ключами, а не в мітки списку
                self.писати(і.target.id, мк[0] - {F}, мутація=True)
                for кл, в in мк[1].items():
                    self.ключі[і.target.id][кл] = self.ключі[і.target.id][кл] | в
            else:
                мітки = self.e(і.value) | self.e(і.target)
                self.присвоїти(і.target, мітки - {F})
        elif isinstance(і, ast.AnnAssign):
            if і.value is not None:
                self.присвоїти(і.target, self.e(і.value), і.value)
        elif isinstance(і, (ast.For, ast.AsyncFor)):
            self.ітерація(і.target, і.iter)
            self.тіло(і.body); self.тіло(і.orelse)
        elif isinstance(і, ast.While):
            self.e(і.test); self.тіло(і.body); self.тіло(і.orelse)
        elif isinstance(і, ast.If):
            self.e(і.test)
            self.невідоме_в_гілці(і)
            в_тілі, в_іншому = self.звуження(і.test)
            self.у_звуженні(в_тілі, і.body)
            self.у_звуженні(в_іншому, і.orelse)
        elif isinstance(і, (ast.With, ast.AsyncWith)):
            for п in і.items:
                м = self.e(п.context_expr)
                if п.optional_vars is not None:
                    self.присвоїти(п.optional_vars, м)
            self.тіло(і.body)
        elif isinstance(і, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            self.тіло(і.body)
            for о in і.handlers:
                self.тіло(о.body)
            self.тіло(і.orelse); self.тіло(і.finalbody)
        elif isinstance(і, ast.Return):
            if і.value is not None:
                мітки, ключі = self.значення(і.value)
                self.пов |= мітки
                for к, з in (ключі or {}).items():
                    self.ключі_пов[к] = self.ключі_пов.get(к, E) | з
                if isinstance(і.value, ast.Tuple) and not any(isinstance(x, ast.Starred) for x in і.value.elts):
                    ел = [_ел(*self.значення(x)) for x in і.value.elts]
                    if self.кортеж is None and not self.кортеж_зламано:
                        self.кортеж = ел
                    elif self.кортеж is not None and len(self.кортеж) == len(ел):
                        self.кортеж = [_злити_ел(x, y) for x, y in zip(self.кортеж, ел)]
                    else:
                        self.кортеж, self.кортеж_зламано = None, True
                elif not (isinstance(і.value, ast.Constant) and і.value.value is None):
                    self.кортеж, self.кортеж_зламано = None, True
        elif isinstance(і, ast.Expr):
            self.e(і.value)
        elif isinstance(і, (ast.Raise,)):
            if і.exc is not None:
                self.e(і.exc)
        elif isinstance(і, ast.Assert):
            self.e(і.test)
        elif isinstance(і, ast.Match):
            self.e(і.subject)
            for к in і.cases:
                self.тіло(к.body)

    # ── п.2: гілка «невідомо» ──
    def гілка_невідомо(self, т):
        """Тест → "так" (гілка тіла — невідомо), "ні" (гілка else — невідомо) чи None; лише коли тест дивиться на S."""
        if isinstance(т, ast.Compare) and len(т.ops) == 1:
            ліво, оп, право = т.left, т.ops[0], т.comparators[0]
            if S not in self.наявне(ліво):
                return None
            if isinstance(право, ast.Constant) and (право.value is None or право.value is False):
                return "так" if isinstance(оп, (ast.Is, ast.Eq)) else "ні" if isinstance(оп, (ast.IsNot, ast.NotEq)) else None
            if _рядок(право) and НЕВІДОМЕ.search(право.value):
                return "так" if isinstance(оп, (ast.Is, ast.Eq)) else "ні" if isinstance(оп, (ast.IsNot, ast.NotEq)) else None
            return None
        if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
            if isinstance(т.operand, ast.Name) and т.operand.id in self.невідомо:
                return {"так": "ні", "ні": "так"}[self.невідомо[т.operand.id]]
            if isinstance(т.operand, ast.Name) and т.operand.id in self.послідовності():
                return None   # порожній перелік, зібраний тут (знахідки, речі), — «нема жодного», а не незнання
            return "так" if S in self.наявне(т.operand) and not isinstance(т.operand, (ast.Compare, ast.Call)) else None
        if isinstance(т, ast.Name) and т.id in self.невідомо:
            return self.невідомо[т.id]
        if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And):
            for в in т.values:
                г = self.гілка_невідомо(в)
                if г == "так":
                    return "так"
        return None

    ПОСЛІДОВНІСТЬ = (ast.List, ast.ListComp, ast.Set, ast.SetComp, ast.Tuple)

    def послідовності(self):
        """Локальні імена, яким функція присвоює лише перелік (`[]`, `[… for …]`, `list(…)`, `sorted(…)`)."""
        if not hasattr(self, "_послідовності"):
            види = collections.defaultdict(set)
            for n in self._обійти(self.ф.вузол.body if isinstance(self.ф.вузол.body, list) else []):
                if isinstance(n, ast.Assign):
                    пари = [(ц, n.value) for ц in n.targets]
                    for ц, з in list(пари):   # `а, б = [], []` — поелементно
                        if isinstance(ц, ast.Tuple) and isinstance(з, (ast.Tuple, ast.List)) \
                                and len(ц.elts) == len(з.elts):
                            пари.extend(zip(ц.elts, з.elts))
                    for ц, з in пари:
                        if isinstance(ц, ast.Name):
                            види[ц.id].add(isinstance(з, self.ПОСЛІДОВНІСТЬ) or (
                                isinstance(з, ast.Call) and isinstance(з.func, ast.Name)
                                and з.func.id in ("list", "sorted", "tuple", "set")))
            self._послідовності = {ім for ім, в in види.items() if в == {True}}
        return self._послідовності

    def наявне(self, в):
        """Мітки, на які дивиться перевірка «є / нема» (`not x`, `x is None`) запису чи списку записів з ключами: як пара
        (`_пара`) — запис, у чиїх ключах поруч з її значенням є дані входу чи файлу (речі з полем її палітри), про річ,
        і його порожнеча — не незнання про неї; її власний запис (смуга, риса) лишається її."""
        км = self.ключі.get(в.id, {}) if isinstance(в, ast.Name) else {}
        if any(км.values()):
            return _пара(self.читати_env(в.id), *[з for к, з in км.items() if к != МАПА])
        return self.e(в)

    def значення_замість(self, в, число=False):
        """Вираз — клас чи число, поставлене кодом (стала, стала модуля, параметр зі сталим типовим).
        `число`: запасне за `or`/`.get` — лише число; рядок там — ім'я, шлях чи підпис, а не її клас (клас замість
        незнання ловить гілка «невідомо»), крім рядка, що зве незнання виміром."""
        if isinstance(в, ast.Constant):
            з = в.value
            if з is None or isinstance(з, bool) or з == "":
                return False
            if isinstance(з, str):
                return bool(ВИМІР.search(з)) if число else not НЕВІДОМЕ.search(з)
            # ±1e9 замість межі — «межі нема», а не число замість її значення
            return isinstance(з, (int, float)) and abs(з) < 1e6
        if isinstance(в, ast.UnaryOp) and isinstance(в.operand, ast.Constant):
            return self.значення_замість(в.operand, число)
        if isinstance(в, ast.Tuple) and в.elts:
            return all(self.значення_замість(x, число) for x in в.elts)
        if isinstance(в, ast.Name) and not self.e(в):
            if в.id in self.ф.типові:
                return self.значення_замість(self.ф.типові[в.id], число)
            з = self.м.присвоєння.get(в.id)
            if з is not None and в.id not in self.локальні:
                return self.значення_замість(з, число)
        return False

    def невідоме_в_гілці(self, і):
        г = self.гілка_невідомо(і.test)
        if not г:
            return
        гілка = і.body if г == "так" else і.orelse
        for x in гілка:
            в = x.value if isinstance(x, (ast.Assign, ast.Return)) else None
            if в is not None and self.значення_замість(в):
                self.а.місце(self.м, і.test, 2, "гілка «невідомо» (%s) ставить %s"
                             % (ast.unparse(і.test)[:60], ast.unparse(в)[:40]))
                return

    # ── вирази ──
    def e(self, в):
        if в is None:
            return E
        if isinstance(в, ast.Constant):
            return E
        if isinstance(в, ast.Name):
            return self.читати(в.id)
        if isinstance(в, ast.Attribute):
            if в.attr == "AXIS_RELIABILITY":
                return frozenset({R})
            if isinstance(в.value, ast.Name) and в.value.id in self.м.імпорти:
                мод = self.м.імпорти[в.value.id].split(".")[-1]
                return self.а.глоб.get((мод, в.attr), E)
            return self.e(в.value)
        if isinstance(в, ast.Subscript):
            if isinstance(в.value, ast.Name) and _рядок(в.slice):
                return self.ключ_імені(в.value.id, в.slice.value, в)
            if isinstance(в.value, ast.Subscript) and _рядок(в.slice):
                корінь, префікс, змінний = _шлях(в)
                if корінь and not змінний and len(префікс) <= ГЛИБИНА and self.ключі.get(корінь):
                    км = self.ключі[корінь]
                    вих = self.індекс(self.читати_env(корінь), ast.Constant(префікс[0]), в)
                    for і in range(1, len(префікс) + 1):
                        вих = вих | км.get("/".join(префікс[:і]), E)
                    return вих | _усі(_під(км, "/".join(префікс)))
            if isinstance(в.value, ast.Name) and isinstance(в.slice, ast.Constant) and type(в.slice.value) is int \
                    and ("#%d" % в.slice.value) in self.ключі.get(в.value.id, {}):
                return self.ключ_імені(в.value.id, "#%d" % в.slice.value, в)
            база = self.e(в.value)
            if isinstance(в.value, ast.Call) and _рядок(в.slice) and id(в.value) in self.ключі_викликів:
                поза, ключі = self.ключі_викликів[id(в.value)]
                return ключі.get(в.slice.value, E) | self.індекс(поза, в.slice, в)
            return self.індекс(база, в.slice, в)
        if isinstance(в, ast.Call):
            return self.виклик(в)
        if isinstance(в, ast.BinOp):
            # число з довіри (вага × значення) — нове число, а не сама довіра: R далі не йде
            return _пара(self.e(в.left), self.e(в.right)) - {F, R}
        if isinstance(в, ast.UnaryOp):
            return self.e(в.operand) - {F}
        if isinstance(в, ast.BoolOp):
            мітки = [self.e(x) for x in в.values]
            if isinstance(в.op, ast.Or) and len(в.values) >= 2 and any(S in м for м in мітки[:-1]) \
                    and self.значення_замість(в.values[-1], число=True):
                self.а.місце(self.м, в, 2, "запасне число: %s" % ast.unparse(в)[:70])
            вих = E
            for м in мітки:
                вих |= м
            return вих
        if isinstance(в, ast.Compare):
            return self.порівняння(в)
        if isinstance(в, ast.IfExp):
            self.e(в.test)
            г = self.гілка_невідомо(в.test)
            if г:
                гілка = в.body if г == "так" else в.orelse
                інша = в.orelse if г == "так" else в.body
                if self.значення_замість(гілка) and not (_рядок(інша) and НЕВІДОМЕ.search(інша.value)):
                    # інша гілка сама каже «невідомо» — отже ця гілка не про незнання (`не_вимір(x) is None` — «вимір»)
                    self.а.місце(self.м, в, 2, "гілка «невідомо» (%s) ставить %s"
                                 % (ast.unparse(в.test)[:50], ast.unparse(гілка)[:40]))
            return self.e(в.body) | self.e(в.orelse)
        if isinstance(в, ast.Dict):
            мітки = [self.e(з) for з in в.values]
            for к in в.keys:
                self.e(к)
            self.довіра(в, мітки, [(м, з) for к, м, з in zip(в.keys, мітки, в.values) if к is not None])
            вих = E
            for к, м in zip(в.keys, мітки):
                вих |= м if к is None else (м - {F})
            return вих
        if isinstance(в, (ast.List, ast.Tuple, ast.Set)):
            вих = E
            for x in в.elts:
                вих |= self.e(x)
            return вих
        if isinstance(в, ast.Starred):
            return self.e(в.value)
        if isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            збережено = self.область(в)
            try:
                if isinstance(в, ast.DictComp):
                    self.e(в.key)
                    return self.e(в.value) - {F}
                return self.e(в.elt) - {F}
            finally:
                self.відновити(збережено)
        if isinstance(в, ast.JoinedStr):
            вих = E
            for x in в.values:
                вих |= self.e(x)
            return вих - {F}
        if isinstance(в, ast.FormattedValue):
            return self.e(в.value)
        if isinstance(в, (ast.Await, ast.YieldFrom)):
            м = self.e(в.value)
            if id(в.value) in self.кортежі_викликів:
                self.кортежі_викликів[id(в)] = self.кортежі_викликів[id(в.value)]
            return м
        if isinstance(в, ast.Yield):
            if в.value is not None:
                self.e(в.value)
                м, кл = self.значення(в.value)
                self.пов |= м
                for к, з in (кл or {}).items():
                    self.ключі_пов[к] = self.ключі_пов.get(к, E) | з
            return E
        if isinstance(в, ast.NamedExpr):
            м = self.e(в.value)
            self.присвоїти(в.target, м, в.value)
            return м
        if isinstance(в, ast.Lambda):
            return self.e(в.body)
        if isinstance(в, ast.Slice):
            self.e(в.lower); self.e(в.upper); self.e(в.step)
            return E
        return E

    def індекс(self, база, ключ, вузол, типове=None):
        if isinstance(ключ, ast.Constant):
            к = ключ.value
        else:
            self.e(ключ)
            к = None
        вих = set()
        if R in база:
            вих.add(R)
        if self.зерно and isinstance(к, str) and self.а.зерно and к in self.а.зерно["ключі"]:
            вих.add(S)
            self.а.місце(self.м, вузол, 1, "поле відповіді моделі зору `%s` (hex) стає її рисою без позначки оцінки" % к)
        if S in база:
            if isinstance(к, str) and СЛУЖБОВІ.match(к):
                pass
            else:
                вих.add(S)
        if P in база:
            if isinstance(к, str) and к in self.а.носії:
                вих.add(S)
            elif not (isinstance(к, (int, float)) and not isinstance(к, bool)):
                вих.add(P)
        if типове is not None:
            мт = self.e(типове)
            вих |= мт
            if S in вих and not мт and self.значення_замість(типове, число=True):
                self.а.місце(self.м, вузол, 2, "запасне число: %s" % ast.unparse(вузол)[:70])
        return frozenset(вих)

    def порівняння(self, в):
        мітки = [self.e(в.left)] + [self.e(x) for x in в.comparators]
        операнди = [в.left] + list(в.comparators)
        for i, оп in enumerate(в.ops):
            л, п = мітки[i], мітки[i + 1]
            if S not in л and S not in п:
                continue
            if S not in _пара(л, п):   # її ознака проти запису з файлу — порівняння про річ
                continue
            if isinstance(оп, ПОРЯДОК):
                if id(в) in self.а.формульні:
                    continue
                self.а.місце(self.м, в, 1, "поріг на пораховане з hex моделі: %s" % ast.unparse(в)[:70])
            elif isinstance(оп, (ast.Eq, ast.NotEq)):
                інший = операнди[i + 1] if S in л else операнди[i]
                if isinstance(інший, ast.Constant) and isinstance(інший.value, (int, float)) \
                        and not isinstance(інший.value, bool):
                    self.а.місце(self.м, в, 1, "рівність числу на порахованому з hex моделі: %s" % ast.unparse(в)[:70])
        return E

    def довіра(self, вузол, мітки, прямі):
        """п.1: запис поєднує оцінку моделі (S без R) і довіру знімку (R) — оцінка дістає довіру виміру камери.
        Довіру дає пряме значення ключа (`прямі`: мітки й вираз), узяте з таблиці довіри тут: вираз читає
        `AXIS_RELIABILITY`, кличе `reliability` чи ім'я, присвоєне з них у цій функції. Запис, що лише копіюється
        (`dict(р, …)`, `{**р}`), чи число, пораховане з довіри далі, несе довіру, дану раніше, — місце там, де її дали."""
        if any(S in м and R not in м for м in мітки) and \
                any(R in м and self.з_таблиці_довіри(з) for м, з in прямі):
            self.а.місце(self.м, вузол, 1, "оцінці моделі дано довіру знімку (`AXIS_RELIABILITY`)")

    def з_таблиці_довіри(self, вираз):
        if not hasattr(self, "_імена_довіри"):
            імена = set()
            присвоєння = [(ц.id, n.value) for n in self._обійти(self.ф.вузол.body if isinstance(self.ф.вузол.body, list)
                                                                  else []) if isinstance(n, ast.Assign)
                          for ц in n.targets if isinstance(ц, ast.Name)]
            while True:
                нові = {ім for ім, з in присвоєння if ім not in імена and self._джерело_довіри(з, імена)}
                if not нові:
                    break
                імена |= нові
            self._імена_довіри = імена
        return self._джерело_довіри(вираз, self._імена_довіри)

    @staticmethod
    def _джерело_довіри(вираз, імена):
        for n in ast.walk(вираз):
            if isinstance(n, ast.Attribute) and n.attr == "AXIS_RELIABILITY":
                return True
            if isinstance(n, ast.Call) and "reliab" in (_ім_виклику(n.func) or ""):
                return True
            if isinstance(n, ast.Name) and n.id in імена:
                return True
        return False

    def виклик(self, в):
        ім = _ім_виклику(в.func)
        if ім == "map" and isinstance(в.func, ast.Name) and len(в.args) == 2 and not в.keywords \
                and not isinstance(в.args[0], ast.Lambda) and not any(isinstance(x, ast.Starred) for x in в.args):
            # `map(f, xs)`: f над елементом xs (мітки й ключі елемента), не над сумою списку
            с = self.а.синтетичні.get(id(в))
            if с is None:
                с = ast.Call(func=в.args[0], args=[ast.Subscript(value=в.args[1], slice=ast.Name(id="_і"))],
                             keywords=[])
                ast.copy_location(с, в); ast.copy_location(с.args[0], в)
                self.а.синтетичні[id(в)] = с
                self.а.тримати.append((в, с))
            self.e(в.args[1])
            вих = self.e(с)
            if id(с) in self.ключі_викликів:
                self.ключі_викликів[id(в)] = self.ключі_викликів[id(с)]
            return вих
        приймач = E
        if isinstance(в.func, ast.Attribute):
            приймач = self.e(в.func.value)
        elif isinstance(в.func, ast.Subscript):
            self.e(в.func.slice)
        позиційні, іменні, зірка, дві = [], {}, E, E
        поз_к, імен_к = [], {}   # те саме з ключами dict: (мітки поза ключами, ключі)
        лямбди = []
        for а in в.args:
            рз = self.розгорнуті.get(а.value.id) if isinstance(а, ast.Starred) and isinstance(а.value, ast.Name) \
                and а.value.id == self.ф.зірка else None
            if рз:
                for кл in sorted(рз):
                    мітки, ключі = рз[кл]
                    позиційні.append(мітки | _усі(ключі))
                    поз_к.append((мітки, ключі) if ключі else мітки)
            elif isinstance(а, ast.Starred):
                зірка |= self.e(а.value)
            elif isinstance(а, ast.Lambda):
                лямбди.append(а)
                позиційні.append(E)
                поз_к.append(E)
            else:
                мітки, ключі = self.значення(а)
                позиційні.append(мітки | _усі(ключі))
                поз_к.append((мітки, ключі) if ключі else мітки)
        for к in в.keywords:
            if isinstance(к.value, ast.Lambda):
                лямбди.append(к.value)
                if к.arg:
                    іменні[к.arg] = E
                    імен_к[к.arg] = E
                continue
            рз = self.розгорнуті.get(к.value.id) if isinstance(к.value, ast.Name) and к.arg is None \
                and к.value.id == self.ф.дві_зірки else None
            if рз:
                for кл, (мітки, ключі) in рз.items():
                    іменні[кл] = мітки | _усі(ключі)
                    імен_к[кл] = (мітки, ключі) if ключі else мітки
            elif к.arg is None:
                мітки, ключі = self.значення(к.value)
                дві |= мітки
                for кл in {str(x).split("/")[0] for x in (ключі or {}) if x != МАПА}:   # `**запис`: ключ — аргумент
                    м, під = ключі.get(кл, E), _під(ключі, кл)
                    іменні[кл] = іменні.get(кл, E) | м | _усі(під)
                    імен_к[кл] = (м, під) if під else м
            else:
                мітки, ключі = self.значення(к.value)
                іменні[к.arg] = мітки | _усі(ключі)
                імен_к[к.arg] = (мітки, ключі) if ключі else мітки
        усі = приймач | зірка | дві
        for м in позиційні:
            усі |= м
        for м in іменні.values():
            усі |= м
        елемент = None
        if ім in ("sorted", "sort", "min", "max", "filter", "map", "nsmallest", "nlargest", "groupby"):
            джерело = в.func.value if ім == "sort" and isinstance(в.func, ast.Attribute) else \
                next((x for x in в.args if not isinstance(x, (ast.Lambda, ast.Starred, ast.Constant))), None)
            if джерело is not None:
                елемент = _перебір(*self.значення(джерело))
        for л in лямбди:
            for а in л.args.args:
                if елемент is not None and len(л.args.args) == 1:
                    # ключ сорту чи фільтр: параметр — елемент послідовності з ключами запису
                    м, кл = елемент
                    м = self.індекс(м, ast.Constant(0), в)
                    self.env[а.arg] = self.env.get(а.arg, E) | (м - {F})
                    for кк, вв in (_без_першого(кл) or {}).items():
                        self.ключі[а.arg][кк] = self.ключі[а.arg][кк] | вв
                else:
                    self.env[а.arg] = self.env.get(а.arg, E) | (усі - {F})
                self.локальні.add(а.arg)
            self.e(л.body)
        # методи-мутації й читання dict
        if isinstance(в.func, ast.Attribute):
            if ім in МУТАЦІЇ:
                корінь = _корінь_імені(в.func.value)
                if ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Name) and корінь in self.локальні:
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        self.писати(корінь, мітки - {F})
                        for кл, вв in (ключі or {}).items():
                            self.ключі[корінь][кл] = self.ключі[корінь][кл] | вв
                elif ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Subscript) and isinstance(в.func.value.value, ast.Name) and \
                        not _рядок(в.func.value.slice) and корінь in self.локальні and корінь not in self.глобальні:
                    # `d[ключ].append(запис)`: як `d[ід] = запис` — ключі запису стають ключами елемента d
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        self.писати(корінь, мітки - {F}, мутація=True)
                        for кл, вв in (ключі or {}).items():
                            self.ключі[корінь][кл] = self.ключі[корінь][кл] | вв
                        if ключі:
                            self.ключі[корінь][МАПА] = МАПА_М
                elif ім in ("append", "add", "appendleft", "extend", "extendleft", "insert") and \
                        isinstance(в.func.value, ast.Subscript) and _шлях(в.func.value)[1] and \
                        корінь in self.локальні and корінь not in self.глобальні:
                    for з in (поз_к[1:] if ім == "insert" else поз_к):
                        мітки, ключі = з if isinstance(з, tuple) else (з, None)
                        self.у_шлях(ast.Subscript(value=в.func.value, slice=ast.Name(id="_")), мітки, ключі)
                elif ім == "update" and isinstance(в.func.value, ast.Name) and not в.args:
                    pass   # лише іменні: кожне — свій ключ (нижче)
                elif ім == "update" and isinstance(в.func.value, ast.Name):
                    for з in поз_к:
                        self.писати(корінь, (з[0] if isinstance(з, tuple) else з) - {F}, мутація=True)
                elif ім == "setdefault" and len(в.args) == 2 and isinstance(в.func.value, ast.Name) \
                        and корінь in self.локальні:
                    pass   # запис у мапу — нижче; ключ, як у `d[ід] = запис`, міток елемента не дає
                elif корінь:
                    self.писати(корінь, (усі - приймач) - {F}, мутація=True)
                if ім == "update" and isinstance(в.func.value, ast.Name):
                    for а in в.args:
                        self.ключі_з(в.func.value.id, а)
                    for к in в.keywords:
                        if к.arg:
                            кк = self.ключі[в.func.value.id]
                            м, підк = імен_к[к.arg] if isinstance(імен_к.get(к.arg), tuple) else (іменні.get(к.arg, E), None)
                            кк[к.arg] = кк[к.arg] | м
                            for кл, вв in _з_префіксом(к.arg, підк).items():
                                кк[кл] = кк[кл] | вв
                if ім == "setdefault" and isinstance(в.func.value, ast.Name) and len(в.args) == 2 \
                        and корінь in self.локальні:
                    # `е = d.setdefault(к, запис)`: елемент мапи d — запис із ключами, а не сума всіх ключів d
                    мд, кд = self.значення(в.args[1])
                    км = self.ключі[корінь]
                    for кл, вв in (кд or {}).items():
                        км[кл] = км[кл] | вв
                    км[МАПА] = МАПА_М
                    self.писати(корінь, мд - {F}, мутація=True)
                    ключі = _злити_ключі(_без_першого(км), кд)
                    поза = (self.читати_env(корінь) | мд) - {F}
                    if ключі:
                        self.ключі_викликів[id(в)] = (поза, ключі)
                    return поза | _усі(ключі)
                return (приймач | усі) - {F} if ім == "setdefault" else E
            if ім in ("get", "pop") and в.args and not self.а.викликані(self.м, в.func, self.ф):
                if isinstance(в.func.value, ast.Name) and _рядок(в.args[0]):
                    return self.ключ_імені(в.func.value.id, в.args[0].value, в, в.args[1] if len(в.args) > 1 else None)
                if not isinstance(в.func.value, ast.Name) and _рядок(в.args[0]):
                    мз, кз = self.значення(в.func.value)
                    к = в.args[0].value
                    if кз and (к in кз or _під(кз, к)):
                        return кз.get(к, E) | _усі(_під(кз, к)) | self.індекс(мз, в.args[0], в,
                                                                             в.args[1] if len(в.args) > 1 else None)
                if isinstance(в.func.value, ast.Name) and self.можливі_ключі(в.args[0]) \
                        and self.ключі.get(в.func.value.id):
                    self.e(в.args[0])
                    вих = set()
                    for к in self.можливі_ключі(в.args[0]):
                        вих |= self.ключ_імені(в.func.value.id, к, в, в.args[1] if len(в.args) > 1 else None)
                    return frozenset(вих)
                return self.індекс(приймач, в.args[0], в, в.args[1] if len(в.args) > 1 else None)
            if ім == "keys" or (ім in ПОЗИЦІЙНІ and not self.а.викликані(self.м, в.func, self.ф)):
                return E
            if ім in ("items", "values", "copy"):
                return приймач - ({F} if ім != "copy" else set())
            if ім in ("pop",) and в.args:
                return self.індекс(приймач, в.args[0], в, в.args[1] if len(в.args) > 1 else None)
        # зерно: hex із тексту відповіді (запасний хід читача)
        if self.зерно and ім in ("finditer", "findall", "fullmatch", "match", "search"):
            шаблон = в.args[0] if ім != "fullmatch" or not isinstance(в.func, ast.Attribute) else None
            текст_шаблону = ""
            if isinstance(шаблон, ast.Constant) and isinstance(шаблон.value, str):
                текст_шаблону = шаблон.value
            if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                з = self.м.присвоєння.get(в.func.value.id)
                if isinstance(з, ast.Call) and з.args and _рядок(з.args[0]):
                    текст_шаблону += з.args[0].value
            if HEX_РЕГ.search(текст_шаблону) and (P in усі) and S not in усі:
                self.а.місце(self.м, в, 1, "hex із тексту відповіді моделі зору (запасний хід) стає її рисою")
                return frozenset({S})
            if HEX_РЕГ.search(текст_шаблону) and S in усі:
                return frozenset({S})
        if ім in ("any", "all", "bool") and isinstance(в.func, ast.Name) and self.ф.повне in self.а.перевірки:
            self.наявність(в)
        цілі = self.а.викликані(self.м, в.func, self.ф)
        if not цілі:
            if ім in БУЛЕВІ and isinstance(в.func, ast.Name):
                return E
            вих = усі
            if ім in ФАЙЛОВІ:
                return frozenset((усі | {C}) - {S, F})
            if ім in ("loads", "deepcopy", "copy", "list", "sorted", "tuple", "set", "reversed", "frozenset") \
                    and len(поз_к) == 1 and isinstance(поз_к[0], tuple):
                мітки, ключі = поз_к[0]   # той самий запис: ключі dict ідуть далі
                if МАПА in ключі and ім not in ("loads", "deepcopy", "copy"):
                    return мітки     # `list(d)`, `sorted(d)` над мапою — її ключі-рядки
                self.ключі_викликів[id(в)] = (мітки, ключі)
                return мітки | _усі(ключі)
            if ім not in ВМІСТИЩА:
                # зовнішня функція над записом бачить запис цілим, але число з неї — не поле запису: ключі запису
                # з її колоритом у нього не йдуть (інакше один ключ із S робив S кожне число з пакета)
                поза = [з[0] if isinstance(з, tuple) else з for з in поз_к + list(імен_к.values())]
                пр = приймач
                if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name) \
                        and self.ключі.get(в.func.value.id):
                    пр = self.читати_env(в.func.value.id)
                вих = _пара(пр, зірка, дві, *поза)
            if ім == "reliability":
                вих = вих | {R}
            if ім == "dict" and isinstance(в.func, ast.Name):
                if в.args:
                    вих = self.e(в.args[0]) | ((усі - self.e(в.args[0])) - {F})
                self.довіра(в, позиційні + list(іменні.values()),
                            [(іменні.get(к.arg, E), к.value) for к in в.keywords if к.arg])
                return frozenset(вих)
            return frozenset(вих - {F})
        вих = E
        кортеж = None
        ключі_пов = {}
        for ц in цілі:
            if в.args and _рядок(в.args[0]) and ц.позиційні and ц.позиційні[0] == "код" and поз_к:
                # заява за кодом: сталий код несе токен, і значення її заяви (`ключі_виразу`) знають, з якого
                # вони коду; неоднорідний перелік заяв читач звужує перевіркою коду (`звуження`)
                поз_к = [frozenset({ТОКЕН + в.args[0].value})] + list(поз_к[1:])
            пов = self.а.виклик(ц, поз_к, імен_к, зірка, дві)
            for кл, з in (self.а.останні_ключі or {}).items():
                ключі_пов[кл] = ключі_пов.get(кл, E) | з
            к = self.а.останній_кортеж
            кортеж = к if кортеж is None else ([_злити_ел(x, y) for x, y in zip(кортеж, к)] if к and len(к) == len(кортеж) else [])
            if ц.ім == "reliability" or (ц.модуль.ім.endswith("надійність") and "reliab" in ц.ім):
                пов = пов | {R}
            вих |= пов
            self.риса(в, ц, позиційні, іменні, пов)
            if ц.ім == "зібрати" and ц.модуль.ім == "збирач_промптів":
                self.опис_полів(в)
        if кортеж:
            self.кортежі_викликів[id(в)] = кортеж
        if ключі_пов:
            self.ключі_викликів[id(в)] = (вих, ключі_пов)
        return вих | _усі(ключі_пов)

    def наявність(self, в):
        """п.3: перевірка причини дивиться, чи є запис (`x.get(k) or {}`, `x.get(k, {})`), а не на його значення."""
        for а in в.args:
            вираз = а.elt if isinstance(а, ast.GeneratorExp) else а
            запис = None
            if isinstance(вираз, ast.BoolOp) and isinstance(вираз.op, ast.Or) and isinstance(вираз.values[-1], ast.Dict) \
                    and not вираз.values[-1].keys:
                запис = вираз.values[0]
            elif isinstance(вираз, ast.Call) and _ім_виклику(вираз.func) == "get" and len(вираз.args) == 2 \
                    and isinstance(вираз.args[1], ast.Dict) and not вираз.args[1].keys:
                запис = вираз
            if запис is not None and S in self.e(запис):
                self.а.місце(self.м, в, 3, "причина проходить за наявністю запису, не за значенням: %s" % ast.unparse(в)[:60])
                for м, к, код in self.а.перевірки[self.ф.повне]:
                    self.а.місця.setdefault((м.шлях, к.lineno), set()).add(
                        (3, "причина `%s` звіряється наявністю запису її ознаки, а не значенням" % код))

    def риса(self, в, ц, позиційні, іменні, пов):
        """п.1: hex моделі (S) стає рисою з довірою знімку — виклик будівника рис (`from_photo`) чи запис рис (F)."""
        аргументи = позиційні + list(іменні.values())
        є_оцінка = any(S in м and F not in м for м in аргументи)
        if not є_оцінка:
            return
        if "from_photo" in іменні or any(к.arg == "from_photo" for к in в.keywords):
            self.а.місце(self.м, в, 1, "hex моделі стає рисою з довірою знімку (`from_photo`): %s" % ast.unparse(в.func))
        elif F in пов and any(F in м for м in аргументи):
            self.а.місце(self.м, в, 1, "hex моделі додано рисою в запис рис з довірою знімку: %s" % ast.unparse(в.func))

    def опис_полів(self, в):
        """п.4: поле оголошення, якому дано значення з цього джерела, а опис зве його виміром коду."""
        if len(в.args) < 2:
            return
        оголошення = None
        for а in [в.args[0]] + (list(в.args[0].args) if isinstance(в.args[0], ast.Call) else []):
            if isinstance(а, ast.Name):
                if (self.м.ім, а.id) in self.а.оголошення:
                    оголошення = (self.м.ім, а.id)
                elif а.id in self.м.з_імпортів:
                    мод, ім = self.м.з_імпортів[а.id]
                    if (мод, ім) in self.а.оголошення:
                        оголошення = (мод, ім)
            if оголошення:
                break
        if not оголошення:
            return
        ключі = self.ключі_виразу(в.args[1])
        поля = self.а.оголошення[оголошення]
        м = self.а.модулі[оголошення[0]]
        for к in sorted({str(кл).split("/")[0] for кл in ключі}):
            мітки = ключі.get(к, E) | _усі(_під(ключі, к))
            if S in мітки and к in поля and ВИМІР.search(поля[к][1]):
                рядок, текст = поля[к]
                self.а.місця.setdefault((м.шлях, рядок), set()).add(
                    (4, "опис поля `%s` для моделі зве оцінку моделі виміром: «%s»"
                     % (к, ВИМІР.search(текст).group(0))))


# ── самоперевірка: відомі місця паспорта (8 ід) і не-місця ─────────────────────────
ВІДОМІ = (
    ("г:вихід:колір_портрета:skin", "міст_вхід.py", r'_hex_кольору\(об\.get\("skin"\)\)'),
    ("г:вихід:колір_портрета:hair", "міст_вхід.py", r'_hex_кольору\(об\.get\("hair"\)\)'),
    ("г:вихід:колір_портрета:eyes", "міст_вхід.py", r'_hex_кольору\(об\.get\("eyes"\)\)'),
    ("г:вихід:колір_портрета:limbal_ring", "міст_вхід.py", r'_hex_кольору\(об\.get\("limbal_ring"\)\)'),
    ("г:вхід:вибір_палітри:person", "палітра_температура.py", r"elif знак_придатний is False"),
    ("г:вхід:складання:person.palette.kind_colours", "brief.py", r"h = запас_h if вільний else"),
    ("г:вихід:вибір_палітри:scheme_reasons", "вибір_палітри.py", r'return lambda ч, о, пер: \(any\(\(пер\["особа"\]'),
    ("г:вихід:вибір_палітри:base_reasons", "вибір_палітри.py", r'"why_her_contrast": _у_особі'),
)
ПРИКЛАДИ = (
    ("п.1 риса з from_photo", "міст_вхід.py", r"F = cs\.features\(ш, вл\[0\], о, from_photo"),
    ("п.1 пасма волосся_N", "міст_вхід.py", r'F = cs\.перерахувати_рису\(F, "волосся_%d"'),
    ("п.1 кільце", "міст_вхід.py", r'F = cs\.перерахувати_рису\(F, "очі_кільце"'),
    ("п.1 рівень контрасту", "face_features.py", r"РІВНІ_КОНТРАСТУ|value_gap|рівень"),
    ("п.1 «її чорний»", "personal_palette.py", r"."),
    ("п.1 echo/set_off", "вибір_палітри.py", r'float\(р\.get\("C"\) or 0\) >= _ТОН_РИСИ_С_МІН'),
    ("п.4 as the code measured it", "вибір_палітри.py", r'_ЗП\.Поле\("person", "her colouring as the code measured'),
)
НЕ_МІСЦЯ = (
    ("самозвіт / елісітація", "палітра_температура.py", r"^\s*elif знак_з_елісітації:"),
    ("самозвіт / елісітація", "палітра_температура.py", r'клас = "тепла" if ел\["w"\] > 0'),
    ("spectro", "міст_вхід.py", r'з_фото = дж != "spectro"'),
    ("light_cast", "міст_вхід.py", r'вид = об\.get\("light_cast"\)'),
    ("light_correction", "міст_вхід.py", r'сила = об\.get\("light_correction"\)'),
)


def рядки_якоря(корінь, файл, шаблон):
    шлях = os.path.join(корінь, "джерела", файл)
    if not os.path.isfile(шлях):
        return []
    with open(шлях, encoding="utf-8") as ф:
        return [н for н, р in enumerate(ф.read().splitlines(), 1) if re.search(шаблон, р)]


def самоперевірка(корінь, місця):
    рядки = []
    за_файлом = collections.defaultdict(set)
    for (ф, н) in місця:
        за_файлом[os.path.basename(ф)].add(н)
    for ід, файл, шаблон in ВІДОМІ + ПРИКЛАДИ:
        якорі = рядки_якоря(корінь, файл, шаблон)
        if файл == "personal_palette.py" or шаблон.startswith("РІВНІ"):
            є = bool(за_файлом.get(файл))
        else:
            є = any(н in за_файлом.get(файл, ()) for н in якорі)
        рядки.append("  %s %s — %s%s" % ("✓" if є else "✗", ід, файл,
                                       (":%s" % ",".join(map(str, якорі))) if якорі and файл != "personal_palette.py"
                                       and not шаблон.startswith("РІВНІ") else ""))
    for ід, файл, шаблон in НЕ_МІСЦЯ:
        якорі = рядки_якоря(корінь, файл, шаблон)
        хибні = [н for н in якорі if н in за_файлом.get(файл, ())]
        рядки.append("  %s не місце: %s — %s:%s" % ("✗ ЛІЧЕНО" if хибні else "✓", ід, файл,
                                                   ",".join(map(str, якорі)) or "якоря нема"))
    return рядки


def стенд():
    """Синтетичне дерево: зерно, межа JS, потік і кожен пункт; не-місця не лічаться."""
    import tempfile, textwrap
    with tempfile.TemporaryDirectory() as т:
        os.makedirs(os.path.join(т, "джерела", "показ"))
        файли = {
            "збирач_промптів.py": """
                class Поле:
                    pass
                class Оголошення:
                    pass
                def зібрати(о, дані):
                    return дані
            """,
            "реєстр.py": """
                import читач as _Ч
                СХЕМИ = {"FACE": dict(розбір=_Ч.прийняти)}
            """,
            "читач.py": """
                import re
                import збирач_промптів as _ЗП
                ЧИТАННЯ = _ЗП.Оголошення(задача="колір", вхід=(_ЗП.Поле("photo_of_her", "photo"),), вихід="FACE",
                                         скелет={"skin": ["<hex>"], "eyes": "<hex>", "light_cast": "none|yellow"})
                _HEX = re.compile(r"#?([0-9a-fA-F]{6})")
                def прийняти(відповідь):
                    об = dict(відповідь)
                    р = dict(шкіра=None, очі=None)
                    р["шкіра"] = об.get("skin")
                    р["очі"] = об.get("eyes")
                    світло = об.get("light_cast")
                    return dict(р, світло=світло)
            """,
            "bridge.py": """
                from риси import палітра
                def виклик(ім, вхід):
                    return {"палітра": палітра}[ім](вхід)
            """,
            "надійність.py": """
                AXIS_RELIABILITY = {"uncontrolled": {"hue": 0.35}}
                def reliability(дж):
                    return AXIS_RELIABILITY[дж]
            """,
            "риси.py": """
                import збирач_промптів as _ЗП
                from надійність import reliability
                ТАБЛ = {(15, 0): 30.0}
                ВИБІР = _ЗП.Оголошення(задача="в", вхід=(_ЗП.Поле("person", "her colouring as the code measured it"),
                                                       _ЗП.Поле("day", "the weather measured today")), вихід="X")
                def features(ш, о, from_photo=False):
                    F = {"шкіра": {"L": ш}, "очі": {"h": о}}
                    F["_meta"] = dict(from_photo=from_photo, protocol="uncontrolled")
                    return F
                def додати(F, ім, lab):
                    F = dict(F)
                    F[ім] = {"L": lab}
                    return F
                def _у(*к):
                    return lambda п: (any((п["особа"].get(x) or {}) for x in к), "none")
                ЗВІРКА = {"why_her_contrast": _у("contrast"),
                          "why_her_metal": lambda п: (bool(п["особа"].get("metal")), "")}
                def рівень(F):
                    L = F["шкіра"]["L"]
                    if F["_meta"]["protocol"] == "spectro":
                        return "spectro"
                    return "високий" if L > 45 else "низький"
                def знак(F, самозвіт):
                    п = F["шкіра"].get("знак")
                    if п is False:
                        клас = "нейтральна"
                    if самозвіт["w"] > 0:
                        клас = "тепла"
                    вільний = F["очі"].get("h") is None
                    h = 30.0 if вільний else F["очі"]["h"]
                    C = F["очі"].get("C") or 0
                    return клас, h, C
                ЯКОРІ = ((0.0, 25.0), (22.0, 25.0), (100.0, 100.0))
                def створити_з(код, значення):
                    return dict(code=код, values=значення)
                def заява(код, **значення):
                    return створити_з(код, значення)
                ТАБ_РІВНІВ = {"level_item": ("level",), "level_other": ("level",)}
                def рівень_кодом(x):
                    return 1 if x <= 3 else 2
                def дріт(код, в):
                    if код in ТАБ_РІВНІВ:
                        return {к: рівень_кодом(v) for к, v in в.items()}
                    if код == "colour_her":
                        return в["L"] > 5
                    return в
                def поле_сл(F):
                    return dict(L=F["шкіра"]["L"], спроба=0), 1
                def палітра(d):
                    F = features(d["шкіра"], d["очі"], from_photo=True)
                    F = додати(F, "очі_кільце", d["очі_кільце"])
                    довіра = dict(reliability("uncontrolled"))
                    риси = {"шкіра": dict(F["шкіра"], довіра=довіра)}
                    особа = {"contrast": {"level": рівень(F), "gap": F["шкіра"]["L"]}}
                    for к in ЗВІРКА:
                        ЗВІРКА[к]({"особа": особа})
                    _ЗП.зібрати(ВИБІР, dict(person=особа, day=d.get("день")))
                    if d.get("зріст") > 150:
                        pass
                    заяви_х = [заява("colour_her", L=F["шкіра"]["L"]), заява("level_item", level=d.get("рівень"))]
                    for з_х in заяви_х:
                        дріт(з_х["code"], з_х["values"])
                    записи = [dict(id=i, шкіра_L=F["шкіра"]["L"]) for i in range(3)]
                    пари = [(F["шкіра"]["L"], з) for з in записи]
                    for л, з in пари:
                        if л > 60:
                            pass
                        if з["id"] > 1:
                            pass
                    кошик = {}
                    for з in записи:
                        кошик[з["id"]] = з
                    for _к, з in кошик.items():
                        if з["шкіра_L"] < 20:
                            pass
                    звіт = {"стани": {}}
                    звіт["стани"]["x"] = dict(id=1, L=F["шкіра"]["L"])
                    if звіт["стани"]["x"]["id"] > 1:
                        pass
                    if звіт["стани"]["x"]["L"] < 10:
                        pass
                    for з, н in zip(записи, range(3)):
                        if н > 1:
                            pass
                    перший = next((з for з in записи if з["id"] > 0), None)
                    if перший["id"] > 1:
                        pass
                    if перший["шкіра_L"] > 1:
                        pass
                    сп = {"поле": "id"}
                    стан_х = звіт["стани"]["x"]
                    if стан_х.get(сп["поле"]) > 1:
                        pass
                    for с in list(кошик):
                        if с > 1:
                            pass
                    for з in кошик.values():
                        if з["шкіра_L"] > 2:
                            pass
                    група = {"всі": кошик}
                    з1 = група["всі"].get(1)
                    if з1["id"] > 3:
                        pass
                    знайдені = [з for з in записи if з["id"] > 5]
                    стан_зн = "нема" if not знайдені else "є"
                    клас_в = "так" if F["очі"].get("h") is None else "невідомо"
                    край = ТАБЛ.get((15, 0)) if F["шкіра"]["L"] < 15 else None
                    копія = dict(риси["шкіра"], L2=F["шкіра"]["L"])
                    вузли_г = {}
                    for з in записи:
                        в_г = вузли_г.setdefault(F["шкіра"]["L"], dict(ребер=0))
                        в_г["ребер"] += 1
                        if в_г["ребер"] == 1:
                            pass
                    дуга_а, дуга_б = F["очі"]["h"], F["шкіра"]["h"]
                    if дуга_б < дуга_а:
                        дуга_б += 360.0
                    верх_b = F["шкіра"].get("b_max") or 1e9
                    чому_б = F["очі"].get("чому") or "у профілі нема кольору очей — бік не читається"
                    назва_р = F["шкіра"].get("назва") or "корінь"
                    джерело_р = F["шкіра"].get("джерело") or "вимір"
                    поля_сл = {}
                    for с in ("верх", "низ"):
                        поля_сл[с], _зайве = поле_сл(F)
                    for с, v_сл in поля_сл.items():
                        if v_сл["спроба"] > 0:
                            pass
                        if v_сл["L"] > 9:
                            pass
                    for (x0_я, y0_я), (x1_я, y1_я) in zip(ЯКОРІ, ЯКОРІ[1:]):
                        if F["шкіра"]["L"] <= x1_я:
                            pass
                    for с in ("верх",):
                        поля_сл[с]["якір"] = F["шкіра"]["L"]
                    зібрані = []
                    зібрані += [з for з in записи if з["id"] > 0]
                    for з in зібрані:
                        if з["id"] > 7:
                            pass
                    return знак(F, d.get("самозвіт") or {}), риси
            """,
        }
        for ім, текст in файли.items():
            with open(os.path.join(т, "джерела", ім), "w", encoding="utf-8") as ф:
                ф.write(textwrap.dedent(текст))
        with open(os.path.join(т, "джерела", "показ", "кольори.js"), "w", encoding="utf-8") as ф:
            ф.write("let КОЛІР = {};\nfunction з(из){ КОЛІР = {шкіра:из.шкіра, очі:из.очі, кільце:из.очі};\n}\n"
                    "function вх(){ return {шкіра: КОЛІР.шкіра, очі: КОЛІР.очі, очі_кільце: КОЛІР.кільце || null,"
                    " зріст: 1}; }\n")
        with open(os.path.join(т, "джерела", "показ", "воркер_міст.js"), "w", encoding="utf-8") as ф:
            ф.write("'    r = bridge.виклик(im, json.loads(ryadok))\\n' +\n")
        а = Аналіз(т)
        а.прогін()
        за = collections.defaultdict(set)
        for (ф, н), пп in а.місця.items():
            for п, _ in пп:
                за[os.path.basename(ф)].add((н, п))

        def є(файл, шаблон, пункт):
            with open(os.path.join(т, "джерела", файл), encoding="utf-8") as ф:
                рядки = [н for н, р in enumerate(ф.read().splitlines(), 1) if re.search(шаблон, р)]
            return any((н, пункт) in за[файл] for н in рядки)

        випадки = [
            ("зерно: поле skin", є("читач.py", r'об\.get\("skin"\)', 1), True),
            ("зерно: поле eyes", є("читач.py", r'об\.get\("eyes"\)', 1), True),
            ("не місце: light_cast", є("читач.py", r"light_cast", 1), False),
            ("межа JS: носії", sorted(а.носії) == ["очі", "очі_кільце", "шкіра"], True),
            ("п.1 from_photo", є("риси.py", r"F = features\(", 1), True),
            ("п.1 заява її коду — поріг під охороною коду", є("риси.py", r'в\["L"\] > 5', 1), True),
            ("не місце: значення заяви іншого коду (охорона `код in ТАБЛ`)", є("риси.py", r"x <= 3", 1), False),
            ("п.1 риса в запис", є("риси.py", r"F = додати\(", 1), True),
            ("п.1 довіра знімку", є("риси.py", r"риси = \{", 1), True),
            ("п.1 поріг", є("риси.py", r"L > 45", 1), True),
            ("не місце: spectro", є("риси.py", r'"spectro":', 1), False),
            ("п.2 незнання → клас", є("риси.py", r"if п is False", 2), True),
            ("п.2 вільний → кут", є("риси.py", r"h = 30.0 if вільний", 2), True),
            ("п.2 запасне число", є("риси.py", r'get\("C"\) or 0', 2), True),
            ("не місце: самозвіт", є("риси.py", r'самозвіт\["w"\]', 1), False),
            ("не місце: зріст", є("риси.py", r"зріст", 1), False),
            ("п.1 позиція кортежу зі списку", є("риси.py", r"л > 60", 1), True),
            ("не місце: інша позиція кортежу", є("риси.py", r'з\["id"\] > 1', 1), False),
            ("п.1 поле запису з .items()", є("риси.py", r'шкіра_L"\] < 20', 1), True),
            ("п.1 поле за шляхом ключів", є("риси.py", r'\["x"\]\["L"\] < 10', 1), True),
            ("не місце: сусіднє поле за шляхом", є("риси.py", r'\["x"\]\["id"\] > 1', 1), False),
            ("не місце: друга послідовність zip", є("риси.py", r"н > 1", 1), False),
            ("не місце: next над записами — чужий ключ", є("риси.py", r"перший\[.id.\] > 1", 1), False),
            ("next над записами — її ключ", є("риси.py", r"перший\[.шкіра_L.\] > 1", 1), True),
            ("не місце: ключ із поля літерала модуля", є("риси.py", r"сп\[.поле.\]\) > 1", 1), False),
            ("не місце: перебір мапи дає ключі", є("риси.py", r"if с > 1", 1), False),
            ("п.1 d.values() мапи — її записи", є("риси.py", r'шкіра_L"\] > 2', 1), True),
            ("не місце: d[к].get(змінний) — чужий ключ", є("риси.py", r'з1\["id"\] > 3', 1), False),
            ("не місце: порожній перелік", є("риси.py", r"стан_зн =", 2), False),
            ("не місце: інша гілка — «невідомо»", є("риси.py", r"клас_в =", 2), False),
            ("не місце: край сітки таблиці", є("риси.py", r"край =", 1), False),
            ("не місце: копія запису з довірою", є("риси.py", r"копія =", 1), False),
            ("не місце: += записів — чужий ключ", є("риси.py", r'з\["id"\] > 7', 1), False),
            ("не місце: розгортка дуги через 0°", є("риси.py", r"дуга_б < дуга_а", 1), False),
            ("не місце: ±1e9 — межі нема", є("риси.py", r"верх_b =", 2), False),
            ("не місце: текст, що називає незнання", є("риси.py", r"чому_б =", 2), False),
            ("не місце: запасне ім'я-рядок", є("риси.py", r"назва_р =", 2), False),
            ("п.2 запасне «вимір» замість джерела", є("риси.py", r"джерело_р =", 2), True),
            ("не місце: запис позиції кортежу в мапу — чужий ключ", є("риси.py", r'v_сл\["спроба"\] > 0', 1), False),
            ("не місце: поле елемента мапи d[к][\"поле\"] — чужий ключ", є("риси.py", r'v_сл\["спроба"\] > 0', 1), False),
            ("п.1 запис позиції кортежу в мапу — її ключ", є("риси.py", r'v_сл\["L"\] > 9', 1), True),
            ("не місце: відрізок інтерполяції за якорями", є("риси.py", r"<= x1_я", 1), False),
            ("не місце: лічильник setdefault за її ключем", є("риси.py", r'в_г\["ребер"\] == 1', 1), False),
            ("п.3 наявність запису", є("риси.py", r"return lambda п: \(any", 3), True),
            ("п.3 рядок таблиці", є("риси.py", r'"why_her_contrast"', 3), True),
            ("не п.3: значення metal", є("риси.py", r'"why_her_metal"', 3), False),
            ("п.4 measured", є("риси.py", r'Поле\("person"', 4), True),
            ("не п.4: поле без S", є("риси.py", r'Поле\("day"', 4), False),
        ]
        погані = [ім for ім, факт, треба in випадки if факт != треба]
        for ім, факт, треба in випадки:
            print("  %s %s" % ("✓" if факт == треба else "✗", ім))
        print("стенд: %d з %d" % (len(випадки) - len(погані), len(випадки)))
        return not погані


def main():
    п = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    п.add_argument("--корінь", default=os.path.dirname(ТУТ))
    п.add_argument("--стенд", action="store_true", help="синтетичні випадки класу; код 1, коли хоч один хибний")
    а = п.parse_args()
    if а.стенд:
        sys.exit(0 if стенд() else 1)
    ан = Аналіз(а.корінь)
    ан.прогін()
    місця = ан.місця
    за_пунктом = collections.Counter()
    for (ф, н), пп in sorted(місця.items()):
        пункти = sorted({x[0] for x in пп})
        for x in пункти:
            за_пунктом[x] += 1
        чому = " | ".join(sorted({x[1] for x in пп}))[:200]
        print("%s:%d · п.%s · %s" % (ф, н, ",".join(map(str, пункти)), чому))
    print("— за пунктами (місце з кількома пунктами — у кожному): " +
          ", ".join("п.%d: %d" % (x, за_пунктом[x]) for x in (1, 2, 3, 4)))
    з = ан.зерно or {}
    print("— зерно: %s.%s (рядок %s), hex-поля %s, форма %s, читач %s" % (
        з.get("модуль"), з.get("ім"), з.get("рядок"), ",".join(sorted(з.get("ключі", ()))), з.get("форма"),
        з["читач"].повне if з.get("читач") else None))
    м = ан.межа
    print("— межа Python→JS: поля читача %s → КОЛІР.%s → ключі входу моста %s; читачів КОЛІР у показі %d, "
          "з них обчислень %d" % (",".join(м.get("поля_читача", ())), ",".join(м.get("поля_колір", ())),
                                  ",".join(м.get("носії", ())), len(м.get("читачі", ())), len(м.get("обчислення", ()))))
    for ф, н, р in м.get("обчислення", ()):
        print("  JS обчислення: %s:%d %s" % (ф, н, р))
    print("— функцій із міткою S: %d; файлів із місцями: %d" % (
        len({к[0] for к, в in ан.пам.items() if S in в}), len({ф for ф, _ in місця})))
    print("— самоперевірка (паспорт: 8 ід і приклади; не-місця):")
    for р in самоперевірка(а.корінь, місця):
        print(р)
    print("місць: %d" % len(місця))


if __name__ == "__main__":
    main()
