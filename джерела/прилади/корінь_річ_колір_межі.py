"""Прилад кореня Річ-колір-межі (`аудит/корені/Річ-колір-межі.md`, «Клас місць»): місця коду (Python і JS), що самі
рахують тон, сім'ю, межу, шов, вікно коду кольору, відношення кольорів чи допуск «той самий» поза єдиним модулем
визначення. Пункти класу: 1 — лічба поза модулем визначення; 2 — кут CIELAB, рівний сектор, HSV чи RGB замість вікна
на колі художника; 3 — сталий кут допуску чи «так»/«ні» замість «невідомо»; 4 — вікно коду кольору не з вжитку
(ручний рядок, затиск старим вікном, слово крамниці замість коду).

    python3 джерела/прилади/корінь_річ_колір_межі.py [дерево] [--шляхи]

`дерево` — корінь репозиторію (типово — поточна тека з `джерела/`, інакше той, де лежить прилад); храповик дає дерево голови й дерево бази. Два шляхи
до того самого: А — від визначень (функції й таблиці, що за ім'ям чи параметрами є тоном, сім'єю, межею, вікном),
Б — від викликачів (функції, що викликають такі визначення). Вузол-ознака спільний; шлях визначає, у яких функціях
його шукають; «підлога» — безпосередня лічба кута (`% 360`, `360 −`, `atan2`) де завгодно: це і є лічба тону.
Місце = пара (файл, рядок); число = об'єднання шляхів і підлоги. Вивід: `файл:рядок · пункт · чому [шлях]`, підсумки
за пунктами, останній рядок `місць: <N>`, код 0. `--шляхи` — ще збіг і розбіжність шляхів А/Б.
Модуль визначення — `джерела/колір_тон.py`; якщо його в дереві нема, поза модулем — усе (розрахунок чесний ДО його
появи). Згенеровані читачі (шапка «згенеровано») — не місця."""
import ast, os, re, sys, warnings

warnings.filterwarnings("ignore")

МОДУЛЬ_ВИЗНАЧЕННЯ = "колір_тон"
ПРОПУСК_ДИРЕКТОРІЙ = {"проби", "прилади", "аудит", "node_modules", "__pycache__", "дані_5191_5194", "траса", "лабораторія"}
ПЕРЕТВОРЕННЯ_ПРОСТОРУ = {"колір_простір_перетворення"}   # Lab↔LCh, OKLab, ΔE2000 однієї точки — вимір, не місце (паспорт, 29.10)
БЕЗ_ПУНКТУ_1 = {МОДУЛЬ_ВИЗНАЧЕННЯ} | ПЕРЕТВОРЕННЯ_ПРОСТОРУ
ПРОПУСК_ФАЙЛІВ = re.compile(r"^(тест_|проба|проб_|стенд_знімок)")
JS_ДИРЕКТОРІЇ = {"показ"}
JS_ФАЙЛИ = re.compile(r"^(worker|міст_воркер|показ_шаблон)")

ІМ_ВИЗНАЧЕННЯ = re.compile(r"(тон|сім_?[яʼ'’]|сімʼя|меж[аі]|шов|шви|вікн|дуг|коло|кут|hue|family|window|arc|відлун|той_сам|та_сама"
                           r"|збіг|тепл|холод|підтон|сектор|близьк|поруч|допуск|похибк)", re.I)
ІМ_ТОНУ = re.compile(r"^(?:h|hue|dh|h_?\d|h_\w+|\w+_h|\w+_h\d|ΔH\w*|тон\w*|\w+_тон\w*|кут\w*|\w+_кут|дуг\w*|\w+_дуг\w*|півдуга)$", re.I)
ІМ_ПАРАМ = re.compile(r"^(h|hue|h_?\w*|дуга|дуги|тон\w*|lo|hi)$", re.I)
ІМ_ТАБЛИЦІ_МЕЖ = re.compile(r"(ТОН(?![КІ])|ΔH|ДУГ|СЕКТОР|ТЕПЛИЙ_ПОЛЮС|МЕЖА_БЛИЗЬКИХ|ВІДЛУНН|FAMILIES|RELATIONS|ОЧЕЙ|_КОЛО$|СІМ_Ї|HUE|_H$)")
ІМ_ТАБЛИЦІ_ВІКОН = re.compile(r"(ВІКН|ВІКНА|ЛЕКСИКОН|ВЖИТОК)")
КУТ_ВИКЛИК = re.compile(r"^(кут|кут_\w+|різниця_тону\w*|розкид_\w*тон\w*|розкид_дуг|відстань_\w*тон\w*|dh\w*|hue_diff\w*|ΔH\w*)$", re.I)
КОЛО_ХУДОЖНИКА = re.compile(r"(коло_художника|кола_художника|на_колі|вікн|колір_тон)")
ЧИТАЧ_СЛОВА = re.compile(r"^_?(назва_кольору|вікно_зі_слова|вікно_назви|сім_я_слова|слово_називає_тон|вікно_слова)$")
ПОРІГ_ІМ = re.compile(r"(доп|поріг|межа|tol|тол|ТОН_|ПОХИБ|КРОК|ΔH|МАКС|МІН)", re.I)
СЕКТОРИ_Н = {10, 12, 15, 20, 30, 36, 40, 45, 60, 72, 90, 120}
КАНАЛИ = {"r", "g", "b", "R", "G", "B"}


def число(n, v=None):
    return isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and not isinstance(n.value, bool) \
        and (v is None or n.value == v)


def ім(n):
    return n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None


def ім_виклику(c):
    return ім(c.func) if isinstance(c, ast.Call) else None


def вузли(тіло):
    for ст in (тіло if isinstance(тіло, list) else [тіло]):
        yield from ast.walk(ст)


def має_тон(n):
    return any(isinstance(x, ast.Name) and ІМ_ТОНУ.match(x.id) for x in ast.walk(n))


def кут_тон(n):
    """Вираз — кутова різниця тонів: `% 360` над різницею, `360 − x`, `min(d, 360 − d)`, виклик `кут(...)`."""
    for x in ast.walk(n):
        if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Mod) and число(x.right, 360) \
                and isinstance(x.left, ast.BinOp) and isinstance(x.left.op, ast.Sub):
            return True
        if isinstance(x, ast.BinOp) and isinstance(x.op, ast.Sub) and число(x.left, 360):
            return True
        if isinstance(x, ast.Call) and КУТ_ВИКЛИК.match(ім_виклику(x) or ""):
            return True
    return False


def ознаки_п1(n):
    """Безпосередня лічба кута (пункт 1): [(чому)] для вузла."""
    if isinstance(n, ast.BinOp):
        if isinstance(n.op, ast.Mod) and число(n.right, 360):
            return ["`% 360` — власна лічба кола"]
        if isinstance(n.op, ast.Sub) and число(n.left, 360):
            return ["`360 − x` — власна згортка кута"]
        if isinstance(n.op, (ast.Add, ast.Sub)) and число(n.right, 360):
            return ["`± 360` — власний зсув кола"]
    if isinstance(n, ast.Call) and ім_виклику(n) == "atan2" and len(n.args) == 2 \
            and not any(isinstance(a, ast.BinOp) for a in n.args):
        return ["`atan2(b, a)` — власний тон із Lab"]
    return []


ІМ_ТОНУ_ТОЧНЕ = re.compile(r"^(?:h|hue|h_?\d|h_\w+|\w+_h|\w+_h\d)$", re.I)


ІМ_КОЛЬОРУ = re.compile(r"^(?:lab|lch|L|C|Cc|C_|L_|hex\w*|дуг\w*|тон\w*|colou?r|колір\w*|Lab)$")


def у_кольорі(тіло, файл):
    """Контекст кольору: у функції (чи модулі) є імена Lab/L/C/дуги/тону або файл — з кольором. `h` без цього — висота."""
    if any(isinstance(x, ast.Name) and x.id in ("w", "width", "W") for x in вузли(тіло)):
        return False   # поруч із шириною `h` — висота, не тон
    return bool(re.search(r"колір|палітр|verify|palettes|фід_|жнива|річ|помада|bases|surface|міст_основи|brief", файл)) \
        and any(isinstance(x, ast.Name) and ІМ_КОЛЬОРУ.match(x.id) for x in вузли(тіло))


def ознаки_п1_межа_числом(n):
    """Межа тону числом у коді: `h < 30`, `20 ≤ h < 50` — власна межа сім'ї чи шва."""
    if not isinstance(n, ast.Compare):
        return []
    ел = [n.left] + list(n.comparators)
    імена = [e for e in ел if isinstance(e, ast.Name) and ІМ_ТОНУ_ТОЧНЕ.match(e.id)]
    числа = [e for e in ел if число(e) and 5 <= e.value <= 355]
    if імена and числа and all(isinstance(o, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for o in n.ops):
        return ["межа тону числом у коді (`%s` проти %g)" % (імена[0].id, числа[0].value)]
    return []


ІМ_ХРОМИ = re.compile(r"^(?:C|Cc|C_\w*|c|хром\w*)$")
ІМ_ПЕРЕТВОРЕННЯ = re.compile(r"^_?(де_?00|de2000|ciede\w*|delta_?e\w*|oklab\w*|to_oklab|lab_з_lch|lch_to_lab|lab_to_lch|lch|_lab|\w*hex_?lch)$", re.I)
ІМ_ТЕПЛА = re.compile(r"(тепл|холод|warm|cool|температур|temperature)", re.I)
КЛЮЧ_ДУГИ = re.compile(r"(дуг|hue|arc|сектор|^h$|^h_|_h$|_h\d)", re.I)


def рад_імена(тіло):
    """Імена, присвоєні `radians(<тон>)`: `r = radians(h)`."""
    r = set()
    for x in вузли(тіло):
        if isinstance(x, ast.Assign) and isinstance(x.value, ast.Call) and ім_виклику(x.value) == "radians" \
                and x.value.args and має_тон(x.value.args[0]):
            r |= {t.id for t in x.targets if isinstance(t, ast.Name)}
    return r


def кут_радіани_тону(c, рад):
    """cos/sin(radians(h)) чи cos/sin(r), r = radians(h)."""
    if not (isinstance(c, ast.Call) and ім_виклику(c) in ("cos", "sin") and c.args):
        return False
    a = c.args[0]
    return (isinstance(a, ast.Call) and ім_виклику(a) == "radians" and a.args and має_тон(a.args[0])) \
        or (isinstance(a, ast.Name) and a.id in рад)


def ознаки_п1_копія_перетворення(n, рад, у_теплій=False):
    """Друга копія перетворення простору поза його модулем (паспорт, п.1): LCh→Lab, хрома Lab→LCh."""
    if кут_радіани_тону(n, рад) and not у_теплій:
        return ["cos/sin кута тону — друга копія LCh→Lab чи власне кругове середнє поза модулем перетворення"]
    if isinstance(n, ast.Call) and ім_виклику(n) == "hypot" and len(n.args) == 2 and лаб_пара(n.args):
        return ["друга копія Lab→LCh (хрома `hypot(a, b)`) поза модулем перетворення"]
    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and ІМ_ПЕРЕТВОРЕННЯ.match(n.name):
        return ["друге визначення перетворення простору (`%s`) поза модулем" % n.name]
    return []


def лаб_пара(args):
    def ключ(a):
        while isinstance(a, ast.BinOp):
            a = a.left
        if isinstance(a, ast.Name):
            return a.id
        if isinstance(a, ast.Subscript):
            пл = a.slice.elts[-1] if isinstance(a.slice, ast.Tuple) else a.slice
            return пл.value if isinstance(пл, ast.Constant) else None
        return None
    k = (ключ(args[0]), ключ(args[1]))
    return k in {("a", "b"), ("a1", "b1"), ("a2", "b2"), (1, 2)} or (isinstance(k[0], int) and k == (1, 2))


def ознаки_п1_дуга(n):
    if isinstance(n, ast.IfExp) and isinstance(n.test, ast.Compare) and len(n.test.ops) == 1 \
            and isinstance(n.test.ops[0], (ast.Lt, ast.LtE)) and not число(n.test.left) and not число(n.test.comparators[0]) \
            and isinstance(n.orelse, ast.BoolOp) and isinstance(n.orelse.op, ast.Or) \
            and isinstance(n.body, ast.Compare) and len(n.body.ops) == 2:
        return ["власна належність до дуги з переходом через 0° (`lo ≤ h ≤ hi if lo ≤ hi else h ≥ lo or h ≤ hi`)"]
    return []


def ознаки_п1_вікно(n):
    """Належність до дуги власним порівнянням (пункт 1): `h ≥ lo or h ≤ hi`, `lo ≤ h ≤ hi` над тоном."""
    if isinstance(n, ast.BoolOp) and len(n.values) == 2 and all(isinstance(c, ast.Compare) and len(c.ops) == 1 for c in n.values):
        a, b = n.values
        if ast.dump(a.left) == ast.dump(b.left) and not число(a.comparators[0]) and not число(b.comparators[0]) \
                and has_ops(a, b) and має_тон(a.left):
            return ["власна належність до дуги (`h ≥ lo` `h ≤ hi`)"]
    if isinstance(n, ast.Compare) and len(n.ops) == 2 and all(isinstance(o, (ast.Lt, ast.LtE)) for o in n.ops) \
            and має_тон(n.comparators[0]) and isinstance(n.comparators[0], (ast.Name, ast.Subscript)) \
            and isinstance(n.comparators[0], ast.Name):
        return ["власна належність до дуги (`lo ≤ h ≤ hi`)"]
    return []


def has_ops(a, b):
    return type(a.ops[0]) in (ast.Gt, ast.GtE, ast.Lt, ast.LtE) and type(b.ops[0]) in (ast.Gt, ast.GtE, ast.Lt, ast.LtE) \
        and type(a.ops[0]) is not type(b.ops[0])


def ознаки_п2(n, є_коло):
    """Пункт 2: рівний сектор, HSV, канали RGB, кут CIELAB без кола художника."""
    ч = []
    знач = None
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.FloorDiv) and число(n.right) and n.right.value in СЕКТОРИ_Н \
            and (має_тон(n.left) or any(isinstance(x, ast.BinOp) and число(x.right, 360) for x in ast.walk(n.left))):
        ч.append("рівний сектор кута (`h // %g`)" % n.right.value)
    if isinstance(n, ast.Call) and ім_виклику(n) in ("int", "floor", "round", "ceil") and n.args \
            and isinstance(n.args[0], ast.BinOp) and isinstance(n.args[0].op, ast.Div) and число(n.args[0].right) \
            and n.args[0].right.value in СЕКТОРИ_Н and має_тон(n.args[0].left):
        ч.append("рівний сектор кута (`int(h / %g)`)" % n.args[0].right.value)
    if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name) and n.value.id == "colorsys":
        ч.append("HSV/HLS (`colorsys`)")
    if isinstance(n, ast.Call) and re.match(r"(rgb_to_(hsv|hls|hsl)|\w*hsv\w*|\w*hsl\w*)$", ім_виклику(n) or "", re.I):
        ч.append("HSV/HSL у коді")
    if isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.left, ast.Name) and n.left.id in КАНАЛИ \
            and isinstance(n.comparators[0], ast.Name) and n.comparators[0].id in КАНАЛИ:
        ч.append("сім'я/тон за порядком каналів RGB")
    return ч


def ознаки_п3_порівняння(n, кутні, ф_є_коло):
    """Пункт 3: кутова відстань тонів проти сталої (число чи ВЕЛИКА_КОНСТАНТА) — допуск без похибки виміру."""
    if not (isinstance(n, ast.Compare) and len(n.ops) == 1 and isinstance(n.ops[0], (ast.Lt, ast.LtE, ast.Gt, ast.GtE))):
        return [], []
    л, п = n.left, n.comparators[0]

    def кутній(x):
        return kut_expr(x, кутні)
    def стала(x):
        return число(x) or (isinstance(x, (ast.Name, ast.Attribute)) and re.match(r"^[_А-ЯІЇЄҐA-ZΔ0-9]+$", ім(x) or "") is not None
                            and ПОРІГ_ІМ.search(ім(x)) is not None) or (isinstance(x, ast.UnaryOp) and число(x.operand))
    if (кутній(л) and стала(п)) or (кутній(п) and стала(л)):
        ч3 = ["відстань тонів проти сталого кута (допуск не з похибки виміру)"]
        ч2 = [] if ф_є_коло else ["відношення тонів кутом CIELAB, без вікна на колі художника"]
        return ч3, ч2
    return [], []


def kut_expr(x, кутні):
    return кут_тон(x) or any(isinstance(y, ast.Name) and y.id in кутні for y in ast.walk(x)) \
        or (isinstance(x, ast.Call) and ім_виклику(x) == "abs" and x.args and isinstance(x.args[0], ast.BinOp)
            and isinstance(x.args[0].op, ast.Sub) and має_тон(x.args[0]))


def кутні_імена(тіло):
    """Імена, що в функції присвоєні кутовій різниці тонів: `d = abs(a − b) % 360`, `dh = кут(a, b)`."""
    r = set()
    for x in вузли(тіло):
        if isinstance(x, ast.Assign) and kut_expr(x.value, set()) and has_name_targets(x):
            r |= {t.id for t in x.targets if isinstance(t, ast.Name)}
    return r


def has_name_targets(a):
    return any(isinstance(t, ast.Name) for t in a.targets)


def ознаки_п3_невідомо(f):
    """Функція відношення тонів із `None`-входом повертає `True`/`False` замість «невідомо» (None)."""
    if not re.search(r"(той_сам|та_сама|same|збіг|поруч|близьк|суміжн|співпад)", f.name, re.I):
        return []
    if not any(ІМ_ПАРАМ.match(a.arg) or "тон" in a.arg or "дуг" in a.arg for a in f.args.args):
        return []
    повертає_none = any(isinstance(r, ast.Return) and (r.value is None or (isinstance(r.value, ast.Constant) and r.value.value is None)
                        or isinstance(r.value, ast.Constant) and isinstance(r.value.value, str) and r.value.value == "невідомо")
                        for r in ast.walk(f))
    for i in ast.walk(f):
        if isinstance(i, ast.If) and re.search(r"None|not \w+$", ast.unparse(i.test)) and len(i.body) == 1 \
                and isinstance(i.body[0], ast.Return) and isinstance(i.body[0].value, ast.Constant) \
                and isinstance(i.body[0].value.value, bool) and not повертає_none:
            return [(i.lineno, "тон не виміряно, а відповідь `%s` — не «невідомо»" % i.body[0].value.value)]
    return []


def рядки_таблиці_вікон(присв, цілі):
    """Пункт 4: ручний рядок вікна — запис таблиці вікон (слово → числа L/C/дуга) літералом."""
    знач = присв.value
    r = []
    if not isinstance(знач, ast.Dict) or len(знач.keys) < 3:
        return r
    назви = " ".join(цілі)
    за_ім = ІМ_ТАБЛИЦІ_ВІКОН.search(назви) is not None
    def числа_в(v):
        індекси = {id(x.slice) for x in ast.walk(v) if isinstance(x, ast.Subscript)}
        return sum(1 for x in ast.walk(v) if число(x) and id(x) not in індекси)
    for к, v in zip(знач.keys, знач.values):
        if k_is_str(к) and isinstance(v, (ast.Tuple, ast.List)) and числа_в(v) >= 4 and (за_ім or len(знач.keys) >= 8):
            r.append((к.lineno, "ручний рядок вікна слова «%s» (літерал, не вихід методу на вжитку)" % к.value))
    return r


def k_is_str(k):
    return isinstance(k, ast.Constant) and isinstance(k.value, str)


def ознаки_п4_функція(f):
    """Пункт 4: затиск старим вікном (огорта ∪ вікно-параметр) і читач слова крамниці як вікна."""
    r = []
    параметри = {a.arg for a in f.args.args}
    if re.search(r"вікн|window", f.name, re.I) and any(re.search(r"вікн|window", p, re.I) for p in параметри):
        розпаковано = set()
        for x in ast.walk(f):
            if isinstance(x, ast.Assign) and isinstance(x.value, ast.Name) and x.value.id in параметри \
                    and isinstance(x.targets[0], ast.Tuple):
                розпаковано |= {t.id for t in x.targets[0].elts if isinstance(t, ast.Name)}
        for x in ast.walk(f):
            if isinstance(x, ast.Call) and ім_виклику(x) in ("min", "max") \
                    and any(isinstance(a, ast.Name) and a.id in розпаковано for a in x.args):
                r.append((x.lineno, "новий вихід затиснуто старим вікном (`%s` над вікном-параметром)" % ім_виклику(x)))
    if ЧИТАЧ_СЛОВА.match(f.name):
        r.append((f.lineno, "вікно/тон із слова крамниці, а не з коду кольору (`%s`)" % f.name))
    return r


class Збір:
    def __init__(self):
        self.м = {}     # (файл, рядок) -> {пункт: чому}, шляхи

    def дод(self, файл, рядок, пункт, чому, шлях):
        if пункт == 1 and os.path.basename(файл)[:-3] in БЕЗ_ПУНКТУ_1:
            return    # модуль визначення і модуль перетворення простору звільнені лише від пункту 1; пункти 2–4 діють і в них
        з = self.м.setdefault((файл, рядок), {"пункти": {}, "шляхи": set()})
        з["пункти"].setdefault(пункт, чому)
        з["шляхи"].add(шлях)


def функції(дерево):
    for x in ast.walk(дерево):
        if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield x


def веде_до_вікна(f):
    """Слово крамниці, прочитане `назва_кольору`, веде до вікна/сім'ї/дуги в тій самій функції (а не лише «слово назване»)."""
    return any(re.search(r"вікн|ЛЕКСИКОН|ВЖИТОК|сім_я|дуг|ФОРМИ", n) for n in
               [x.id for x in ast.walk(f) if isinstance(x, ast.Name)] + [x.attr for x in ast.walk(f) if isinstance(x, ast.Attribute)])


def обхід_python(шлях, файл, збір, імена_визначень_усі, тепла_функції):
    t = open(шлях, encoding="utf-8").read()
    try:
        дерево = ast.parse(t)
    except SyntaxError:
        return
    ф_є_коло = bool(КОЛО_ХУДОЖНИКА.search(t))
    рядки = t.split("\n")

    def шукати(тіло, ш, кутні, у_теплій=False):
        колір = у_кольорі(тіло, файл)
        рад = рад_імена(тіло)
        for x in вузли(тіло):
            for ч in ознаки_п1_копія_перетворення(x, рад, у_теплій):
                збір.дод(файл, x.lineno, 1, ч, ш)
            if у_теплій and кут_радіани_тону(x, рад):
                збір.дод(файл, x.lineno, 2, "тепле ↔ холодне кутом CIELAB (sin/cos кута тону)", ш)
            if isinstance(x, ast.Call) and ім_виклику(x) in тепла_функції:
                збір.дод(файл, x.lineno, 2, "тепле ↔ холодне кутом CIELAB (читач `%s`), а не вікном на колі художника" % ім_виклику(x), ш)
            for ч in ознаки_п1(x) + ознаки_п1_дуга(x) + (ознаки_п1_вікно(x) + ознаки_п1_межа_числом(x) if колір else []):
                збір.дод(файл, x.lineno, 1, ч, ш)
            if колір:
                for ч in ознаки_п1_межа_числом(x):
                    збір.дод(файл, x.lineno, 2, "сім'я/шов тону кутом LCh числом, без вікна на колі художника", ш)
            for ч in ознаки_п2(x, ф_є_коло):
                if колір or not ч.startswith("рівний сектор"):
                    збір.дод(файл, x.lineno, 2, ч, ш)
            ч3, ч2 = ознаки_п3_порівняння(x, кутні, ф_є_коло)
            for ч in ч3:
                збір.дод(файл, x.lineno, 3, ч, ш)
            for ч in ч2:
                збір.дод(файл, x.lineno, 2, ч, ш)

    # таблиці (присвоєння на будь-якому рівні) — шлях А
    for х in ast.walk(дерево):
        if isinstance(х, ast.Assign) and any(isinstance(t_, ast.Name) for t_ in х.targets):
            цілі = [t_.id for t_ in х.targets if isinstance(t_, ast.Name)]
            if х in дерево.body and any(ІМ_ТАБЛИЦІ_МЕЖ.search(ц) for ц in цілі) and таблиця_меж(х.value):
                збір.дод(файл, х.lineno, 1, "власна межа/таблиця тону (%s)" % ",".join(цілі), "А")
            if not any(ІМ_ТАБЛИЦІ_МЕЖ.search(ц) for ц in цілі) or х not in дерево.body:
                for рядок, ч in рядки_дуг_за_ключем(х.value, " ".join(цілі)):
                    збір.дод(файл, рядок, 1, ч, "А")
            for рядок, ч in рядки_таблиці_вікон(х, цілі):
                з_приміткою = re.search(r"#\s*\d+: нейтр\.", рядки[рядок - 1]) is not None
                збір.дод(файл, рядок, 4, ч + (" — з приміткою виміру" if з_приміткою else ""), "А")
    # модульний код поза функціями — лише підлога
    шукати([x for x in дерево.body if not isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))], "підлога", set())
    # функції: шлях А (ім'я чи параметри — тон/сім'я/межа/вікно), шлях Б (викликає такі визначення); решта — підлога
    for f in функції(дерево):
        for ч in ознаки_п1_копія_перетворення(f, set()):
            збір.дод(файл, f.lineno, 1, ч, "А")
        if f.name in тепла_функції:
            збір.дод(файл, f.lineno, 2, "тепле ↔ холодне кутом CIELAB: `%s` (sin/cos кута тону)" % f.name, "А")
        в_а = bool(ІМ_ВИЗНАЧЕННЯ.search(f.name)) or any(ІМ_ПАРАМ.match(a.arg) for a in f.args.args)
        викликає = {ім_виклику(c) for c in вузли(f.body) if isinstance(c, ast.Call)}
        в_б = bool(викликає & імена_визначень_усі - {f.name})
        шляхи = [к for к, ок in (("А", в_а), ("Б", в_б)) if ок] or ["підлога"]
        кутні = кутні_імена(f.body)
        for один in шляхи:
            шукати(f.body, один, кутні, f.name in тепла_функції)
            for рядок, ч in ознаки_п3_невідомо(f):
                збір.дод(файл, рядок, 3, ч, один)
            for рядок, ч in ознаки_п4_функція(f):
                збір.дод(файл, рядок, 4, ч, один)
        for c in вузли(f.body):
            if isinstance(c, ast.Call) and ЧИТАЧ_СЛОВА.match(ім_виклику(c) or "") and not ЧИТАЧ_СЛОВА.match(f.name) \
                    and (ім_виклику(c) not in ("назва_кольору", "слово_називає_тон") or веде_до_вікна(f)):
                збір.дод(файл, c.lineno, 4, "вікно/тон із слова крамниці, а не з коду кольору (виклик `%s`)" % ім_виклику(c), "Б")


def рядки_дуг_за_ключем(v, назви_цілей=""):
    """Таблиця меж за структурою значення: ключ (рядок словника чи kwarg) називає дугу/тон/сектор, значення — число чи
    пара чисел кута; ще — ≥ 3 трійки (від, до, «ім'я») з кутами."""
    r = []
    пари = []
    for x in ast.walk(v):
        if isinstance(x, ast.Dict):
            пари += [(k.value, k, val) for k, val in zip(x.keys, x.values) if isinstance(k, ast.Constant) and isinstance(k.value, str)]
        if isinstance(x, ast.Call):
            пари += [(k.arg, k.value, k.value) for k in x.keywords if k.arg]
    for назва, вузол, val in пари:
        кути = [e for e in ast.walk(val) if число(e)]
        скаляр_дуги = re.search(r"(^|_)(дуга|дуги|arc|півдуга)$", назва) is not None
        if КЛЮЧ_ДУГИ.search(назва) and кути and all(-1 <= e.value <= 360 for e in кути) and not re.search(r"поза|^нп_", назва) \
                and ((число(val) and скаляр_дуги) or (isinstance(val, (ast.Tuple, ast.List)) and len(кути) >= 2)):
            r.append((val.lineno, "власна дуга/межа тону за ключем «%s» (структура значення, не ім'я таблиці)" % назва))
    for назва, вузол, val in пари:
        # запис реєстру: ключ про тепле/холодне/дугу, у значенні `val=(від, до, …)` — кути
        if re.search(r"warm|cool|тепл|холод|hue|дуг|arc", назва, re.I) and isinstance(val, (ast.Call, ast.Dict)):
            for ключ, знач in ([(k.arg, k.value) for k in val.keywords] if isinstance(val, ast.Call) else
                               [(k.value, w) for k, w in zip(val.keys, val.values) if isinstance(k, ast.Constant)]):
                кути = [e for e in ast.walk(знач) if число(e)] if ключ == "val" and isinstance(знач, (ast.Tuple, ast.List)) else []
                if len(кути) >= 2 and all(-1 <= e.value <= 360 for e in кути):
                    r.append((знач.lineno, "власна дуга/межа тону в записі реєстру «%s»" % назва))
    трійки = [x for x in ast.walk(v) if isinstance(x, ast.Tuple) and len(x.elts) == 3 and число(x.elts[0]) and число(x.elts[1])
              and isinstance(x.elts[2], ast.Constant) and isinstance(x.elts[2].value, str)
              and -1 <= x.elts[0].value <= 360 and -1 <= x.elts[1].value <= 360]
    if len(трійки) >= 3 and not re.search(r"ITA", назви_цілей):
        r.append((v.lineno, "таблиця сімей тону (від, до, ім'я) — %d рядків" % len(трійки)))
    return r


def таблиця_меж(v):
    """Літерал межі тону: число, пара чисел чи таблиця з ≥ 2 чисел (дуги, вікна, сім'ї, сектори)."""
    чисел = sum(1 for x in ast.walk(v) if число(x))
    return число(v) or (isinstance(v, ast.UnaryOp) and число(v.operand)) or (чисел >= 2 and not isinstance(v, ast.Call) or isinstance(v, ast.Call) and чисел >= 2)


# ---------------------------------------------------------------- JS
def без_коментарів(t):
    t = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), t, flags=re.S)
    t = re.sub(r"(?<![:\\'\"`])//[^\n]*", "", t)
    return re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"", "''", t)


JS_П1 = [(re.compile(r"%\s*360\b"), "`% 360` — власна лічба кола"), (re.compile(r"\b360\s*-\s*[\w(]"), "`360 − x` — власна згортка кута"),
         (re.compile(r"Math\.atan2\s*\(\s*[^,()]+,\s*[^()]+\)"), "`atan2(b, a)` — власний тон із Lab")]
JS_П2 = [(re.compile(r"\bhs[lv]\s*\(|rgbToHs[lv]|rgb2hs[lv]|\bhsv\b", re.I), "HSV/HSL у коді"),
         (re.compile(r"Math\.(?:floor|round)\s*\(\s*\w*[hH]\w*\s*/\s*(?:10|12|15|20|30|36|45|60|90|120)\s*\)"), "рівний сектор кута")]
JS_П3 = re.compile(r"Math\.abs\s*\(\s*\w*[hH]\w*\s*-\s*\w*[hH]\w*\s*\)\s*[<>]=?\s*[\d.]+")
JS_ЧИТАЧ_СЛОВА = re.compile(r"\b(?:назваКольору|вікноЗіСлова|вікноНазви)\s*\(")
JS_ДУГА = re.compile(r"\b([A-Za-zА-Яа-яІіЇїЄєҐґ_]*[hH]\w*)\s*>=?\s*(\w+)\s*\|\|\s*\1\s*<=?\s*(\w+)|\b(\w+)\s*<=?\s*([A-Za-zА-Яа-яІіЇїЄєҐґ_]*[hH]\w*)\s*&&\s*\5\s*<=?\s*(\w+)")
JS_ВІКНА = re.compile(r"^\s*['\"]?[\wа-яіїєґ' -]+['\"]?\s*:\s*\[\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+")


def обхід_js(шлях, файл, збір):
    t = open(шлях, encoding="utf-8").read()
    if re.search(r"згенеров|generated", t[:600], re.I):
        return
    for i, рядок in enumerate(без_коментарів(t).split("\n"), 1):
        for р, ч in JS_П1:
            if р.search(рядок):
                збір.дод(файл, i, 1, ч, "підлога")
        for р, ч in JS_П2:
            if р.search(рядок):
                збір.дод(файл, i, 2, ч, "А")
        if JS_П3.search(рядок):
            збір.дод(файл, i, 3, "відстань тонів проти сталого кута", "А")
        if JS_ДУГА.search(рядок):
            збір.дод(файл, i, 1, "власна належність до дуги тону", "А")
        if JS_ВІКНА.search(рядок):
            збір.дод(файл, i, 4, "ручний рядок вікна (літерал)", "А")
        if JS_ЧИТАЧ_СЛОВА.search(рядок):
            збір.дод(файл, i, 4, "вікно/тон із слова крамниці, а не з коду кольору", "Б")


# ---------------------------------------------------------------- керування
def файли(корінь):
    дж = os.path.join(корінь, "джерела")
    for dp, dn, fn in os.walk(дж):
        dn[:] = sorted(d for d in dn if d not in ПРОПУСК_ДИРЕКТОРІЙ or (d in JS_ДИРЕКТОРІЇ))
        for f in sorted(fn):
            шлях = os.path.join(dp, f)
            відн = os.path.relpath(шлях, корінь)
            ця_директорія = os.path.relpath(dp, дж)
            if f.endswith(".py") and ця_директорія == "." and not ПРОПУСК_ФАЙЛІВ.match(f) \
                    :
                yield шлях, відн, "py"
            elif f.endswith(".js") and not f.startswith("тест_") and (ця_директорія in JS_ДИРЕКТОРІЇ or (ця_директорія == "." and JS_ФАЙЛИ.match(f))):
                yield шлях, відн, "js"


def імена_визначень(корінь):
    """Шлях А, крок 1: імена функцій-визначень тону/сім'ї/межі/вікна — для пошуку викликачів (шлях Б)."""
    r = set()
    for шлях, відн, вид in файли(корінь):
        if вид != "py":
            continue
        try:
            дерево = ast.parse(open(шлях, encoding="utf-8").read())
        except SyntaxError:
            continue
        for f in функції(дерево):
            if ІМ_ВИЗНАЧЕННЯ.search(f.name) and len(f.name) > 2:
                r.add(f.name)
    return r


def тепла_кутом(корінь):
    """Функції теплого/холодного бока, що рахують його кутом тону (`sin/cos(radians(h))`): їхні визначення й читачі — пункт 2."""
    r = set()
    for шлях, відн, вид in файли(корінь):
        if вид != "py":
            continue
        try:
            дерево = ast.parse(open(шлях, encoding="utf-8").read())
        except SyntaxError:
            continue
        for f in функції(дерево):
            if ІМ_ТЕПЛА.search(f.name) and len(f.name) > 3:
                рад = рад_імена(f.body)
                if any(кут_радіани_тону(x, рад) for x in вузли(f.body)):
                    r.add(f.name)
    return r


def головна(арг):
    корінь = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    if os.path.isdir(os.path.join(os.getcwd(), "джерела")):
        корінь = os.getcwd()    # храповик: дерево бази — поточна тека, прилад — з голови
    показати_шляхи = "--шляхи" in арг
    поз = [a for a in арг if not a.startswith("--")]
    if поз:
        корінь = os.path.abspath(поз[0])
    збір = Збір()
    імена = імена_визначень(корінь)
    тепло = тепла_кутом(корінь)
    for шлях, відн, вид in файли(корінь):
        if вид == "py":
            обхід_python(шлях, відн, збір, імена, тепло)
        else:
            обхід_js(шлях, відн, збір)
    для_виводу = sorted(збір.м.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    ш_назви = {"підлога": "підлога", "А": "А", "Б": "Б"}
    for (файл, рядок), з in для_виводу:
        for п in sorted(з["пункти"]):
            print("%s:%d · пункт %d · %s [%s]" % (файл, рядок, п, з["пункти"][п], "+".join(sorted(з["шляхи"]))))
    if показати_шляхи:
        а = {k for k, з in збір.м.items() if "А" in з["шляхи"]}
        б = {k for k, з in збір.м.items() if "Б" in з["шляхи"]}
        п = {k for k, з in збір.м.items() if "підлога" in з["шляхи"]}
        print("шляхи: А %d · Б %d · А∩Б %d · лише А %d · лише Б %d · підлога %d · поза А і Б (лише підлога) %d" %
              (len(а), len(б), len(а & б), len(а - б), len(б - а), len(п), len(п - а - б)))
    for п in (1, 2, 3, 4):
        print("пункт %d: %d" % (п, sum(1 for з in збір.м.values() if п in з["пункти"])))
    print("модуль визначення `%s`: %s" % (МОДУЛЬ_ВИЗНАЧЕННЯ, "є" if os.path.exists(os.path.join(корінь, "джерела", МОДУЛЬ_ВИЗНАЧЕННЯ + ".py")) else "нема — поза модулем усе"))
    print("місць: %d" % len(збір.м))
    return 0


if __name__ == "__main__":
    sys.exit(головна(sys.argv[1:]))
