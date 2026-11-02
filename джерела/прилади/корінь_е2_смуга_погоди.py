# -*- coding: utf-8 -*-
"""прилади/корінь_е2_смуга_погоди.py — прилад кореня Е2-смуга-погоди: градуси повітря нагоди в коді продукту.

Клас — `аудит/корені/Е2-смуга-погоди.md` («Клас місць», «Стан і що лишилось» — «Вгору»): місце — кожна точка коду
продукту (`джерела/` на будь-якій глибині: Python, JS, HTML і промпти в них; проби, прилади й тести — ні), де градуси
повітря нагоди — названі нею чи число коду з відчуття — є полем, ключем, числом, порогом чи текстом показу. Пункти:
  1  мовну модель просять градуси (схема, опис поля `temperature_c`, промпт, заява з `temperature_c`/`temp_c`) чи код
     приймає їх із відповіді;
  2  код читає, пише, зберігає чи передає градуси (паспорт, картка, сцена, кеш, правила, бриф, промпт, заява суду,
     дріт, протокол стилістки), зокрема прапорець походження градусів (`темп_з_відчуття`);
  3  код перетворює відчуття на градуси (таблиця `weather_feel`) чи градуси на смугу, факт чи величину — порогом
     реєстру чи літералом, пошуком у таблиці смуг, відстанню чи часткою в °C; сам поріг реєстру, межа таблиці смуг,
     з якою порівнюють градуси нагоди, і літерал межі — теж місце;
  4  панель дає ввести градуси числом, картка й показ показують градуси;
  5  рішення правила погоди судить межею, якої база знань не дає (межі K-WEA-01 — з бази, `тема-4` §IX.4), чи межу
     визначено двічі (літерал, що повторює поріг реєстру). Місце — саме рішення (порівняння), не кожна точка з ід.

ВІД ЗНАЧЕННЯ, НЕ ВІД ІМЕН. Зерна — ознаки самого значення градусів нагоди:
  · ключі `темп_c`, `temperature_c`, `temp_c` (рядок-ключ: індекс, `.get`/`.pop`/`.setdefault`, ключ dict, `dict(к=)`,
    геттер з рядком-ключем, іменований аргумент) і параметри з цими іменами — поле градусів паспорта, сцени, дроту,
    протоколу й відповіді моделі;
  · таблиця відчуття → градуси: запис `"weather_feel": {код: число}` і її читачі (`ключ("weather_feel", …)`,
    `ТАБЛИЦЯ["weather_feel"]`);
  · поле панелі `<input type="number">` з «°C» у тому самому рядку розмітки (його `id`).
  Куди тече (до нерухомої точки, через усі модулі): присвоєння — псевдонім за присвоєнням, що досягає точки (останнє
  перед нею в області), а не за ім'ям у функції (`_т` у `brief.бриф` — два значення); обгортки числа (`float`, `int`,
  `round`, `abs`, `min`, `max`, `next`), `or`/`and`, умовний вираз, `+`/`−` (різниця з межею — відстань у °C),
  форматування в текст (`"%+.0f °C" % т`, f-рядок, `+` з рядком); повернення функції продукту з єдиним ім'ям (усі
  повернення — градуси чи порожнє); аргумент → параметр (усі виклики, що його дають, — градуси); ключ запису й атрибут
  (усі записи ключа — градуси); глобальне ім'я модуля й імпорт (`from m import X`, `import m as M` → `M.X`);
  прапорець, що пишуть поруч із градусами в одному присвоєнні (`п["темп_c"], п["темп_з_відчуття"] = _т, True`).
  Множення й ділення дають іншу величину (частку, силу): рядок — місце, далі значення не тече.
  Пороги (п.3): інший бік порівняння з градусами розгортається назад — літерал, глобальне ім'я, імпорт, запис
  реєстру (`РЕЄСТР["к"]["val"]`, `C["к"]`), локальне присвоєння, змінна циклу чи генератора (таблиця смуг, яку
  обходять: `for lo, hi, d in ТЕМП_МАПА`), параметр (аргументи всіх викликів), — і кожен рядок визначення, до якого
  дійшло, — місце; так само операнд-ім'я `+`/`−`/`*`/`/` з градусами (допуск, масштаб, межа частки).
  JS і HTML — свій лексер (коментарі — не місця): токен-ключ градусів чи `id` поля градусів, рядок показу з «°C»,
  локальне ім'я, якому присвоєно вираз із градусами (`const т = parseFloat($('сц-темп').value)`), у його сегменті.

ЩО НЕ МІСЦЕ: коментарі й докстрінги; слово відчуття (`погода_відчуття`, `weather_feel`), що йде як є, без таблиці
чисел; смуги речі (тканина, ноги, шар), коли їх не порівнюють з градусами нагоди; колірна температура
(`пояснення.температура`), відтінок, `temperature` виклику моделі, тривалість; ключ, який пишуть і градусами, і
іншими значеннями (`вимір`, `значення` знахідки), — місце лише запис градусів у нього, не кожне читання.

Вивід детермінований: перелік `файл:рядок · п.N[,M] · доказ`, підсумки за пунктами й файлами, функції-читачі, пороги
й рішення п.5, останній рядок `місць: <N>` (N — різних `файл:рядок`), код 0. Запуск з кореня репозиторію
(чи `--корінь <шлях>`):
    python3 джерела/прилади/корінь_е2_смуга_погоди.py [--тихо] [--імена] [--читачі] [--самоперевірка]
"""
import ast
import os
import re
import shutil
import sys
import tempfile
import warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

# ── межі обходу (як `корінь_е2_частина_дня.py`) ─────────────────────────────────────────────────────────────────
ПОЗА_ТЕКИ = {"проби", "прилади", "node_modules", "__pycache__"}
ТЕСТ = re.compile(r"^(тест|test|стенд|батарея|gate_|pair_test|проба)|(_test|_тест)\.|\.test\.", re.IGNORECASE)
РОЗШИРЕННЯ = (".py", ".js", ".mjs", ".html")

# ── зерна значення ──────────────────────────────────────────────────────────────────────────────────────────────
КЛЮЧІ_ЗЕРНА = ("темп_c", "temperature_c", "temp_c")
ВІДЧУТТЯ = "weather_feel"
# Імена без змісту: значення будь-якого поля, тож градусів не несуть як ключ чи параметр, виведений потоком.
ЗАГАЛЬНІ = {
    "value", "val", "значення", "quote", "уривок", "key", "ключ", "поле", "field", "type", "тип", "data", "дані",
    "name", "ім", "імя", "id", "ід", "текст", "text", "джерело", "source", "код", "code", "вихід", "result",
    "items", "item", "row", "рядок", "запис", "default", "типове", "мітка", "label", "self", "cls", "args", "kwargs",
    "kw", "вимір", "поріг", "сила", "сила_нп", "x", "y", "v", "a", "b", "n", "т", "д", "в", "п", "с", "з", "к",
    "о", "р", "і", "ч", "м", "л", "у", "е", "а", "б", "н", "ф", "г", "ш", "щ", "ж", "х", "ц", "й", "ю", "я", "є",
    "ї", "lo", "hi", "low", "high", "min", "max", "низ", "верх", "межа", "число", "num", "number", "amount",
}
ОБГОРТКИ = {"int", "float", "round", "abs", "min", "max", "next", "str", "sorted", "list", "tuple"}
ПОРЯДОК = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)
РІВНІСТЬ = (ast.Eq, ast.NotEq)
ГРАДУС_ТЕКСТ = re.compile(r"°\s?C")


def рядок_константи(в):
    """Значення str-константи чи None."""
    return в.value if isinstance(в, ast.Constant) and isinstance(в.value, str) else None


def число_константи(в):
    """Значення числової константи (не bool), зокрема `-N`, чи None."""
    if isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool):
        return float(в.value)
    if isinstance(в, ast.UnaryOp) and isinstance(в.op, (ast.USub, ast.UAdd)) and число_константи(в.operand) is not None:
        return -число_константи(в.operand) if isinstance(в.op, ast.USub) else число_константи(в.operand)
    return None


def значуще(ім):
    """Ім'я, що може нести градуси як ключ, атрибут чи параметр, виведений потоком."""
    return isinstance(ім, str) and len(ім) > 2 and ім not in ЗАГАЛЬНІ


def порожнє(в):
    """Константа без значення (None, "", False) — не інше значення."""
    return isinstance(в, ast.Constant) and в.value in (None, "", False)


# ── Python ──────────────────────────────────────────────────────────────────────────────────────────────────────
ОБЛАСТІ = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)
КОМПРЕГЕНСІЇ = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


class Пі:
    """Модуль Python: дерево, батьки, області, присвоєння за областю й рядком, імпорти, глобальні визначення."""

    def __init__(self, шлях, текст):
        self.шлях = шлях
        self.ім_модуля = os.path.splitext(os.path.basename(шлях))[0]
        self.рядки = текст.splitlines()
        self.дерево = ast.parse(текст)
        self.батько, self.обл = {}, {}
        self.докстрінги = set()
        self.вузли = []
        стек = [(self.дерево, None)]
        while стек:
            в, обл = стек.pop()
            self.обл[id(в)] = обл
            self.вузли.append(в)
            if isinstance(в, ast.Expr) and рядок_константи(в.value) is not None:
                self.докстрінги.add(id(в.value))
            нова = в if isinstance(в, ОБЛАСТІ) else обл
            for д in ast.iter_child_nodes(в):
                self.батько[id(д)] = в
                стек.append((д, обл if (isinstance(в, ОБЛАСТІ) and isinstance(д, ast.arguments)) else нова))
        self.вузли.sort(key=lambda в: (getattr(в, "lineno", 0), getattr(в, "col_offset", 0)))
        self.параметри = {}
        self.функції = []
        for в in self.вузли:
            if isinstance(в, ОБЛАСТІ):
                а = в.args
                self.параметри[id(в)] = [п.arg for п in (а.posonlyargs + а.args + а.kwonlyargs)] + \
                    [п.arg for п in (а.vararg, а.kwarg) if п]
                if not isinstance(в, ast.Lambda):
                    self.функції.append(в)
        # присвоєння: (ід області, ім'я) → [(вузол-оператор, значення | None, вид)], вид — «знач» чи «цикл» (ітерація:
        # значення — ітерований вираз) чи «інше» (+=, with, except)
        self.присвоєння = {}
        глобальні_в = {}
        for в in self.вузли:
            обл = self.обл[id(в)]
            к = id(обл) if обл is not None else None
            if isinstance(в, (ast.Global, ast.Nonlocal)):
                глобальні_в.setdefault(к, set()).update(в.names)
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None:
                for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                    if isinstance(ц, ast.Name):
                        self.присвоєння.setdefault((к, ц.id), []).append((в, в.value, "знач"))
                    elif isinstance(ц, (ast.Tuple, ast.List)):
                        if isinstance(в.value, (ast.Tuple, ast.List)) and len(в.value.elts) == len(ц.elts):
                            for е, з in zip(ц.elts, в.value.elts):
                                if isinstance(е, ast.Name):
                                    self.присвоєння.setdefault((к, е.id), []).append((в, з, "знач"))
                        else:
                            for е in ц.elts:
                                for н in ast.walk(е):
                                    if isinstance(н, ast.Name):
                                        self.присвоєння.setdefault((к, н.id), []).append((в, в.value, "розпак"))
            elif isinstance(в, (ast.For, ast.AsyncFor)):
                for н in ast.walk(в.target):
                    if isinstance(н, ast.Name):
                        self.присвоєння.setdefault((к, н.id), []).append((в, в.iter, "цикл"))
            elif isinstance(в, ast.comprehension):
                for н in ast.walk(в.target):
                    if isinstance(н, ast.Name):
                        self.присвоєння.setdefault((к, н.id), []).append((self.батько[id(в)], в.iter, "ген"))
            elif isinstance(в, ast.NamedExpr):
                self.присвоєння.setdefault((к, в.target.id), []).append((в, в.value, "знач"))
            elif isinstance(в, (ast.AugAssign, ast.withitem, ast.ExceptHandler)):
                ціль = getattr(в, "target", None) or getattr(в, "optional_vars", None)
                оп = self.батько[id(в)] if isinstance(в, ast.withitem) else в
                if isinstance(в, ast.ExceptHandler) and в.name:
                    self.присвоєння.setdefault((к, в.name), []).append((оп, None, "інше"))
                for н in (ast.walk(ціль) if ціль is not None else ()):
                    if isinstance(н, ast.Name):
                        self.присвоєння.setdefault((к, н.id), []).append((оп, None, "інше"))
        self.глобальні_в = глобальні_в
        # імпорти: ім'я → (модуль, ім'я | None)
        self.імпорти = {}
        for в in self.дерево.body:
            for і in ([в] if isinstance(в, (ast.Import, ast.ImportFrom)) else []):
                if isinstance(і, ast.Import):
                    for а in і.names:
                        self.імпорти[а.asname or а.name.split(".")[0]] = (а.name.split(".")[-1], None)
                elif і.module:
                    for а in і.names:
                        self.імпорти[а.asname or а.name] = (і.module.split(".")[-1], а.name)
        # усі імпорти будь-де (у функціях теж): ім'я → (модуль, ім'я | None)
        for в in self.вузли:
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.імпорти.setdefault(а.asname or а.name.split(".")[0], (а.name.split(".")[-1], None))
            elif isinstance(в, ast.ImportFrom) and в.module:
                for а in в.names:
                    self.імпорти.setdefault(а.asname or а.name, (в.module.split(".")[-1], а.name))
        # `_М = importlib.import_module("м")` — теж модуль
        for в in self.вузли:
            if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name) \
                    and isinstance(в.value, ast.Call) and в.value.args and рядок_константи(в.value.args[0]) \
                    and isinstance(в.value.func, ast.Attribute) and в.value.func.attr == "import_module":
                self.імпорти.setdefault(в.targets[0].id, (рядок_константи(в.value.args[0]).split(".")[-1], None))
        self.за_видом = {}
        for в in self.вузли:
            self.за_видом.setdefault(type(в).__name__, []).append(в)

    def вид(self, *імена):
        for ім in імена:
            yield from self.за_видом.get(ім, ())

    def область(self, в):
        """Найближча функція чи лямбда (None — модуль)."""
        return self.обл.get(id(в))

    def локальне(self, обл, ім):
        """Чи ім'я локальне в області (параметр чи присвоєння без `global`)."""
        if обл is None:
            return False
        if ім in self.глобальні_в.get(id(обл), ()):
            return False
        return ім in self.параметри.get(id(обл), ()) or (id(обл), ім) in self.присвоєння

    def усередині(self, в, предок):
        """Чи вузол `в` — нащадок `предок`."""
        б = в
        while б is not None:
            if б is предок:
                return True
            б = self.батько.get(id(б))
        return False

    def досяжне(self, обл, ім, в):
        """Присвоєння, що досягає точки `в`: останнє в області, що скінчилось до неї (не те, у чиє значення
        вона входить); None — нема (тоді — параметр чи глобальне)."""
        к = id(обл) if обл is not None else None
        кращий = None
        for оп, знач, вид in self.присвоєння.get((к, ім), ()):
            if вид == "ген":
                if self.усередині(в, оп) and not self.усередині(в, знач):
                    return (оп, знач, "цикл")     # змінна генератора всередині нього самого
                continue                         # поза ним не живе
            if self.усередині(в, оп):
                if вид == "цикл" and not self.усередині(в, оп.iter):
                    return (оп, знач, вид)        # тіло циклу
                continue
            if (getattr(оп, "end_lineno", оп.lineno), getattr(оп, "end_col_offset", 0)) <= (в.lineno, в.col_offset):
                if кращий is None or (оп.lineno, оп.col_offset) >= (кращий[0].lineno, кращий[0].col_offset):
                    кращий = (оп, знач, вид)
        return кращий

    def функція_вузла(self, в):
        """FunctionDef, що містить вузол (без лямбд), чи None."""
        б = self.батько.get(id(в))
        while б is not None and not isinstance(б, (ast.FunctionDef, ast.AsyncFunctionDef)):
            б = self.батько.get(id(б))
        return б

    def рядки_токена(self, вузол, токен):
        """Рядки коду, у яких рядкова константа `вузол` несе токен (неявна склейка — кілька рядків)."""
        вих = []
        for н in range(вузол.lineno, (вузол.end_lineno or вузол.lineno) + 1):
            if 0 < н <= len(self.рядки) and токен in self.рядки[н - 1]:
                вих.append(н)
        return вих or [вузол.lineno]


class Стан:
    """Що прилад вивів: ключі, атрибути, функції, параметри, глобальні імена, прапорці; звідки кожне."""

    def __init__(self):
        self.К = set(КЛЮЧІ_ЗЕРНА)    # ключі записів і атрибути, що несуть градуси
        self.Ф = {}                  # функція продукту (ім'я) → вид повернення
        self.П = {}                  # (модуль, ід функції) → {параметр: вид}
        self.Г = {}                  # (модуль, глобальне ім'я) → вид
        self.ПР = set()              # прапорці походження градусів
        self.ГЕТ = set()             # геттери поля за назвою
        self.ПОРІГ = set()           # (модуль, глобальне ім'я) — поріг градусів нагоди чи таблиця смуг з ним
        self.ІД = {}                 # `id` поля градусів панелі → де
        self.звідки = {}
        self.змінено = True

    def додати(self, словник, ключ, вид, звідки):
        if isinstance(словник, set):
            if ключ in словник:
                return
            словник.add(ключ)
        else:
            if ключ in словник:
                return
            словник[ключ] = вид
        self.звідки.setdefault(ключ if isinstance(ключ, str) else "%s:%s" % (ключ[0], ключ[1]), звідки)
        self.змінено = True


class АналізПі:
    """Вивід носіїв градусів і пошук місць у Python."""

    def __init__(self, модулі, стан):
        self.модулі = модулі
        self.за_іменем = {м.ім_модуля: м for м in модулі}
        self.с = стан
        self.визначення = {}
        for м in модулі:
            for ф in м.функції:
                self.визначення.setdefault(ф.name, []).append((м, ф))
        for м in модулі:
            for ф in м.функції:
                пар = [а.arg for а in ф.args.args]
                if len(пар) == 1 and any(
                        (isinstance(х, ast.Subscript) and isinstance(х.slice, ast.Name) and х.slice.id == пар[0])
                        or (isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr == "get"
                            and х.args and isinstance(х.args[0], ast.Name) and х.args[0].id == пар[0])
                        for х in ast.walk(ф)):
                    self.с.ГЕТ.add(ф.name)

    # ── розв'язання імен ──
    def єдина(self, ім):
        """(модуль, FunctionDef) функції продукту з єдиним ім'ям чи None."""
        в = self.визначення.get(ім, ())
        return в[0] if len(в) == 1 else None

    def глобальне(self, м, ім, глибина=0):
        """(модуль, ім'я) глобального імені `ім` модуля `м` з урахуванням імпорту; None — не знайдено."""
        if глибина > 6:
            return None
        if (None, ім) in м.присвоєння:
            return (м, ім)
        if ім in м.імпорти:
            мод, назва = м.імпорти[ім]
            ціль = self.за_іменем.get(мод)
            if ціль is not None and назва is not None:
                return self.глобальне(ціль, назва, глибина + 1)
        return None

    def модуль_імені(self, м, ім):
        """Модуль продукту, на який вказує ім'я (`import m as M`), чи None."""
        if ім in м.імпорти and м.імпорти[ім][1] is None:
            return self.за_іменем.get(м.імпорти[ім][0])
        if ім in м.імпорти:
            мод, назва = м.імпорти[ім]
            return self.за_іменем.get(назва) if назва in self.за_іменем and мод not in self.за_іменем else None
        return None

    def ключі_ланцюга(self, в):
        """Str-ключі ланцюга підписок і `.get("к")`."""
        ключі = []
        while True:
            if isinstance(в, ast.Subscript):
                р = рядок_константи(в.slice)
                if р is not None:
                    ключі.append(р)
                в = в.value
            elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and \
                    в.func.attr in ("get", "pop", "setdefault") and в.args and рядок_константи(в.args[0]) is not None:
                ключі.append(рядок_константи(в.args[0]))
                в = в.func.value
            else:
                return ключі

    @staticmethod
    def ім_виклику(в):
        if isinstance(в.func, ast.Name):
            return в.func.id
        if isinstance(в.func, ast.Attribute):
            return в.func.attr
        return None

    def таблиця_відчуття(self, в):
        """Чи вираз — таблиця відчуття → градуси (`ТАБЛИЦЯ["weather_feel"]`)."""
        return isinstance(в, ast.Subscript) and рядок_константи(в.slice) == ВІДЧУТТЯ

    # ── вид значення: «т» градуси, «д» різниця з межею (°C), «р» текст із градусами; None — не градуси ──
    def вид(self, м, в):
        if в is None:
            return None
        if isinstance(в, ast.Name):
            return self.вид_імені(м, в)
        if isinstance(в, ast.Attribute):
            мод = self.модуль_імені(м, в.value.id) if isinstance(в.value, ast.Name) else None
            if мод is not None:
                return self.с.Г.get((мод.шлях, в.attr))
            return "т" if (в.attr in self.с.К and значуще(в.attr)) else None
        if isinstance(в, (ast.Subscript,)) or (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                                                and в.func.attr in ("get", "pop", "setdefault")):
            ключі = self.ключі_ланцюга(в)
            if ключі and ключі[-1] in self.с.К:
                return "т"
            if isinstance(в, ast.Subscript) and self.таблиця_відчуття(в.value):
                return "т"
            if isinstance(в, ast.Call) and self.таблиця_відчуття(в.func.value):
                return "т"
            if isinstance(в, ast.Subscript) and not ключі:
                return None
            return None
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if ім == "ключ" and в.args and рядок_константи(в.args[0]) == ВІДЧУТТЯ:
                return "т"
            if ім in ОБГОРТКИ and isinstance(в.func, ast.Name):
                for а in в.args:
                    if isinstance(а, (ast.GeneratorExp, ast.ListComp)):
                        к = self.вид(м, а.elt)
                    else:
                        к = self.вид(м, а)
                    if к:
                        return "р" if ім == "str" else к
                return None
            if ім in self.с.Ф:
                return self.с.Ф[ім]
            if ім in self.с.ГЕТ and len(в.args) == 1 and рядок_константи(в.args[0]) in self.с.К:
                return "т"
            if isinstance(в.func, ast.Attribute) and ім == "format" and рядок_константи(в.func.value) is not None:
                if any(self.вид(м, а) for а in list(в.args) + [к.value for к in в.keywords]):
                    return "р"
            return None
        if isinstance(в, ast.BinOp):
            л, п = self.вид(м, в.left), self.вид(м, в.right)
            if isinstance(в.op, ast.Mod) and рядок_константи(в.left) is not None:
                права = в.right.elts if isinstance(в.right, ast.Tuple) else [в.right]
                return "р" if any(self.вид(м, е) for е in права) else None
            if isinstance(в.op, ast.Add) and (рядок_константи(в.left) is not None or рядок_константи(в.right) is not None
                                             or "р" in (л, п)):
                return "р" if (л or п) else None
            if isinstance(в.op, ast.Sub):
                if л and п:
                    return "д"
                if л or п:
                    інший = в.right if л else в.left
                    return (л or п) if число_константи(інший) == 0 else "д"
                return None
            if isinstance(в.op, ast.Add):
                return л or п
            return None
        if isinstance(в, ast.UnaryOp) and isinstance(в.op, (ast.USub, ast.UAdd)):
            return self.вид(м, в.operand)
        if isinstance(в, ast.BoolOp):
            for з in в.values:
                к = self.вид(м, з)
                if к:
                    return к
            return None
        if isinstance(в, ast.IfExp):
            return self.вид(м, в.body) or self.вид(м, в.orelse)
        if isinstance(в, ast.JoinedStr):
            for з in в.values:
                if isinstance(з, ast.FormattedValue) and self.вид(м, з.value):
                    return "р"
            return None
        if isinstance(в, ast.NamedExpr):
            return self.вид(м, в.value)
        return None

    def вид_імені(self, м, в):
        обл = м.область(в)
        if м.локальне(обл, в.id):
            д = м.досяжне(обл, в.id, в)
            if д is None:
                return self.вид_параметра(м, обл, в.id)
            оп, знач, вид = д
            if вид == "знач":
                if знач is в or (знач is not None and м.усередині(в, знач)):
                    return None
                return self.вид(м, знач)
            if вид == "цикл" and isinstance(знач, (ast.List, ast.Tuple)) and знач.elts and \
                    all(self.вид(м, е) for е in знач.elts):
                return self.вид(м, знач.elts[0])
            return None
        г = self.глобальне(м, в.id)
        if г is not None:
            return self.с.Г.get((г[0].шлях, г[1]))
        return None

    def вид_параметра(self, м, обл, ім):
        if обл is None or ім not in м.параметри.get(id(обл), ()):
            return None
        if ім in КЛЮЧІ_ЗЕРНА:
            return "т"
        return self.с.П.get((м.шлях, id(обл)), {}).get(ім)

    # ── один прохід виводу ──
    def прохід(self, м):
        с = self.с
        де = lambda в: "%s:%d" % (м.шлях, в.lineno)
        # глобальні імена модуля
        for (к, ім), записи in м.присвоєння.items():
            if к is not None:
                continue
            види = [self.вид(м, з) for _, з, вид in записи if вид == "знач"]
            if any(види) and all(к_ or порожнє(з) for к_, (_, з, _) in zip(види, [з for з in записи if з[2] == "знач"])):
                с.додати(с.Г, (м.шлях, ім), next(к_ for к_ in види if к_), "%s:%d · глобальне ім'я" % (
                    м.шлях, записи[0][0].lineno))
        # повернення функцій
        for ф in м.функції:
            if self.єдина(ф.name) is None or ф.name in с.Ф:
                continue
            повернення = [в for в in ast.walk(ф) if isinstance(в, ast.Return) and м.функція_вузла(в) is ф
                          and м.область(в) is ф]
            значущі = [в.value for в in повернення if в.value is not None and not порожнє(в.value)]
            види = [self.вид(м, з) for з in значущі]
            if види and all(види):
                с.додати(с.Ф, ф.name, види[0], "%s:%d · повертає градуси" % (м.шлях, ф.lineno))
        # прапорці: присвоєння кортежем, де поруч із градусами — bool
        for в in м.вид("Assign"):
            for ц in в.targets:
                if isinstance(ц, ast.Tuple) and isinstance(в.value, ast.Tuple) and len(ц.elts) == len(в.value.elts) \
                        and any(self.вид(м, з) for з in в.value.elts):
                    for ціль, знач in zip(ц.elts, в.value.elts):
                        if isinstance(знач, ast.Constant) and isinstance(знач.value, bool) \
                                and isinstance(ціль, ast.Subscript) and значуще(рядок_константи(ціль.slice)):
                            с.додати(с.ПР, рядок_константи(ціль.slice), "прапорець", де(в) + " · прапорець походження")
        # аргументи → параметри
        for в in м.вид("Call"):
            ім = self.ім_виклику(в)
            ціль = self.єдина(ім) if ім else None
            if ціль is None:
                continue
            цм, цф = ціль
            пар = [а.arg for а in (цф.args.posonlyargs + цф.args.args)]
            if isinstance(в.func, ast.Attribute) and пар and пар[0] in ("self", "cls") and \
                    self.модуль_імені(м, в.func.value.id if isinstance(в.func.value, ast.Name) else "") is None:
                пар = пар[1:]
            пари = list(zip(пар, в.args)) if not any(isinstance(а, ast.Starred) for а in в.args) else []
            пари += [(к.arg, к.value) for к in в.keywords if к.arg]
            for п, а in пари:
                к_ = self.вид(м, а)
                if к_ and значуще(п) and п not in с.П.get((цм.шлях, id(цф)), {}):
                    if self.усі_виклики(цм, цф, п):
                        с.П.setdefault((цм.шлях, id(цф)), {})[п] = к_
                        с.звідки.setdefault("%s:%s(%s)" % (цм.шлях, цф.name, п), де(в) + " · аргумент")
                        с.змінено = True
        # ключі записів і атрибути: усі записи ключа — градуси
        for ключ, з in self.записи_ключів(м):
            if ключ in с.К or not значуще(ключ):
                continue
            к_ = self.вид(м, з)
            if к_ in ("т", "д") and self.усі_записи(ключ):
                с.додати(с.К, ключ, к_, "%s:%d · ключ запису" % (м.шлях, з.lineno))

    def записи_ключів(self, м):
        """(ключ, значення) кожного запису ключа в модулі: dict-літерал, `x["к"] = з`, `dict(к=з)`, `.update`,
        `.setdefault`, `x.атрибут = з`."""
        for в in м.вид("Dict"):
            for к, з in zip(в.keys, в.values):
                if к is not None and рядок_константи(к):
                    yield рядок_константи(к), з
        for в in м.вид("Assign"):
            for ц in в.targets:
                пари = zip(ц.elts, в.value.elts) if isinstance(ц, ast.Tuple) and isinstance(в.value, ast.Tuple) \
                    and len(ц.elts) == len(в.value.elts) else [(ц, в.value)]
                for ціль, знач in пари:
                    if isinstance(ціль, ast.Subscript) and рядок_константи(ціль.slice):
                        yield рядок_константи(ціль.slice), знач
                    elif isinstance(ціль, ast.Attribute):
                        yield ціль.attr, знач
        for в in м.вид("Call"):
            ім = self.ім_виклику(в)
            if ім in ("dict", "update"):
                for к in в.keywords:
                    if к.arg:
                        yield к.arg, к.value
            if ім == "setdefault" and len(в.args) > 1 and рядок_константи(в.args[0]):
                yield рядок_константи(в.args[0]), в.args[1]

    def усі_записи(self, ключ):
        """Чи кожен запис ключа в усьому коді — градуси (чи порожнє)."""
        for м in self.модулі:
            for к, з in self.записи_ключів(м):
                if к == ключ and not (порожнє(з) or self.вид(м, з) in ("т", "д")):
                    return False
        return True

    def усі_виклики(self, цм, цф, п):
        """Чи кожен виклик функції, що дає параметр `п`, дає градуси (чи порожнє)."""
        пар = [а.arg for а in (цф.args.posonlyargs + цф.args.args)]
        for м in self.модулі:
            for в in м.вид("Call"):
                if self.ім_виклику(в) != цф.name:
                    continue
                пп = пар
                if isinstance(в.func, ast.Attribute) and пп and пп[0] in ("self", "cls") and \
                        self.модуль_імені(м, в.func.value.id if isinstance(в.func.value, ast.Name) else "") is None:
                    пп = пп[1:]
                if any(isinstance(а, ast.Starred) for а in в.args) or any(к.arg is None for к in в.keywords):
                    continue
                дано = dict(zip(пп, в.args))
                дано.update({к.arg: к.value for к in в.keywords})
                if п in дано and not (порожнє(дано[п]) or self.вид(м, дано[п])):
                    return False
        return True

    # ── пороги: інший бік порівняння й операнди арифметики, розгорнуті назад до визначень ──
    def пороги(self, м, в, додати, причина, глибина=0, бачено=None):
        """Розгортає вираз-поріг до визначень; кожен рядок визначення — місце п.3. → множина значень (числа)."""
        бачено = set() if бачено is None else бачено
        знач = set()
        if в is None or глибина > 8 or (м.шлях, id(в)) in бачено:
            return знач
        бачено.add((м.шлях, id(в)))
        ч = число_константи(в)
        if ч is not None:
            знач.add(ч)
            return знач
        if isinstance(в, ast.Name):
            обл = м.область(в)
            if м.локальне(обл, в.id):
                д = м.досяжне(обл, в.id, в)
                if д is None:
                    знач |= self.пороги_параметра(м, обл, в.id, додати, причина, глибина, бачено)
                else:
                    оп, з, вид = д
                    if вид == "цикл":
                        знач |= self.таблиця_смуг(м, з, додати, причина, глибина, бачено)
                    elif з is not None:
                        підзнач = self.пороги(м, з, додати, причина, глибина + 1, бачено)
                        if підзнач and число_константи(з) is None:
                            додати(м.шлях, оп.lineno, 3, "%s: поріг у локальному «%s»" % (причина, в.id))
                        знач |= підзнач
                return знач
            г = self.глобальне(м, в.id)
            if г is not None:
                return self.визначення_глобального(г[0], г[1], додати, причина, глибина, бачено)
            return знач
        if isinstance(в, ast.Attribute):
            мод = self.модуль_імені(м, в.value.id) if isinstance(в.value, ast.Name) else None
            if мод is not None:
                return self.визначення_глобального(мод, в.attr, додати, причина, глибина, бачено)
            return знач
        if isinstance(в, ast.Subscript):
            ключі = self.ключі_ланцюга(в)
            корінь = в
            while isinstance(корінь, ast.Subscript):
                корінь = корінь.value
            запис = self.запис_реєстру(м, корінь, ключі)
            if запис is not None:
                зм, зв = запис
                рег = self.реєстр_запису(зм, зв)
                if рег:
                    self.с.ПОРІГ.add((зм.шлях, рег, ключі[-1]))
                додати(зм.шлях, зв.lineno, 3, "%s: поріг реєстру «%s»" % (причина, "/".join(reversed(ключі))))
                for н in ast.walk(зв):
                    if isinstance(н, ast.keyword) and н.arg == "val":
                        знач |= self.пороги(зм, н.value, додати, причина, глибина + 1, бачено)
                    elif isinstance(н, (ast.Name, ast.Attribute)) and глибина < 4 and not isinstance(зв, ast.Dict):
                        pass
                if isinstance(зв, ast.Dict) or not any(isinstance(н, ast.keyword) and н.arg == "val"
                                                       for н in ast.walk(зв)):
                    знач |= self.пороги(зм, зв, додати, причина, глибина + 1, бачено)
                return знач
            # елемент таблиці смуг: `своя[0]`, `смуга[1]`
            if isinstance(корінь, ast.Name):
                знач |= self.пороги(м, корінь, додати, причина, глибина + 1, бачено)
            return знач
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if ім in ОБГОРТКИ or ім in ("items", "values", "keys", "get"):
                for а in в.args:
                    if isinstance(а, КОМПРЕГЕНСІЇ):
                        for г in а.generators:
                            знач |= self.таблиця_смуг(м, г.iter, додати, причина, глибина, бачено)
                    else:
                        знач |= self.пороги(м, а, додати, причина, глибина + 1, бачено)
                if isinstance(в.func, ast.Attribute) and ім in ("items", "values", "keys", "get"):
                    знач |= self.таблиця_смуг(м, в.func.value, додати, причина, глибина, бачено)
            return знач
        if isinstance(в, ast.BinOp):
            return self.пороги(м, в.left, додати, причина, глибина + 1, бачено) | \
                self.пороги(м, в.right, додати, причина, глибина + 1, бачено)
        if isinstance(в, (ast.Tuple, ast.List)):
            for е in в.elts:
                знач |= self.пороги(м, е, додати, причина, глибина + 1, бачено)
        return знач

    def запис_реєстру(self, м, корінь, ключі):
        """Вузол запису `"к": …` реєстру-літерала за ланцюгом ключів (`РЕЄСТР["к"]["val"]`, `C["к"]`)."""
        if not ключі:
            return None
        if isinstance(корінь, ast.Name):
            г = self.глобальне(м, корінь.id)
        elif isinstance(корінь, ast.Attribute) and isinstance(корінь.value, ast.Name):
            мод = self.модуль_імені(м, корінь.value.id)
            г = (мод, корінь.attr) if мод is not None and (None, корінь.attr) in мод.присвоєння else None
        else:
            г = None
        if г is None:
            return None
        зм, ім = г
        перший = ключі[-1]
        for оп, з, вид in зм.присвоєння.get((None, ім), ()):
            if isinstance(з, ast.Dict):
                for к, зн in zip(з.keys, з.values):
                    if к is not None and рядок_константи(к) == перший:
                        return зм, зн
            if isinstance(з, ast.DictComp):
                к_ = з.value
                while isinstance(к_, ast.Subscript) and not (isinstance(к_.value, ast.Name)
                                                            and (None, к_.value.id) in зм.присвоєння):
                    к_ = к_.value
                if isinstance(к_, ast.Subscript) and isinstance(к_.value, ast.Name) and к_.value.id != ім:
                    return self.запис_реєстру(зм, к_.value, [перший])
        # реєстр, наповнений `C["к"] = …` чи `РЕЄСТР.update(к=…)`
        for в in зм.вид("Assign"):
            for ц in в.targets:
                if isinstance(ц, ast.Subscript) and рядок_константи(ц.slice) == перший and \
                        isinstance(ц.value, ast.Name) and ц.value.id == ім:
                    return зм, в.value
        for в in зм.вид("Call"):
            if isinstance(в.func, ast.Name) and в.func.id == "dict" and isinstance(зм.батько.get(id(в)), ast.Assign):
                ціль = зм.батько[id(в)].targets[0]
                if isinstance(ціль, ast.Name) and ціль.id == ім:
                    for к in в.keywords:
                        if к.arg == перший:
                            return зм, к.value
        return None

    @staticmethod
    def реєстр_запису(зм, зв):
        """Ім'я глобального реєстру, у літералі якого стоїть запис `зв`."""
        б = зм.батько.get(id(зв))
        while б is not None and not isinstance(б, (ast.Assign, ast.Module)):
            б = зм.батько.get(id(б))
        if isinstance(б, ast.Assign) and isinstance(б.targets[0], ast.Name):
            return б.targets[0].id
        return None

    def визначення_глобального(self, зм, ім, додати, причина, глибина, бачено):
        """Рядок визначення глобального порогу й далі — його джерело."""
        знач = set()
        self.с.ПОРІГ.add((зм.шлях, ім))
        for оп, з, вид in зм.присвоєння.get((None, ім), ()):
            if вид != "знач" or з is None:
                continue
            if isinstance(з, (ast.Dict, ast.List, ast.Tuple)) and len(getattr(з, "elts", getattr(з, "keys", ()))) > 2:
                знач |= self.таблиця_смуг(зм, з, додати, причина, глибина, бачено)
                continue
            додати(зм.шлях, оп.lineno, 3, "%s: поріг «%s»" % (причина, ім))
            знач |= self.пороги(зм, з, додати, причина, глибина + 1, бачено)
        return знач

    def таблиця_смуг(self, м, в, додати, причина, глибина, бачено):
        """Таблиця смуг, яку обходять при порівнянні з градусами нагоди: кожен рядок літерала з межею (число чи
        поріг-ім'я в кортежі межі) — місце; межі-імена — далі до визначень. → значення меж."""
        знач = set()
        self._таблиця(м, в, додати, причина, глибина, бачено, знач)
        return знач

    def _таблиця(self, м, в, додати, причина, глибина, бачено, знач):
        if в is None or глибина > 8:
            return
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if isinstance(в.func, ast.Attribute) and ім in ("items", "values", "keys"):
                self._таблиця(м, в.func.value, додати, причина, глибина + 1, бачено, знач)
            elif ім in ОБГОРТКИ or ім in ("zip", "enumerate", "reversed"):
                for а in в.args:
                    self._таблиця(м, а, додати, причина, глибина + 1, бачено, знач)
            return
        if isinstance(в, (ast.Name, ast.Attribute)):
            if isinstance(в, ast.Name):
                обл = м.область(в)
                if м.локальне(обл, в.id):
                    д = м.досяжне(обл, в.id, в)
                    if д is not None and д[1] is not None:
                        if isinstance(д[1], КОМПРЕГЕНСІЇ):
                            for г in д[1].generators:
                                self._таблиця(м, г.iter, додати, причина, глибина + 1, бачено, знач)
                        else:
                            self._таблиця(м, д[1], додати, причина, глибина + 1, бачено, знач)
                    return
                г = self.глобальне(м, в.id)
            else:
                мод = self.модуль_імені(м, в.value.id) if isinstance(в.value, ast.Name) else None
                г = (мод, в.attr) if мод is not None else None
            if г is None or (г[0].шлях, г[1]) in бачено:
                return
            бачено.add((г[0].шлях, г[1]))
            self.с.ПОРІГ.add((г[0].шлях, г[1]))
            for оп, з, вид in г[0].присвоєння.get((None, г[1]), ()):
                if вид == "знач" and з is not None:
                    if isinstance(з, (ast.Dict, ast.List, ast.Tuple, ast.ListComp, ast.DictComp)):
                        self._таблиця(г[0], з, додати, причина + " · таблиця «%s»" % г[1], глибина + 1, бачено, знач)
            return
        if isinstance(в, (ast.ListComp, ast.DictComp, ast.GeneratorExp)):
            for г in в.generators:
                self._таблиця(м, г.iter, додати, причина, глибина + 1, бачено, знач)
            return
        елементи = list(в.values) if isinstance(в, ast.Dict) else list(getattr(в, "elts", ()))
        for е in елементи:
            межі = е.elts[:2] if isinstance(е, ast.Tuple) else ([е] if число_константи(е) is not None else [])
            for мж in межі:
                if число_константи(мж) is not None or isinstance(мж, (ast.Name, ast.Attribute)):
                    додати(м.шлях, мж.lineno, 3, "%s: межа таблиці смуг" % причина)
                    if число_константи(мж) is not None:
                        знач.add(число_константи(мж))
                    else:
                        знач |= self.пороги(м, мж, додати, причина, глибина + 1, бачено)

    def пороги_параметра(self, м, обл, ім, додати, причина, глибина, бачено):
        """Поріг-параметр: аргументи всіх викликів функції."""
        знач = set()
        if обл is None or isinstance(обл, ast.Lambda) or self.єдина(обл.name) is None or глибина > 5:
            return знач
        пар = [а.arg for а in (обл.args.posonlyargs + обл.args.args)]
        for мм in self.модулі:
            for в in мм.вид("Call"):
                if self.ім_виклику(в) != обл.name:
                    continue
                пп = пар
                if isinstance(в.func, ast.Attribute) and пп and пп[0] in ("self", "cls"):
                    пп = пп[1:]
                дано = dict(zip(пп, в.args))
                дано.update({к.arg: к.value for к in в.keywords if к.arg})
                if ім in дано and not self.вид(мм, дано[ім]):
                    знач |= self.пороги(мм, дано[ім], додати, причина, глибина + 1, бачено)
        return знач

    def пороги_вперед(self, додати):
        """Визначення на рівні модуля, що беруть поріг градусів нагоди (`float(_ПОГОДА.МОРОЗ_ДО_C)` у реєстрі,
        межі `СЕЗОН_ТКАНИНИ`, `РЕЄСТР_ПОРИ`), — теж поріг градусів: рядок посилання — місце, ціль — поріг."""
        с = self.с
        змінено = True
        while змінено:
            змінено = False
            for м in self.модулі:
                for оп in м.дерево.body:
                    if not isinstance(оп, (ast.Assign, ast.AnnAssign)) or оп.value is None:
                        continue
                    цілі = [ц.id for ц in (оп.targets if isinstance(оп, ast.Assign) else [оп.target])
                            if isinstance(ц, ast.Name)]
                    if not цілі:
                        continue
                    з = оп.value
                    if isinstance(з, ast.Dict):
                        # реєстр: запис, чиє значення бере поріг, — поріг (запис, не весь реєстр)
                        for к, зн in zip(з.keys, з.values):
                            if рядок_константи(к) and self.посилання_порогу(м, зн, додати):
                                for ц in цілі:
                                    if (м.шлях, ц, рядок_константи(к)) not in с.ПОРІГ:
                                        с.ПОРІГ.add((м.шлях, ц, рядок_константи(к)))
                                        змінено = True
                        if з.values and all(self.посилання_порогу(м, зн, None) for зн in з.values) and \
                                all(isinstance(зн, (ast.Tuple, ast.List)) for зн in з.values):
                            for ц in цілі:
                                if (м.шлях, ц) not in с.ПОРІГ:
                                    с.ПОРІГ.add((м.шлях, ц))      # таблиця смуг: кожен запис — межі
                                    змінено = True
                        continue
                    if isinstance(з, ast.DictComp):
                        continue        # похідний реєстр (`C = {k: РЕЄСТР[k]["val"] …}`) — його записи вже пороги
                    if self.посилання_порогу(м, з, додати):
                        for ц in цілі:
                            if (м.шлях, ц) not in с.ПОРІГ:
                                с.ПОРІГ.add((м.шлях, ц))
                                змінено = True

    def посилання_порогу(self, м, вираз, додати):
        """Чи вираз рівня модуля бере поріг градусів (ім'я, атрибут модуля, запис реєстру); рядки — місця."""
        с = self.с
        знайдено = False
        for н in ast.walk(вираз):
            г = None
            if isinstance(н, ast.Name) and isinstance(н.ctx, ast.Load):
                г = self.глобальне(м, н.id)
            elif isinstance(н, ast.Attribute) and isinstance(н.value, ast.Name):
                мод = self.модуль_імені(м, н.value.id)
                г = (мод, н.attr) if мод is not None else None
            elif isinstance(н, ast.Subscript):
                ключі = self.ключі_ланцюга(н)
                корінь = н
                while isinstance(корінь, ast.Subscript):
                    корінь = корінь.value
                if ключі and isinstance(корінь, (ast.Name, ast.Attribute)):
                    if isinstance(корінь, ast.Name):
                        гг = self.глобальне(м, корінь.id)
                    else:
                        мод = self.модуль_імені(м, корінь.value.id) if isinstance(корінь.value, ast.Name) else None
                        гг = (мод, корінь.attr) if мод is not None else None
                    if гг is not None and (гг[0].шлях, гг[1], ключі[-1]) in с.ПОРІГ:
                        знайдено = True
                        if додати:
                            додати(м.шлях, н.lineno, 3, "межа з порогу реєстру «%s»" % ключі[-1])
                continue
            if г is not None and г[0] is not None and (г[0].шлях, г[1]) in с.ПОРІГ:
                знайдено = True
                if додати:
                    додати(м.шлях, н.lineno, 3, "межа з порогу градусів «%s»" % г[1])
        return знайдено

    # ── місця ──
    def місця(self, м, додати, рішення):
        с = self.с
        позначені = set()

        def місце(в, п, доказ):
            додати(м.шлях, в.lineno, п, доказ)

        for в in м.вузли:
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in м.докстрінги:
                р = в.value
                self.код_у_рядку(м, в, додати)
                if re.search(r"(?m)^\s*assert\b", р):
                    continue            # код гейта рядком (стенди `build_артефакт.py`) — тест
                if р in с.ІД:
                    місце(в, 4, "поле градусів панелі «%s»" % р)
                    continue
                if р in с.К:
                    б = м.батько.get(id(в))
                    if isinstance(б, ast.Dict):
                        for к, з in zip(б.keys, б.values):
                            if к is в and (isinstance(з, (ast.Dict, ast.JoinedStr, ast.Lambda))
                                           or " " in (рядок_константи(з) or "")):
                                for н in range(з.lineno, (з.end_lineno or з.lineno) + 1):
                                    рд = м.рядки[н - 1].strip() if н <= len(м.рядки) else ""
                                    if рд and not рд.startswith("#"):
                                        додати(м.шлях, н, 1, "опис чи специфікація поля градусів «%s»" % р)
                    місце(в, 2, "ключ градусів «%s»" % р)
                    continue
                if р in с.ПР:
                    місце(в, 2, "прапорець походження градусів «%s»" % р)
                    continue
                if р == ВІДЧУТТЯ and isinstance(м.батько.get(id(в)), ast.Dict):
                    д = м.батько[id(в)]
                    for к, з in zip(д.keys, д.values):
                        if к is в and isinstance(з, ast.Dict) and з.values and \
                                all(число_константи(х) is not None for х in з.values):
                            for н in range(з.lineno, (з.end_lineno or з.lineno) + 1):
                                додати(м.шлях, н, 3, "таблиця відчуття → градуси")
                for т in sorted(с.К | с.ПР):
                    if "_" in т and re.search(r"(?<![\w])%s(?![\w])" % re.escape(т), р):
                        проза = len(re.findall(r"\b[a-z]{3,}\b", р)) >= 3
                        кодове = re.search(r"\w\.%s\b" % re.escape(т), р) or " " not in р.strip()
                        if not проза and not кодове and len(re.findall(r"[а-яіїєґ]{3,}", р.lower())) > 3:
                            break       # українська примітка в даних (суть реєстру) — опис, не читання й не запит
                        for н in м.рядки_токена(в, т):
                            додати(м.шлях, н, 1 if проза else 2, "%s з полем градусів «%s»" % (
                                "текст моделі чи заяви" if проза else "текст коду", т))
                        break
            elif isinstance(в, (ast.Name, ast.Attribute, ast.Subscript, ast.Call, ast.JoinedStr, ast.BinOp)):
                if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store):
                    continue
                к = self.вид(м, в)
                if к and id(в) not in позначені:
                    місце(в, 2 if к != "р" else 4 if self.показ(м, в) else 2, "градуси (%s): %s" % (
                        {"т": "число", "д": "різниця °C", "р": "текст"}[к], ast.unparse(в)[:50]))
                    for н in ast.walk(в):
                        позначені.add(id(н))
            if (isinstance(в, ast.Call) and self.ім_виклику(в) == "ключ" and в.args
                    and рядок_константи(в.args[0]) == ВІДЧУТТЯ) or (
                    self.таблиця_відчуття(в) and isinstance(м.батько.get(id(в)), (ast.Subscript, ast.Attribute))):
                місце(в, 3, "відчуття → градуси (таблиця «%s»)" % ВІДЧУТТЯ)
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None and self.вид(м, в.value):
                місце(в, 2, "записано градуси")
            if isinstance(в, ast.Subscript) and рядок_константи(в.slice) in с.ПР:
                місце(в, 2, "прапорець походження градусів")
            if isinstance(в, ast.arg) and (в.arg in КЛЮЧІ_ЗЕРНА or в.arg in с.ПР):
                місце(в, 2, "параметр градусів «%s»" % в.arg)
            if isinstance(в, ast.Call):
                for к in self.кварги_літерали(м, в):
                    місце(к.value, 2, "літерал градусів «%s» у виклику" % к.arg)
            if isinstance(в, ast.keyword) and в.arg in с.ПР:
                додати(м.шлях, в.value.lineno, 2, "прапорець походження градусів")
            if isinstance(в, ast.Compare):
                self.порівняння(м, в, додати, рішення)
            if isinstance(в, ast.BinOp) and isinstance(в.op, (ast.Add, ast.Sub, ast.Mult, ast.Div)):
                л, п = self.вид(м, в.left), self.вид(м, в.right)
                if (л in ("т", "д")) != (п in ("т", "д")) and "р" not in (л, п):
                    інший = в.right if л else в.left
                    if not isinstance(інший, ast.Constant):
                        self.пороги(м, інший, додати, "%s:%d величина з градусів" % (м.шлях, в.lineno))
                    if isinstance(в.op, (ast.Mult, ast.Div)):
                        місце(в, 3, "величина з градусів (частка, сила)")
        # параметри, виведені потоком
        for ф in м.функції:
            for п, к in с.П.get((м.шлях, id(ф)), {}).items():
                for а in ф.args.posonlyargs + ф.args.args + ф.args.kwonlyargs:
                    if а.arg == п:
                        додати(м.шлях, а.lineno, 2, "параметр градусів «%s» (з викликів)" % п)

    def функція_за_модулем(self, м, в):
        """(модуль, FunctionDef) за кваліфікованим викликом: `M.f(…)` (`import m as M`) чи `f(…)` (`from m import f`),
        з проходом через реекспорт (`from верхнє_суд import … f`); None — виклик не кваліфіковано."""
        ім_модуля = нове = None
        if isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
            мод, нове = self.модуль_імені(м, в.func.value.id), в.func.attr
        elif isinstance(в.func, ast.Name) and в.func.id in м.імпорти and м.імпорти[в.func.id][1]:
            мод, нове = self.за_іменем.get(м.імпорти[в.func.id][0]), м.імпорти[в.func.id][1]
        else:
            return None
        for _ in range(6):
            if мод is None:
                return None
            ф = [д for д in мод.дерево.body if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef)) and д.name == нове]
            if ф:
                return мод, ф[0]
            if нове not in мод.імпорти or not мод.імпорти[нове][1]:
                return None
            мод, нове = self.за_іменем.get(мод.імпорти[нове][0]), мод.імпорти[нове][1]
        return None

    def кварги_літерали(self, м, в):
        """Літерали градусів ключовим аргументом виклику (`ф(…, темп_c=8.0)`): `ast.keyword`, коли визначення, що
        досягає параметра, є — функція продукту з єдиним ім'ям, що має цей параметр чи `**kw`, або `dict`/`update`
        (запис ключа). Функція не з продукту чи з кількома визначеннями — не місце: параметра не видно."""
        ім = self.ім_виклику(в)
        if ім is None:
            return []
        запис = ім in ("dict", "update")
        ціль = None if запис else (self.функція_за_модулем(м, в) or self.єдина(ім))
        if not запис and ціль is None:
            return []
        арг = None if запис else ціль[1].args
        імена = set() if запис else {а.arg for а in арг.posonlyargs + арг.args + арг.kwonlyargs}
        return [к for к in в.keywords if к.arg in КЛЮЧІ_ЗЕРНА and число_константи(к.value) is not None
                and (запис or к.arg in імена or арг.kwarg is not None)]

    def код_у_рядку(self, м, в, додати):
        """Python-код у рядку-шаблоні (стенд, що збирає скрипт текстом): його виклики з літералом градусів — місця
        на рядку файлу, де стоїть токен. Рядок, у якому є літерал градусів ключем, але код не розібрано, — обсяг
        не прочитано (Д10)."""
        р = в.value
        літерал = re.compile(r"\b(%s)\s*=\s*[-+]?\d" % "|".join(КЛЮЧІ_ЗЕРНА))
        if not літерал.search(р):
            return
        код = ОБСЯГ.розібрати_мовчки(р.replace("%%", "%"))  # шаблон із `%`-підстановкою
        if код is None:
            ОБСЯГ.непрочитано("%s:%d" % (м.шлях, в.lineno), "код у рядку-шаблоні не розібрано")
            return
        рядки = list(range(в.lineno, (в.end_lineno or в.lineno) + 1))
        # вхід токена у рядку файлу — за порядком у коді (шаблон склеєно з кількох рядків файлу)
        у_коді = sorted((к.value.lineno, к.value.col_offset, к.arg) for н in ast.walk(код)
                        if isinstance(н, ast.Call) for к in self.кварги_літерали(м, н))
        токени = re.compile(r"\b(%s)\s*=\s*[-+]?\d" % "|".join(КЛЮЧІ_ЗЕРНА))
        у_файлі = [(л, х.group(1)) for л in рядки if л <= len(м.рядки) for х in токени.finditer(м.рядки[л - 1])]
        for (_, _, арг), (де, _) in zip(у_коді, у_файлі):
            додати(м.шлях, де, 2, "літерал градусів «%s» у коді рядка-шаблону" % арг)

    def показ(self, м, в):
        """Текст із градусами — показ (картка, нотатка), коли рядок несе «°C»."""
        return any(isinstance(н, ast.Constant) and isinstance(н.value, str) and ГРАДУС_ТЕКСТ.search(н.value)
                   for н in ast.walk(в))

    def порівняння(self, м, в, додати, рішення):
        сторони = [в.left] + list(в.comparators)
        види = [self.вид(м, с) for с in сторони]
        if not any(к in ("т", "д") for к in види):
            return
        if all(isinstance(о, (ast.Is, ast.IsNot, ast.In, ast.NotIn)) for о in в.ops):
            return
        if all(isinstance(о, РІВНІСТЬ) for о in в.ops) and not any(
                число_константи(с) is not None for с, к in zip(сторони, види) if not к):
            return
        причина = "%s:%d порівняння градусів" % (м.шлях, в.lineno)
        значення, літерали = set(), set()
        for с, к in zip(сторони, види):
            if к:
                continue
            if число_константи(с) is not None:
                літерали.add(число_константи(с))
            значення |= self.пороги(м, с, додати, причина)
        різниця = any(к == "д" for к in види) and not any(к == "т" for к in види)
        додати(м.шлях, в.lineno, 3, "порівняння %s з межею %s" % (
            "відстані в °C" if різниця else "градусів",
            ", ".join("%g" % з for з in sorted(значення)) or "(не розгорнуто)"))
        рішення.append((м.шлях, в.lineno, різниця, frozenset(значення), frozenset(літерали)))


# ── JS і HTML ──────────────────────────────────────────────────────────────────────────────────────────────────
ОП3 = ("===", "!==", "**=", "...", ">>>", "<<=", ">>=", "&&=", "||=", "??=")
ОП2 = ("==", "!=", "<=", ">=", "&&", "||", "??", "=>", "?.", "++", "--", "+=", "-=", "*=", "/=", "%=", "**",
       "<<", ">>", "|=", "&=", "^=")
ПЕРЕД_РЕГУЛЯРКОЮ = set("(,=:[!&|?{};+-*%<>~^") | {"return", "typeof", "case", "do", "else", "in", "of", "new",
                                                 "delete", "void", "throw", "=>", "&&", "||", "??", "==", "===",
                                                 "!=", "!==", "<=", ">="}


def лексер_js(т, перший_рядок=1):
    """Токени JS: (вид, значення, рядок); вид — ім, ряд, чис, оп, рег. Коментарі відкинуто, шаблони розгорнуто
    (той самий лексер, що в `корінь_е2_частина_дня.py`)."""
    токени, і, р, н = [], 0, перший_рядок, len(т)
    стек = []

    def шаблон(і, р):
        поч_р, буф = р, []
        while і < н:
            ч = т[і]
            if ч == "\\":
                буф.append(т[і:і + 2])
                р += т[і:і + 2].count("\n")
                і += 2
                continue
            if ч == "`":
                токени.append(("ряд", "".join(буф), поч_р))
                return і + 1, р, True
            if ч == "$" and т[і + 1:і + 2] == "{":
                токени.append(("ряд", "".join(буф), поч_р))
                return і + 2, р, False
            if ч == "\n":
                р += 1
            буф.append(ч)
            і += 1
        токени.append(("ряд", "".join(буф), поч_р))
        return і, р, True

    while і < н:
        ч = т[і]
        if ч == "\n":
            р += 1
            і += 1
            continue
        if ч.isspace():
            і += 1
            continue
        if т.startswith("//", і):
            j = т.find("\n", і)
            і = н if j < 0 else j
            continue
        if т.startswith("/*", і):
            j = т.find("*/", і + 2)
            j = н if j < 0 else j + 2
            р += т.count("\n", і, j)
            і = j
            continue
        if ч in "'\"":
            j, буф = і + 1, []
            while j < н and т[j] != ч and т[j] != "\n":
                if т[j] == "\\":
                    буф.append(т[j:j + 2])
                    j += 2
                    continue
                буф.append(т[j])
                j += 1
            токени.append(("ряд", "".join(буф), р))
            і = j + 1
            continue
        if ч == "`":
            і, р, кінець = шаблон(і + 1, р)
            if not кінець:
                стек.append(0)
            continue
        if ч == "}" and стек:
            if стек[-1] == 0:
                стек.pop()
                і, р, кінець = шаблон(і + 1, р)
                if not кінець:
                    стек.append(0)
                continue
            стек[-1] -= 1
        if ч == "{" and стек:
            стек[-1] += 1
        if ч.isalpha() or ч in "_$":
            j = і + 1
            while j < н and (т[j].isalnum() or т[j] in "_$"):
                j += 1
            токени.append(("ім", т[і:j], р))
            і = j
            continue
        if ч.isdigit() or (ч == "." and т[і + 1:і + 2].isdigit()):
            j = і + 1
            while j < н and (т[j].isalnum() or т[j] in "._"):
                j += 1
            токени.append(("чис", т[і:j], р))
            і = j
            continue
        if ч == "/":
            п = токени[-1] if токени else None
            if п is None or (п[0] == "оп" and п[1] in ПЕРЕД_РЕГУЛЯРКОЮ) or (п[0] == "ім" and п[1] in ПЕРЕД_РЕГУЛЯРКОЮ):
                j, клас = і + 1, False
                while j < н and т[j] != "\n":
                    if т[j] == "\\":
                        j += 2
                        continue
                    if т[j] == "[":
                        клас = True
                    elif т[j] == "]":
                        клас = False
                    elif т[j] == "/" and not клас:
                        break
                    j += 1
                j += 1
                while j < н and т[j].isalpha():
                    j += 1
                токени.append(("рег", т[і:j], р))
                і = j
                continue
        for оп in ОП3 + ОП2:
            if т.startswith(оп, і):
                токени.append(("оп", оп, р))
                і += len(оп)
                break
        else:
            токени.append(("оп", ч, р))
            і += 1
    return токени


class Джс:
    """Файл JS (чи скрипти HTML): токени й сегменти (верхні оператори й функції)."""

    def __init__(self, шлях, токени):
        self.шлях = шлях
        self.т = токени
        self.сегмент = [0] * len(токени)
        сег, глиб = 0, 0
        for і, (вид, зн, _) in enumerate(токени):
            self.сегмент[і] = сег
            if вид == "оп" and зн in "{([":
                глиб += 1
            elif вид == "оп" and зн in "})]":
                глиб = max(0, глиб - 1)
                if глиб == 0 and зн == "}":
                    сег += 1
            elif вид == "оп" and зн == ";" and глиб == 0:
                сег += 1
        self.розмітка = []      # (рядок, доказ, пункт) поза скриптами HTML


class Хтмл(Джс):
    """HTML: поле градусів панелі (`<input type="number">` з «°C» у рядку), розмітка з його `id`, вбудовані скрипти."""

    ВХІД = re.compile(r"<input\b[^>]*>", re.IGNORECASE)

    def __init__(self, шлях, текст):
        токени, скрипти = [], set()
        for м in re.finditer(r"<script\b[^>]*>(.*?)</script>", текст, re.DOTALL | re.IGNORECASE):
            поч = текст.count("\n", 0, м.start(1)) + 1
            токени += лексер_js(м.group(1), поч)
            скрипти |= set(range(поч, текст.count("\n", 0, м.end(1)) + 2))
        super().__init__(шлях, токени)
        self.рядки_html = текст.splitlines()
        self.скрипти = скрипти
        self.поля = {}
        for н, рядок in enumerate(self.рядки_html, 1):
            if н in скрипти:
                continue
            без = re.sub(r"<!--.*?-->", "", рядок)
            for м in self.ВХІД.finditer(без):
                тег = м.group(0)
                ід = re.search(r"\bid=[\"']([^\"']+)", тег)
                if ід and re.search(r"type=[\"']?number", тег) and ГРАДУС_ТЕКСТ.search(без):
                    self.поля[ід.group(1)] = н


ЧИСЛОВІ_JS = {"parseFloat", "parseInt", "Number", "String", "$", "round", "abs", "min", "max"}


class АналізДжс:
    """Місця в JS і HTML: токени-ключі градусів, `id` поля градусів, текст показу з «°C», локальні носії."""

    def __init__(self, файли, стан):
        self.файли = файли
        self.с = стан
        self.ІД = {}
        for ф in файли:
            for ід, н in getattr(ф, "поля", {}).items():
                self.ІД.setdefault(ід, "%s:%d" % (ф.шлях, н))
        self.ФН = set()         # функції JS, що повертають градуси

    def носій_токен(self, ток, попередній):
        вид, зн, _ = ток
        if вид == "ім":
            return зн in self.с.К and "_" in зн
        if вид == "ряд":
            return зн in self.с.К or зн in self.ІД
        return False

    def вираз_носій(self, т, j, імена):
        """Чи вираз від токена j (до `;` чи коми верхнього рівня) несе градуси; → (так/ні, кінець).
        Об'єкт чи масив — не градуси (їхні ключі лічаться самі); носій усередині виклику не з `ЧИСЛОВІ_JS`
        (`типовеЧислоП('сц-темп')`) — аргумент, а не значення виразу."""
        if j < len(т) and т[j][1] in ("{", "["):
            return False, j
        стек, носій = [], False
        while j < len(т):
            вв, зз, _ = т[j]
            if вв == "оп" and зз in "([{":
                поп_ = т[j - 1]
                стек.append(False if зз == "{" else (поп_[0] in ("ім", "ряд") or поп_[1] in (")", "]")) if зз == "["
                            else поп_[0] != "ім" or поп_[1] in ЧИСЛОВІ_JS or поп_[1] in self.ФН)
            elif вв == "оп" and зз in ")]}":
                if not стек:
                    break
                стек.pop()
            elif вв == "оп" and зз in (";", ",") and not стек:
                break
            elif вв == "ім" and зз in ("return", "const", "let", "var", "if", "else") and not стек and j:
                break
            if all(стек) and (self.носій_токен(т[j], т[j - 1]) or (вв == "ряд" and ГРАДУС_ТЕКСТ.search(зз))
                              or (вв == "ім" and т[j - 1][1] != "." and (
                                  зз in імена or (зз in self.ФН and j + 1 < len(т) and т[j + 1][1] == "(")))):
                носій = True
            j += 1
        return носій, j

    def локальні(self, ф):
        """Сегмент → імена локальних, яким присвоєно вираз із градусами (`const т = parseFloat($('сц-темп').value)`)."""
        т, локальні = ф.т, {}
        for і, (вид, зн, р) in enumerate(т):
            if вид == "ім" and зн in ("const", "let", "var") and і + 3 < len(т) and т[і + 1][0] == "ім" \
                    and т[і + 2][1] == "=":
                if self.вираз_носій(т, і + 3, локальні.get(ф.сегмент[і], ()))[0]:
                    локальні.setdefault(ф.сегмент[і], set()).add(т[і + 1][1])
        return локальні

    def функції_носії(self):
        """Оголошені функції (`function X(){…}`), чиї повернення — градуси чи порожнє (до нерухомої точки)."""
        for _ in range(10):
            нові = set()
            for ф in self.файли:
                т, локальні = ф.т, self.локальні(ф)
                for і, (вид, зн, р) in enumerate(т):
                    if not (вид == "ім" and зн == "function" and і + 2 < len(т) and т[і + 1][0] == "ім"
                            and т[і + 2][1] == "("):
                        continue
                    j = і + 2
                    while j < len(т) and т[j][1] != "{":
                        j += 1
                    глиб, кінець = 0, j
                    for кінець in range(j, len(т)):
                        if т[кінець][1] == "{":
                            глиб += 1
                        elif т[кінець][1] == "}":
                            глиб -= 1
                            if глиб == 0:
                                break
                    повернення = [к for к in range(j, кінець) if т[к][:2] == ("ім", "return")]
                    if not повернення:
                        continue
                    види = []
                    for к in повернення:
                        if т[к + 1][1] in (";", "}") or т[к + 1][1] in ("null", "undefined"):
                            види.append(None)
                            continue
                        види.append(self.вираз_носій(т, к + 1, локальні.get(ф.сегмент[к + 1], ()))[0])
                    if any(види) and all(в is not False for в in види):
                        нові.add(т[і + 1][1])
            if нові == self.ФН:
                return
            self.ФН = нові

    def місця(self, ф, додати):
        т = ф.т
        локальні = self.локальні(ф)
        for і, ток in enumerate(т):
            вид, зн, р = ток
            поп = т[і - 1] if і else ("оп", "", 0)
            if self.носій_токен(ток, поп):
                додати(ф.шлях, р, 4 if зн in self.ІД else 2, "%s «%s»" % ("поле градусів панелі" if зн in self.ІД
                                                                          else "ключ градусів", зн))
            elif вид == "ряд" and ГРАДУС_ТЕКСТ.search(зн):
                додати(ф.шлях, р, 4, "текст показу з «°C»")
            elif вид == "ім" and зн in self.ФН and поп[1] not in (".", "function") and і + 1 < len(т) \
                    and т[і + 1][1] == "(":
                додати(ф.шлях, р, 2, "градуси з функції «%s»" % зн)
            elif вид == "ім" and зн in локальні.get(ф.сегмент[і], ()) and поп[1] != ".":
                наст = т[і + 1] if і + 1 < len(т) else ("оп", "", 0)
                if наст[1] == ":" and поп[1] in ("{", ","):
                    continue        # ключ об'єкта з тим самим ім'ям — не носій
                додати(ф.шлях, р, 2, "градуси в локальному «%s»" % зн)
            if вид == "оп" and зн in ("<", "<=", ">", ">=") and і + 1 < len(т):
                сусіди = т[max(0, і - 8):і + 4]
                if any(self.носій_токен(х, т[0]) or (х[0] == "ім" and х[1] in локальні.get(ф.сегмент[і], ()))
                       for х in сусіди) and any(х[0] == "чис" for х in т[і + 1:і + 3]) and not any(
                        т[j][1] == "?" and т[j + 1] == ("ряд", "+", т[j + 1][2]) for j in range(і + 1, min(і + 5, len(т) - 1))):
                    # `т > 0 ? '+' : ''` — знак числа в тексті показу, не межа (рядок — місце п.4)
                    додати(ф.шлях, р, 3, "порівняння градусів з літералом у показі")
        for н, доказ, п in ф.розмітка:
            додати(ф.шлях, н, п, доказ)

    def розмітка(self, ф):
        """Рядки розмітки HTML поза скриптами: атрибути з `id` поля градусів і текст «°C» поруч із полем."""
        if not isinstance(ф, Хтмл):
            return
        for н, рядок in enumerate(ф.рядки_html, 1):
            if н in ф.скрипти:
                continue
            без = re.sub(r"<!--.*?-->", "", рядок)
            for м in re.finditer(r"\b(?:id|for|name|data-[\w-]+)=[\"']([^\"']+)[\"']", без):
                if м.group(1) in self.ІД:
                    ф.розмітка.append((н, "розмітка поля градусів «%s»" % м.group(1), 4))
                    if re.search(r"\bvalue=[\"']?-?\d", без):
                        ф.розмітка.append((н, "типові градуси поля панелі", 3))
                    break


# ── правила бази знань (п.5) ────────────────────────────────────────────────────────────────────────────────────
# Межі смуг K-WEA-01 — з самої бази (карта шарів торса, тема-4 §IX.4): рядок-якір мусить там бути, межі читаються з
# нього. Рішення з порогом поза ними (сніг 0, 12 літніх речей, допуски) чи літерал, що повторює поріг реєстру, — п.5.
БАЗА_СМУГ = ("джерела/тема-4_композиція-і-когерентність-EN.md", r"The map, so it exists somewhere other than code")
ПОЗА_МЕЖАМИ = {999.0, -999.0}


def межі_бази(корінь):
    """Межі смуг K-WEA-01 з рядка-якоря бази; (множина, звіт)."""
    шлях = os.path.join(корінь, БАЗА_СМУГ[0])
    if not os.path.exists(шлях):
        return None, "база K-WEA-01: файлу %s нема — п.5 не судиться" % БАЗА_СМУГ[0]
    with open(шлях, encoding="utf-8") as ф:
        for н, рядок in enumerate(ф, 1):
            if re.search(БАЗА_СМУГ[1], рядок):
                карта = рядок[рядок.find("≥"):]
                карта = карта[:карта.find(".", карта.find("<−"))] if "<−" in карта else карта[:400]
                межі = set()
                for м in re.finditer(r"([≥<]?)([−-]?\d+)(?:\s?°C)?\s?(?:–([−-]?\d+))?\s?→", карта):
                    for ч in (м.group(2), м.group(3)):
                        if ч:
                            межі.add(float(ч.replace("−", "-")))
                return межі, "база K-WEA-01: %s:%d — межі смуг %s" % (
                    БАЗА_СМУГ[0], н, ", ".join("%g" % х for х in sorted(межі)))
    return None, "база K-WEA-01: якоря «%s» у %s нема — п.5 не судиться" % (БАЗА_СМУГ[1], БАЗА_СМУГ[0])


def рішення_бази(корінь, рішення, пороги_реєстру, додати, звіт, без_бази=False):
    """П.5: рішення (порівняння градусів) з межею поза K-WEA-01 чи з літералом, що повторює поріг реєстру."""
    межі, рядок = (None, "база K-WEA-01: самоперевірка без бази — межі 26, 18, 10, 2, −8") if без_бази else \
        межі_бази(корінь)
    if без_бази:
        межі = {26.0, 18.0, 10.0, 2.0, -8.0}
    звіт.append(рядок)
    поза, двічі = 0, 0
    for файл, н, різниця, значення, літерали in рішення:
        if межі is not None and not різниця:
            чужі = sorted(з for з in значення if з not in межі and з not in ПОЗА_МЕЖАМИ)
            if чужі:
                додати(файл, н, 5, "межа, якої база не дає: %s" % ", ".join("%g" % з for з in чужі))
                поза += 1
        if різниця:
            чужі = sorted(з for з in значення if з != 0)
            if чужі:
                додати(файл, н, 5, "допуск у °C, якого база не дає: %s" % ", ".join("%g" % з for з in чужі))
                поза += 1
        # відстань від смуги з 0 — «поза смугою», не повтор порогу (сніг 0) реєстру
        повтор = sorted(з for з in літерали if з in пороги_реєстру and not різниця)
        if повтор:
            додати(файл, н, 5, "межу визначено двічі: літерал %s = поріг реєстру %s" % (
                ", ".join("%g" % з for з in повтор), ", ".join(sorted(пороги_реєстру[повтор[0]]))))
            двічі += 1
    звіт.append("п.5: рішень з межею поза базою — %d; літералів, що повторюють поріг реєстру, — %d" % (поза, двічі))


# ── обхід ───────────────────────────────────────────────────────────────────────────────────────────────────────
def файли_продукту(корінь):
    """(шлях від кореня) файлів коду продукту і число файлів поза класом (тести й проби за іменем)."""
    дж = os.path.join(корінь, "джерела")
    файли, поза = [], 0
    for база, теки, імена in os.walk(дж):
        теки[:] = sorted(т for т in теки if т not in ПОЗА_ТЕКИ and not т.startswith("."))
        for ім in sorted(імена):
            if not ім.endswith(РОЗШИРЕННЯ):
                continue
            if ТЕСТ.search(ім):
                поза += 1
                continue
            файли.append(os.path.relpath(os.path.join(база, ім), корінь).replace(os.sep, "/"))
    return sorted(файли), поза


def лічити(корінь, без_бази=False):
    """Повний обхід: → (місця {(файл, рядок): {пункти, докази}}, стан, звіт, лік, читачі)."""
    файли, поза = файли_продукту(корінь)
    пі, джс, помилки = [], [], []
    for шлях in файли:
        with open(os.path.join(корінь, шлях), encoding="utf-8", errors="replace") as ф:
            текст = ф.read()
        if шлях.endswith(".py"):
            try:
                пі.append(Пі(шлях, текст))
            except SyntaxError as е:
                помилки.append("%s: не розібрано (%s)" % (шлях, е.msg))
                ОБСЯГ.непрочитано(шлях, "SyntaxError: %s" % е)
        elif шлях.endswith(".html"):
            джс.append(Хтмл(шлях, текст))
        else:
            джс.append(Джс(шлях, лексер_js(текст)))
    стан = Стан()
    ап = АналізПі(пі, стан)
    проходів = 0
    while стан.змінено and проходів < 40:
        стан.змінено = False
        проходів += 1
        for м in пі:
            ап.прохід(м)
    місця = {}

    def додати(файл, рядок, пункт, доказ):
        з = місця.setdefault((файл, рядок), {"пункти": set(), "докази": []})
        з["пункти"].add(пункт)
        if доказ not in з["докази"]:
            з["докази"].append(доказ)

    рішення = []
    адж = АналізДжс(джс, стан)
    стан.ІД = адж.ІД
    адж.функції_носії()
    for м in пі:
        ап.місця(м, додати, рішення)
    ап.пороги_вперед(додати)
    for ф in джс:
        адж.розмітка(ф)
        адж.місця(ф, додати)
    # пороги реєстру: значення → імена записів (для «визначено двічі»)
    пороги_реєстру = {}
    for (файл, н), з in місця.items():
        for д in з["докази"]:
            м_ = re.search(r"поріг реєстру «([^»]+)»", д)
            if м_:
                мод = next((м for м in пі if м.шлях == файл), None)
                if мод is not None:
                    for в in мод.вид("keyword"):
                        if в.arg == "val" and в.value.lineno == н and число_константи(в.value) is not None:
                            пороги_реєстру.setdefault(число_константи(в.value), set()).add(м_.group(1).split("/")[0])
    звіт = []
    рішення_бази(корінь, рішення, пороги_реєстру, додати, звіт, без_бази)
    читачі = set()
    for м in пі:
        for ф in м.функції:
            рядки = range(ф.lineno, (ф.end_lineno or ф.lineno) + 1)
            вкладені = {н for в in ast.walk(ф) if в is not ф and isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))
                        for н in range(в.lineno, (в.end_lineno or в.lineno) + 1)}
            if any((м.шлях, н) in місця for н in рядки if н not in вкладені):
                читачі.add((м.шлях, ф.name))
    лік = dict(py=sum(ф.endswith(".py") for ф in файли), js=sum(ф.endswith((".js", ".mjs")) for ф in файли),
               html=sum(ф.endswith(".html") for ф in файли), поза=поза, проходів=проходів, помилки=помилки)
    return місця, стан, звіт, лік, читачі


def друк(місця, стан, звіт, лік, читачі, тихо=False, імена=False, з_читачами=False):
    """Детермінований вивід; останній рядок — `місць: N`."""
    рядки = ["корінь Е2-смуга-погоди: градуси повітря нагоди в коді продукту (клас — аудит/корені/Е2-смуга-погоди.md)",
             "файлів коду продукту: %d (py %d, js %d, html %d); поза класом за іменем (тести, проби): %d; "
             "проходів виводу: %d" % (лік["py"] + лік["js"] + лік["html"], лік["py"], лік["js"], лік["html"],
                                      лік["поза"], лік["проходів"])]
    рядки += ["ПОМИЛКА розбору: " + п for п in лік["помилки"]]
    if not тихо:
        рядки.append("")
        for (файл, рядок), з in sorted(місця.items()):
            рядки.append("%s:%d · п.%s · %s" % (файл, рядок, ",".join(str(п) for п in sorted(з["пункти"])),
                                                 "; ".join(з["докази"][:3])))
    рядки.append("")
    за_пунктами = {п: sum(п in з["пункти"] for з in місця.values()) for п in range(1, 6)}
    рядки.append("за пунктами класу (місце з кількома пунктами — у кожному): " +
                 "; ".join("п.%d — %d" % (п, н) for п, н in за_пунктами.items()))
    за_файлами = {}
    for (файл, _) in місця:
        за_файлами[файл] = за_файлами.get(файл, 0) + 1
    рядки.append("за файлами (%d): " % len(за_файлами) + "; ".join(
        "%s — %d" % (ф, н) for ф, н in sorted(за_файлами.items(), key=lambda х: (-х[1], х[0]))))
    порівнянь = sorted({к for к, з in місця.items() if any(д.startswith("порівняння") for д in з["докази"])})
    рядки.append("порівнянь градусів з межею (рядків): %d" % len(порівнянь))
    рядки.append("функцій-читачів Python (функція, у тілі якої є місце): %d" % len(читачі))
    рядки += звіт
    if з_читачами:
        рядки.append("")
        рядки += ["читач: %s:%s" % ч for ч in sorted(читачі)]
    if імена:
        рядки.append("")
        рядки.append("ключі й атрибути градусів (%d): %s" % (len(стан.К), ", ".join(sorted(стан.К))))
        рядки.append("прапорці походження (%d): %s" % (len(стан.ПР), ", ".join(sorted(стан.ПР))))
        рядки.append("функції, що повертають градуси (%d):" % len(стан.Ф))
        for ім in sorted(стан.Ф):
            рядки.append("  %s [%s] ← %s" % (ім, стан.Ф[ім], стан.звідки.get(ім, "?")))
        рядки.append("глобальні імена-градуси (%d): %s" % (len(стан.Г), ", ".join(
            "%s:%s" % к for к in sorted(стан.Г))))
        рядки.append("параметри з викликів (%d):" % sum(len(х) for х in стан.П.values()))
        for к in sorted(к_ for к_ in стан.звідки if "(" in к_):
            рядки.append("  %s ← %s" % (к, стан.звідки[к]))
    рядки.append("місць: %d" % len(місця))
    return "\n".join(рядки)

# ── самоперевірка ───────────────────────────────────────────────────────────────────────────────────────────────
# Штучні файли: кожен пункт класу й кожне «не місце» паспорта. Позначка `М:<ім'я>` у коментарі рядка (коментарі —
# не місця); очікуване — точний набір пунктів рядка, порожній — рядок не місце.
ШТУЧНІ = {
    "джерела/ш_нагода.py": """\
РЕЄСТР_ПОГОДИ = {
    "мороз": dict(t="T3", val=-8),  # М:поріг
    "літо": dict(t="T3", val=12),  # М:поріг_поза
    "сніг": dict(t="T3", val=0),  # М:поріг_без_порівняння
}
НОТА = {"літо": "межу судять градусами темп_c паспорта нагоди"}  # М:примітка
ТАБЛИЦЯ = {
    "weather_feel": {"frost": -10, "hot": 30},  # М:таблиця
}
СХЕМА = {
    "temperature_c": {"type": "number", "description": "Air temperature in Celsius"},  # М:схема
}
ПРОМПТ = "Return temperature_c as the air temperature in degrees Celsius"  # М:промпт
ТЕМП_МАПА = [
    (26, 999, "спека"),  # М:смуга
    (-999, 26, "решта"),
]
СМУГИ_НІГ = [(-30, 5, "чоботи")]  # М:смуга_речі
ГЕЙТ = "assert сц['темп_c'] > 0"  # М:гейт


def градуси(нагода):
    т = (нагода or {}).get("темп_c")  # М:читання
    if т is None:
        т = ТАБЛИЦЯ["weather_feel"].get((нагода or {}).get("погода_відчуття"))  # М:відчуття
    return т


def позначити(нагода):
    _т = градуси(нагода)
    нагода["темп_c"], нагода["темп_з_відчуття"] = _т, True  # М:прапорець


def з_відчуття(нагода):
    return bool(нагода.get("темп_з_відчуття"))  # М:прапорець_читання


def суд(нагода):
    т = градуси(нагода)  # М:повернення
    if т is not None and т <= РЕЄСТР_ПОГОДИ["мороз"]["val"]:  # М:порівняння
        return "мороз"
    if т is not None and т <= РЕЄСТР_ПОГОДИ["літо"]["val"]:  # М:поза_базою
        return "літо"
    if т is not None and т >= 22:  # М:літерал_поза
        return "тепло"
    if т is not None and т <= -8:  # М:двічі
        return "мороз2"
    if т is not None and abs(т - 18) <= 4:  # М:допуск
        return "близько"
    if т is not None and abs(т - 18) > 0:  # М:поза_смугою
        return "поза"
    if т is not None and т <= 0:  # М:двічі_нуль
        return "сніг"
    for lo, hi, смуга in ТЕМП_МАПА:
        if т is not None and lo <= т < hi:  # М:пошук_смуги
            return смуга
    return None


def ноги(річ):
    for lo, hi, назва in СМУГИ_НІГ:
        if lo < 0:  # М:смуга_речі_без_нагоди
            return назва
    return річ


def передати(нагода):
    return показати(градуси(нагода))  # М:аргумент


def показати(значення_т):  # М:параметр
    return "%+.0f °C" % значення_т  # М:показ_тексту


def бриф(нагода, пояснення):
    _т = пояснення.температура  # М:колір
    if _т > 0.1:  # М:колір_поріг
        нагода = dict(нагода)
    _т = нагода.get("темп_c")  # М:псевдонім
    return _т is not None and _т <= 18  # М:псевдонім_поріг


def модель(клієнт):
    return клієнт.create(model="m", temperature=0.2)  # М:temperature_моделі


def тривалість(нагода):
    год = нагода.get("тривалість_год")  # М:тривалість
    return год > 2  # М:тривалість_поріг


def слово(нагода):
    return нагода.get("погода_відчуття")  # М:слово_відчуття


def знахідка(з, нагода):
    з["вимір"] = градуси(нагода)  # М:запис_вимір
    х = з["вимір"]  # М:читання_вимір
    return х
""",
    "джерела/ш_кварг.py": """\
def приймач(речі, темп_c=None):
    return речі


def без_параметра(речі):
    return речі


def виклики(речі):
    приймач(речі, темп_c=8.0)  # М:кварг_літерал
    приймач(речі, темп_c=-1.0)  # М:кварг_мінус
    без_параметра(речі, темп_c=5.0)  # М:кварг_без_параметра
    чужа(речі, темп_c=5.0)  # М:кварг_чужа
    приймач(речі, темп_c=речі)  # М:кварг_не_число
    стенд = ("x = dict(a=1,\\n"
             "     темп_c=18.0)\\n"  # М:кварг_шаблон
             "assert x\\n")
    return стенд
""",
    "джерела/показ/ш.js": """\
function картка(){
  const т = parseFloat($('ш-темп').value);  // М:js_локальний
  const н = типове('ш-темп') ? іншеП() : null;  // М:js_поле_в_аргументі
  const сц = {нагода: 'x', темп_c: т};  // М:js_обʼєкт
  if (т <= 0) сніг();  // М:js_порівняння
  const р = (т > 0 ? '+' : '') + т + ' °C';  // М:js_показ
  return [н.пора, сц.нагода];  // М:js_не_носій
}
function градусиП(){
  return типове('ш-темп') ? NaN : parseFloat($('ш-темп').value);  // М:js_повернення
}
function словоП(){
  return типове('ш-темп') ? 'так' : 'ні';  // М:js_повернення_не_носій
}
function рядокП(){
  const г = градусиП();  // М:js_виклик
  const с = словоП();  // М:js_виклик_не_носій
  return г + с;  // М:js_локальний_з_виклику
}
""",
    "джерела/ш.html": """\
<label for="ш-темп">Надворі</label> <!-- М:html_мітка -->
<input type="number" id="ш-темп" value="18"><b>°C</b> <!-- М:html_поле -->
<input type="number" id="ш-вітер" value="3"><b>м/с</b> <!-- М:html_не_поле -->
<script src="показ/ш.js"></script>
""",
    "джерела/тест_ш.py": """\
т = {"темп_c": 5}  # М:тест
""",
}
ОЧІКУВАНІ = {
    "поріг": {3}, "поріг_поза": {3}, "примітка": set(), "таблиця": {3}, "схема": {1, 2}, "промпт": {1},
    "смуга": {3}, "смуга_речі": set(), "гейт": set(), "читання": {2}, "відчуття": {2, 3}, "прапорець": {2},
    "прапорець_читання": {2}, "повернення": {2}, "порівняння": {2, 3}, "поза_базою": {2, 3, 5},
    "літерал_поза": {2, 3, 5}, "двічі": {2, 3, 5}, "допуск": {2, 3, 5}, "поріг_без_порівняння": set(), "поза_смугою": {2, 3},
    "двічі_нуль": {2, 3, 5}, "пошук_смуги": {2, 3},
    "смуга_речі_без_нагоди": set(), "кварг_літерал": {2}, "кварг_мінус": {2}, "кварг_без_параметра": set(), "кварг_чужа": set(),
    "кварг_не_число": set(), "кварг_шаблон": {2}, "аргумент": {2}, "параметр": {2}, "показ_тексту": {4}, "колір": set(),
    "колір_поріг": set(), "псевдонім": {2}, "псевдонім_поріг": {2, 3}, "temperature_моделі": set(),
    "тривалість": set(), "тривалість_поріг": set(), "слово_відчуття": set(), "запис_вимір": {2},
    "читання_вимір": set(), "js_локальний": {2, 4}, "js_поле_в_аргументі": {4}, "js_обʼєкт": {2},
    "js_порівняння": {2, 3}, "js_показ": {2, 4}, "js_не_носій": set(), "js_повернення": {4},
    "js_повернення_не_носій": {4}, "js_виклик": {2}, "js_виклик_не_носій": set(), "js_локальний_з_виклику": {2}, "html_мітка": {4}, "html_поле": {3, 4},
    "html_не_поле": set(), "тест": set(),
}


def самоперевірка():
    """[(назва, так/ні)]: кожна позначка штучних файлів — очікуваний набір пунктів; вивід — однаковий двічі."""
    тека = tempfile.mkdtemp(prefix="е2_смуга_")
    try:
        позначки = {}
        for шлях, текст in ШТУЧНІ.items():
            повний = os.path.join(тека, шлях)
            os.makedirs(os.path.dirname(повний), exist_ok=True)
            with open(повний, "w", encoding="utf-8") as ф:
                ф.write(текст)
            for н, рядок in enumerate(текст.splitlines(), 1):
                for м in re.finditer(r"М:(\w+)", рядок):
                    позначки[м.group(1)] = (шлях, н)
        перший = лічити(тека, без_бази=True)
        другий = лічити(тека, без_бази=True)
        місця = перший[0]
        підсумок = []
        for ім, очікуване in ОЧІКУВАНІ.items():
            if ім not in позначки:
                підсумок.append((ім + " (позначки нема)", False))
                continue
            є = місця.get(позначки[ім], {}).get("пункти", set())
            ок = set(є) == очікуване
            підсумок.append(("%s — %s" % (ім, "п." + ",".join(map(str, sorted(є))) if є else "не місце")
                             if ок else "%s — є %s, чекали %s" % (ім, sorted(є), sorted(очікуване)), ок))
        підсумок.append(("позначки без очікуваного: %s" % (", ".join(sorted(set(позначки) - set(ОЧІКУВАНІ)))
                                                           or "нема"), not (set(позначки) - set(ОЧІКУВАНІ))))
        підсумок.append(("вивід детермінований", друк(*перший) == друк(*другий)))
        return підсумок
    finally:
        shutil.rmtree(тека, ignore_errors=True)


def main(арг):
    корінь = os.getcwd()
    if "--корінь" in арг:
        корінь = арг[арг.index("--корінь") + 1]
    if "--самоперевірка" in арг:
        п = самоперевірка()
        for ім, ок in п:
            print("самоперевірка: %s — %s" % (ім, "так" if ок else "НІ"))
        print("самоперевірка: %d з %d" % (sum(ок for _, ок in п), len(п)))
        return 0 if all(ок for _, ок in п) else 1
    місця, стан, звіт, лік, читачі = лічити(корінь)
    print(друк(місця, стан, звіт, лік, читачі, тихо="--тихо" in арг, імена="--імена" in арг,
               з_читачами="--читачі" in арг))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
