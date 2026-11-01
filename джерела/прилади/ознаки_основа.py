"""Спільні визначення й чисті операції AST для приладу ознак обличчя."""
import ast, collections, functools, os, re
from ознаки_рішення import (шкали_ваги, пари_функції, вузли_тіла, кутові_пари,
                           множини_функції, вільні_свідки_пари, числові_цикли,
                           форматований_текст, поля_підписів, межі_сортування)

ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВИКЛЮЧЕНО = re.compile(r"^(батарея_|gate_|measure_|стенд_|тест_|audit_|pair_test|run_outfit|status_перевірки)")
S, P, F, R, C, Q, K, B, V = "S", "P", "F", "R", "C", "Q", "K", "B", "V"
# B — саме пакет входу шва. Однаковий ключ у вкладених даних не є полем hex цього пакета.
# V — поле явно перезаписане до можливого повернення; його джерело не успадковується від цілого запису.
# Q — пораховане рішення: вага чи сила пари, споживач якої вже не є входом її ознаки.
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
    if S in вих and any(S not in м and (P in м or C in м or K in м) for м in мітки):
        вих = вих - {S}
    return вих
E = frozenset()
# Лічильники масок мають окреме джерело — пікселі фото, а не hex відповіді моделі.
СЛУЖБОВІ = re.compile(r"^(_meta|_пікселі$|_макіяж|макіяж_|protocol$|from_photo$|source$|photo_note$)")
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
        self.власні = tuple(вузли_тіла(self))
        self.локальні = {в.id for в in self.власні if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store)}
        self.глобальні = {ім for в in self.власні if isinstance(в, ast.Global) for ім in в.names}
        self.верх = frozenset() if isinstance(вузол, ast.Lambda) else frozenset(id(в) for в in вузол.body)
        перше_повернення = min((в.lineno for в in self.власні if isinstance(в, ast.Return)), default=float('inf'))
        self.точні_записи = frozenset() if isinstance(вузол, ast.Lambda) else frozenset(
            id(в) for в in вузол.body if isinstance(в, ast.Assign) and в.lineno < перше_повернення)
        self.множини = множини_функції(self)
        self.вільні_пари = вільні_свідки_пари(self)
        self.прогресії, self.предикати_формул, self.числовий_пошук, self.повертає_сітку = числові_цикли(self)
        self.предикати_формул.update(межі_сортування(self))
        self.сіткові_імена = {ц.id for в in self.власні if id(в) in self.прогресії
                            for ц in в.targets if isinstance(ц, ast.Name)}

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


@functools.lru_cache(maxsize=32768)
def _текст(в):
    """Кешує незмінний текст вузла AST для повторних контекстів потоку."""
    return ast.unparse(в)


@functools.cache
def _імена(в):
    return {x.id for x in ast.walk(в) if isinstance(x, ast.Name)}


def _число(в):
    return isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool)


def _стала_формули(в):
    """Впізнає числову сталу формули, зокрема дріб, без обчислення коду."""
    return _число(в) or isinstance(в, ast.UnaryOp) and isinstance(в.op, (ast.UAdd, ast.USub)) \
        and _стала_формули(в.operand) or isinstance(в, ast.BinOp) \
        and _стала_формули(в.left) and _стала_формули(в.right)


def _словесні_пороги(дерево, поля=()):
    """Знаходить вибір самих слів усередині форматованого підпису."""
    def слова(в):
        return _рядок(в) or isinstance(в, ast.JoinedStr) or isinstance(в, ast.IfExp) and слова(в.body) and слова(в.orelse)
    def лише_підпис(тіло):
        """Відрізняє зміну самого підпису від зміни числа чи класу поруч із ним."""
        return all(isinstance(і, ast.Pass) or isinstance(і, ast.Assign) and форматований_текст(і.value)
                   and all(isinstance(ц, ast.Subscript) and _рядок(ц.slice) and ц.slice.value in поля for ц in і.targets)
                   or isinstance(і, ast.If) and лише_підпис(і.body) and лише_підпис(і.orelse) for і in тіло)
    вихід = set()
    for в in ast.walk(дерево):
        if isinstance(в, ast.If) and лише_підпис(в.body) and лише_підпис(в.orelse) \
                and any(isinstance(н, ast.Assign) for і in в.body + в.orelse for н in ast.walk(і)):
            вихід.update(id(т) for т in ast.walk(в.test) if isinstance(т, ast.Compare))
        формат = isinstance(в, ast.JoinedStr) or isinstance(в, ast.BinOp) and isinstance(в.op, ast.Mod) and _рядок(в.left)
        if формат:
            for г in ast.walk(в):
                if isinstance(г, ast.IfExp) and слова(г.body) and слова(г.orelse):
                    вихід.update(id(т) for т in ast.walk(г.test) if isinstance(т, ast.Compare))
    for ф in ast.walk(дерево):
        if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        вузли = list(вузли_тіла(ф))
        батьки = {id(д): в for в in вузли for д in ast.iter_child_nodes(в)}
        усі = list(ast.walk(ф))
        предки = {id(д): в for в in усі for д in ast.iter_child_nodes(в)}
        псевдоніми, джерела, читання = collections.defaultdict(set), {}, collections.defaultdict(list)
        for н in усі:
            if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Name):
                ім = н.targets[0].id
                if isinstance(н.value, ast.Name):
                    псевдоніми[н.value.id].add(ім)
                elif isinstance(н.value, ast.IfExp) and слова(н.value):
                    джерела[ім] = н.value
            if isinstance(н, ast.Name) and isinstance(н.ctx, ast.Load):
                читання[н.id].append(н)
        текстові, нетекстові = set(), set()
        for ім in set(псевдоніми) | set(джерела) | set().union(*псевдоніми.values(), set()):
            for н in читання[ім]:
                б = предки.get(id(н))
                if isinstance(б, ast.Assign) and б.value is н and len(б.targets) == 1 and isinstance(б.targets[0], ast.Name):
                    continue
                формат = False
                while б is not None:
                    if форматований_текст(б):
                        формат = True
                        break
                    if isinstance(б, (ast.Call, ast.Compare, ast.stmt)):
                        break
                    б = предки.get(id(б))
                (текстові if формат else нетекстові).add(ім)
        while True:
            погані = {ім for ім, до in псевдоніми.items() if до & нетекстові} - нетекстові
            добрі = {ім for ім, до in псевдоніми.items() if до & текстові} - текстові
            if not погані and not добрі:
                break
            нетекстові |= погані
            текстові |= добрі
        for ім, вираз in джерела.items():
            if ім in текстові and ім not in нетекстові:
                for г in ast.walk(вираз):
                    if isinstance(г, ast.IfExp) and слова(г):
                        вихід.update(id(т) for т in ast.walk(г.test) if isinstance(т, ast.Compare))
        for виклик in вузли:
            if not (isinstance(виклик, ast.Call) and isinstance(виклик.func, ast.Attribute)
                    and виклик.func.attr == 'append' and isinstance(виклик.func.value, ast.Name)
                    and len(виклик.args) == 1 and isinstance(виклик.args[0], ast.IfExp)):
                continue
            г = виклик.args[0]
            if not (слова(г.body) and слова(г.orelse)):
                continue
            ім = виклик.func.value.id
            є_злиття, лише_текст = False, True
            for н in вузли:
                if not (isinstance(н, ast.Name) and isinstance(н.ctx, ast.Load) and н.id == ім):
                    continue
                б = батьки.get(id(н))
                if isinstance(б, ast.Attribute) and б.value is н and б.attr == 'append':
                    continue
                if isinstance(б, ast.Call) and isinstance(б.func, ast.Attribute) and б.func.attr == 'join' and _рядок(б.func.value):
                    є_злиття = True
                    continue
                лише_текст = False
            if є_злиття and лише_текст:
                вихід.update(id(т) for т in ast.walk(г.test) if isinstance(т, ast.Compare))
    return вихід


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
        сусідні = None
        if isinstance(в, ast.For) and isinstance(в.iter, ast.Call) and len(в.iter.args) == 2:
            сусідні = в.iter.args[1]
            if isinstance(сусідні, ast.BinOp) and isinstance(сусідні.op, ast.Add):
                сусідні = сусідні.left
        if isinstance(в, ast.For) and isinstance(в.iter, ast.Call) and isinstance(в.iter.func, ast.Name) \
                and в.iter.func.id == "zip" and len(в.iter.args) == 2 and isinstance(в.iter.args[0], ast.Name) \
                and isinstance(сусідні, ast.Subscript) and isinstance(сусідні.slice, ast.Slice) \
                and isinstance(сусідні.value, ast.Name) and сусідні.value.id == в.iter.args[0].id:
            # `for (x0, y0), (x1, y1) in zip(якорі, якорі[1:]): if g <= x1: …` — відрізок кусково-лінійної
            # функції за таблицею якорів, а не поріг: межі ставить таблиця формули
            цілі = _імена(в.target)
            for і in в.body:
                т = і.value.test if isinstance(і, ast.Assign) and isinstance(і.value, ast.IfExp) else getattr(і, "test", None)
                if isinstance(т, ast.Compare) and all(isinstance(оп, ПОРЯДОК) for оп in т.ops) \
                        and all((_імена(л) and _імена(л) <= цілі) or (_імена(п) and _імена(п) <= цілі)
                                for л, п in zip([т.left] + т.comparators, т.comparators)):
                    вих.add(id(т))
        т = getattr(в, "test", None)
        if isinstance(в, ast.IfExp) and isinstance(в.body, ast.ListComp) \
                and isinstance(в.body.elt, ast.Tuple) and isinstance(в.orelse, ast.List) \
                and len(в.orelse.elts) == 1 and isinstance(в.orelse.elts[0], ast.Tuple) \
                and len(в.orelse.elts[0].elts) == len(в.body.elt.elts) \
                and all(_число(н) and н.value == 0 for н in в.orelse.elts[0].elts) \
                and all(isinstance(н, ast.Name) for н in в.body.elt.elts) \
                and _імена(в.body.elt) == set().union(*(_імена(г.target) for г in в.body.generators)) \
                and isinstance(т, ast.Compare) and len(т.ops) == 1 and isinstance(т.ops[0], ast.Gt) \
                and _число(т.comparators[0]) and т.comparators[0].value == 0:
            вих.add(id(т))  # сітка зсувів або її виродження в нуль: спосіб інтегрування
        if isinstance(в, ast.If) and isinstance(т, ast.Compare) and len(т.ops) == 1 \
                and isinstance(т.ops[0], ast.Eq) and isinstance(т.left, ast.BinOp) and isinstance(т.left.op, ast.Mult) \
                and _число(т.comparators[0]) and т.comparators[0].value == 0 and в.body and в.orelse \
                and all(isinstance(і, (ast.Assign, ast.AugAssign)) for і in в.body + в.orelse) \
                and any(isinstance(н, ast.BinOp) for і in в.orelse for н in ast.walk(і)) \
                and not any(isinstance(н, ast.Constant) and isinstance(н.value, str) for н in ast.walk(в)):
            вих.add(id(т))
        if isinstance(в, ast.AugAssign) and isinstance(в.target, ast.Name) and isinstance(в.value, ast.IfExp):
            числа = [н.value for н in ast.walk(в.value) if _число(н)]
            if 360 in числа and all(abs(н) <= 360 for н in числа):
                for к in ast.walk(в.value):
                    if isinstance(к, ast.Compare) and _імена(к) == {в.target.id}:
                        вих.add(id(к))
        if isinstance(в, ast.If) and not в.orelse and len(в.body) == 1 and isinstance(в.body[0], ast.AugAssign) \
                and isinstance(т, ast.Compare) and len(т.ops) == 1 and isinstance(в.body[0].target, ast.Name) \
                and _число(в.body[0].value) and abs(в.body[0].value.value) == 360 \
                and в.body[0].target.id in _імена(т):
            вих.add(id(т))   # `if b < a: b += 360` — розгортка дуги через 0°, а не поріг
            continue
        порівняння = т.values if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And) else [т]
        if not all(isinstance(x, ast.Compare) and len(x.ops) == 1 and _стала_формули(x.comparators[0]) for x in порівняння):
            continue
        if len(порівняння) > 1:   # `f(r) if σ > 0 and r > 0 else 0.0` — охорона ділення чи кореня всієї формули
            if isinstance(в, ast.IfExp) and isinstance(в.body, ast.BinOp) and _число(в.orelse) and в.orelse.value == 0 \
                    and set().union(*(_імена(x.left) for x in порівняння)) <= _імена(в.body):
                вих.update(id(x) for x in порівняння)
            continue
        ім = _імена(т.left)
        if not ім:
            continue
        if isinstance(в, ast.IfExp) and isinstance(т.left, ast.Name) \
                and isinstance(т.ops[0], ПОРЯДОК) and (
                    isinstance(в.body, ast.Name) and в.body.id == т.left.id
                    and ast.dump(в.orelse) == ast.dump(т.comparators[0]) or
                    isinstance(в.orelse, ast.Name) and в.orelse.id == т.left.id
                    and ast.dump(в.body) == ast.dump(т.comparators[0])):
            вих.add(id(т))  # min/max тієї самої величини, записаний умовним виразом
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


def _ваги_знахідки(корінь, супровід=False):
    """Поля знахідки, оголошені в `протокол.ЗНАХІДКА` і `ЗНАХІДКА_ВЕРДИКТУ` числом (`ЧИСЛО`, `ЦІЛЕ`, `або_нуль(…)`):
    вага правила, лічильник злитих. Число виходить із правила, яке свій вхід уже порахувало; читач ваги не лічиться
    (рішення менеджера 01.11: вага, зведена з осей, — не місце; лічити читачів — «не латаємо окремих читачів»)."""
    шлях = os.path.join(корінь, "джерела", "протокол.py")
    вих, поля = set(), set()
    try:
        with open(шлях, encoding="utf-8") as ф:
            дерево = ast.parse(ф.read())
    except (OSError, SyntaxError):
        return frozenset()
    числові = ("ЧИСЛО", "ЦІЛЕ")
    for н in ast.walk(дерево):
        if isinstance(н, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id in ("ЗНАХІДКА", "ЗНАХІДКА_ВЕРДИКТУ")
                                             for ц in н.targets) and isinstance(н.value, ast.Call) and н.value.args \
                and isinstance(н.value.args[0], ast.Dict):
            for к, з in zip(н.value.args[0].keys, н.value.args[0].values):
                if _рядок(к):
                    поля.add(к.value)
                if isinstance(з, ast.Call) and _ім_виклику(з.func) == "або_нуль" and з.args:
                    з = з.args[0]
                if _рядок(к) and isinstance(з, ast.Name) and з.id in числові:
                    вих.add(к.value)
    return frozenset(к + '_джерело' for к in вих if к + '_джерело' in поля) if супровід else frozenset(вих)


@functools.cache
def _сітка(в):
    """Включення `[вираз з i for i in range(…)]`, де вираз — арифметика над номером кроку без читання з колекції:
    точки сітки, яку код будує сам у вікні. Кандидат сітки — не її значення (рішення менеджера 01.11)."""
    if not (isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and len(в.generators) == 1):
        return False
    г = в.generators[0]
    if not (isinstance(г.iter, ast.Call) and _ім_виклику(г.iter.func) == "range" and isinstance(г.iter, ast.Call)
            and isinstance(г.iter.func, ast.Name) and isinstance(г.target, ast.Name)):
        return False
    if any(isinstance(n, (ast.Subscript, ast.Attribute)) and г.target.id in _імена(n) for n in ast.walk(в.elt)):
        return False
    return any(isinstance(n, ast.BinOp) and any(isinstance(m, ast.Name) and m.id == г.target.id for m in ast.walk(n))
               for n in ast.walk(в.elt))


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
    if ключі and МАПА not in ключі:
        вих = E.union(*set(ключі.values()))
    else:
        вих = E.union(*(в for к, в in (ключі or {}).items() if к != МАПА))
    return вих - {V} if V in вих else вих


def _без_мапи(ключі):
    """Ключі елемента словника-мапи чи списку: без позначки МАПА верхнього рівня."""
    return {к: в for к, в in (ключі or {}).items() if к != МАПА} or None


def _перебір(мітки, ключі):
    """Елемент перебору: мапа дає ключі-рядки (мітки поза ключами), список записів — запис із ключами."""
    if ключі and МАПА in ключі:
        return мітки, None
    return мітки, ключі


ГЛИБИНА = 3   # ключі запису за шляхом «ключ/під/…»: список записів ділить ключі з записом


@functools.lru_cache(maxsize=65536)
def _хвіст_ключа(ключ, префікс):
    """Відділяє сталий префікс шляху поля незалежно від поточних міток запису."""
    return ключ[len(префікс):] if isinstance(ключ, str) and ключ.startswith(префікс) else None


def _під(ключі, ключ):
    """Ключі значення під `ключ` (шлях «ключ/під»)."""
    п = "%s/" % ключ
    return {хвіст: в for к, в in (ключі or {}).items() if (хвіст := _хвіст_ключа(к, п)) is not None}


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
            в = в - {V}  # точне поле не робить точним згорнутий запис-предок
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


