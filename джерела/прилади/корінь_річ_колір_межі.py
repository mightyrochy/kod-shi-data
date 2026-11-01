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
Ще два класи з паспорта («Наступний крок», рішення менеджера 31.10), кожен своїм шляхом: Г10 (пункт 4) — виклик
функції, що транзитивно кличе `verify.назва_кольору`, на слові поля `колір_назва` (потік значення через присвоєння,
параметри, повернення, поля й межу JSON — `місця_г10`); Г2 (пункт 1) — словник-літерал «слово → код» поза
`внутрішня_мова.py`, що ділить пари з `ТАБЛИЦЯ["palette_family"]` чи `["color_name"]`, з кодом, іншим за таблицю
(`місця_г2`). Підсумок друкує, скільки місць дав кожен.
Модуль визначення — `джерела/колір_тон.py`; якщо його в дереві нема, поза модулем — усе (розрахунок чесний ДО його
появи). Згенеровані читачі (шапка «згенеровано») — не місця."""
import ast, collections, functools, json, os, re, subprocess, sys, warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

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


def у_кольорі(тіло):
    """Контекст кольору з документованого змісту, ключів даних і перетворень; адреса файлу не є доказом."""
    for x in вузли(тіло):
        if ознаки_п1(x):
            return True
        if isinstance(x, ast.Constant) and isinstance(x.value, str) and re.search(
                r"\b(?:Lab|LCh|CIELAB|hue|undertone)\b|підтон|тон[уаі]?\b|дуг[аиу]|хром|"
                r"оливков|рожев|жовт|червон|помаранч|фіолет|бірюз|синьо", x.value, re.I):
            return True
        if isinstance(x, ast.Call) and re.search(r"lab|lch|колір|підтон|hue", ім_виклику(x) or "", re.I):
            return True
    return False


def ознаки_п1_межа_числом(n, тони=()):
    """Межа тону числом у коді: `h < 30`, `20 ≤ h < 50` — власна межа сім'ї чи шва."""
    if not isinstance(n, ast.Compare):
        return []
    ел = [n.left] + list(n.comparators)
    імена = [e for e in ел if isinstance(e, ast.Name) and (e.id in тони or ІМ_ТОНУ_ТОЧНЕ.match(e.id))]
    числа = [e for e in ел if число(e) and 5 <= e.value <= 355]
    if імена and числа and all(isinstance(o, (ast.Lt, ast.LtE, ast.Gt, ast.GtE)) for o in n.ops):
        return ["межа тону числом у коді (`%s` проти %g)" % (імена[0].id, числа[0].value)]
    return []


def тони_значень(тіло):
    """Передає роль тону від поля hue/тону й третьої координати LCh через присвоєння й псевдоніми."""
    тони = set()
    присвоєння = [x for x in вузли(тіло) if isinstance(x, (ast.Assign, ast.AnnAssign)) and x.value is not None]
    while True:
        до = set(тони)
        for x in присвоєння:
            цілі = x.targets if isinstance(x, ast.Assign) else [x.target]
            v = x.value
            поле = isinstance(v, ast.Subscript) and isinstance(v.slice, ast.Constant) and v.slice.value in ("hue", "тон", "h")
            поле = поле or (isinstance(v, ast.Attribute) and v.attr in ("hue", "тон"))
            координата = (isinstance(v, ast.Call) and re.search(r"lch", ім_виклику(v) or "", re.I)) \
                or (isinstance(v, ast.Name) and re.search(r"lch", v.id, re.I))
            for ц in цілі:
                if isinstance(ц, ast.Name) and (поле or isinstance(v, ast.Name) and v.id in тони):
                    тони.add(ц.id)
                if координата and isinstance(ц, (ast.Tuple, ast.List)) and len(ц.elts) == 3 and isinstance(ц.elts[2], ast.Name):
                    тони.add(ц.elts[2].id)
        if тони == до:
            return тони


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
    кандидат_сектора = (isinstance(n, ast.BinOp) and isinstance(n.op, ast.FloorDiv)) \
        or (isinstance(n, ast.Call) and ім_виклику(n) in ("int", "floor", "round", "ceil"))
    геометрія = кандидат_сектора and any(isinstance(x, ast.Name) and x.id in ("w", "width", "W") for x in ast.walk(n))
    if not геометрія and isinstance(n, ast.BinOp) and isinstance(n.op, ast.FloorDiv) and число(n.right) and n.right.value in СЕКТОРИ_Н \
            and (має_тон(n.left) or any(isinstance(x, ast.BinOp) and число(x.right, 360) for x in ast.walk(n.left))):
        ч.append("рівний сектор кута (`h // %g`)" % n.right.value)
    if not геометрія and isinstance(n, ast.Call) and ім_виклику(n) in ("int", "floor", "round", "ceil") and n.args \
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
    дерево = ОБСЯГ.розібрати(t, файл)
    if дерево is None:
        return
    ф_є_коло = bool(КОЛО_ХУДОЖНИКА.search(t))
    рядки = t.split("\n")

    def шукати(тіло, ш, кутні, у_теплій=False):
        колір = у_кольорі(тіло)
        тони = тони_значень(тіло)
        колір = колір or bool(тони)
        рад = рад_імена(тіло)
        for x in вузли(тіло):
            for ч in ознаки_п1_копія_перетворення(x, рад, у_теплій):
                збір.дод(файл, x.lineno, 1, ч, ш)
            if у_теплій and кут_радіани_тону(x, рад):
                збір.дод(файл, x.lineno, 2, "тепле ↔ холодне кутом CIELAB (sin/cos кута тону)", ш)
            if isinstance(x, ast.Call) and ім_виклику(x) in тепла_функції:
                збір.дод(файл, x.lineno, 2, "тепле ↔ холодне кутом CIELAB (читач `%s`), а не вікном на колі художника" % ім_виклику(x), ш)
            for ч in ознаки_п1(x) + ознаки_п1_дуга(x) + (ознаки_п1_вікно(x) + ознаки_п1_межа_числом(x, тони) if колір else []):
                збір.дод(файл, x.lineno, 1, ч, ш)
            if колір:
                for ч in ознаки_п1_межа_числом(x, тони):
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
        if isinstance(х, (ast.Assign, ast.AnnAssign)) and х.value is not None:
            цілі = [t_.id for t_ in (х.targets if isinstance(х, ast.Assign) else [х.target]) if isinstance(t_, ast.Name)]
            if not цілі:
                continue
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
    return re.sub(r"'(?:\\.|[^'\\\n])*'|\"(?:\\.|[^\"\\\n])*\"|`(?:\\.|[^`\\])*`",
                  lambda m: " " * len(m.group(0)) if "\n" not in m.group(0) else
                  "\n".join(" " * len(s) for s in m.group(0).split("\n")), t)


JS_П1 = [(re.compile(r"%\s*360\b"), "`% 360` — власна лічба кола"), (re.compile(r"\b360\s*-\s*[\w(]"), "`360 − x` — власна згортка кута"),
         (re.compile(r"Math\.atan2\s*\(\s*[^,()]+,\s*[^()]+\)"), "`atan2(b, a)` — власний тон із Lab")]
JS_П2 = [(re.compile(r"\bhs[lv]\s*\(|rgbToHs[lv]|rgb2hs[lv]|\bhsv\b", re.I), "HSV/HSL у коді"),
         (re.compile(r"Math\.(?:floor|round)\s*\(\s*\w*[hH]\w*\s*/\s*(?:10|12|15|20|30|36|45|60|90|120)\s*\)"), "рівний сектор кута")]
JS_П3 = re.compile(r"Math\.abs\s*\(\s*\w*[hH]\w*\s*-\s*\w*[hH]\w*\s*\)\s*[<>]=?\s*[\d.]+")
JS_ЧИТАЧ_СЛОВА = re.compile(r"\b(?:назваКольору|вікноЗіСлова|вікноНазви)\s*\(")
JS_ДУГА = re.compile(r"\b([A-Za-zА-Яа-яІіЇїЄєҐґ_]*[hH]\w*)\s*>=?\s*(\w+)\s*\|\|\s*\1\s*<=?\s*(\w+)|\b(\w+)\s*<=?\s*([A-Za-zА-Яа-яІіЇїЄєҐґ_]*[hH]\w*)\s*&&\s*\5\s*<=?\s*(\w+)")
JS_ВІКНА = re.compile(r"^\s*['\"]?[\wа-яіїєґ' -]+['\"]?\s*:\s*\[\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+")


def js_копії(t):
    """Парні C·cos(h), C·sin(h) з кутом у радіанах і виходом трьох координат — копія LCh→Lab."""
    # Ідентифікатори довільні: зв'язуємо обидва виходи з тією самою хромою й кутом.
    добуток = re.compile(r"\b(\w+)\s*\*\s*Math\.(cos|sin)\s*\(\s*([^();]+)\s*\)"
                        r"|Math\.(cos|sin)\s*\(\s*([^();]+)\s*\)\s*\*\s*(\w+)")
    блоки, стек, номер = {}, [0], 0
    межі = {0: [0, len(t)]}
    події = re.compile(r"[{}]|" + добуток.pattern)
    for m in події.finditer(t):
        if m.group() == "{":
            номер += 1
            стек.append(номер)
            межі[номер] = [m.start(), len(t)]
        elif m.group() == "}":
            if len(стек) > 1:
                межі[стек[-1]][1] = m.end()
                стек.pop()
        else:
            c, дія, h = (m[1], m[2], m[3]) if m[1] else (m[6], m[4], m[5])
            ключ = (стек[-1], c, re.sub(r"\s+", "", h))
            блоки.setdefault(ключ, []).append((дія, m.start()))
    for (блок, c, h), збіги in блоки.items():
        if {дія for дія, _ in збіги} != {"cos", "sin"}:
            continue
        # Кут безпосередньо або через присвоєння перетворено з градусів.
        до = t[:min(pos for _, pos in збіги)]
        тіло = t[slice(*межі[блок])]
        трійка = re.search(r"\breturn\s*\[\s*\w+\s*,[^,\]\n]+,[^\]\n]+\]", тіло)
        lab = re.search(r"\{[^{}]*\b[Ll]\s*[:,][^{}]*\ba\s*[:,][^{}]*\bb\b", тіло)
        рад = "Math.PI" in h or re.search(r"\b" + re.escape(h) + r"\s*=\s*[^;\n]*Math\.PI\s*/\s*180\b", до)
        if рад and (трійка or lab):
            for _, pos in збіги:
                yield t.count("\n", 0, pos) + 1


JS_RGB = re.compile(r"\b([rgbRGB])\s*(?:[<>]=?)\s*([rgbRGB])\b"
                    r"|\b(\w+)\s*\[\s*([012])\s*\]\s*[<>]=?\s*\3\s*\[\s*([012])\s*\]")


def обхід_js(шлях, файл, збір):
    t = open(шлях, encoding="utf-8").read()
    if re.search(r"згенеров|generated", t[:600], re.I):
        return
    чистий = без_коментарів(t)
    for i in js_копії(чистий):
        збір.дод(файл, i, 1, "парні cos/sin кута тону — друга копія LCh→Lab", "А")
    for i, рядок in enumerate(чистий.split("\n"), 1):
        for m in JS_RGB.finditer(рядок):
            if (m[1] and m[1].lower() != m[2].lower()) or (m[3] and re.search(r"rgb", m[3], re.I) and m[4] != m[5]):
                збір.дод(файл, i, 2, "сім'я/тон за порядком каналів RGB", "А")
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
        дерево = ОБСЯГ.розібрати(open(шлях, encoding="utf-8").read(), відн)
        if дерево is None:
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
        дерево = ОБСЯГ.розібрати(open(шлях, encoding="utf-8").read(), відн)
        if дерево is None:
            continue
        for f in функції(дерево):
            if ІМ_ТЕПЛА.search(f.name) and len(f.name) > 3:
                рад = рад_імена(f.body)
                if any(кут_радіани_тону(x, рад) for x in вузли(f.body)):
                    r.add(f.name)
    return r


# ---------------------------------------------------------------- Г10: слово крамниці (`колір_назва`) → `назва_кольору`
# Пункт 4 «код читає слово крамниці» за полем (рішення менеджера 31.10): місце — виклик функції, що транзитивно кличе
# `verify.назва_кольору`, на значенні поля `колір_назва`. Назва, тип, тканина, візерунок, крій — корінь
# `Річ-запис-речі` п.3, не тут. Потік значення, а не імена: мітка SRC — значення `колір_назва`; («ф», K, м) — «у полі K
# лежить значення з міткою м» (поле йде разом зі значенням, а не глобально за іменем ключа; кортеж — поля «#0», «#1»,
# ключ невідомий — «?»); («п», параметр, шлях) — символьне значення параметра в підсумку функції; («к», рядок) —
# сталий ключ у розгорнутому циклі над літералом. Аналіз іде інструкціями з об'єднанням гілок, підсумок функції —
# символьний (повернення й мутація параметрів, з підстановкою на виклику), вхід параметрів — конкретний (об'єднання
# всіх викликів). Список і його елемент — ті самі мітки. JSON туди й назад (`json.dumps`/`loads`) — та сама структура.
# Поле, яке кожен писач наповнює саме словом крамниці, — «чисте»: читання його будь-де дає SRC (так слово переходить
# межу збереженого каталогу: `фото_сестри_колір` → `також_у` → `є_також_у`, `shop_color`).
# Стік — параметр, чиє власне значення (не поле) доходить до першого параметра `назва_кольору`. Місце — виклик стоку,
# де аргумент несе SRC і слово взято тут (поле запису, джерело чи чисте поле), а не прохідний параметр функції:
# прохідний — місце її викликача, тож один потік — одне місце.
SRC = ("с",)
ДЖЕРЕЛО_ПОЛЕ = "колір_назва"
СТІК_Г10 = ("verify", "назва_кольору")
ГЛИБИНА_ПОЛІВ = 3
МЕЖА_ПРОХОДІВ = 100     # нерухома точка монотонна й скінченна; межа — лише запобіжник (на main 9e282d8c — 10 проходів)
_П = frozenset()
_ПРОХІДНІ_ВБУДОВАНІ = {"str", "list", "tuple", "set", "frozenset", "sorted", "reversed", "next", "iter", "min", "max",
                       "dict", "enumerate", "zip", "filter", "deepcopy"}
_ПРОХІДНІ_МЕТОДИ = {"strip", "lower", "upper", "title", "capitalize", "replace", "split", "rsplit", "partition",
                    "rpartition", "casefold", "lstrip", "rstrip", "copy", "splitlines", "removeprefix", "removesuffix"}
_ДОДАТИ = {"append", "extend", "add", "insert", "appendleft"}
_ВКЛАДЕНІ = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)


@functools.lru_cache(maxsize=None)
def _глибина(м):
    return 1 + _глибина(м[2]) if м[0] == "ф" else 0


@functools.lru_cache(maxsize=None)
def _поле(K, l):
    return frozenset(("ф", K, x) for x in l if _глибина(x) < ГЛИБИНА_ПОЛІВ and x[0] != "к")


@functools.lru_cache(maxsize=None)
def _читати(l, K, чисті=_П):
    """Значення поля K (None — будь-якого) зі значення з мітками l."""
    r = set()
    for x in l:
        if x[0] == "ф" and (K is None or x[1] == K):
            r.add(x[2])
        elif x[0] == "п" and len(x[2]) < ГЛИБИНА_ПОЛІВ:
            r.add(("п", x[1], x[2] + (K or "*",)))
    if K == ДЖЕРЕЛО_ПОЛЕ or K in чисті:
        r.add(SRC)
    return frozenset(r)


@functools.lru_cache(maxsize=None)
def _слова(l):
    """Що лишається від значення, вклеєного в рядок: саме слово (SRC чи параметр), без полів записів."""
    return frozenset(x for x in l if x == SRC or x[0] == "п")


@functools.lru_cache(maxsize=None)
def _позиція(l, i):
    """Позиція i кортежу (поле «#i»); список — той самий, що його елемент (решта міток, крім позицій)."""
    return _читати(l, "#%d" % i) | frozenset(x for x in l if x[0] not in ("п", "ф") or (x[0] == "ф" and x[1][:1] != "#"))


@functools.lru_cache(maxsize=None)
def _ітер(l):
    """Елемент при обході: список — ті самі мітки, що й список; кортеж — будь-яка позиція."""
    return frozenset(x for x in l if not (x[0] == "ф" and x[1][:1] == "#")) \
        | frozenset(x[2] for x in l if x[0] == "ф" and x[1][:1] == "#")


@functools.lru_cache(maxsize=None)
def _елемент(l):
    """Елемент контейнера: список речей зливається з речами (мітки ті самі), словник — зі значеннями полів."""
    return _читати(l, None) | l


@functools.lru_cache(maxsize=None)
def _шлях(l, шлях, чисті=_П):
    for K in шлях:
        l = _елемент(l) if K == "*" else _читати(l, K, чисті)
    return l


def _підставити(мітки, прив, чисті=_П):
    if not мітки:
        return _П
    r = set()
    for x in мітки:
        if x[0] == "п":
            r |= _шлях(прив.get(x[1], _П), x[2], чисті)
        elif x[0] == "ф":
            r |= _поле(x[1], _підставити({x[2]}, прив, чисті))
        else:
            r.add(x)
    return frozenset(r)


def _сталий(e):
    return isinstance(e, ast.Constant) and isinstance(e.value, str)


class _Одиниця:
    """Функція (вкладена й метод теж) чи тіло модуля."""
    def __init__(s, м, вузол, ім):
        s.м, s.ім = м, ім
        if isinstance(вузол, ast.Module):
            s.парам, s.тіло, іменні = [], вузол.body, []
        else:
            a = вузол.args
            s.парам = [x.arg for x in a.posonlyargs + a.args]
            іменні = [x.arg for x in a.kwonlyargs]
            s.тіло = вузол.body
        s.усі = set(s.парам) | set(іменні)
        s.рет = _П                                     # символьний підсумок повернення
        s.мут = collections.defaultdict(frozenset)     # параметр → що функція дописує в його об'єкт
        s.стік = set()                                 # параметри, чиє значення-слово доходить до `назва_кольору`
        s.вхід = collections.defaultdict(frozenset)    # параметр → конкретні мітки від усіх викликів


class ПотікГ10:
    def __init__(s, модулі):
        s.мод = модулі
        s.ал = {м: s._аліаси(д) for м, д in модулі.items()}
        s.визн = collections.defaultdict(list)
        s.одиниці = []
        for м, д in модулі.items():
            s.одиниці.append(_Одиниця(м, д, "<модуль>"))
            for x in ast.walk(д):
                if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    о = _Одиниця(м, x, x.name)
                    s.одиниці.append(о)
                    s.визн[(м, x.name)].append(о)
        for о in s.визн.get(СТІК_Г10, []):
            if о.парам:
                о.стік = {о.парам[0]}
        s.чисті = frozenset()
        s.власні = set()       # (модуль, рядок, модуль стоку, стік): аргумент-слово взято на місці виклику
        s.місця = {}

    def _аліаси(s, д):
        a = {}
        for x in ast.walk(д):
            if isinstance(x, ast.Import):
                for n in x.names:
                    if n.name in s.мод:
                        a[n.asname or n.name] = ("м", n.name)
            elif isinstance(x, ast.ImportFrom) and x.module in s.мод and not x.level:
                for n in x.names:
                    a[n.asname or n.name] = ("ф", x.module, n.name)
        return a

    def визначення(s, м, ім, глиб=0):
        """Визначення імені в модулі — своє чи переекспортоване `from X import ім` (`pipeline.опис_обʼєкт`)."""
        if (м, ім) in s.визн:
            return s.визн[(м, ім)]
        a = s.ал.get(м, {}).get(ім)
        if a and a[0] == "ф" and глиб < 6:
            return s.визначення(a[1], a[2], глиб + 1)
        return None

    def розв(s, м, c):
        f = c.func
        if isinstance(f, ast.Name):
            return s.визначення(м, f.id)
        if isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            a = s.ал[м].get(f.value.id)
            if a and a[0] == "м":
                return s.визначення(a[1], f.attr)
        return None

    def запустити(s):
        s.проходів = 0
        while s.проходів < МЕЖА_ПРОХОДІВ:
            s.проходів += 1
            s.зміна = False
            s.записи = collections.defaultdict(lambda: [0, 0])
            for о in s.одиниці:
                _АналізГ10(s, о, "символ").пройти()
                _АналізГ10(s, о, "конкрет").пройти()
            нові = {K for K, (усього, слів) in s.записи.items() if усього and усього == слів} - s.чисті
            if нові:
                s.чисті = frozenset(s.чисті | нові)
                s.зміна = True
            if not s.зміна:
                break
        for о in s.одиниці:
            _АналізГ10(s, о, "збір").пройти()
        return s.місця


class _АналізГ10:
    def __init__(s, п, о, режим):
        s.п, s.о, s.режим = п, о, режим
        s.символ = режим == "символ"
        s.корені = {}      # ім'я елемента циклу → ім'я контейнера (мутація елемента — мутація контейнера)

    # ---- записи й мутації
    def записати(s, K, l, вузол):
        """Запис значення з мітками l у поле K: облік «чистих» полів (конкретний прохід)."""
        if s.режим != "конкрет":
            return
        if isinstance(вузол, ast.Constant) or (isinstance(вузол, (ast.List, ast.Tuple, ast.Dict, ast.Set))
                                               and not getattr(вузол, "elts", getattr(вузол, "keys", None))):
            return     # сталий чи порожній запис нічого не каже про поле
        з = s.п.записи[K]
        з[0] += 1
        з[1] += l == {SRC}     # саме слово, а не запис чи пакет, що його несе

    def мутувати(s, ім, дод, env, бачені=()):
        if not дод or ім in бачені:
            return
        env[ім] = env.get(ім, _П) | дод
        if ім in s.о.усі and s.символ:
            н = s.доречні(frozenset(x for x in дод if not (x[0] == "п" and x[1] == ім))) - s.о.мут[ім]
            if н:
                s.о.мут[ім] = s.о.мут[ім] | н
                s.п.зміна = True
        if ім in s.корені:
            s.мутувати(s.корені[ім], дод, env, бачені + (ім,))

    @staticmethod
    def корінь(e):
        while True:
            if isinstance(e, ast.Name):
                return e.id
            if isinstance(e, ast.Subscript):
                e = e.value
            elif isinstance(e, ast.Call) and isinstance(e.func, ast.Attribute) and e.func.attr in ("values", "items", "copy"):
                e = e.func.value
            elif isinstance(e, ast.Call) and isinstance(e.func, ast.Name) and e.func.id in ("sorted", "list", "reversed", "enumerate", "tuple") and e.args:
                e = e.args[0]
            else:
                return None

    def ключі(s, e, env):
        """Сталі ключі виразу: рядок чи ім'я з розгорнутого циклу над літералом пар."""
        if _сталий(e):
            return [e.value]
        if isinstance(e, ast.Name):
            l = env.get(e.id, _П)
            if l and all(x[0] == "к" for x in l):
                return [x[1] for x in l]
        return None

    # ---- вирази
    def L(s, e, env):
        if e is None:
            return _П
        if isinstance(e, ast.Name):
            return env.get(e.id, _П)
        if isinstance(e, ast.Subscript):
            v = s.L(e.value, env)
            if isinstance(e.slice, ast.Constant) and type(e.slice.value) is int:
                return _позиція(v, e.slice.value)
            кл = s.ключі(e.slice, env)
            if кл:
                return _П.union(*[_читати(v, K, s.п.чисті) for K in кл])
            s.L(e.slice, env)
            return _елемент(v)
        if isinstance(e, ast.Attribute):
            return _читати(s.L(e.value, env), "." + e.attr, s.п.чисті) | (frozenset({SRC}) if e.attr == ДЖЕРЕЛО_ПОЛЕ else _П)
        if isinstance(e, ast.BoolOp):
            return _П.union(*[s.L(v, env) for v in e.values])
        if isinstance(e, ast.IfExp):
            s.L(e.test, env)
            return s.L(e.body, env) | s.L(e.orelse, env)
        if isinstance(e, ast.Tuple) and not any(isinstance(v, ast.Starred) for v in e.elts):
            # кортеж — позиційно («#0», «#1»): розпакування `a, b = …` не змішує позицій
            return _П.union(*[_поле("#%d" % i, s.L(v, env)) for i, v in enumerate(e.elts)])
        if isinstance(e, (ast.List, ast.Tuple, ast.Set)):
            return _П.union(*[s.L(v, env) for v in e.elts])
        if isinstance(e, (ast.YieldFrom, ast.Starred, ast.Await)):
            return s.L(e.value, env)
        if isinstance(e, ast.Yield):
            s.L(e.value, env)
            return _П
        if isinstance(e, ast.NamedExpr):
            l = s.L(e.value, env)
            env[e.target.id] = l
            return l
        if isinstance(e, ast.Dict):
            r = _П
            for k, v in zip(e.keys, e.values):
                lv = s.L(v, env)
                кл = s.ключі(k, env) if k is not None else None
                if k is None:
                    r |= lv                      # **інший — його поля
                elif кл:
                    for K in кл:
                        s.записати(K, lv, v)
                        r |= _поле(K, lv)
                else:
                    s.L(k, env)
                    r |= _поле("?", lv)           # ключ невідомий
            return r
        if isinstance(e, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            вн = dict(env)
            for g in e.generators:
                s.присвоїти(g.target, _ітер(s.L(g.iter, вн)), вн)
                for у in g.ifs:
                    s.L(у, вн)
            if isinstance(e, ast.DictComp):
                кл = s.ключі(e.key, вн)
                if not кл:
                    s.L(e.key, вн)
                lv = s.L(e.value, вн)
                return _П.union(*[_поле(K, lv) for K in кл]) if кл else _поле("?", lv)
            return s.L(e.elt, вн)
        if isinstance(e, ast.Call):
            return s.виклик(e, env)
        if isinstance(e, (ast.JoinedStr, ast.FormattedValue)) or (isinstance(e, ast.BinOp) and isinstance(e.op, ast.Add)):
            # складений рядок несе слово, що в нього вклеєне (f-рядок, «+»), але не поля записів
            return _слова(_П.union(*[s.L(д, env) for д in ast.iter_child_nodes(e) if isinstance(д, ast.expr)]))
        for д in ast.iter_child_nodes(e):           # порівняння, арифметика: слова не несуть
            if isinstance(д, ast.expr) and not isinstance(д, ast.Lambda):
                s.L(д, env)
        return _П

    def виклик(s, c, env):
        п, о = s.п, s.о
        f = c.func
        арг = [s.L(a, env) for a in c.args]
        кв = [(k.arg, s.L(k.value, env), k.value) for k in c.keywords]
        цілі = п.розв(о.м, c)
        if цілі:
            r = _П
            for g in цілі:
                прив, вузли = {}, {}
                for i, a in enumerate(c.args):
                    if i < len(g.парам) and not isinstance(a, ast.Starred):
                        прив[g.парам[i]], вузли[g.парам[i]] = арг[i], a
                for k, l, v in кв:
                    if k:
                        прив[k], вузли[k] = l, v
                r |= _підставити(g.рет, прив, п.чисті)
                for p, мут in list(g.мут.items()):
                    if isinstance(вузли.get(p), ast.Name):
                        s.мутувати(вузли[p].id, _підставити(мут, прив, п.чисті), env)
                if s.символ:
                    for p in list(g.стік):
                        if any(x == SRC or (x[0] == "п" and x[2]) for x in прив.get(p, _П)):
                            п.власні.add((о.м, c.lineno, g.м, g.ім))     # слово взяте тут, а не прохідний параметр
                        for x in прив.get(p, _П):
                            # саме слово (чи елемент списку слів), а не поле об'єкта, що його несе
                            if x[0] == "п" and not x[2] and x[1] not in о.стік:
                                о.стік.add(x[1])
                                п.зміна = True
                    continue
                for p, l in прив.items():
                    н = frozenset(x for x in l if x[0] != "к") - g.вхід[p]
                    if н:
                        g.вхід[p] = g.вхід[p] | н
                        п.зміна = True
                if s.режим == "збір":
                    for p in g.стік:
                        if p in прив and SRC in прив[p] and (о.м, c.lineno, g.м, g.ім) in п.власні:
                            п.місця.setdefault((о.м, c.lineno), set()).add("%s.%s" % (g.м, g.ім))
            return r
        if isinstance(f, ast.Attribute):
            v = s.L(f.value, env)
            ім = f.value.id if isinstance(f.value, ast.Name) else None
            if f.attr in ("get", "pop", "setdefault") and c.args:
                кл = s.ключі(c.args[0], env)
                база = _П.union(*[_читати(v, K, п.чисті) for K in кл]) if кл else _читати(v, None, п.чисті)
                return база | (арг[1] if len(арг) > 1 else _П)
            if f.attr == "update" and ім:
                дод = _П.union(*арг)
                for k, l, вуз in кв:
                    if k:
                        s.записати(k, l, вуз)
                        дод |= _поле(k, l)
                    else:
                        дод |= l
                s.мутувати(ім, дод, env)
                return _П
            if f.attr in _ДОДАТИ and ім:
                s.мутувати(ім, _П.union(*арг), env)
                return _П
            if f.attr == "values":
                return _читати(v, None, п.чисті)
            if f.attr == "items":
                return _поле("#1", _читати(v, None, п.чисті))
            if f.attr in _ПРОХІДНІ_МЕТОДИ:
                return v
            if f.attr in ("join", "format"):
                return _слова(v | _П.union(*арг) | _П.union(*[l for _, l, _ in кв]))
            if f.attr in ("dumps", "loads", "deepcopy", "copy") and арг:
                return арг[0]          # JSON туди й назад (`_json.loads(показ(d))`) — та сама структура
            return _П
        if isinstance(f, ast.Name) and f.id == "enumerate" and арг:
            return _поле("#1", арг[0])
        if isinstance(f, ast.Name) and f.id == "zip":
            return _П.union(*[_поле("#%d" % i, a) for i, a in enumerate(арг)])
        if isinstance(f, ast.Name) and f.id == "dict" and арг:
            r = _П.union(*[_поле("?", _читати(a, "#1")) | frozenset(x for x in a if x[0] == "ф" and not x[1].startswith("#")) for a in арг])
            for k, l, вуз in кв:
                if k:
                    s.записати(k, l, вуз)
                    r |= _поле(k, l)
                else:
                    r |= l
            return r
        if isinstance(f, ast.Name) and f.id in _ПРОХІДНІ_ВБУДОВАНІ:
            r = _П.union(*арг)
            if f.id == "dict":
                for k, l, вуз in кв:
                    if k:
                        s.записати(k, l, вуз)
                        r |= _поле(k, l)
                    else:
                        r |= l
            return r
        if not isinstance(f, ast.Name):
            s.L(f, env)
        return _П

    # ---- присвоєння
    def присвоїти(s, ц, l, env, сильно=True, вузол=None):
        if isinstance(ц, ast.Name):
            env[ц.id] = l if сильно else env.get(ц.id, _П) | l
            s.корені.pop(ц.id, None) if сильно else None
        elif isinstance(ц, (ast.Tuple, ast.List)):
            if isinstance(вузол, (ast.Tuple, ast.List)) and len(вузол.elts) == len(ц.elts) \
                    and not any(isinstance(x, ast.Starred) for x in ц.elts + вузол.elts):
                env_зн = [s.L(x, dict(env)) for x in вузол.elts]
                for x, lx, вх in zip(ц.elts, env_зн, вузол.elts):
                    s.присвоїти(x, lx, env, сильно, вх)
            else:
                for i, x in enumerate(ц.elts):
                    if isinstance(x, ast.Starred):
                        s.присвоїти(x, l, env, сильно)
                    else:
                        s.присвоїти(x, _позиція(l, i), env, сильно)
        elif isinstance(ц, ast.Starred):
            s.присвоїти(ц.value, l, env, сильно)
        elif isinstance(ц, ast.Subscript):
            кл = s.ключі(ц.slice, env)
            if кл:
                for K in кл:
                    s.записати(K, l, вузол if вузол is not None else ц)
                дод = _П.union(*[_поле(K, l) for K in кл])
            else:
                s.L(ц.slice, env)
                дод = _поле("?", l)
            ім = s.корінь(ц.value)
            if ім:
                s.мутувати(ім, дод, env)
        elif isinstance(ц, ast.Attribute):
            s.записати("." + ц.attr, l, вузол if вузол is not None else ц)
            ім = s.корінь(ц.value)
            if ім:
                s.мутувати(ім, _поле("." + ц.attr, l), env)

    # ---- інструкції
    @staticmethod
    def злити(*envs):
        r = {}
        for e in envs:
            for k, v in e.items():
                r[k] = r.get(k, _П) | v
        return r

    def блок(s, інстр, env):
        for x in інстр:
            env = s.інструкція(x, env)
        return env

    def доречні(s, l):
        """Підсумок функції — лише мітки, що можуть нести слово: SRC, прохідне значення параметра (шлях з «*»,
        для стоку) чи шлях параметра, на якому в її вході є слово. Решта (поля пакетів без слова) роздувала
        підсумки до сотень тисяч міток і нічого не важила для лічби."""
        о, ч = s.о, s.п.чисті
        def д(x):
            if x[0] == "п":
                return not x[2] or bool(_шлях(о.вхід[x[1]], x[2], ч)) if x[1] in о.усі else False
            if x[0] == "ф":
                return д(x[2])
            return x[0] == "с"
        return frozenset(x for x in l if д(x))

    def повернути(s, l):
        l = s.доречні(l) if s.символ else l
        if s.символ and not l <= s.о.рет:
            s.о.рет = s.о.рет | l
            s.п.зміна = True

    def цикл_пар(s, x, env):
        """`for k, v in (("колір", ...), ("тип", ...))` — розгорнуто: ключ кожного кроку сталий (`річ[k] = v`)."""
        it, ц = x.iter, x.target
        if isinstance(it, (ast.Tuple, ast.List, ast.Set)) and isinstance(ц, ast.Name) and 0 < len(it.elts) <= 64 \
                and all(_сталий(e) for e in it.elts):
            виходи = [s.блок(x.body, dict(env, **{ц.id: frozenset({("к", e.value)})})) for e in it.elts]
            return s.блок(x.orelse, s.злити(env, *виходи))
        if not (isinstance(it, (ast.Tuple, ast.List)) and isinstance(ц, ast.Tuple) and 0 < len(it.elts) <= 64
                and all(isinstance(e, ast.Tuple) and len(e.elts) == len(ц.elts) for e in it.elts)
                and all(isinstance(t, ast.Name) for t in ц.elts)):
            return None
        виходи = []
        for e in it.elts:
            в = dict(env)
            for t, к in zip(ц.elts, e.elts):
                в[t.id] = frozenset({("к", к.value)}) if _сталий(к) else s.L(к, env)
            виходи.append(s.блок(x.body, в))
        return s.блок(x.orelse, s.злити(env, *виходи))

    def інструкція(s, x, env):
        if isinstance(x, _ВКЛАДЕНІ):
            return env
        if isinstance(x, ast.Assign):
            l = s.L(x.value, env)
            for t in x.targets:
                s.присвоїти(t, l, env, вузол=x.value)
            return env
        if isinstance(x, ast.AnnAssign):
            if x.value is not None:
                s.присвоїти(x.target, s.L(x.value, env), env, вузол=x.value)
            return env
        if isinstance(x, ast.AugAssign):
            s.присвоїти(x.target, s.L(x.value, env), env, сильно=False, вузол=x.value)
            return env
        if isinstance(x, ast.Return):
            s.повернути(s.L(x.value, env))
            return env
        if isinstance(x, ast.Expr):
            s.L(x.value, env)
            return env
        if isinstance(x, ast.If):
            s.L(x.test, env)
            return s.злити(s.блок(x.body, dict(env)), s.блок(x.orelse, dict(env)))
        if isinstance(x, (ast.For, ast.AsyncFor)):
            розгорнуто = s.цикл_пар(x, env)
            if розгорнуто is not None:
                return розгорнуто
        if isinstance(x, (ast.For, ast.AsyncFor, ast.While)):
            вихід = dict(env)
            for _ in range(4):
                e = dict(вихід)
                if isinstance(x, ast.While):
                    s.L(x.test, e)
                else:
                    s.присвоїти(x.target, _ітер(s.L(x.iter, e)), e)
                    к = s.корінь(x.iter)
                    if к:
                        for t in ast.walk(x.target):
                            if isinstance(t, ast.Name):
                                s.корені[t.id] = к
                нове = s.блок(x.body, e)
                if all(v <= вихід.get(k, _П) for k, v in нове.items()):
                    break
                вихід = s.злити(вихід, нове)
            return s.блок(x.orelse, вихід)
        if isinstance(x, (ast.With, ast.AsyncWith)):
            for w in x.items:
                l = s.L(w.context_expr, env)
                if w.optional_vars is not None:
                    s.присвоїти(w.optional_vars, l, env)
            return s.блок(x.body, env)
        if isinstance(x, (ast.Try, getattr(ast, "TryStar", ast.Try))):
            тіло = s.блок(x.body, dict(env))
            після = s.злити(env, тіло)
            гілки = [s.блок(h.body, dict(після)) for h in x.handlers]
            інакше = s.блок(x.orelse, dict(тіло))
            return s.блок(x.finalbody, s.злити(тіло, інакше, *гілки))
        if isinstance(x, ast.Match):
            s.L(x.subject, env)
            return s.злити(env, *[s.блок(к.body, dict(env)) for к in x.cases])
        for д in ast.iter_child_nodes(x):
            if isinstance(д, ast.expr):
                s.L(д, env)
        return env

    def пройти(s):
        if s.символ:
            env = {p: frozenset({("п", p, ())}) for p in s.о.усі}
        else:
            env = {p: s.о.вхід[p] for p in s.о.усі}
        s.блок(s.о.тіло, env)


def місця_г10(корінь):
    """Г10: [(файл, рядок, стоки)] — виклик на слові `колір_назва` функції, що транзитивно кличе `назва_кольору`."""
    модулі, відн = {}, {}
    for шлях, в, вид in файли(корінь):
        if вид != "py":
            continue
        дерево = ОБСЯГ.розібрати(open(шлях, encoding="utf-8").read(), в)
        if дерево is None:
            continue
        модулі[os.path.basename(шлях)[:-3]] = дерево
        відн[os.path.basename(шлях)[:-3]] = в
    if СТІК_Г10[0] not in модулі:
        return []
    місця = ПотікГ10(модулі).запустити()
    return [(відн[м], р, sorted(г)) for (м, р), г in місця.items()]


# ---------------------------------------------------------------- Г2: другий словник «слово сім'ї чи кольору → код»
# Пункт 1 «рахує поза одним модулем визначення» (паспорт, «Наступний крок»): словник-літерал (≥ 3 пари «кирилиця →
# код») поза `внутрішня_мова.py`, що ділить ≥ 2 точні пари з `ТАБЛИЦЯ["palette_family"]` чи `["color_name"]`; місце —
# кожна його пара, де слово таблиці має інший код. Таблицю бере з вимірюваного дерева окремим процесом (`-I`, шлях
# `джерела/` дерева першим): імпорт у процес приладу змішав би дерево бази з деревом голови.
ПОЛЯ_Г2 = ("palette_family", "color_name")
МОДУЛЬ_ТАБЛИЦІ = "внутрішня_мова"


def таблиця_г2(корінь):
    дж = os.path.join(корінь, "джерела")
    if not os.path.exists(os.path.join(дж, МОДУЛЬ_ТАБЛИЦІ + ".py")):
        return {}
    код = ("import sys, json; sys.path.insert(0, sys.argv[1]); import %s as В; "
           "print(json.dumps({п: В.ТАБЛИЦЯ.get(п) or {} for п in sys.argv[2:]}, ensure_ascii=False))" % МОДУЛЬ_ТАБЛИЦІ)
    try:
        вих = subprocess.run([sys.executable, "-I", "-c", код, дж, *ПОЛЯ_Г2], cwd=дж, capture_output=True, text=True,
                             timeout=120)
        if вих.returncode == 0:
            return json.loads(вих.stdout.strip().splitlines()[-1])
        ОБСЯГ.непрочитано("джерела/%s.py" % МОДУЛЬ_ТАБЛИЦІ, "ТАБЛИЦЯ: код %d %s" % (
            вих.returncode, (вих.stderr.strip().splitlines() or ["—"])[-1]))
        return {}
    except (subprocess.SubprocessError, ValueError, IndexError, OSError) as е:
        ОБСЯГ.непрочитано("джерела/%s.py" % МОДУЛЬ_ТАБЛИЦІ, "ТАБЛИЦЯ: %s: %s" % (type(е).__name__, е))
        return {}


def місця_г2(корінь):
    """Г2: [(файл, рядок, чому)] — пара словника-літерала з кодом, іншим за таблицю внутрішньої мови."""
    таблиця = таблиця_г2(корінь)
    слово_коди = {п: {} for п in таблиця}
    for п, т in таблиця.items():
        for к, w in (т or {}).items():
            слово_коди[п].setdefault(w, set()).add(к)
    r = []
    for шлях, в, вид in файли(корінь):
        if вид != "py" or os.path.basename(шлях)[:-3] == МОДУЛЬ_ТАБЛИЦІ:
            continue
        дерево = ОБСЯГ.розібрати(open(шлях, encoding="utf-8").read(), в)
        if дерево is None:
            continue
        for x in ast.walk(дерево):
            if not isinstance(x, ast.Dict):
                continue
            пари = [(k.value, v.value, k.lineno) for k, v in zip(x.keys, x.values)
                    if k_is_str(k) and isinstance(v, ast.Constant) and isinstance(v.value, str)
                    and re.search(r"[а-яіїєґ]", k.value, re.I) and re.fullmatch(r"[a-z_]+", v.value)]
            if len(пари) < 3:
                continue
            for п, ск in слово_коди.items():
                if sum(1 for w, к, _ in пари if к in ск.get(w, ())) < 2:
                    continue
                for w, к, рядок in пари:
                    if w in ск and к not in ск[w]:
                        r.append((в, рядок, "словник «слово → код» поза `%s`: «%s» → `%s`, у `ТАБЛИЦЯ[\"%s\"]` — `%s` (Г2)"
                                  % (МОДУЛЬ_ТАБЛИЦІ, w, к, п, "`, `".join(sorted(ск[w])))))
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
    for файл, рядок, стоки in місця_г10(корінь):
        ланцюг = "`%s` → " % "`, `".join(стоки) if стоки != ["verify.назва_кольору"] else ""
        збір.дод(файл, рядок, 4, "слово крамниці (`колір_назва`) → %s`назва_кольору` (Г10)" % ланцюг, "Г10")
    for файл, рядок, чому in місця_г2(корінь):
        збір.дод(файл, рядок, 1, чому, "Г2")
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
    for ш, п in (("Г10", 4), ("Г2", 1)):
        print("з них %s (пункт %d): %d" % (ш, п, sum(1 for з in збір.м.values() if ш in з["шляхи"])))
    print("модуль визначення `%s`: %s" % (МОДУЛЬ_ВИЗНАЧЕННЯ, "є" if os.path.exists(os.path.join(корінь, "джерела", МОДУЛЬ_ВИЗНАЧЕННЯ + ".py")) else "нема — поза модулем усе"))
    print("місць: %d" % len(збір.м))
    return 0


if __name__ == "__main__":
    sys.exit(головна(sys.argv[1:]))
