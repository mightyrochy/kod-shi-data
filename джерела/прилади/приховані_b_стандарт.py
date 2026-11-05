# -*- coding: utf-8 -*-
"""Приховані вади, частина (б): лічба місць коду продукту, де код робить не те, що велить `аудит/СТАНДАРТ_КОДУ.md`.

Наряд `аудит/наряди/Приховані-розвідка.md`, частина (б). Прилад не судить і не лагодить: для кожного з 24 пунктів
стандарту він або лічить місця статично (AST і токени коментарів по всіх модулях `status.МОДУЛІ_ПРОДУКТУ`), або
прямо каже, що пункт статично не міряється і чим його міряти. Знаменник покриття — 24 пункти; одиниця пункту —
модуль ядра (180), тож покриття пункту — скільки модулів прилад обійшов із 180.

Принцип ядра «код знає лише те, що може точно порахувати» лічить сусідній `приховані_b_точність.py`.

Запуск з кореня репозиторію:
  python3 джерела/прилади/приховані_b_стандарт.py               підсумок: рядок на пункт (статус, місць, приклади)
  python3 джерела/прилади/приховані_b_стандарт.py --пункт 10    усі місця пункту, рядок на місце (файл:рядок ⇥ що)
Останній рядок — `місць: <N>` (сума статично виміряних пунктів).
"""
import argparse
import ast
import glob
import io
import os
import re
import sys
import tokenize
import warnings

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ДЖ = os.path.join(КОРІНЬ, "джерела")
sys.path.insert(0, ДЖ)

КИР = "а-яіїєґʼ'"
_КИР = re.compile("[а-яіїєґА-ЯІЇЄҐ]")
_ЛАТ = re.compile("[a-zA-Z]")


def _ядро():
    """Імена модулів ядра зі `status.МОДУЛІ_ПРОДУКТУ` — той самий список, що вантажить збірка."""
    import status
    return sorted(status.МОДУЛІ_ПРОДУКТУ)


def _дерево(шлях):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ast.parse(io.open(шлях, encoding="utf-8").read())


def _коментарі(шлях):
    """[(рядок, текст)] коментарів `#` файлу."""
    з = []
    with io.open(шлях, encoding="utf-8") as ф:
        try:
            for т in tokenize.generate_tokens(ф.readline):
                if т.type == tokenize.COMMENT:
                    з.append((т.start[0], т.string))
        except (tokenize.TokenError, IndentationError):
            pass
    return з


def _докстрінги(дерево):
    """[(рядок, текст)] докстрінгів модуля, класів і функцій."""
    з = []
    for в in [дерево] + [x for x in ast.walk(дерево)
                         if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))]:
        if в.body and isinstance(в.body[0], ast.Expr) and isinstance(в.body[0].value, ast.Constant) \
                and isinstance(в.body[0].value.value, str):
            з.append((в.body[0].lineno, в.body[0].value.value))
    return з


def _функції(дерево):
    return [в for в in ast.walk(дерево) if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _імпорти(дерево):
    """[(рядок, ім'я модуля)] усіх імпортів, зокрема всередині функцій; `from x import y` дає x."""
    з = []
    for в in ast.walk(дерево):
        if isinstance(в, ast.Import):
            з += [(в.lineno, а.name.split(".")[0]) for а in в.names]
        elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
            з.append((в.lineno, в.module.split(".")[0]))
            if в.module in ("прилади", "лабораторія", "проби"):
                з += [(в.lineno, в.module + "/" + а.name) for а in в.names]
    return з


class Скан:
    """Один обхід ядра: дерева, коментарі й рядки файлів, спільні для всіх пунктів."""

    def __init__(self):
        self.ядро = _ядро()
        self.файл = {м: os.path.join(ДЖ, м + ".py") for м in self.ядро}
        self.дерево = {м: _дерево(ф) for м, ф in self.файл.items()}
        self.рядки = {м: io.open(ф, encoding="utf-8").read().splitlines() for м, ф in self.файл.items()}
        self.верхні = {os.path.basename(ф)[:-3] for ф in glob.glob(os.path.join(ДЖ, "*.py"))}
        self.теки = {т: {os.path.basename(ф)[:-3] for ф in glob.glob(os.path.join(ДЖ, т, "*.py"))}
                     for т in ("прилади", "лабораторія", "проби")}

    def відн(self, м, рядок):
        return "джерела/%s.py:%d" % (м, рядок)


# ─────────────────────────────── §1 межа ядра ───────────────────────────────
ФАСАДИ = {"аксесуари_": "accessory", "фід_": "feed", "суд_": "суд_образу", "палітра_": "palette",
          "силует_": "silhouette", "композитор_": "composer", "міст_": "bridge", "верхнє_": "outer",
          "батарея_": "gate_reach"}


def п1(с):
    """Ядро імпортує з `прилади/`, `лабораторія/`, `проби/` чи модуль верхнього рівня поза ядром; чужий модуль ядра
    імпортує тіло гілки повз фасад (виняток стандарт дозволяє лише з причиною в п.1 — причин там нема)."""
    місця = []
    for м in с.ядро:
        for р, ім in _імпорти(с.дерево[м]):
            if "/" in ім or any(ім in мн for мн in с.теки.values()) and ім not in с.верхні:
                місця.append((с.відн(м, р), "ядро імпортує з теки: %s" % ім))
            elif ім in с.верхні and ім not in с.ядро:
                місця.append((с.відн(м, р), "ядро імпортує модуль поза ядром: %s" % ім))
            for преф, фасад in ФАСАДИ.items():
                if ім.startswith(преф) and ім != фасад and not м.startswith(преф) and м != фасад:
                    місця.append((с.відн(м, р), "повз фасад %s: %s" % (фасад, ім)))
    return "виміряно", місця


def п2(с):
    """Функція ядра без виконання на живому шляху й без тесту — міряє `досяжність.py` (CI), не цей прилад."""
    return "приладом досяжність.py", []


# ─────────────────────────────── §2 імена ───────────────────────────────
ДОЗВОЛЕНА_ЛАТИНКА = {"L", "a", "b", "C", "h", "lab", "hex", "de00", "Lab", "LCh", "rgb", "srgb", "xyz", "XYZ",
                     "id", "json", "re", "os", "sys", "self", "cls", "args", "kwargs", "math", "dict", "list",
                     "_"}


def _імена_оголошені(дерево):
    """[(рядок, ім'я)] імен, які модуль оголошує сам: функції, класи, параметри, присвоєння, цикли."""
    з = []
    for в in ast.walk(дерево):
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            з.append((в.lineno, в.name))
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            а = в.args
            з += [(x.lineno, x.arg) for x in а.posonlyargs + а.args + а.kwonlyargs + [а.vararg, а.kwarg] if x]
        elif isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store):
            з.append((в.lineno, в.id))
    return з


def _сегменти_змішані(ім):
    """Чи ім'я змішує письма поза дозволеними латинськими сегментами (`lab_рядок` — ні, `Lзнач`, `rule_правило` — так)."""
    сегм = [x for x in ім.strip("_").split("_") if x]
    лат = [x for x in сегм if _ЛАТ.search(x) and not _КИР.search(x)]
    кир = [x for x in сегм if _КИР.search(x)]
    в_слові = any(_ЛАТ.search(x) and _КИР.search(x) for x in сегм)
    return в_слові or (кир and any(x not in ДОЗВОЛЕНА_ЛАТИНКА and not x.isdigit() and not re.fullmatch(r"[A-Za-z]\d*", x)
                                   for x in лат))


def п3(с):
    """Ім'я, що змішує письма в одному ідентифікаторі (поза `L a b C h lab hex de00`), і модуль, де предметні імена
    стоять і латиницею (не зі списку), і кирилицею — «одна мова на модуль»."""
    місця = []
    for м in с.ядро:
        бачено = set()
        лат, кир = [], 0
        for р, ім in _імена_оголошені(с.дерево[м]):
            if ім in бачено:
                continue
            бачено.add(ім)
            if _сегменти_змішані(ім):
                місця.append((с.відн(м, р), "змішане ім'я: %s" % ім))
            elif _КИР.search(ім):
                кир += 1
            elif ім not in ДОЗВОЛЕНА_ЛАТИНКА and len(ім.strip("_")) > 2 and not ім.isupper():
                лат.append((р, ім))
        if кир and лат:
            місця.append((с.відн(м, лат[0][0]), "модуль двома мовами: латиницею %d імен (%s), кирилицею %d"
                           % (len(лат), ", ".join(x for _, x in лат[:4]), кир)))
    return "виміряно", місця


_ГОМОГЛІФ = re.compile(r"[а-яіїєґ][acepoxyikb](?![a-z])|(?<![a-z])[acepoxyikb][а-яіїєґ]")


def п4(с):
    """Гомогліф: латинська `a c e o p x y i k b` впритул до кириличної літери в імені (і навпаки)."""
    місця = []
    for м in с.ядро:
        for р, ім in set(_імена_оголошені(с.дерево[м])) | {(в.lineno, в.attr) for в in ast.walk(с.дерево[м])
                                                            if isinstance(в, ast.Attribute)}:
            if re.search(r"[а-яіїєґА-ЯІЇЄҐ][a-zA-Z]|[a-zA-Z][а-яіїєґА-ЯІЇЄҐ]", ім) and _ГОМОГЛІФ.search(ім.lower()):
                місця.append((с.відн(м, р), "гомогліф: %s" % ім))
    return "виміряно", sorted(set(місця))


ФОРМИ = {
    "намір": ("conventional", "fashion_forward", "editorial", "statement"),
    "джерело": ("uncontrolled", "protocolized", "spectro"),
}
_ІНШІ_ФОРМИ = re.compile(r"^(fashion[- ]forward|fashionforward|Fashion[_ -]?[Ff]orward|Conventional|Editorial|"
                         r"Statement|protocolised|protocolled|Uncontrolled|Spectro|spectrophotometer)$")


def п5(с):
    """Друга форма того самого значення наміру чи джерела (рядок-літерал не в каноні) і нормалізатор наміру поза одним
    місцем (`.replace("-", "_")` чи `.lower()` поруч із наміром); словник опадів поза `сценарій.канон_опади`."""
    місця = []
    for м in с.ядро:
        for в in ast.walk(с.дерево[м]):
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and _ІНШІ_ФОРМИ.match(в.value):
                місця.append((с.відн(м, в.lineno), "друга форма: %r" % в.value))
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "replace" \
                    and len(в.args) == 2 and all(isinstance(x, ast.Constant) for x in в.args) \
                    and {в.args[0].value, в.args[1].value} == {"-", "_"}:
                текст = с.рядки[м][в.lineno - 1]
                if re.search("намір|intent|fashion", текст):
                    місця.append((с.відн(м, в.lineno), "нормалізатор наміру"))
            if isinstance(в, ast.Dict) and м != "сценарій":
                ключі = {k.value for k in в.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                if len(ключі & {"дощ", "сніг", "мряка", "злива", "rain", "snow", "drizzle"}) >= 2:
                    місця.append((с.відн(м, в.lineno), "словник опадів поза сценарієм"))
    return "виміряно", місця


def п6(с):
    """Модуль ядра з українським іменем (стандарт: ядро — англійські імена); двох імен для однієї речі статично не
    видно."""
    місця = [("джерела/%s.py:1" % м, "ядро з українським іменем") for м in с.ядро if _КИР.search(м)]
    return "виміряно", місця


# ─────────────────────────────── §3 знахідки й правила ───────────────────────────────
def п7(с):
    """Знахідка зібрана словником з ключем `правило` поза конструктором `реєстр_сила.зн`, і `сила_нп`, записана після
    конструктора (`x["сила_нп"] = …`, `.update(сила_нп=…)`, `dict(…, сила_нп=…)`)."""
    місця = []
    for м in с.ядро:
        конструктор = {(м, в.lineno) for в in _функції(с.дерево[м]) if м == "реєстр_сила" and в.name == "зн"}
        межі = [(в.lineno, в.end_lineno) for в in _функції(с.дерево[м]) if (м, в.lineno) in конструктор]
        for в in ast.walk(с.дерево[м]):
            if any(п <= getattr(в, "lineno", 0) <= к for п, к in межі):
                continue
            if isinstance(в, ast.Dict):
                ключі = {k.value for k in в.keys if isinstance(k, ast.Constant)}
                if "правило" in ключі and ({"суть", "чому"} & ключі):
                    місця.append((с.відн(м, в.lineno), "знахідка словником поза зн()"))
            elif isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict" \
                    and {"правило"} <= {k.arg for k in в.keywords} and {"суть", "чому"} & {k.arg for k in в.keywords}:
                місця.append((с.відн(м, в.lineno), "знахідка dict() поза зн()"))
            elif isinstance(в, ast.Assign) and any(isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant)
                                                   and ц.slice.value == "сила_нп" for ц in в.targets):
                місця.append((с.відн(м, в.lineno), "сила_нп записана після конструктора"))
    return "виміряно", місця


def _корпус():
    """Коди правил корпусу (`корпус.ід` — той самий читач, що в `audit_contracts` і `gate_reach`) і коди, які
    `реєстр_правил.ПОЗА_КОРПУСОМ` оголошує свідомо поза корпусом."""
    import корпус
    import реєстр_правил
    return set(корпус.ід(корпус.тека())) | set(реєстр_правил.ПОЗА_КОРПУСОМ)


_СХОЖЕ_НА_ІД = re.compile(r"\b[KRPE]-[A-ZА-Я0-9]{2,6}-?\d{1,3}[a-zа-я]?\b")


def п8(с):
    """ID правила рядком у коді, що не проходить шаблон `ід_правил` (схоже, але криве), чи якого нема в корпусі;
    «порядок у коментарі» (правило № N замість ID) — ознака `правило \\d` у коментарі."""
    import ід_правил
    корпус = _корпус()
    місця = []
    for м in с.ядро:
        докстр = {р for р, _ in _докстрінги(с.дерево[м])}
        for в in ast.walk(с.дерево[м]):
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and в.lineno not in докстр:
                for x in _СХОЖЕ_НА_ІД.findall(в.value):
                    if not ід_правил.ІД.search(x):
                        місця.append((с.відн(м, в.lineno), "криве ID: %s" % x))
                for x in ід_правил.усі_в_тексті(в.value):
                    б = ід_правил.база(x)
                    if б and б not in корпус and not re.search("CONF|JOIN|UA", б):
                        місця.append((с.відн(м, в.lineno), "ID поза корпусом і поза ПОЗА_КОРПУСОМ: %s" % б))
        for р, т in _коментарі(с.файл[м]):
            if re.search(r"правил[оа] *(№|#) *\d", т):
                місця.append((с.відн(м, р), "порядок правила в коментарі"))
    return "виміряно", sorted(set(місця))


def п9(с):
    """Регістр (`гейт`/`репліка`/`питання`) присвоєно літералом поза функцією `реєстр_тіри.регістр` і поза таблицею
    `реєстр_політика` (вона — «одна таблиця» п.9)."""
    місця = []
    for м in с.ядро:
        if м == "реєстр_політика":
            continue
        межі = [(в.lineno, в.end_lineno) for в in _функції(с.дерево[м]) if м == "реєстр_тіри" and в.name == "регістр"]
        for в in ast.walk(с.дерево[м]):
            if any(п <= getattr(в, "lineno", 0) <= к for п, к in межі):
                continue
            пари = []
            if isinstance(в, ast.Dict):
                пари = [(k, v) for k, v in zip(в.keys, в.values) if isinstance(k, ast.Constant)]
            elif isinstance(в, ast.Call):
                пари = [(ast.Constant(к.arg), к.value) for к in в.keywords if к.arg]
            elif isinstance(в, ast.Assign):
                пари = [(ц.slice, в.value) for ц in в.targets if isinstance(ц, ast.Subscript)]
            for k, v in пари:
                if isinstance(k, ast.Constant) and k.value == "регістр" and isinstance(v, ast.Constant) \
                        and v.value in ("гейт", "репліка", "питання"):
                    місця.append((с.відн(м, в.lineno), "регістр %r літералом" % v.value))
    return "виміряно", місця


_РЕЄСТР = re.compile(r"^(REGISTRY|РЕЄСТР|[A-ZА-ЯІЇЄҐ_]*РЕЄСТР[A-ZА-ЯІЇЄҐ_]*|[A-Z_]*REGISTRY[A-Z_]*)$")
_СЛУЖБОВІ_ЧИСЛА = {0, 1, 2, -1, 0.0, 1.0, 2.0, 0.5, 100, 100.0, 10, 10.0, 3, 4, 60, 360, 180}  # = audit_anchors.БЕЗПЕЧНІ


def _число(в):
    if isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool):
        return в.value
    if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.USub) and isinstance(в.operand, ast.Constant) \
            and isinstance(в.operand.value, (int, float)) and not isinstance(в.operand.value, bool):
        return -в.operand.value
    return None


def п10(с):
    """Голе число в логіці функції ядра: числовий літерал поза службовими (`audit_anchors.БЕЗПЕЧНІ`), поза індексом і
    `round(x, n)`; запис реєстру без полів `t`, `val`, `прав`, `джерело` (`src` — те саме джерело іншим ім'ям)."""
    місця = []
    for м in с.ядро:
        for ф in _функції(с.дерево[м]):
            службові = set()
            for в in ast.walk(ф):
                if isinstance(в, ast.Subscript):
                    службові |= {id(x) for x in ast.walk(в.slice)}
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ("round", "range") \
                        and len(в.args) >= 2:
                    службові |= {id(x) for x in в.args[1:]}
                if isinstance(в, ast.Call):
                    службові |= {id(к.value) for к in в.keywords if к.arg in ("indent", "ensure_ascii", "maxsplit")}
                if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.USub):
                    службові.add(id(в.operand))
            for в in ast.walk(ф):
                ч = _число(в)
                if ч is None or id(в) in службові or ч in _СЛУЖБОВІ_ЧИСЛА:
                    continue
                if isinstance(в, ast.Constant) and в.col_offset >= 0:
                    місця.append((с.відн(м, в.lineno), "голе число %r у %s()" % (ч, ф.name)))
                elif isinstance(в, ast.UnaryOp):
                    місця.append((с.відн(м, в.lineno), "голе число %r у %s()" % (ч, ф.name)))
        for в in с.дерево[м].body:
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and _РЕЄСТР.match(ц.id) for ц in в.targets) \
                    and isinstance(в.value, ast.Dict):
                for k, v in zip(в.value.keys, в.value.values):
                    поля = set()
                    if isinstance(v, ast.Dict):
                        поля = {x.value for x in v.keys if isinstance(x, ast.Constant)}
                    elif isinstance(v, ast.Call):
                        поля = {x.arg for x in v.keywords}
                    else:
                        continue
                    if "src" in поля:
                        поля.add("джерело")  # колір_простір_реєстр пише джерело полем `src`
                    бракує = {"t", "val", "прав", "джерело"} - поля
                    if {"t", "val"} <= бракує:
                        бракує = {"форма не реєстру констант"}
                    if бракує:
                        ім = k.value if isinstance(k, ast.Constant) else "?"
                        місця.append((с.відн(м, v.lineno), "запис реєстру %s без %s" % (ім, ",".join(sorted(бракує)))))
    return "виміряно", місця


_ДЕФОЛТИ_МАСКИ = {"regular", "uncontrolled", "near", "середній", "medium", "regular_fit"}


def п11(с):
    """Дефолт, що маскує брак входу: `.get(к, x)` / `… or x` з рядковим (з літерами, не заглушка показу) чи ненульовим
    числовим x у функції ядра, де поля `джерело_…` нема; окремо — названі стандартом маски (`regular`, `uncontrolled`, `near`, площа 1/3)."""
    місця = []
    for м in с.ядро:
        for ф in _функції(с.дерево[м]):
            текст = "\n".join(с.рядки[м][ф.lineno - 1:ф.end_lineno])
            має_джерело = "джерело_" in текст
            for в in ast.walk(ф):
                x = None
                if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" \
                        and len(в.args) == 2 and isinstance(в.args[0], ast.Constant):
                    x = в.args[1]
                elif isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or):
                    x = в.values[-1]
                if not isinstance(x, ast.Constant) or x.value in (None, "", 0, 0.0, False, True):
                    continue
                if isinstance(x.value, str) and (not re.search("[A-Za-zА-Яа-яІіЇїЄєҐґ]", x.value)
                                                 or x.value.lower() in ("none", "unknown", "невідомо", "річ")):
                    continue  # заглушка показу («—», «?»), не значення входу
                if isinstance(x.value, str) and x.value in _ДЕФОЛТИ_МАСКИ:
                    місця.append((с.відн(м, в.lineno), "маска стандарту %r у %s()%s" % (
                        x.value, ф.name, " (джерело_ є)" if має_джерело else "")))
                elif not має_джерело and isinstance(x.value, (int, float, str)):
                    місця.append((с.відн(м, в.lineno), "дефолт %r у %s() без джерело_" % (x.value, ф.name)))
            for в in ast.walk(ф):
                if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Div) and _число(в.left) == 1 \
                        and _число(в.right) == 3:
                    місця.append((с.відн(м, в.lineno), "площа 1/3 у %s()" % ф.name))
    return "виміряно", місця


# ─────────────────────────────── §4 контракти ───────────────────────────────
def п12(с):
    """Поле без читача чи без писача — міряє `audit_contracts.py` (CI); прилад бере його рядки `⚠`."""
    return "приладом audit_contracts.py", []


def п13(с):
    """Параметр функції ядра, який тіло не читає (не `_`-ім'я, не `self`/`cls`, тіло не лише `...`/докстрінг)."""
    місця = []
    for м in с.ядро:
        for ф in _функції(с.дерево[м]):
            тіло = [x for x in ф.body if not (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant))]
            if not тіло or all(isinstance(x, (ast.Pass, ast.Raise)) for x in тіло):
                continue
            а = ф.args
            пар = [x.arg for x in а.posonlyargs + а.args + а.kwonlyargs + [а.vararg, а.kwarg] if x]
            читає = {в.id for в in ast.walk(ф) if isinstance(в, ast.Name)}
            for п in пар:
                if п.startswith("_") or п in ("self", "cls") or п in читає:
                    continue
                місця.append((с.відн(м, ф.lineno), "параметр %s не читає %s()" % (п, ф.name)))
    return "виміряно", місця


def п14(с):
    """`except`, що ковтає виняток: тіло без `raise`, без запису `помилка`/`код` і без виклику журналу —
    лише `pass`, присвоєння чи `return` без сигналу."""
    місця = []
    for м in с.ядро:
        for в in ast.walk(с.дерево[м]):
            if not isinstance(в, ast.ExceptHandler):
                continue
            тіло = ast.Module(body=в.body, type_ignores=[])
            текст = ast.unparse(тіло)
            if any(isinstance(x, ast.Raise) for x in ast.walk(тіло)):
                continue
            if re.search(r"помилк|\bкод\b|warn|print|log|stderr|чому", текст):
                continue
            тип = ast.unparse(в.type) if в.type else "голий"
            широкий = тип in ("голий", "Exception", "BaseException") or "Exception" in тип
            місця.append((с.відн(м, в.lineno), "except %s ковтає мовчки (%s)" % (тип, "широкий" if широкий else "вузький")))
    return "виміряно", місця


def п15(с):
    """Оголошеної схеми виходу ендпойнта моста ще нема — стандарт сам каже «мета»: місць не лічить."""
    return "мета стандарту", []


# ─────────────────────────────── §5 файли й структура ───────────────────────────────
def п16(с):
    """Файл ядра довший за 1 500 рядків."""
    return "виміряно", [(с.відн(м, 1), "%d рядків" % len(с.рядки[м])) for м in с.ядро if len(с.рядки[м]) > 1500]


def п17(с):
    """Функція ядра без докстрінга (абзац «чому так» — питання змісту, статично не видно)."""
    місця = []
    for м in с.ядро:
        for ф in _функції(с.дерево[м]):
            if not ast.get_docstring(ф):
                місця.append((с.відн(м, ф.lineno), "без докстрінга %s()" % ф.name))
    return "виміряно", місця


def п18(с):
    """Робота при імпорті модуля ядра: виклик, цикл, `with` чи `open` на верхньому рівні поза
    `if __name__ == "__main__":` (присвоєння константи з виклику — окремою міткою)."""
    місця = []
    for м in с.ядро:
        for в in с.дерево[м].body:
            if isinstance(в, ast.If) and "__name__" in ast.unparse(в.test):
                continue
            if isinstance(в, ast.Expr) and isinstance(в.value, ast.Call):
                ім = ast.unparse(в.value.func)
                if ім in ("warnings.filterwarnings", "sys.path.insert", "sys.path.append"):
                    місця.append((с.відн(м, в.lineno), "налаштування при імпорті: %s" % ім))
                else:
                    місця.append((с.відн(м, в.lineno), "виклик при імпорті: %s" % ім))
            elif isinstance(в, (ast.For, ast.While, ast.With)):
                місця.append((с.відн(м, в.lineno), "%s при імпорті" % type(в).__name__))
            elif isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None:
                for x in ast.walk(в.value):
                    if isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id == "open" or \
                            isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr in ("load", "loads", "read"):
                        місця.append((с.відн(м, в.lineno), "читання файлу при імпорті"))
                        break
    return "виміряно", місця


def п19(с):
    """Згенероване не з одного джерела: коміт `index.html` не від збірки CI (останні 200 комітів файлу без злиттів);
    `ДОВІДНИК` літералом у `показ.html`."""
    import subprocess
    місця = []
    try:
        автори = subprocess.run(["git", "log", "-200", "--no-merges", "--format=%h\t%an\t%s", "--", "index.html"], cwd=КОРІНЬ,
                                capture_output=True, text=True, timeout=60).stdout.split("\n")
    except (OSError, subprocess.SubprocessError) as е:
        автори = []
        print("п.19: git log не вдався: %s" % е, file=sys.stderr)
    for р in автори:
        поля = р.split("\t")
        # межа неглибокого клону показує злиття без батьків — його `--no-merges` не відсіює
        if len(поля) == 3 and not поля[1].startswith("github-actions") and not поля[2].startswith("Merge "):
            місця.append(("index.html:1", "коміт %s (%s) не від збірки" % (поля[0], поля[1])))
    показ = os.path.join(ДЖ, "показ.html")
    if os.path.exists(показ):
        for і, р in enumerate(io.open(показ, encoding="utf-8"), 1):
            if re.search(r"ДОВІДНИК\s*=\s*[\[{]", р):
                місця.append(("джерела/показ.html:%d" % і, "ДОВІДНИК літералом у показі"))
    return "виміряно", місця


_ІСТОРІЯ = re.compile(r"рядок\s+\d{3,5}|рядки\s+\d{3,5}|\bPR\s*#?\d{3,4}|#\d{3,4}\b|\b\d{1,2}\.(?:09|10|11)\b|"
                      r"\bН-\d\d-\d\d|ЩО БУЛО|\bбуло:|\bБУЛО\b|прогін\s+\d|наряд\s+[А-ЯA-Z]")
_КОНТРАКТ = re.compile(r"ЄДИН[ИИІ][ЙЕ]|ЄДИНЕ|ЄДИНА|\b\d+\s+модул|\b\d+\s*%\s+каталог|ЗАБЛОКУЄ|НІКОЛИ\b|ЗАВЖДИ\b")


def п20(с):
    """Історія правки в коментарі чи докстрінгу (рядок дошки, PR, дата, наряд, «було»); коментар-контракт
    («ЄДИНИЙ», «N модулів», «НІКОЛИ/ЗАВЖДИ») без тесту — лічиться як кандидат, бо тест статично не звірити.
    Чи коментар збігається з кодом — статично не видно."""
    місця = []
    for м in с.ядро:
        тексти = _коментарі(с.файл[м]) + [(р + і, рядок) for р, т in _докстрінги(с.дерево[м])
                                           for і, рядок in enumerate(т.splitlines())]
        for р, т in тексти:
            if _ІСТОРІЯ.search(т):
                місця.append((с.відн(м, р), "історія: %s" % _ІСТОРІЯ.search(т).group(0)))
            if _КОНТРАКТ.search(т):
                місця.append((с.відн(м, р), "контракт: %s" % _КОНТРАКТ.search(т).group(0)))
    return "виміряно", місця


# ─────────────────────────────── §6 тести й прилади ───────────────────────────────
def п21(с):
    """Прилад (`джерела/прилади/*.py`), у якому нема жодного виходу з ненульовим кодом (`sys.exit(…)`, `exit(1)`,
    `SystemExit`, `raise`, `assert`) — провал не дасть коду 1; `unittest` виходить кодом 1 сам; лічильники з рядком `місць:` (корені, ці прилади) — поза
    пунктом: їм `аудит/КОД.md` велить код 0. ДО/ПІСЛЯ зміни поведінки — процес, не код."""
    місця = []
    for ф in sorted(glob.glob(os.path.join(ДЖ, "прилади", "*.py"))):
        try:
            д = _дерево(ф)
        except SyntaxError:
            місця.append((os.path.relpath(ф, КОРІНЬ) + ":1", "не розбирається"))
            continue
        текст = io.open(ф, encoding="utf-8").read()
        if "місць:" in текст or "unittest" in текст:
            continue  # лічильник кореня виходить кодом 0 за `аудит/КОД.md`, провал — це число, не код виходу
        має = any(isinstance(в, (ast.Raise, ast.Assert)) or isinstance(в, ast.Call) and
                  ast.unparse(в.func) in ("sys.exit", "exit", "SystemExit", "os._exit") for в in ast.walk(д))
        if not має:
            місця.append((os.path.relpath(ф, КОРІНЬ) + ":1", "прилад без ненульового виходу"))
    return "виміряно", місця


def п22(с):
    """Батарея й проби перед PR, ДО/ПІСЛЯ в тілі PR — процес, міряє частина (ґ/д), не код."""
    return "процес", []


def п23(с):
    """Сканер у CI: `досяжність.py` і `audit_contracts.py` мають бути кроками `zbirka.yml`; лінтера імен (п.3–5) нема —
    стандарт сам це каже, тож п.3–5 у CI ніхто не тримає."""
    місця = []
    yml = os.path.join(КОРІНЬ, ".github", "workflows", "zbirka.yml")
    текст = io.open(yml, encoding="utf-8").read() if os.path.exists(yml) else ""
    for ім in ("досяжність", "audit_contracts"):
        if ім not in текст:
            місця.append((".github/workflows/zbirka.yml:1", "нема кроку %s" % ім))
    місця.append(("аудит/СТАНДАРТ_КОДУ.md:73", "п.3–5 без лінтера в CI (гомогліфи, змішані імена, форми наміру)"))
    return "виміряно", місця


def п24(с):
    """Списки приладів: кожен модуль (`gate_reach`, `audit_contracts`, `відбиток`, `досяжність`, `status`), що тримає
    власний перелік імен приладів замість одного спільного."""
    місця = []
    for ім in ("gate_reach", "audit_contracts", "відбиток", "досяжність", "status", "status_перевірки"):
        ф = os.path.join(ДЖ, ім + ".py")
        if not os.path.exists(ф):
            continue
        for в in _дерево(ф).body:
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and re.search("ПРИЛАД|ІНСТРУМЕНТ|НЕ_СИСТЕМА|TOOLS",
                                                                                        ц.id) for ц in в.targets):
                if isinstance(в.value, (ast.Tuple, ast.List, ast.Set, ast.Dict, ast.Call)):
                    місця.append(("джерела/%s.py:%d" % (ім, в.lineno), "власний список приладів %s" %
                                  ",".join(ц.id for ц in в.targets if isinstance(ц, ast.Name))))
    if len(місця) <= 1:
        return "виміряно", []
    return "виміряно", місця


ПУНКТИ = {1: п1, 2: п2, 3: п3, 4: п4, 5: п5, 6: п6, 7: п7, 8: п8, 9: п9, 10: п10, 11: п11, 12: п12, 13: п13,
          14: п14, 15: п15, 16: п16, 17: п17, 18: п18, 19: п19, 20: п20, 21: п21, 22: п22, 23: п23, 24: п24}


def main():
    п = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    п.add_argument("--пункт", type=int, default=None)
    а = п.parse_args()
    с = Скан()
    if а.пункт:
        статус, місця = ПУНКТИ[а.пункт](с)
        print("п.%d · %s · місць %d" % (а.пункт, статус, len(місця)))
        for м, що in місця:
            print("%s\t%s" % (м, що))
        print("місць: %d" % len(місця))
        return 0
    разом, виміряно = 0, 0
    for н, ф in ПУНКТИ.items():
        статус, місця = ф(с)
        if статус == "виміряно":
            виміряно += 1
            разом += len(місця)
        прикл = "; ".join("%s %s" % x for x in місця[:2])
        print("п.%-2d %-28s місць %-5d %s" % (н, статус, len(місця), прикл[:160]))
    print("модулів ядра обійдено: %d · пунктів виміряно цим приладом: %d з %d" % (len(с.ядро), виміряно, len(ПУНКТИ)))
    print("місць: %d" % разом)
    return 0


if __name__ == "__main__":
    sys.exit(main())
