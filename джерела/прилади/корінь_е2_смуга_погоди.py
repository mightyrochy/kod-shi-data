# -*- coding: utf-8 -*-
"""прилади/корінь_е2_смуга_погоди.py — градуси повітря й м/с вітру нагоди в коді продукту.

Клас — `аудит/корені/Е2-смуга-погоди.md` («Клас місць», «Стан і що лишилось» — «Вгору»): місце — кожна точка коду
продукту (`джерела/`, `zhnyvarka/` на будь-якій глибині: Python, JS, HTML і промпти; проби, прилади й тести — ні), де градуси
повітря нагоди — названі нею чи число коду з відчуття — є полем, ключем, числом, порогом чи текстом показу. Пункти:
  1  мовну модель просять градуси (схема, опис поля `temperature_c`, промпт, заява з `temperature_c`/`temp_c`) чи код
     приймає їх із відповіді;
  2  код читає, пише, зберігає чи передає градуси (паспорт, картка, сцена, кеш, правила, бриф, промпт, заява суду,
     дріт, протокол стилістки), зокрема прапорець походження градусів (`темп_з_відчуття`) і її словами: цитата поля
     смуги погоди в плоских цитатах паспорта (`цитати_полів` → `field_quotes`, «Твої слова») і в джерелі поля
     (`sources[].quote`) — доповнено 15.11 (`АналізСлів`, Ц і Д); число з її уривка (Ч, рішення менеджера 15523);
     рядок з °C будь-якою мовою в змістовому полі знахідки суду (`знахідка.ЗМІСТОВІ`, до запиту стилістки; показ
     читає — ще й п.4) — З, рішення менеджера 15584: місце визначає читач рядка, а не мова;
  3  код перетворює відчуття на градуси (таблиця `weather_feel`) чи градуси на смугу, факт чи величину — порогом
     реєстру чи літералом, пошуком у таблиці смуг, відстанню чи часткою в °C; сам поріг реєстру, межа таблиці смуг,
     з якою порівнюють градуси нагоди, і літерал межі — теж місце;
  4  панель дає ввести градуси числом, картка й показ показують градуси, зокрема текстом моделі: шапка картки з
     вільного рядка відповіді моделі про погоду — доповнено 15.11 (`АналізСлів`, Ш); поріг у °C текстом моделі
     (англійська рядкова константа з числом °C, «at +20 °C and warmer») — п.3 (`АналізСлів`, Т);
  5  рішення правила погоди судить межею, якої база знань не дає (межі K-WEA-01 — з бази, `тема-4` §IX.4), чи межу
     визначено двічі (літерал, що повторює поріг реєстру). Місце — саме рішення (порівняння), не кожна точка з ід.
  6  м/с вітру нагоди: поле, ключ, перетворення плитки чи слова на м/с, поріг і показ.

М/с лічаться окремим проходом того самого потоку: зерна — одиниця `м/с` / `m/s` у специфікації числового поля,
суфікс одиниці (`wind_ms`, `wind_mps`, `вітер_мс`) й числовий ввід HTML із м/с. Від писача такого поля потік іде
назад до виробника числа й значень таблиці, а далі вперед — через присвоєння, повернення, виклики й пороги.
Індекс таблиці (бал плитки чи слово смуги) одиниці не набуває. Назв таблиць і чисел порогів у правилі пошуку нема.
Увесь потік м/с — п.6; він не змінює градусного потоку чи меж K-WEA-01. Однаковий файл:рядок лічиться один раз.

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
    python3 джерела/прилади/корінь_е2_смуга_погоди.py [--вітер | --градуси]
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
ВІТЕР_ТЕКСТ = re.compile(r"(?<![\w/])(?:м\s*/\s*с|m\s*/\s*s)(?!\w)")
МЕТРИ_ІМЯ = re.compile(r"(?:^|_)(?:wind.*_(?:ms|mps)|вітер.*_мс|швидкість_мс)$", re.IGNORECASE)
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

    def __init__(self, вітер=False):
        self.вітер = вітер
        self.зерна = set() if вітер else set(КЛЮЧІ_ЗЕРНА)
        self.одиниця = ВІТЕР_ТЕКСТ if вітер else ГРАДУС_ТЕКСТ
        self.відчуття = "" if вітер else ВІДЧУТТЯ
        self.К = set(self.зерна)    # ключі записів і атрибути, що несуть градуси
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
        return isinstance(в, ast.Subscript) and рядок_константи(в.slice) == self.с.відчуття

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
            if ім == "ключ" and в.args and рядок_константи(в.args[0]) == self.с.відчуття:
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
        if ім in self.с.зерна:
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
    def перелік_відкидання(self, м, в):
        """Рядок-ключ — елемент переліку, який лише відкидають: кожне вживання імені переліку — `for к in ПЕРЕЛІК`, а
        кожне вживання `к` у тілі циклу — перший аргумент `.pop(к, None)` чи індекс `del ...[к]`. Клас паспорта
        (рішення 05.11): таке місце не читає, не пише й не передає градуси, а знімає давній ключ на вході збережених
        даних — тримає інваріант, а не ламає його; за іменем функції чи файлу тут нічого не вирішується."""
        вміст = м.батько.get(id(в))
        власник = м.батько.get(id(вміст))
        if not isinstance(вміст, (ast.Tuple, ast.List, ast.Set)) or not isinstance(власник, ast.Assign) \
                or len(власник.targets) != 1 or not isinstance(власник.targets[0], ast.Name) \
                or not isinstance(м.батько.get(id(власник)), ast.Module):
            return False
        ім = власник.targets[0].id
        вжито = False
        for ін in self.модулі:
            for н in ін.вузли:
                if isinstance(н, ast.Attribute) and н.attr == ім:
                    return False
                if isinstance(н, ast.alias) and н.name == ім:
                    return False
                if not (isinstance(н, ast.Name) and н.id == ім) or н is власник.targets[0]:
                    continue
                цикл = ін.батько.get(id(н))
                if not (isinstance(цикл, ast.For) and цикл.iter is н and isinstance(цикл.target, ast.Name)):
                    return False
                зм = цикл.target.id
                for т in цикл.body:
                    for у in ast.walk(т):
                        if not (isinstance(у, ast.Name) and у.id == зм):
                            continue
                        б = ін.батько.get(id(у))
                        знято = (isinstance(б, ast.Call) and isinstance(б.func, ast.Attribute)
                                 and б.func.attr == "pop" and б.args and б.args[0] is у and len(б.args) == 2
                                 and isinstance(б.args[1], ast.Constant) and б.args[1].value is None)
                        видалено = isinstance(б, ast.Subscript) and б.slice is у \
                            and isinstance(ін.батько.get(id(б)), ast.Delete)
                        if not (знято or видалено):
                            return False
                вжито = True
        return вжито

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
                    if self.перелік_відкидання(м, в):
                        continue        # давній ключ знімають на вході — не читання градусів (рішення 05.11)
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
                if р == self.с.відчуття and isinstance(м.батько.get(id(в)), ast.Dict):
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
                    and рядок_константи(в.args[0]) == self.с.відчуття) or (
                    self.таблиця_відчуття(в) and isinstance(м.батько.get(id(в)), (ast.Subscript, ast.Attribute))):
                місце(в, 3, "відчуття → градуси (таблиця «%s»)" % self.с.відчуття)
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None and self.вид(м, в.value):
                місце(в, 2, "записано градуси")
            if isinstance(в, ast.Subscript) and рядок_константи(в.slice) in с.ПР:
                місце(в, 2, "прапорець походження градусів")
            if isinstance(в, ast.arg) and (в.arg in self.с.зерна or в.arg in с.ПР):
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
        return [к for к in в.keywords if к.arg in self.с.зерна and число_константи(к.value) is not None
                and (запис or к.arg in імена or арг.kwarg is not None)]

    def код_у_рядку(self, м, в, додати):
        """Python-код у рядку-шаблоні (стенд, що збирає скрипт текстом): його виклики з літералом градусів — місця
        на рядку файлу, де стоїть токен. Рядок, у якому є літерал градусів ключем, але код не розібрано, — обсяг
        не прочитано (Д10)."""
        р = в.value
        if not self.с.зерна:
            return
        літерал = re.compile(r"\b(%s)\s*=\s*[-+]?\d" % "|".join(map(re.escape, sorted(self.с.зерна))))
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
        токени = re.compile(r"\b(%s)\s*=\s*[-+]?\d" % "|".join(map(re.escape, sorted(self.с.зерна))))
        у_файлі = [(л, х.group(1)) for л in рядки if л <= len(м.рядки) for х in токени.finditer(м.рядки[л - 1])]
        for (_, _, арг), (де, _) in zip(у_коді, у_файлі):
            додати(м.шлях, де, 2, "літерал градусів «%s» у коді рядка-шаблону" % арг)

    def показ(self, м, в):
        """Текст із градусами — показ (картка, нотатка), коли рядок несе «°C»."""
        return any(isinstance(н, ast.Constant) and isinstance(н.value, str) and self.с.одиниця.search(н.value)
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


class АналізВітру(АналізПі):
    """Той самий потік для м/с; зерна — одиниця поля, суфікс одиниці й числовий ввід, а не назва таблиці."""

    def __init__(self, модулі, стан):
        super().__init__(модулі, стан)
        self.витоки = []
        self.джерела_мс = set()
        self.не_мс = set()
        for м in модулі:
            for в in м.вид("Compare"):
                сторони = [в.left] + list(в.comparators)
                if any((рядок_константи(з) or "") != "" or
                       (isinstance(з, (ast.Tuple, ast.List)) and з.elts and
                        all(рядок_константи(е) is not None for е in з.elts) and
                        any(рядок_константи(е) for е in з.elts)) for з in сторони):
                    self.не_мс.update(id(н) for н in ast.walk(в))
            for в in м.вузли:
                ім = в.arg if isinstance(в, (ast.arg, ast.keyword)) else в.id if isinstance(в, ast.Name) else \
                    в.attr if isinstance(в, ast.Attribute) else рядок_константи(в)
                if ім and МЕТРИ_ІМЯ.search(ім):
                    стан.зерна.add(ім)
            for ключ, значення in self.записи_ключів(м):
                if self.опис_мс(значення):
                    стан.зерна.add(ключ)
            for ф in м.функції:
                опис = (ast.get_docstring(ф) or "").splitlines()
                if МЕТРИ_ІМЯ.search(ф.name) or (опис and re.search(r"[→]|->", опис[0])
                                               and ВІТЕР_ТЕКСТ.search(опис[0])):
                    стан.Ф[ф.name] = "т"
                    self.витоки.extend((м, в.value) for в in ast.walk(ф) if isinstance(в, ast.Return)
                                       and м.функція_вузла(в) is ф and в.value is not None)
        стан.К.update(стан.зерна)
        # Писач поля в м/с задає одиницю результату; зворотний потік доходить до таблиці значень, але не до бала-індексу.
        for м in модулі:
            for ключ, значення in self.записи_ключів(м):
                if ключ in стан.К and not self.опис_мс(значення):
                    self.витоки.append((м, значення))
        for м, в in self.витоки:
            self.витік(м, в, None, set())

    @staticmethod
    def опис_мс(в):
        """Чи специфікація поля оголошує одиницю м/с (без слів про переклад бала)."""
        if not isinstance(в, (ast.Dict, ast.Call)):
            return False
        значення = в.values if isinstance(в, ast.Dict) else [к.value for к in в.keywords]
        рядки = [н.value for з in значення for н in (з.elts if isinstance(з, (ast.List, ast.Tuple)) else [з])
                 if isinstance(н, ast.Constant) and isinstance(н.value, str)]
        return any(ВІТЕР_ТЕКСТ.fullmatch(р.strip()) for р in рядки) or \
            (any(р in ("number", "integer", "float") for р in рядки)
             and any(ВІТЕР_ТЕКСТ.search(р) for р in рядки))

    def вид(self, м, в):
        """Одиниця джерела таблиці тече в її значення, а її бал чи слово-індекс одиниці не набуває."""
        if в is not None and id(в) in self.не_мс:
            return None
        if в is not None and (м.шлях, id(в)) in self.джерела_мс:
            return "т"
        return super().вид(м, в)

    def витік(self, м, в, додати, бачено):
        """Йде від запису м/с до виробника числа, позначає значення таблиці й пороги, не її індекс."""
        if в is None or (м.шлях, id(в)) in бачено:
            return
        бачено.add((м.шлях, id(в)))
        if isinstance(в, ast.Name):
            обл = м.область(в)
            if м.локальне(обл, в.id):
                запис = м.досяжне(обл, в.id, в)
                if запис and запис[2] == "знач":
                    self.витік(м, запис[1], додати, бачено)
                return
            г = self.глобальне(м, в.id)
            if г:
                for оп, значення, вид in г[0].присвоєння.get((None, г[1]), ()):
                    if вид == "знач":
                        self.витік(г[0], значення, додати, бачено)
            return
        if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name):
            мод = self.модуль_імені(м, в.value.id)
            if мод is not None:
                for _, значення, вид in мод.присвоєння.get((None, в.attr), ()):
                    if вид == "знач":
                        self.витік(мод, значення, додати, бачено)
            return
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if isinstance(в.func, ast.Attribute) and ім in ("get", "pop", "setdefault"):
                self.витік(м, в.func.value, додати, бачено)
                # Саме результат читання таблиці — м/с, аргумент (бал плитки) — ні.
                self.джерела_мс.add((м.шлях, id(в)))
                return
            if ім in ОБГОРТКИ or ім == "число":
                for арг in в.args:
                    self.витік(м, арг, додати, бачено)
                return
            ціль = self.функція_за_модулем(м, в) or self.єдина(ім)
            if ціль:
                зм, ф = ціль
                self.с.Ф[ф.name] = "т"
                for з in ast.walk(ф):
                    if isinstance(з, ast.Return) and зм.функція_вузла(з) is ф:
                        self.витік(зм, з.value, додати, бачено)
            return
        if isinstance(в, ast.Subscript):
            if рядок_константи(в.slice) not in self.с.К:
                self.джерела_мс.add((м.шлях, id(в)))
                if додати and self.ключі_ланцюга(в):
                    self.пороги(м, в, додати, "значення джерела м/с")
                else:
                    self.витік(м, в.value, додати, бачено)
            return
        if isinstance(в, ast.Dict):
            for значення in в.values:
                if додати and (число_константи(значення) is not None
                               or isinstance(значення, (ast.Name, ast.Attribute, ast.Subscript, ast.Call))):
                    додати(м.шлях, значення.lineno, 3, "значення таблиці → м/с вітру нагоди")
                    self.пороги(м, значення, додати, "значення таблиці м/с")
            return
        if isinstance(в, ast.IfExp):
            self.витік(м, в.body, додати, бачено)
            self.витік(м, в.orelse, додати, бачено)
        elif isinstance(в, (ast.BoolOp, ast.BinOp)):
            for з in ast.iter_child_nodes(в):
                if isinstance(з, ast.expr):
                    self.витік(м, з, додати, бачено)

    def джерела(self, додати):
        """Додає визначення виробників м/с до того самого переліку, що й прямий потік."""
        for м, в in self.витоки:
            self.витік(м, в, додати, set())

    def місця(self, м, додати, рішення):
        """Лічить м/с; порівняння зі словом смуги й властивістю тканини не є числовим вітром нагоди."""
        вузли = м.вузли
        try:
            м.вузли = [в for в in вузли if id(в) not in self.не_мс]
            super().місця(м, додати, рішення)
        finally:
            м.вузли = вузли
        for ключ, значення in self.записи_ключів(м):
            if ключ in self.с.К and self.опис_мс(значення):
                додати(м.шлях, значення.lineno, 1, "специфікація поля м/с «%s»" % ключ)
        for в in м.вузли:
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in м.докстрінги \
                    and ВІТЕР_ТЕКСТ.search(в.value):
                додати(м.шлях, в.lineno, 4, "текст одиниці м/с вітру нагоди")


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

    def __init__(self, шлях, текст, одиниця=ГРАДУС_ТЕКСТ):
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
                if ід and re.search(r"type=[\"']?number", тег) and одиниця.search(без):
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
            if all(стек) and (self.носій_токен(т[j], т[j - 1]) or (вв == "ряд" and self.с.одиниця.search(зз))
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
            elif вид == "ряд" and self.с.одиниця.search(зн):
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


# ── градуси її словами й словами моделі (п.2 — цитата поля, п.4 — шапка, п.3 — поріг текстом моделі) ──────────────
# Доповнення класу 15.11 (дошка 15497, #3888): смугу код тримав, а її слова з градусами йшли далі як є. Значення тут
# — слова, а не число, тож зерно — не ключ градусів, а поле смуги погоди (`смуга_погоди` паспорта, `weather_band`
# дроту й мовної моделі), чий уривок — її градуси («мінус десять», «+12 °C»), і вільний текст моделі про нього.
#   Ц  — плоска цитата паспорта (`цитати_полів` → `field_quotes` стилістці, `quotes` мовній моделі, «Твої слова»):
#        запис у колекцію плоских цитат з ключем поля погоди чи з ключем-змінною, якої на цьому шляху поле погоди не
#        минає. Колекція — індекс із ключем `цитати_полів`, її `setdefault`/`get` чи ім'я, присвоєне з них або
#        присвоєне назад у `…["цитати_полів"]`; JS — `….цитати_полів[к] = …`.
#   Д  — джерело поля (`sources[].quote`): виклик складача походження (функція, що пише параметр у ключ `quote`)
#        з її уривком поля в функції, загальній за полем (параметр-поле), — уривком факту картки (`["уривок"]`,
#        `.get("уривок")`) чи плоскою цитатою поля (`цитати_полів` + `.get(поле)`).
#   Ш  — шапка картки з тексту моделі: таблиця пар (ключ відповіді моделі, поле паспорта), з перших елементів якої код
#        будує схему відповіді вільним рядком (`{к: {"type": "string"} for к, _ in ТАБЛИЦЯ}`); пара з полем погоди —
#        місце (слова моделі про погоду — з її градусами — стоять у шапці над картками).
#   Ч  — читач уривка (рішення менеджера 15523, 15.11): уривок у факті картки (`картка_запиту.записати`, поле
#        `уривок`) і читачі, що звіряють його з її словами (`мовний_шар.тримається`) чи лічать силу факту за тим, чи
#        уривок є, — не місце; місце п.2 — читач, що дістає з уривка поля, яке може бути погодою, число (`float`,
#        `int`, `re.*` з `\d`/`[0-9]`, `.isdigit()`; JS `parseFloat`/`parseInt`/`Number`, `.match`/`.search`/`.exec`
#        з `\d`), і той, що несе його далі картки (Ц, Д).
#   Т  — поріг у °C текстом моделі: рядкова константа (не докстрінг) англійською (мова промптів і описів моделі,
#        `аудит/ПРОДУКТ.md` п.12), де стоїть число з °C («at +20 °C and warmer there is none»); рядок, що вчить
#        перевести градуси в код смуги (°C поруч із кодом смуги), — не місце (п.1).
# Поле погоди «минає» запис, коли умова на шляху до нього (`if`, `and`, JS `if (…)` / `&&`) для поля погоди хибна,
# чи коли кожен виклик функції-складача закінчується зняттям `quote` за умовою, істинною для поля погоди. Умову
# обчислено: порівняння з літералом чи переліком, виклик функції продукту з одним аргументом-полем (функцію
# виконано на дереві, що лічиться), JS — `(А.Б || []).includes(поле)`, де `А` — таблиця довідника, яку код Python
# кладе викликом функції продукту (`таблиці["факт_паспорта"] = К.політика()`). Не обчислено — місце (не менше місць).
ПОЛЕ_ПОГОДИ = ("смуга_погоди", "weather_band")
ЦИТАТИ = "цитати_полів"
УРИВОК = "уривок"
ЦИТАТА_ДЖЕРЕЛА = "quote"
ОПОРИ = "опори"
ЧИСЛО_ГРАДУСІВ = re.compile(r"[+\-−]?\d+(?:[.,]\d+)?\s?°\s?C\b")
КОДИ_СМУГ = re.compile(r"\b(?:deep_frost|frost|cold|cool|mild|warm|hot)\b")
ПОГОДА = ПОЛЕ_ПОГОДИ[0]


def _константа_є(вузол, значення):
    """Чи у виразі є рядкова константа `значення`."""
    return any(рядок_константи(в) == значення for в in ast.walk(вузол))


class Виконавець:
    """Функції продукту дерева, що лічиться: модуль — з його теки, вивід імпорту й виклику поглинуто."""

    def __init__(self, корінь):
        self.корінь = корінь
        self.модулі = {}
        self.помилки = []

    def модуль(self, шлях):
        if шлях in self.модулі:
            return self.модулі[шлях]
        import contextlib
        import importlib.util
        import io
        повний = os.path.join(self.корінь, шлях)
        тека = os.path.dirname(повний)
        ім = os.path.splitext(os.path.basename(шлях))[0]
        м = None
        було = list(sys.path)
        try:
            sys.path.insert(0, тека)
            # той самий модуль з іншої теки (інше дерево) — не наш
            for к, в in list(sys.modules.items()):
                ф = getattr(в, "__file__", None) or ""
                if ф and os.path.dirname(os.path.abspath(ф)) != os.path.abspath(тека) and \
                        os.path.exists(os.path.join(тека, к + ".py")):
                    del sys.modules[к]
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                if ім in sys.modules and os.path.abspath(getattr(sys.modules[ім], "__file__", "") or "") == \
                        os.path.abspath(повний):
                    м = sys.modules[ім]
                else:
                    сп = importlib.util.spec_from_file_location(ім, повний)
                    м = importlib.util.module_from_spec(сп)
                    sys.modules[ім] = м
                    сп.loader.exec_module(м)
        except Exception as е:      # не обчислено — місце лишається
            self.помилки.append("%s: імпорт: %s: %s" % (шлях, type(е).__name__, е))
            м = None
        finally:
            sys.path[:] = було
        self.модулі[шлях] = м
        return м

    def виклик(self, шлях, ім, *арг):
        import contextlib
        import io
        м = self.модуль(шлях)
        ф = getattr(м, ім, None) if м is not None else None
        if not callable(ф):
            return None, False
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                return ф(*арг), True
        except Exception as е:
            self.помилки.append("%s.%s%r: %s: %s" % (шлях, ім, арг, type(е).__name__, е))
            return None, False


class АналізСлів:
    """Ц, Д, Ш, Т — градуси її словами й словами моделі; місця — через `додати(файл, рядок, пункт, доказ)`."""

    def __init__(self, корінь, пі, джс):
        self.пі = пі
        self.джс = джс
        self.за_модулем = {}
        for м in пі:
            self.за_модулем.setdefault(м.ім_модуля, м)
        self.вик = Виконавець(корінь)
        self.лік = {"Ц": 0, "Д": 0, "Ш": 0, "Т": 0, "Ч": 0, "З": 0}
        # поля знахідки суду — з самого дерева (`знахідка.ЗМІСТОВІ`, `знахідка.ОБОВʼЯЗКОВІ`), рішення менеджера 15584
        зм = self.за_модулем.get("знахідка")
        self.змістові = tuple(self.глобальне(зм, "ЗМІСТОВІ") or ()) if зм else ()
        self.обовязкові = tuple(self.глобальне(зм, "ОБОВ\u02bcЯЗКОВІ") or ()) if зм else ()
        self.примітки = []

    # ── функції продукту за іменем у точці виклику ──
    def ціль(self, м, функ):
        """(Пі, ім'я функції) для `f` / `M.f` / `from m import f`; None — не функція продукту."""
        if isinstance(функ, ast.Name):
            if any(ф.name == функ.id for ф in м.функції if ф.col_offset == 0):
                return м, функ.id
            імп = м.імпорти.get(функ.id)
            if імп and імп[1] and імп[0] in self.за_модулем:
                return self.за_модулем[імп[0]], імп[1]
        elif isinstance(функ, ast.Attribute) and isinstance(функ.value, ast.Name):
            імп = м.імпорти.get(функ.value.id)
            if імп and імп[1] is None and імп[0] in self.за_модулем:
                return self.за_модулем[імп[0]], функ.attr
        return None

    def глобальне(self, м, ім):
        """Значення літерала рівня модуля (кортеж, список, множина рядків) чи None."""
        for в in м.дерево.body:
            if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets):
                try:
                    return ast.literal_eval(в.value)
                except (ValueError, SyntaxError, TypeError):
                    return None
        return None

    # ── умова для поля погоди: True / False / None (не обчислено) ──
    def умова(self, м, умова, поле):
        if isinstance(умова, ast.BoolOp):
            значення = [self.умова(м, з, поле) for з in умова.values]
            if isinstance(умова.op, ast.And):
                return False if False in значення else (True if all(з is True for з in значення) else None)
            return True if True in значення else (False if all(з is False for з in значення) else None)
        if isinstance(умова, ast.UnaryOp) and isinstance(умова.op, ast.Not):
            з = self.умова(м, умова.operand, поле)
            return None if з is None else not з
        if isinstance(умова, ast.Compare) and len(умова.ops) == 1 and isinstance(умова.left, ast.Name) \
                and умова.left.id == поле:
            інше = умова.comparators[0]
            оп = умова.ops[0]
            if isinstance(оп, (ast.Eq, ast.NotEq)) and рядок_константи(інше) is not None:
                return (рядок_константи(інше) in ПОЛЕ_ПОГОДИ) == isinstance(оп, ast.Eq)
            if isinstance(оп, (ast.In, ast.NotIn)):
                try:
                    кол = ast.literal_eval(інше)
                except (ValueError, SyntaxError, TypeError):
                    кол = self.глобальне(м, інше.id) if isinstance(інше, ast.Name) else None
                if isinstance(кол, (tuple, list, set, frozenset, dict)):
                    return (ПОГОДА in кол) == isinstance(оп, ast.In)
            return None
        if isinstance(умова, ast.Call) and len(умова.args) == 1 and not умова.keywords \
                and isinstance(умова.args[0], ast.Name) and умова.args[0].id == поле:
            ц = self.ціль(м, умова.func)
            if ц:
                з, ок = self.вик.виклик(ц[0].шлях, ц[1], ПОГОДА)
                return bool(з) if ок else None
        return None

    def згадує(self, вузол, поле):
        return any(isinstance(в, ast.Name) and в.id == поле for в in ast.walk(вузол))

    def минає(self, м, вузол, поле):
        """Чи умова на шляху до вузла (у його функції) для поля погоди хибна."""
        б, дитина = м.батько.get(id(вузол)), вузол
        while б is not None and not isinstance(б, ОБЛАСТІ):
            if isinstance(б, (ast.If, ast.IfExp)) and дитина is not б.test and self.згадує(б.test, поле):
                з = self.умова(м, б.test, поле)
                в_тілі = (дитина in б.body) if isinstance(б, ast.If) else (дитина is б.body)
                if з is (not в_тілі) or (з is False and в_тілі):
                    return True
                if в_тілі and isinstance(б.test, ast.BoolOp) and isinstance(б.test.op, ast.And) and \
                        any(self.згадує(з_, поле) and self.умова(м, з_, поле) is False for з_ in б.test.values):
                    return True
            б, дитина = м.батько.get(id(б)), б
        return False

    # ── Ц: плоска цитата ──
    def колекція(self, м, вираз, вузол):
        """Чи вираз — колекція плоских цитат."""
        if isinstance(вираз, ast.Subscript) and рядок_константи(вираз.slice) == ЦИТАТИ:
            return True
        if isinstance(вираз, ast.Call) and isinstance(вираз.func, ast.Attribute) and \
                вираз.func.attr in ("setdefault", "get") and вираз.args and рядок_константи(вираз.args[0]) == ЦИТАТИ:
            return True
        if isinstance(вираз, ast.Name):
            обл = м.область(вузол)
            д = м.досяжне(обл, вираз.id, вузол)
            if д and д[1] is not None and д[2] == "знач" and _константа_є(д[1], ЦИТАТИ):
                return True
            # ім'я, яке присвоюють назад у `…["цитати_полів"]` у тій самій області
            for в in м.вид("Assign"):
                if м.область(в) is обл and isinstance(в.value, ast.Name) and в.value.id == вираз.id and any(
                        isinstance(ц, ast.Subscript) and рядок_константи(ц.slice) == ЦИТАТИ for ц in в.targets):
                    return True
        return False

    def цитати_пі(self, м, додати):
        for в in м.вид("Assign"):
            for ц in в.targets:
                if not (isinstance(ц, ast.Subscript) and self.колекція(м, ц.value, в)):
                    continue
                ключ = ц.slice
                к = рядок_константи(ключ)
                if к is not None:
                    if к in ПОЛЕ_ПОГОДИ:
                        додати(м.шлях, в.lineno, 2, "плоска цитата поля погоди «%s» (її градуси словами)" % к)
                        self.лік["Ц"] += 1
                    continue
                поле = ключ.id if isinstance(ключ, ast.Name) else None
                if поле and self.минає(м, в, поле):
                    continue
                додати(м.шлях, в.lineno, 2, "плоска цитата поля з ключем `%s`, який поле погоди не минає "
                       "(її градуси словами → field_quotes / «Твої слова»)" % (поле or ast.unparse(ключ)))
                self.лік["Ц"] += 1

    # ── Д: джерело поля з `quote` ──
    def складачі(self):
        """{(шлях, функція): номер параметра}, що пишеться в `quote` результату."""
        вих = {}
        for м in self.пі:
            for ф in м.функції:
                пар = м.параметри.get(id(ф), [])
                for в in ast.walk(ф):
                    ім = None
                    if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Subscript) and
                                                         рядок_константи(ц.slice) == ЦИТАТА_ДЖЕРЕЛА for ц in в.targets):
                        ім = в.value.id if isinstance(в.value, ast.Name) else None
                    elif isinstance(в, ast.Dict):
                        for к, з in zip(в.keys, в.values):
                            if к is not None and рядок_константи(к) == ЦИТАТА_ДЖЕРЕЛА and isinstance(з, ast.Name):
                                ім = з.id
                    if ім in пар:
                        вих[(м.шлях, ф.name)] = пар.index(ім)
        return вих

    def уривок_поля(self, м, вираз, вузол, поле):
        """Чи вираз — її уривок поля: уривок факту чи плоска цитата поля (`цитати_полів` … `.get(поле)`)."""
        if _константа_є(вираз, УРИВОК):
            return True
        if isinstance(вираз, ast.Name):
            д = м.досяжне(м.область(вузол), вираз.id, вузол)
            if д and д[1] is not None and д[2] == "знач":
                return _константа_є(д[1], УРИВОК) or (_константа_є(д[1], ЦИТАТИ) and self.згадує(д[1], поле))
        return False

    def ключ_запису(self, ф, п):
        """Чи параметр `п` — ключ запису у функції: індекс `[п]` чи перший аргумент `.get(п)`."""
        for в in ast.walk(ф):
            if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Name) and в.slice.id == п:
                return True
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                    and isinstance(в.args[0], ast.Name) and в.args[0].id == п:
                return True
        return False

    def знято_обгорткою(self, м, ф, поле_ф):
        """Чи кожен виклик функції `ф` — `V = ф(…)`, після якого `V.pop("quote")` за умовою, істинною для погоди."""
        викликів = 0
        for мм in self.пі:
            for в in мм.вид("Call"):
                ц = self.ціль(мм, в.func)
                if ц != (м, ф.name):
                    continue
                викликів += 1
                ст = мм.батько.get(id(в))
                if not (isinstance(ст, ast.Assign) and len(ст.targets) == 1 and isinstance(ст.targets[0], ast.Name)):
                    return False
                змінна = ст.targets[0].id
                обг = мм.функція_вузла(в)
                if обг is None:
                    return False
                номер = м.параметри.get(id(ф), []).index(поле_ф)
                поле_о = в.args[номер].id if номер < len(в.args) and isinstance(в.args[номер], ast.Name) else None
                знято = False
                for і in ast.walk(обг):
                    if isinstance(і, ast.If) and поле_о and self.згадує(і.test, поле_о) and \
                            self.умова(мм, і.test, поле_о) is True and і.lineno > в.lineno:
                        for п in ast.walk(і):
                            if isinstance(п, ast.Call) and isinstance(п.func, ast.Attribute) and п.func.attr == "pop" \
                                    and isinstance(п.func.value, ast.Name) and п.func.value.id == змінна and \
                                    п.args and рядок_константи(п.args[0]) == ЦИТАТА_ДЖЕРЕЛА:
                                знято = True
                if not знято:
                    return False
        return викликів > 0

    # ── вкладене джерело: `опори` факту картки (її слова по частинах складеного поля) ──
    def з_опор(self, м, виклик):
        """Чи виклик складача стоїть у вкладеному записі, що ітерує `…["опори"]` / `.get("опори")` факту."""
        б = м.батько.get(id(виклик))
        while б is not None and not isinstance(б, ОБЛАСТІ):
            ітери = []
            if isinstance(б, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
                ітери = [г.iter for г in б.generators]
            elif isinstance(б, (ast.For, ast.AsyncFor)):
                ітери = [б.iter]
            if any(isinstance(в, ast.Constant) and в.value == ОПОРИ for і in ітери for в in ast.walk(і)):
                return True
            б = м.батько.get(id(б))
        return False

    def писачі_опор(self):
        """Усі записи ключа `опори`: модуль, вузол, значення та можливі поля факту.

        Невідоме поле лишається None: другий писач не може зникнути через форму значення чи відсутність параметра.
        """
        вих = []
        for м in self.пі:
            for в in м.вид("Assign", "AnnAssign"):
                for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                    if isinstance(ц, ast.Subscript) and рядок_константи(ц.slice) == ОПОРИ:
                        вих.append((м, в, в.value, self.поля_факту(м, ц.value)))
            for в in м.вид("Dict"):
                б = м.батько.get(id(в))
                if isinstance(б, ast.keyword) and б.arg is None:
                    continue  # пакет аргументів — не сам запис факту; його розбирає аргументи_опор
                for к, з in zip(в.keys, в.values):
                    if к is not None and рядок_константи(к) == ОПОРИ:
                        вих.append((м, в, з, self.поля_факту(м, в)))
            for в in м.вид("Call"):
                if isinstance(в.func, ast.Name) and в.func.id == "dict":
                    for к in в.keywords:
                        if к.arg == ОПОРИ:
                            вих.append((м, в, к.value, self.поля_факту(м, в)))
        return вих

    def поля_факту(self, м, вираз, слід=frozenset()):
        """Ключі записів, куди потрапляє факт; невідоме розміщення не доводить відсутності погоди."""
        if id(вираз) in слід:
            return [None]
        слід = слід | {id(вираз)}
        if isinstance(вираз, ast.Subscript):
            return [вираз.slice]
        if isinstance(вираз, ast.Name):
            поля = []
            for в in м.вид("Assign", "AnnAssign"):
                if м.область(в) is м.область(вираз) and isinstance(в.value, ast.Name) and в.value.id == вираз.id:
                    for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                        поля += self.поля_факту(м, ц, слід)
            return поля or [None]
        б = м.батько.get(id(вираз))
        if isinstance(б, (ast.Assign, ast.AnnAssign)):
            return [п for ц in (б.targets if isinstance(б, ast.Assign) else [б.target])
                    for п in self.поля_факту(м, ц, слід)]
        if isinstance(б, ast.Dict):
            return [к for к, з in zip(б.keys, б.values) if з is вираз] or [None]
        return [None]

    def досяжне_опор(self, м, ім, вузол):
        """Останнє присвоєння перед точкою, зокрема всередині циклу; умовне поза шляхом — невідоме."""
        обл = м.область(вузол)
        записи = []
        for оп, знач, вид in м.присвоєння.get((id(обл) if обл is not None else None, ім), ()):
            if м.усередині(вузол, оп):
                if вид in ("цикл", "ген") and not м.усередині(вузол, знач):
                    записи.append((оп, знач, "цикл"))
            elif (getattr(оп, "end_lineno", оп.lineno), getattr(оп, "end_col_offset", 0)) <= \
                    (вузол.lineno, вузол.col_offset):
                записи.append((оп, знач, вид))
        if not записи:
            return None
        оп, знач, вид = max(записи, key=lambda з: (з[0].lineno, з[0].col_offset))
        б = м.батько.get(id(оп))
        while б is not None and б is not обл:
            if isinstance(б, (ast.If, ast.Try, ast.Match, ast.For, ast.AsyncFor, ast.While)) and \
                    not м.усередині(вузол, б):
                return оп, None, "інше"
            if isinstance(б, ast.If) and м.усередині(вузол, б):
                в_тілі = any(м.усередині(оп, д) for д in б.body)
                вузол_в_тілі = any(м.усередині(вузол, д) for д in б.body)
                if в_тілі != вузол_в_тілі:
                    return оп, None, "інше"
            б = м.батько.get(id(б))
        return оп, знач, вид

    def значення_опор(self, м, вираз, вузол, звязки, слід=frozenset()):
        """Можливі значення виразу; Ellipsis означає невідоме, яке не можна використати для вилучення місця."""
        if вираз is None or id(вираз) in слід:
            return [Ellipsis]
        слід = слід | {id(вираз)}
        try:
            return [ast.literal_eval(вираз)]
        except (ValueError, SyntaxError, TypeError):
            pass
        if isinstance(вираз, ast.Name):
            д = self.досяжне_опор(м, вираз.id, вузол)
            if д:
                оп, знач, вид = д
                з = self.значення_опор(м, знач, оп, звязки, слід)
                if вид == "цикл":
                    return [к for кол in з for к in (кол if isinstance(кол, (tuple, list, set, frozenset, dict))
                                                    else [Ellipsis])] or [Ellipsis]
                return з
            if вираз.id in звязки:
                мм, з, точка = звязки[вираз.id]
                return self.значення_опор(мм, з, точка, {}, слід)
            if not м.локальне(м.область(вузол), вираз.id):
                з = self.глобальне(м, вираз.id)
                if з is not None:
                    return [з]
            return [Ellipsis]
        if isinstance(вираз, (ast.BoolOp, ast.IfExp)):
            вирази = вираз.values if isinstance(вираз, ast.BoolOp) else [вираз.body, вираз.orelse]
            return [з for в in вирази for з in self.значення_опор(м, в, вузол, звязки, слід)]
        if isinstance(вираз, (ast.List, ast.Tuple, ast.Set)):
            return [[Ellipsis] if вираз.elts else []]
        if isinstance(вираз, ast.Dict):
            return [Ellipsis] if None in вираз.keys else [{і: Ellipsis for і in range(len(вираз.keys))}]
        if isinstance(вираз, ast.Call):
            ім = вираз.func.id if isinstance(вираз.func, ast.Name) else \
                вираз.func.attr if isinstance(вираз.func, ast.Attribute) else None
            if ім in ("list", "tuple", "set", "frozenset", "deepcopy", "copy") and len(вираз.args) == 1:
                return self.значення_опор(м, вираз.args[0], вузол, звязки, слід)
        return [Ellipsis]

    def аргументи_опор(self, м, виклик, ціль, ф):
        """Зв'язує параметри з позиційними й іменованими аргументами, **словником та типовими значеннями."""
        а = ф.args
        позиційні = а.posonlyargs + а.args
        типові = {п.arg: з for п, з in zip(позиційні[-len(а.defaults):], а.defaults)} if а.defaults else {}
        типові.update({п.arg: з for п, з in zip(а.kwonlyargs, а.kw_defaults) if з is not None})
        задані, невідомі = {}, False
        for п, з in zip(позиційні, виклик.args):
            if isinstance(з, ast.Starred):
                невідомі = True
                break
            задані[п.arg] = з
        for к in виклик.keywords:
            if к.arg is not None:
                задані[к.arg] = к.value
            elif isinstance(к.value, ast.Dict) and all(рядок_константи(з) is not None for з in к.value.keys):
                задані.update({рядок_константи(з): в for з, в in zip(к.value.keys, к.value.values)})
            else:
                невідомі = True
        return {п.arg: (м, задані[п.arg], виклик) if п.arg in задані else
                (м, None, виклик) if невідомі or п.arg not in типові else (ціль, типові[п.arg], ф)
                for п in позиційні + а.kwonlyargs}

    def поле_виклику(self, м, вузол, арг, звязки):
        """Чи хоч одне досяжне значення поля є погодою або невідомим."""
        return any(з is Ellipsis or not isinstance(з, str) or з in ПОЛЕ_ПОГОДИ
                   for з in self.значення_опор(м, арг, вузол, звязки))

    def опори_без_погоди(self):
        """True лише коли кожен писач у всіх відомих викликах доведено не дає опор полю погоди."""
        писачі = self.писачі_опор()
        if not писачі:
            return None
        for м, вузол, опори, поля in писачі:
            ф = м.функція_вузла(вузол)
            контексти = [self.аргументи_опор(мм, в, м, ф) for мм in self.пі for в in мм.вид("Call")
                         if ф is not None and self.ціль(мм, в.func) == (м, ф.name)] or [{}]
            for звязки in контексти:
                if not any(з is Ellipsis or bool(з) for з in self.значення_опор(м, опори, вузол, звязки)):
                    continue
                if any(self.поле_виклику(м, вузол, поле, звязки) for поле in поля):
                    return False
        return True

    def джерела_пі(self, додати):
        складачі = self.складачі()
        for м in self.пі:
            for в in м.вид("Call"):
                ц = self.ціль(м, в.func)
                if not ц or (ц[0].шлях, ц[1]) not in складачі:
                    continue
                номер = складачі[(ц[0].шлях, ц[1])]
                if номер >= len(в.args):
                    continue
                ф = м.функція_вузла(в)
                if ф is None or ф.name == ц[1]:
                    continue
                # функція загальна за полем: параметр, яким беруть запис (`[поле]`, `.get(поле)`)
                ключі = [п for п in м.параметри.get(id(ф), []) if self.ключ_запису(ф, п)]
                поле = next((п for п in ключі if self.уривок_поля(м, в.args[номер], в, п)), None)
                if поле is None:
                    continue
                if self.минає(м, в, поле):
                    continue
                # обгортка знімає `quote` лише з запису, який функція повертає, — не з вкладених (`parts`)
                ст = м.батько.get(id(в))
                верхній = isinstance(ст, ast.Assign) and len(ст.targets) == 1 and isinstance(ст.targets[0], ast.Name) \
                    and any(isinstance(р, ast.Return) and isinstance(р.value, ast.Name) and р.value.id == ст.targets[0].id
                            for р in ast.walk(ф))
                if верхній and self.знято_обгорткою(м, ф, поле):
                    continue
                # вкладений запис `parts` читають з `опори` факту картки: він несе її слова лише там, куди писач `опори`
                # може покласти поле погоди (писач, якого не знайдено чи не обчислено, — місце)
                if self.з_опор(м, в) and self.опори_без_погоди() is True:
                    continue
                додати(м.шлях, в.lineno, 2, "джерело поля `quote` з її уривком (`%s(…)` у `%s`), який поле "
                       "погоди не минає (її градуси словами → sources[].quote)" % (ц[1], ф.name))
                self.лік["Д"] += 1

    # ── Ш: шапка з вільного тексту моделі ──
    def шапки_пі(self, додати):
        таблиці = set()
        for м in self.пі:
            for в in м.вид("DictComp"):
                if not (isinstance(в.value, ast.Dict) and any(рядок_константи(к) == "type" and рядок_константи(з) ==
                                                                "string" for к, з in zip(в.value.keys, в.value.values))
                        and not any(рядок_константи(к) == "enum" for к in в.value.keys)):
                    continue
                for ген in в.generators:
                    і = ген.iter
                    if isinstance(і, ast.Attribute) and isinstance(і.value, ast.Name):
                        імп = м.імпорти.get(і.value.id)
                        if імп and імп[1] is None and імп[0] in self.за_модулем:
                            таблиці.add((self.за_модулем[імп[0]].шлях, і.attr))
                    elif isinstance(і, ast.Name):
                        імп = м.імпорти.get(і.id)
                        if імп and імп[1] and імп[0] in self.за_модулем:
                            таблиці.add((self.за_модулем[імп[0]].шлях, імп[1]))
                        else:
                            таблиці.add((м.шлях, і.id))
        for м in self.пі:
            for в in м.дерево.body:
                if not isinstance(в, ast.Assign):
                    continue
                for ц in в.targets:
                    if isinstance(ц, ast.Name) and (м.шлях, ц.id) in таблиці and isinstance(в.value, (ast.Tuple, ast.List)):
                        for е in в.value.elts:
                            if isinstance(е, (ast.Tuple, ast.List)) and any(рядок_константи(х) in ПОЛЕ_ПОГОДИ
                                                                          for х in е.elts):
                                додати(м.шлях, е.lineno, 4, "шапка картки словами моделі про погоду (`%s`: вільний "
                                       "рядок відповіді моделі → поле погоди; її градуси в шапці)" % ц.id)
                                self.лік["Ш"] += 1

    # ── Т: поріг у °C текстом моделі ──
    def тексти_пі(self, м, додати):
        for в in м.вид("Constant"):
            if not isinstance(в.value, str) or id(в) in м.докстрінги or not ЧИСЛО_ГРАДУСІВ.search(в.value):
                continue
            for н in range(в.lineno, (в.end_lineno or в.lineno) + 1):
                р = м.рядки[н - 1] if 0 < н <= len(м.рядки) else ""
                # шматок у лапках, де стоїть число з °C (коментар рядка — не текст)
                шматок = next((с.group(2) for с in re.finditer(r"([\"'])((?:\\.|(?!\1).)*)\1", р)
                               if ЧИСЛО_ГРАДУСІВ.search(с.group(2))), None)
                if шматок is None:
                    continue
                мм = ЧИСЛО_ГРАДУСІВ.search(шматок)
                if len(re.findall(r"[A-Za-z]", шматок)) <= len(re.findall(r"[А-Яа-яЇїІіЄєҐґ]", шматок)):
                    continue        # українською — примітка чи текст жінці, не мова моделі
                if КОДИ_СМУГ.search(шматок) and re.search(r"→|=>|->", шматок):
                    continue        # п.1: вчить перевести градуси в код смуги
                додати(м.шлях, н, 3, "поріг у °C текстом моделі: «%s»" % мм.group(0))
                self.лік["Т"] += 1

    # ── З: градуси в змістовому полі знахідки суду (рішення менеджера 15584) ──
    # Чи рядок із числом °C — місце, вирішує читач рядка, а не мова. Змістові поля знахідки («суть», «чому» —
    # `знахідка.ЗМІСТОВІ`) читає запит стилістки, тож рядок з °C, що в них іде (прямо, через змінну чи через ключ
    # словника, який код у них вкладає), — п.2, а коли поле читає показ (JS) — ще й п.4. Інше текстове поле
    # конструктора знахідки (`ламається` → `де_ламається`) — місце, лише коли його ключ читає показ; інакше — примітка
    # з переліком читачів. Рядок без такого читача (примітка реєстру, опис поля, текст стенда) — не місце.
    def функція(self, м, ім, глиб=0):
        """(Пі, FunctionDef) верхнього рівня за іменем — з переходом за реекспортом `from m import ім`."""
        for ф in м.функції:
            if ф.col_offset == 0 and ф.name == ім:
                return м, ф
        імп = м.імпорти.get(ім)
        if глиб < 4 and імп and імп[1] and імп[0] in self.за_модулем:
            return self.функція(self.за_модулем[імп[0]], імп[1], глиб + 1)
        return None

    def ціль_ф(self, м, функ):
        if isinstance(функ, ast.Name):
            return self.функція(м, функ.id)
        if isinstance(функ, ast.Attribute) and isinstance(функ.value, ast.Name):
            імп = м.імпорти.get(функ.value.id)
            if імп and імп[1] is None and імп[0] in self.за_модулем:
                return self.функція(self.за_модулем[імп[0]], функ.attr)
        return None

    def форма_знахідки(self, в):
        """{ключ: вираз} словника у формі знахідки (є обов'язкові ключі й хоч один змістовий) чи None."""
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
            пари = {к.arg: к.value for к in в.keywords if к.arg}
        elif isinstance(в, ast.Dict):
            пари = {рядок_константи(к): з for к, з in zip(в.keys, в.values)
                    if к is not None and рядок_константи(к) is not None}
        else:
            return None
        if all(к in пари for к in self.обовязкові) and any(к in пари for к in self.змістові):
            return пари
        return None

    @staticmethod
    def цілим(з):
        """Імена, що стають значенням поля цілими: `п`, `п or …`, `… if … else п` (не вкладені у формат чи виклик)."""
        if isinstance(з, ast.Name):
            return {з.id}
        if isinstance(з, ast.BoolOp):
            return set().union(*(АналізСлів.цілим(х) for х in з.values))
        if isinstance(з, ast.IfExp):
            return АналізСлів.цілим(з.body) | АналізСлів.цілим(з.orelse)
        return set()

    def конструктори(self):
        """{(шлях, ім'я): ({позиція: параметр}, {змістові параметри}, {інший параметр: ключ запису})} — функції, що
        вкладають параметр у змістове поле знахідки: словником у формі знахідки, через інший конструктор чи
        пересиланням `*a, **kw`; до нерухомої точки."""
        к = {}
        змінено = True
        while змінено:
            змінено = False
            for м in self.пі:
                for ф in м.функції:
                    if ф.col_offset:
                        continue
                    а = ф.args
                    поз = [п.arg for п in а.posonlyargs + а.args]
                    усі = set(поз + [п.arg for п in а.kwonlyargs])
                    зм, інші, переслано = set(), {}, None
                    for в in ast.walk(ф):
                        пари = self.форма_знахідки(в)
                        for ключ, з in (пари or {}).items():
                            if ключ in self.змістові:
                                зм |= self.цілим(з) & усі
                        if isinstance(в, ast.Assign) and isinstance(в.value, ast.Name) and в.value.id in усі:
                            for ц in в.targets:
                                if isinstance(ц, ast.Subscript) and рядок_константи(ц.slice):
                                    інші.setdefault(в.value.id, рядок_константи(ц.slice))
                        if not isinstance(в, ast.Call):
                            continue
                        ц = self.ціль_ф(м, в.func)
                        інфо = к.get((ц[0].шлях, ц[1].name)) if ц and ц[1] is not ф else None
                        if not інфо:
                            continue
                        if а.vararg and а.kwarg and \
                                any(isinstance(х, ast.Starred) and isinstance(х.value, ast.Name) and
                                    х.value.id == а.vararg.arg for х in в.args) and \
                                any(кв.arg is None and isinstance(кв.value, ast.Name) and кв.value.id == а.kwarg.arg
                                    for кв in в.keywords):
                            переслано = інфо
                            continue
                        for і, арг in enumerate(в.args):
                            if isinstance(арг, ast.Starred):
                                break
                            if інфо[0].get(і) in інфо[1]:
                                зм |= self.цілим(арг) & усі
                        for кв in в.keywords:
                            if кв.arg in інфо[1]:
                                зм |= self.цілим(кв.value) & усі
                    нове = переслано or ((dict(enumerate(поз)), зм, {п: кл for п, кл in інші.items() if п not in зм})
                                         if зм else None)
                    if нове and к.get((м.шлях, ф.name)) != нове:
                        к[(м.шлях, ф.name)] = нове
                        змінено = True
        return к

    def читання_ключа(self, в):
        """Ключ константи в читанні `X["K"]` / `X.get("K")` чи None."""
        if isinstance(в, ast.Subscript) and isinstance(в.ctx, ast.Load) and рядок_константи(в.slice):
            return рядок_константи(в.slice)
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args and \
                рядок_константи(в.args[0]):
            return рядок_константи(в.args[0])
        return None

    def записи_ключа(self, м, ключ):
        """Значення, що модуль кладе під ключ: `dict(K=…)`, `{"K": …}`, `X["K"] = …`."""
        вих = []
        for в in м.вид("Call", "Dict", "Assign"):
            if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
                вих += [кв.value for кв in в.keywords if кв.arg == ключ]
            elif isinstance(в, ast.Dict):
                вих += [з for к, з in zip(в.keys, в.values) if к is not None and рядок_константи(к) == ключ]
            elif isinstance(в, ast.Assign) and any(isinstance(ц, ast.Subscript) and рядок_константи(ц.slice) == ключ
                                                   for ц in в.targets):
                вих.append(в.value)
        return вих

    def градуси_виразу(self, м, вираз):
        """Рядкові константи з числом °C, що йдуть у вираз: прямо, через змінну, через ключ словника модуля."""
        вих, бачені = [], set()

        def іти(в, глиб):
            for х in ast.walk(в):
                if isinstance(х, ast.Constant) and isinstance(х.value, str) and id(х) not in м.докстрінги and \
                        ЧИСЛО_ГРАДУСІВ.search(х.value):
                    if id(х) not in бачені:
                        бачені.add(id(х))
                        вих.append(х)
                elif isinstance(х, ast.Name) and глиб < 2:
                    д = м.досяжне(м.область(х), х.id, х)
                    if д and д[1] is not None and д[2] == "знач" and ("ім", id(д[1])) not in бачені:
                        бачені.add(("ім", id(д[1])))
                        іти(д[1], глиб + 1)
                elif глиб == 0 and self.читання_ключа(х) and ("ключ", self.читання_ключа(х)) not in бачені:
                    # один перехід ключем: значення, яке код поля читає зі словника модуля (не ланцюг ключів)
                    бачені.add(("ключ", self.читання_ключа(х)))
                    for з in self.записи_ключа(м, self.читання_ключа(х)):
                        іти(з, глиб + 1)
        іти(вираз, 0)
        return вих

    def читачі_ключа(self, ключ):
        """(Python [файл:рядок], показ [файл:рядок]) — читання ключа: `["K"]` / `.get("K")`; JS `.K` / `["K"]`."""
        пі, показ = [], []
        for м in self.пі:
            for в in м.вид("Subscript", "Call"):
                if self.читання_ключа(в) == ключ:
                    пі.append("%s:%d" % (м.шлях, в.lineno))
        for ф in self.джс:
            т = ф.т
            for і in range(1, len(т)):
                if т[і][1] != ключ:
                    continue
                if т[і][0] == "ім" and т[і - 1][1] == "." and not (і + 1 < len(т) and т[і + 1][:2] == ("оп", "=")):
                    показ.append("%s:%d" % (ф.шлях, т[і][2]))
                elif т[і][0] == "ряд" and т[і - 1][1] == "[" and і + 1 < len(т) and т[і + 1][1] == "]" and \
                        not (і + 2 < len(т) and т[і + 2][:2] == ("оп", "=")):
                    показ.append("%s:%d" % (ф.шлях, т[і][2]))
        return sorted(set(пі)), sorted(set(показ))

    def знахідки_пі(self, додати):
        if not self.змістові:
            return
        к = self.конструктори()
        показ_змісту = {кл: bool(self.читачі_ключа(кл)[1]) for кл in self.змістові}
        читачі = {}
        for м in self.пі:
            for в in м.вид("Call", "Dict"):
                вирази = [(з, ключ, None) for ключ, з in (self.форма_знахідки(в) or {}).items()
                          if ключ in self.змістові]
                ц = self.ціль_ф(м, в.func) if isinstance(в, ast.Call) else None
                інфо = к.get((ц[0].шлях, ц[1].name)) if ц else None
                if інфо:
                    поз, зм, інші = інфо
                    for і, арг in enumerate(в.args):
                        if isinstance(арг, ast.Starred):
                            break
                        п = поз.get(і)
                        if п in зм or п in інші:
                            вирази.append((арг, п, None if п in зм else інші[п]))
                    for кв in в.keywords:
                        if кв.arg in зм or кв.arg in інші:
                            вирази.append((кв.value, кв.arg, None if кв.arg in зм else інші[кв.arg]))
                for вираз, поле, ключ in вирази:
                    for конст in self.градуси_виразу(м, вираз):
                        мм = ЧИСЛО_ГРАДУСІВ.search(конст.value)
                        рядки = м.рядки_токена(конст, мм.group(0))
                        if ключ is not None:
                            if ключ not in читачі:
                                читачі[ключ] = self.читачі_ключа(ключ)
                            пі, показ = читачі[ключ]
                            if not показ:
                                self.примітки.append((м.шлях, рядки[0], поле, ключ, мм.group(0), пі))
                                continue
                            пункти = (2, 4)
                            доказ = "°C у полі «%s» знахідки, ключ `%s` читає показ (%s): «%s»" % (
                                поле, ключ, ", ".join(показ[:3]), мм.group(0))
                        else:
                            пункти = (2, 4) if показ_змісту.get(поле) else (2,)
                            доказ = "°C у змістовому полі «%s» знахідки суду (до запиту стилістки): «%s»" % (
                                поле, мм.group(0))
                        for н in рядки:
                            for п in пункти:
                                додати(м.шлях, н, п, доказ)
                        self.лік["З"] += 1

    # ── Ч: число з уривка ──
    ЧИСЛОВІ_ПІ = {"float", "int", "Decimal"}
    ЧИСЛОВІ_RE = {"search", "findall", "match", "fullmatch", "finditer", "sub", "split"}

    def читання_уривка(self, в):
        """Чи вузол — читання уривка: `X["уривок"]` чи `X.get("уривок")`."""
        if isinstance(в, ast.Subscript) and рядок_константи(в.slice) == УРИВОК and isinstance(в.ctx, ast.Load):
            return в.value
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args and \
                рядок_константи(в.args[0]) == УРИВОК:
            return в.func.value
        return None

    def уривки_виразу(self, м, вираз, вузол):
        """[(контейнер, вузол-читання)] уривків у виразі — прямо чи через ім'я, присвоєне з читання."""
        вих = []
        for в in ast.walk(вираз):
            к = self.читання_уривка(в)
            if к is not None:
                вих.append((к, в))
            elif isinstance(в, ast.Name):
                д = м.досяжне(м.область(вузол), в.id, вузол)
                if д and д[1] is not None and д[2] == "знач":
                    вих += [(self.читання_уривка(х), х) for х in ast.walk(д[1]) if self.читання_уривка(х) is not None]
        return вих

    def може_бути_погодою(self, м, контейнер, вузол):
        """Поле факту, чий уривок читають: погода, інше поле (літерал) чи змінна, якої погода не минає."""
        рядки = [рядок_константи(х) for х in ast.walk(контейнер) if рядок_константи(х) is not None]
        if any(р in ПОЛЕ_ПОГОДИ for р in рядки):
            return True
        if any(р not in ("картка_запиту", ЦИТАТИ, УРИВОК) for р in рядки):
            return False
        імена = {х.id for х in ast.walk(контейнер) if isinstance(х, ast.Name)}
        for ім in list(імена):
            д = м.досяжне(м.область(вузол), ім, вузол)
            if д and д[1] is not None:
                імена |= {х.id for х in ast.walk(д[1]) if isinstance(х, ast.Name)}
                рядки = [рядок_константи(х) for х in ast.walk(д[1]) if рядок_константи(х) is not None]
                if any(р in ПОЛЕ_ПОГОДИ for р in рядки):
                    return True
                if any(р not in ("картка_запиту", ЦИТАТИ, УРИВОК) for р in рядки):
                    return False
        return not any(self.минає(м, вузол, ім) for ім in імена)

    def числа_пі(self, м, додати):
        for в in м.вид("Call"):
            ф = в.func
            аргументи = list(в.args)
            if isinstance(ф, ast.Name) and ф.id in self.ЧИСЛОВІ_ПІ:
                що = "%s(…)" % ф.id
            elif isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.attr in self.ЧИСЛОВІ_RE and \
                    м.імпорти.get(ф.value.id, (None,))[0] == "re" and в.args and \
                    re.search(r"\\d|\[0-9|\\D", рядок_константи(в.args[0]) or ""):
                що = "re.%s з цифрою" % ф.attr
                аргументи = аргументи[1:]
            elif isinstance(ф, ast.Attribute) and ф.attr in ("isdigit", "isnumeric", "isdecimal"):
                що = ".%s()" % ф.attr
                аргументи = [ф.value]
            else:
                continue
            for арг in аргументи:
                for контейнер, _ in self.уривки_виразу(м, арг, в):
                    if self.може_бути_погодою(м, контейнер, в):
                        додати(м.шлях, в.lineno, 2, "число з її уривка поля (%s): градуси з її слів у коді" % що)
                        self.лік["Ч"] += 1
                        break
                else:
                    continue
                break

    def числа_джс(self, ф, додати):
        т = ф.т
        for і, (вид, з, р) in enumerate(т):
            if not ((вид == "ім" and з == УРИВОК and і > 0 and т[і - 1][1] == ".") or (вид == "ряд" and з == УРИВОК
                                                                                    and і > 0 and т[і - 1][1] == "[")):
                continue
            # число: уривок у дужках parseFloat/parseInt/Number того самого виразу
            j, глиб, знайдено = і - 1, 0, None
            while j >= 0 and т[j][1] not in (";", "{", "}"):
                if т[j][:2] == ("оп", ")"):
                    глиб += 1
                elif т[j][:2] == ("оп", "("):
                    if глиб == 0 and j > 0 and т[j - 1][0] == "ім" and т[j - 1][1] in ("parseFloat", "parseInt", "Number"):
                        знайдено = т[j - 1][1]
                        break
                    глиб = max(0, глиб - 1)
                j -= 1
            if знайдено is None:
                k = і + 1
                while k + 3 < len(т) and т[k][1] in ("]", ")", "'", "ряд") and т[k][0] == "оп":
                    k += 1
                if т[k][1] == "." and т[k + 1][1] in ("match", "search", "replace", "split") and т[k + 2][1] == "(" \
                        and т[k + 3][0] == "рег" and re.search(r"\\d|\[0-9|\\D", т[k + 3][1]):
                    знайдено = т[k + 1][1]
            if знайдено:
                додати(ф.шлях, р, 2, "число з її уривка поля (JS %s): градуси з її слів у коді" % знайдено)
                self.лік["Ч"] += 1

    # ── JS: плоска цитата ──
    def умова_джс(self, токени, поле):
        """Кон'юнкт умови JS (токени) для поля погоди: True / False / None."""
        текст = " ".join(з if вид != "ряд" else repr(з) for вид, з, _ in токени)
        м_ = re.fullmatch(r"(!\s*)?\(?\s*(\S+)\s*\.\s*(\S+)\s*(?:\|\|\s*\[\s*\]\s*)?\)?\s*\.\s*includes\s*\(\s*%s\s*\)"
                          % re.escape(поле), текст)
        if м_:
            список = self.довідник_джс(м_.group(2), м_.group(3))
            if список is None:
                return None
            є = ПОГОДА in список
            return (not є) if м_.group(1) else є
        м_ = re.fullmatch(r"%s\s*(!==|!=|===|==)\s*'([^']*)'" % re.escape(поле), текст)
        if м_:
            return (м_.group(2) in ПОЛЕ_ПОГОДИ) == м_.group(1).startswith("=")
        return None

    def довідник_джс(self, ім, ключ):
        """Значення `ім.ключ`, де `ім` у JS — `const ім = X.K0`, а K0 Python кладе викликом функції продукту."""
        к0 = self._джс_джерела.get(ім)
        if к0 is None:
            return None
        for м in self.пі:
            for в in м.вид("Assign"):
                if any(isinstance(ц, ast.Subscript) and рядок_константи(ц.slice) == к0 for ц in в.targets) \
                        and isinstance(в.value, ast.Call) and not в.value.args:
                    ц = self.ціль(м, в.value.func)
                    if ц:
                        з, ок = self.вик.виклик(ц[0].шлях, ц[1])
                        if ок and isinstance(з, dict):
                            return list(з.get(ключ) or [])
        return None

    def цитати_джс(self, ф, додати):
        т = ф.т
        self._джс_джерела = {}
        for і in range(len(т) - 4):
            if т[і][0] == "ім" and т[і][1] in ("const", "let", "var") and т[і + 1][0] == "ім" and т[і + 2][1] == "=" \
                    and т[і + 3][0] == "ім" and т[і + 4][1] == "." and і + 5 < len(т) and т[і + 5][0] == "ім" and \
                    (і + 6 >= len(т) or т[і + 6][1] in (";", ")")):
                self._джс_джерела[т[і + 1][1]] = т[і + 5][1]
        for і in range(len(т) - 5):
            if not (т[і][1] == "." and т[і + 1] [:2] == ("ім", ЦИТАТИ) and т[і + 2][1] == "["):
                continue
            j, глиб = і + 3, 1
            while j < len(т) and глиб:
                глиб += т[j][1] == "[" and т[j][0] == "оп"
                глиб -= т[j][1] == "]" and т[j][0] == "оп"
                j += 1
            if j >= len(т) or т[j][:2] != ("оп", "="):
                continue
            ключ = т[і + 3:j - 1]
            if len(ключ) == 1 and ключ[0][0] == "ряд":
                if ключ[0][1] in ПОЛЕ_ПОГОДИ:
                    додати(ф.шлях, т[і][2], 2, "плоска цитата поля погоди «%s» (JS)" % ключ[0][1])
                    self.лік["Ц"] += 1
                continue
            поле = ключ[0][1] if len(ключ) == 1 and ключ[0][0] == "ім" else None
            if поле and self.минає_джс(т, і, поле):
                continue
            додати(ф.шлях, т[і][2], 2, "плоска цитата поля з ключем `%s`, який поле погоди не минає (JS; її "
                   "градуси словами → field_quotes / «Твої слова»)" % (поле or "…"))
            self.лік["Ц"] += 1

    def минає_джс(self, т, і, поле):
        """Умови `if (…)` над записом (той самий оператор чи блок), кон'юнкти `&&` з полем: хоч одна хибна для погоди."""
        j, глиб = і, 0
        while j > 0:
            j -= 1
            вид, з, _ = т[j]
            if вид != "оп":
                continue
            if з in ")]}":
                глиб += 1
                if з == ")" and глиб == 1:
                    # кінець умови `if (…)` прямо перед оператором запису
                    k, г = j, 0
                    while k >= 0:
                        г += т[k][1] == ")" and т[k][0] == "оп"
                        г -= т[k][1] == "(" and т[k][0] == "оп"
                        if г == 0:
                            break
                        k -= 1
                    if k > 0 and т[k - 1][:2] == ("ім", "if") and self._оператор_після(т, j, і):
                        if self._умова_хибна(т[k + 1:j], поле):
                            return True
                continue
            if з in "([{":
                if глиб == 0:
                    if з == "{" and j > 0 and т[j - 1][1] == ")":
                        k, г = j - 1, 0
                        while k >= 0:
                            г += т[k][1] == ")" and т[k][0] == "оп"
                            г -= т[k][1] == "(" and т[k][0] == "оп"
                            if г == 0:
                                break
                            k -= 1
                        if k > 0 and т[k - 1][:2] == ("ім", "if") and self._умова_хибна(т[k + 1:j - 1], поле):
                            return True
                        if k > 0 and т[k - 1][:2] == ("ім", "function"):
                            return False
                    continue
                глиб -= 1
                continue
            if з == ";" and глиб == 0:
                continue
        return False

    def _оператор_після(self, т, кінець_умови, і):
        """Між `)` умови й записом — лише ланцюг запису (без `;`)."""
        return all(т[к][1] != ";" for к in range(кінець_умови + 1, і))

    def _умова_хибна(self, умова, поле):
        частини, поточна, г = [], [], 0
        for т_ in умова:
            if т_[0] == "оп" and т_[1] in "([{":
                г += 1
            elif т_[0] == "оп" and т_[1] in ")]}":
                г -= 1
            if т_[:2] == ("оп", "&&") and г == 0:
                частини.append(поточна)
                поточна = []
                continue
            поточна.append(т_)
        частини.append(поточна)
        return any(any(т_[:2] == ("ім", поле) for т_ in ч) and self.умова_джс(ч, поле) is False for ч in частини)

    def місця(self, додати, звіт):
        for м in self.пі:
            self.цитати_пі(м, додати)
            self.тексти_пі(м, додати)
            self.числа_пі(м, додати)
        self.знахідки_пі(додати)
        self.джерела_пі(додати)
        self.шапки_пі(додати)
        for ф in self.джс:
            if not isinstance(ф, Хтмл):
                self.цитати_джс(ф, додати)
                self.числа_джс(ф, додати)
        звіт.append("її словами й словами моделі: плоска цитата поля — %d; джерело з `quote` — %d; шапка з тексту "
                    "моделі — %d; поріг у °C текстом моделі — %d; число з її уривка — %d; °C у змістовому полі знахідки — %d" % (
                        self.лік["Ц"], self.лік["Д"], self.лік["Ш"], self.лік["Т"], self.лік["Ч"], self.лік["З"]))
        if not self.змістові:
            звіт.append("знахідка.ЗМІСТОВІ у дереві не знайдено — поля знахідки не судяться")
        for шлях, н, поле, ключ, гр, пі in sorted(set((ш, н, п, к, г, tuple(пі)) for ш, н, п, к, г, пі in self.примітки)):
            звіт.append("примітка, не місце: %s:%d — «%s» у полі «%s» знахідки (ключ `%s`) без читача в показі; "
                        "читачі ключа в Python: %s" % (шлях, н, гр, поле, ключ, ", ".join(пі) or "нема"))
        for п in self.вик.помилки:
            звіт.append("умову не обчислено (місце лишається): " + п)


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
    файли, поза = [], 0
    for назва in ("джерела", "zhnyvarka"):
        for база, теки, імена in os.walk(os.path.join(корінь, назва)):
            теки[:] = sorted(т for т in теки if т not in ПОЗА_ТЕКИ and not т.startswith("."))
            for ім in sorted(імена):
                if not ім.endswith(РОЗШИРЕННЯ):
                    continue
                if ТЕСТ.search(ім):
                    поза += 1
                    continue
                файли.append(os.path.relpath(os.path.join(база, ім), корінь).replace(os.sep, "/"))
    return sorted(файли), поза


def лічити_величину(корінь, без_бази=False, вітер=False):
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
            джс.append(Хтмл(шлях, текст, ВІТЕР_ТЕКСТ if вітер else ГРАДУС_ТЕКСТ))
        else:
            джс.append(Джс(шлях, лексер_js(текст)))
    стан = Стан(вітер)
    ап = АналізВітру(пі, стан) if вітер else АналізПі(пі, стан)
    if вітер:
        for ф in джс:
            стан.зерна.update(зн for вид, зн, _ in ф.т if вид in ("ім", "ряд") and МЕТРИ_ІМЯ.search(зн))
        стан.К.update(стан.зерна)
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
    if вітер:
        ап.джерела(додати)
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
    if not вітер:
        рішення_бази(корінь, рішення, пороги_реєстру, додати, звіт, без_бази)
        АналізСлів(корінь, пі, джс).місця(додати, звіт)
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


def лічити(корінь, без_бази=False, лише=None):
    """Незалежні потоки °C та м/с; п.6 не домішується до градусних джерел і меж бази K-WEA-01."""
    градуси = лічити_величину(корінь, без_бази) if лише != "вітер" else None
    вітер = лічити_величину(корінь, без_бази, вітер=True) if лише != "градуси" else None
    основа = градуси or вітер
    місця, стан, звіт, лік, читачі = основа
    if вітер:
        if градуси:
            місця = {к: {"пункти": set(з["пункти"]), "докази": list(з["докази"])} for к, з in місця.items()}
        else:
            місця = {}
        for к, з in вітер[0].items():
            запис = місця.setdefault(к, {"пункти": set(), "докази": []})
            запис["пункти"].add(6)
            for доказ in з["докази"]:
                доказ = "вітер м/с: " + доказ.replace("градусів", "м/с вітру").replace("градуси", "м/с вітру").replace("°C", "м/с")
                if доказ not in запис["докази"]:
                    запис["докази"].append(доказ)
        читачі = читачі | вітер[4]
    звіт = list(звіт) + ["градусних місць: %d; місць вітру (п.6): %d; спільних рядків: %d" % (
        len(градуси[0]) if градуси else 0, len(вітер[0]) if вітер else 0,
        len(градуси[0].keys() & вітер[0].keys()) if градуси and вітер else 0)]
    return місця, стан, звіт, лік, читачі


def друк(місця, стан, звіт, лік, читачі, тихо=False, імена=False, з_читачами=False):
    """Детермінований вивід; останній рядок — `місць: N`."""
    рядки = ["корінь Е2-смуга-погоди: градуси й м/с вітру нагоди в коді продукту (клас — аудит/корені/Е2-смуга-погоди.md)",
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
    за_пунктами = {п: sum(п in з["пункти"] for з in місця.values()) for п in range(1, 7)}
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
ШТУЧНІ.update({
    "джерела/відкидання.py": '''\
ЗНЯТІ = ("темп_c",)  # М:відкидання_знімають
ЧИТАНІ = ("темп_c",)  # М:відкидання_читають
НЕПЕРЕЛІК = ["темп_c"]  # М:відкидання_без_циклу


def зняти(запис):
    for к in ЗНЯТІ:
        запис.pop(к, None)
        запис.get("картка", {}).pop(к, None)
    return запис


def прочитати(запис):
    for к in ЧИТАНІ:
        if запис.get(к) is not None:
            return запис[к]
''',
})
ШТУЧНІ.update({
    "джерела/глибоко/вітер.py": '''\
ОПИС = dict(порив=dict(значення="м/с", джерело="прогноз"))  # М:вітер_опис
ОБГОРТКА = {"контейнер": {"порив": dict(unit="m/s")}}
ШКАЛА = {
    "тихо": 0.0,  # М:вітер_таблиця_тихо
    "дме": 9.0,  # М:вітер_таблиця_дме
}
МЕЖА = 8.0  # М:вітер_межа


def переклад(слово):  # М:вітер_слово_параметр
    return ШКАЛА.get(слово)  # М:вітер_таблиця_читання


def запис(нагода, слово):
    швидкість = переклад(слово)  # М:вітер_переклад
    нагода["порив"] = швидкість  # М:вітер_ключ
    return нагода


def суд_вітру(нагода, wind_ms=None):  # М:вітер_параметр
    швидкість = нагода.get("порив")  # М:вітер_читання
    if швидкість >= МЕЖА:  # М:вітер_поріг_іменем
        return f"{швидкість} м/с"  # М:вітер_показ
    if wind_ms >= 6:  # М:вітер_поріг_6
        return wind_ms >= 10  # М:вітер_поріг_10
    return None


def самі_смуги(нагода):
    бал = нагода.get("вітер_бал")  # М:вітер_бал
    смуга = нагода.get("смуга_вітру")  # М:вітер_смуга
    return бал == 2 or смуга == "сильний"  # М:вітер_смуга_порівняння


def тканина(річ):
    return річ.get("порив") == "так"  # М:вітер_властивість_тканини


def обгортка(нагода):
    return нагода.get("контейнер")  # М:вітер_контейнер_не_число
''',
    "zhnyvarka/ще/глибше/нагода.py": '''\
def інший_модуль(нагода):
    return нагода["порив"] >= 7  # М:вітер_жниварка
''',
    "zhnyvarka/ще/глибше/показ.js": '''\
function вітерП(){
  const v = Number($("ш-вітер").value);  // М:вітер_js_ввід
  const день = {wind_ms: v};  // М:вітер_js_ключ
  if (v >= 6) показ();  // М:вітер_js_поріг
  return v + " м/с";  // М:вітер_js_показ
}
function смугаП(){
  const бал = Number($("вітер-бал").value);  // М:вітер_js_бал
  return {смуга_вітру: бал};  // М:вітер_js_смуга
}
''',
    "zhnyvarka/ще/глибше/ввід.html": '''\
<label for="ш-вітер">Вітер</label> <!-- М:вітер_html_мітка -->
<input type="number" id="інший-порив" value="9"><b>m/s</b> <!-- М:вітер_html_інше_імя -->
<input type="number" id="вітер-бал" value="2"><b>Бал</b> <!-- М:вітер_html_бал -->
''',
    "джерела/проби/вкладено/вітер.py": 'x = {"wind_ms": 10}  # М:вітер_проба\n',
    "zhnyvarka/прилади/вітер.py": 'x = {"wind_ms": 10}  # М:вітер_прилад\n',
    "zhnyvarka/тест_вітер.py": 'x = {"wind_ms": 10}  # М:вітер_тест\n',
})

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
    "html_не_поле": {6}, "тест": set(),
}
ОЧІКУВАНІ.update({
    ім: {6} for ім in (
        "вітер_опис", "вітер_таблиця_тихо", "вітер_таблиця_дме", "вітер_межа", "вітер_таблиця_читання",
        "вітер_переклад", "вітер_ключ", "вітер_параметр", "вітер_читання", "вітер_поріг_іменем", "вітер_показ",
        "вітер_поріг_6", "вітер_поріг_10", "вітер_жниварка", "вітер_js_ввід", "вітер_js_ключ", "вітер_js_поріг",
        "вітер_js_показ", "вітер_html_мітка", "вітер_html_інше_імя",
    )
})
ОЧІКУВАНІ.update({
    "відкидання_знімають": set(), "відкидання_читають": {2}, "відкидання_без_циклу": {2},
})
ОЧІКУВАНІ.update({ім: set() for ім in (
    "вітер_слово_параметр", "вітер_бал", "вітер_смуга", "вітер_смуга_порівняння", "вітер_js_бал", "вітер_js_смуга",
    "вітер_html_бал", "вітер_проба", "вітер_прилад", "вітер_тест", "вітер_властивість_тканини",
    "вітер_контейнер_не_число",
)})

# Її словами й словами моделі (Ц, Д, Ш, Т; доповнення 15.11): місце й не-місце на кожен шлях; умову виконано на
# штучному дереві (`ш_поля.далі`, `ш_картка.політика`), як на дереві продукту.
ШТУЧНІ.update({
    "джерела/ш_поля.py": '''\
ЛИШЕ_МОВІ = frozenset({"смуга_погоди"})


def далі(поле):
    return поле not in ЛИШЕ_МОВІ


def походження(вид, уривок=None):
    вих = {"kind": вид}
    if уривок:
        вих["quote"] = уривок
    return вих


def _джерело(паспорт, поле):
    ф = (паспорт.get("картка") or {}).get(поле) or {}
    вих = походження(ф.get("джерело"), ф.get("уривок"))  # М:слова_джерело_обгорнуте
    вих["parts"] = [походження(о.get("джерело"), о.get("уривок")) for о in ф.get("опори") or []]  # М:слова_джерело_вкладене
    return вих


def джерело(паспорт, поле):
    вих = _джерело(паспорт, поле)
    if not далі(поле):
        вих.pop("quote", None)
    return вих


def джерело_давнє(паспорт, поле):
    ф = (паспорт.get("картка") or {}).get(поле) or {}
    return походження(ф.get("джерело"), ф.get("уривок"))  # М:слова_джерело


def джерело_з_цитат(паспорт, поле):
    цитата = (паспорт.get("цитати_полів") or {}).get(поле)
    return походження("reading", цитата)  # М:слова_джерело_з_цитат


def джерело_не_погоди(паспорт, поле):
    ф = (паспорт.get("картка") or {}).get(поле) or {}
    if поле != "смуга_погоди":
        return походження(ф.get("джерело"), ф.get("уривок"))  # М:слова_джерело_не_погоди
    return {}


def бажання(б):
    return походження("her", б.get("уривок"))  # М:слова_джерело_не_поле
''',
    "джерела/ш_картка.py": '''\
import ш_поля as _П


def політика():
    return dict(лише_мові=sorted(_П.ЛИШЕ_МОВІ))


def проєкція(паспорт, поле, факт):
    цитати = паспорт.setdefault("цитати_полів", {})
    if факт["уривок"] and _П.далі(поле):
        цитати[поле] = факт["уривок"]  # М:слова_цитата_минає
    if факт["уривок"]:
        цитати[поле] = факт["уривок"]  # М:слова_цитата


def погода(паспорт, т):
    паспорт["цитати_полів"]["смуга_погоди"] = т  # М:слова_цитата_погоди
    паспорт["цитати_полів"]["опади"] = т  # М:слова_цитата_інше_поле


def хід(паспорт, цит):
    уривки = dict(паспорт.get("цитати_полів") or {})
    for ім in ("опади", "смуга_погоди"):
        уривки[ім] = цит[ім]  # М:слова_цитата_копія
    паспорт["цитати_полів"] = уривки


def не_погода(паспорт, поле, т):
    if поле != "смуга_погоди":
        паспорт["цитати_полів"][поле] = т  # М:слова_цитата_не_погода
    else:
        паспорт["цитати_полів"][поле] = None  # М:слова_цитата_інакше_погода


def інша_колекція(паспорт, поле, т):
    паспорт["бажання"][поле] = т  # М:слова_не_цитата
''',
    "джерела/ш_довідник.py": '''\
import ш_картка as _К
таблиці = {}
таблиці["факт_ш"] = _К.політика()
''',
    "джерела/показ/ш_цитати.js": '''\
function записатиП(паспорт, картка, поле){
  const політика = ДОВІДНИК.факт_ш;
  if (картка[поле].уривок && !(політика.лише_мові || []).includes(поле)) паспорт.цитати_полів[поле] = картка[поле].уривок;  // М:слова_js_минає
  if (картка[поле].уривок) паспорт.цитати_полів[поле] = картка[поле].уривок;  // М:слова_js_цитата
  if (поле !== 'смуга_погоди') { паспорт.цитати_полів[поле] = 'x'; }  // М:слова_js_блок_минає
  паспорт.цитати_полів['смуга_погоди'] = 'x';  // М:слова_js_погоди
  if (паспорт.цитати_полів[поле] === 'x') return;  // М:слова_js_читання
}
''',
    "джерела/ш_шапка.py": '''\
ШАПКА = (("weather_band", "смуга_погоди"),  # М:слова_шапка
         ("mood", "настрій"))  # М:слова_шапка_інше
КОДИ = (("weather_band", "смуга_погоди"),)  # М:слова_таблиця_кодів
''',
    "джерела/ш_схема.py": '''\
import ш_шапка as _Ш
СХЕМА = {"header": {"type": "object", "properties": {к: {"type": "string"} for к, _ in _Ш.ШАПКА}}}
ПЕРЕЛІК = {к: {"type": "string", "enum": ["deep_frost"]} for к, _ in _Ш.КОДИ}
''',
    "джерела/ш_промпт.py": '''\
ПРОМПТ = ("Dress for the weather band. "
          "An outer layer only when needed; at +20 °C and warmer there is none.")  # М:слова_поріг_текстом
ВЧИТЬ = "Her degrees become a band: below -8 °C → deep_frost."  # М:слова_вчить_смугу
УКР = "при +15 °C у безвітря стійка не заміщає шарфа"  # М:слова_примітка_без_читача


def ф():
    """Model sees +20 °C only in a docstring."""  # М:слова_докстрінг
    return "the band, not degrees"  # М:слова_без_градусів
''',
})
ОЧІКУВАНІ.update({
    "слова_джерело": {2}, "слова_джерело_з_цитат": {2}, "слова_джерело_вкладене": {2},
    "слова_джерело_обгорнуте": set(), "слова_джерело_не_погоди": set(), "слова_джерело_не_поле": set(),
    "слова_цитата": {2}, "слова_цитата_погоди": {2}, "слова_цитата_копія": {2}, "слова_цитата_минає": set(),
    "слова_цитата_інше_поле": set(), "слова_цитата_не_погода": set(), "слова_цитата_інакше_погода": {2},
    "слова_не_цитата": set(), "слова_js_минає": set(), "слова_js_цитата": {2}, "слова_js_блок_минає": set(),
    "слова_js_погоди": {2}, "слова_js_читання": set(), "слова_шапка": {4}, "слова_шапка_інше": set(),
    "слова_таблиця_кодів": set(), "слова_поріг_текстом": {3}, "слова_вчить_смугу": set(),
    "слова_примітка_без_читача": set(), "слова_докстрінг": set(), "слова_без_градусів": set(),
})

# Читач уривка (рішення менеджера 15523): уривок у картці, звірка й сила — не місце; число з уривка поля погоди — п.2.
ШТУЧНІ.update({
    "джерела/ш_уривок.py": '''\
import re


def у_записати(картка, поле, значення, уривок):
    факт = {"значення": значення, "уривок": уривок}  # М:уривок_у_картці
    картка[поле] = факт


def у_тримається(картка, поле, слова):
    return звірити(картка[поле]["уривок"], слова)  # М:уривок_звірка


def у_сила(факт):
    return 2 if факт.get("уривок") else 1  # М:уривок_сила


def у_число(картка):
    return float(re.sub(r"[^0-9-]", "", картка["смуга_погоди"]["уривок"]))  # М:уривок_число


def у_число_поля(картка, поле):
    у = картка[поле]["уривок"]
    return re.findall(r"\\d+", у)  # М:уривок_число_поля


def у_опади(картка):
    return int(картка["опади"]["уривок"])  # М:уривок_число_іншого


def у_не_погода(картка, поле):
    if поле != "смуга_погоди":
        return int(картка[поле]["уривок"])  # М:уривок_число_не_погоди
    return 0


def у_цифра(картка, поле):
    return картка[поле]["уривок"].isdigit()  # М:уривок_цифра
''',
    "джерела/показ/ш_уривок.js": '''\
function числоП(картка, поле){
  const т = parseFloat(картка[поле].уривок);  // М:уривок_js_число
  const ц = картка[поле].уривок.match(/\\d+/);  // М:уривок_js_регулярка
  const мітка = String(картка[поле].уривок || '').trim();  // М:уривок_js_мітка
  return т + ц + мітка;
}
''',
})
ОЧІКУВАНІ.update({
    "уривок_у_картці": set(), "уривок_звірка": set(), "уривок_сила": set(), "уривок_число": {2},
    "уривок_число_поля": {2}, "уривок_число_іншого": set(), "уривок_число_не_погоди": set(), "уривок_цифра": {2},
    "уривок_js_число": {2}, "уривок_js_регулярка": {2}, "уривок_js_мітка": set(),
})

# Знахідка суду (рішення менеджера 15584): чи рядок з °C — місце, вирішує читач, а не мова. Змістові поля знахідки
# (`знахідка.ЗМІСТОВІ`) і все, що код у них вкладає, — п.2 (показ читає їх — ще й п.4); інше поле — лише з читачем у
# показі; примітка без читача поза кодом — не місце.
ШТУЧНІ.update({
    "джерела/знахідка.py": '''\
ОБОВʼЯЗКОВІ = ("правило",)
ЗМІСТОВІ = ("суть", "чому")
''',
    "джерела/ш_зн.py": '''\
def зн(правило, сила, суть, речі, чому, ламається=None, примітка=None):
    d = dict(правило=правило, сила=сила, суть=суть, речі=речі, чому=чому)
    if ламається:
        d["де_ламається"] = ламається
    if примітка:
        d["нота_показу"] = примітка
    return d


def брак(правило, речі, чому=None):
    return зн(правило, "питання", "бракує входу", речі, чому or "rule_input_missing")
''',
    "джерела/ш_реєстр.py": '''\
from ш_зн import зн, брак
''',
    "джерела/ш_обгортка.py": '''\
import ш_реєстр as _Р


def зн(*a, **kw):
    kw.setdefault("сила", "soft")
    return _Р.зн(*a, **kw)
''',
    "джерела/ш_суд.py": '''\
from ш_реєстр import зн as _зн, брак as _брак
import ш_обгортка as _О

НОТИ = {"K-9": dict(нота="при +2 °C успадковано з температурної смуги")}  # М:знахідка_примітка_реєстру
ОПИС = {"випадок": "текст нагоди («офіс, 18 °C»)"}  # М:знахідка_опис_поля


def суд(смуга, словами):
    вих = [_зн("K-1", "soft", "при %s шапки нема" % смуга, [],
               "у смузі нижче −8 °C мапа просить пуху")]  # М:знахідка_чому
    вих.append(_зн("K-2", "soft", "нижче −8°C палітру несуть %s" % "шапка", [], "x"))  # М:знахідка_суть
    вих.append(_О.зн("K-3", суть="s", речі=[], чому="тренч у +5 °C — не шар"))  # М:знахідка_обгортка
    вих.append(_брак("K-4", [], "без шапки при −10 °C"))  # М:знахідка_через_конструктор
    вих.append(_зн("K-5", "soft", "s", [], "x", ламається="гейт лише нижче −8 °C"))  # М:знахідка_ламається
    вих.append(_зн("K-6", "soft", "s", [], "x", примітка="нижче −8 °C"))  # М:знахідка_читач_показу
    вих.append(_зн("K-7", "soft", "у %s шапки нема" % словами(смуга), [], "x"))  # М:знахідка_смугою
    поріг = "нижче −8 °C пух"  # М:знахідка_змінна
    вих.append(_зн("K-8", "soft", "s", [], поріг))
    вих.append(dict(правило="K-10", суть="при −3 °C", речі=[]))  # М:знахідка_словник
    вих.append(dict(слот="шарф", назва="при −3 °C"))  # М:знахідка_не_знахідка
    return вих


def стан(вітер):
    рез = dict(чому="стійка закриває шию", умова="лише за вітру; при +15 °C не заміщає")  # М:знахідка_ключ
    інше = dict(нота="при +15 °C стійка відкрита")  # М:знахідка_ключ_без_читача
    return _зн("K-11", "default", "s", [], "%s. %s" % (рез["чому"], рез["умова"])), інше
''',
    "джерела/показ/ш_знахідка.js": '''\
function рядокП(з){
  return з.суть + ' ' + з.нота_показу;
}
''',
})
ОЧІКУВАНІ.update({
    # штучний показ читає `суть`, а `чому` — ні: п.4 лише там, де поле читає показ
    "знахідка_чому": {2}, "знахідка_суть": {2, 4}, "знахідка_обгортка": {2}, "знахідка_через_конструктор": {2},
    "знахідка_ламається": set(), "знахідка_читач_показу": {2, 4}, "знахідка_смугою": set(),
    "знахідка_змінна": {2}, "знахідка_словник": {2, 4}, "знахідка_не_знахідка": set(), "знахідка_ключ": {2},
    "знахідка_ключ_без_читача": set(), "знахідка_примітка_реєстру": set(), "знахідка_опис_поля": set(),
})


# Вкладене джерело поля — `parts` з `опори` факту картки (її слова по частинах складеного поля; дошка 15930): місце,
# лише коли писач `опори` може покласти туди поле погоди. Писач і читач — у одному дереві, тож кожен випадок —
# окреме штучне дерево (спільне дерево зробило б один випадок чинним для всіх).
_ЧИТАЧ_ОПОР = '''\
ЛИШЕ_МОВІ = frozenset({"смуга_погоди"})


def походження(вид, уривок=None):
    вих = {"kind": вид}
    if уривок:
        вих["quote"] = уривок
    return вих


def _вид(паспорт, поле):
    ф = (паспорт.get("картка") or {}).get(поле) or {}
    вих = походження(ф.get("джерело"), ф.get("уривок"))
    if ф.get("опори"):
        вих["parts"] = [походження(о.get("джерело"), о.get("уривок")) for о in ф["опори"]]  # М:опори_читач
    return вих


def вид(паспорт, поле):
    вих = _вид(паспорт, поле)
    if поле in ЛИШЕ_МОВІ:
        вих.pop("quote", None)
    return вих
'''
_ПИСАЧ_ОПОР = '''\
def записати(паспорт, поле, значення, уривок, опори=None):
    факт = {"значення": значення, "уривок": уривок}
    if опори:
        факт["опори"] = list(опори)
    паспорт["картка"][поле] = факт


def складені(паспорт, внутрішня):
    for поле in %s:
        записати(паспорт, поле, внутрішня[поле], "х", опори=[{"уривок": "х"}])


def без_опор(паспорт):
    записати(паспорт, "смуга_погоди", "cold", "х")
'''
ДЕРЕВА_ОПОР = {
    # писач кладе `опори` лише полям складеного списку — вкладений запис не несе погоди
    "опори_не_погода": ({"джерела/ш_поля.py": _ЧИТАЧ_ОПОР, "джерела/ш_запис.py": _ПИСАЧ_ОПОР % '("бажання", "вето")'},
                        {"опори_читач": set()}),
    # близький справжній: у переліку поля писача є смуга погоди
    "опори_з_погодою": ({"джерела/ш_поля.py": _ЧИТАЧ_ОПОР,
                         "джерела/ш_запис.py": _ПИСАЧ_ОПОР % '("бажання", "смуга_погоди")'},
                        {"опори_читач": {2}}),
    # поле писача не обчислено (параметр, не перелік літералів) — не менше місць
    "опори_поле_не_обчислено": ({"джерела/ш_поля.py": _ЧИТАЧ_ОПОР,
                                 "джерела/ш_запис.py": _ПИСАЧ_ОПОР.replace("for поле in %s:", "for поле in внутрішня:") % ()},
                                {"опори_читач": {2}}),
    # писача `опори` у дереві нема — не доведено, що погоди туди не кладуть
    "опори_без_писача": ({"джерела/ш_поля.py": _ЧИТАЧ_ОПОР}, {"опори_читач": {2}}),
}


def випадки_писачів_опор():
    """Пари писачів із погодою та без неї, а також невідомі значення й перекриття присвоєнь."""
    базовий = _ПИСАЧ_ОПОР % '("бажання", "вето")'
    for поле, пункти in (("смуга_погоди", {2}), ("бажання", set())):
        виклик = базовий.replace('паспорт, поле, внутрішня[поле]', 'паспорт, "%s", внутрішня[поле]' % поле)
        форми = {
            "розпакування": виклик.replace('опори=[{"уривок": "х"}]', '**{"опори": [{"уривок": "х"}]}'),
            "типове": базовий.replace('опори=None', 'опори=({"уривок": "х"},)')
            .replace('паспорт, "смуга_погоди", "cold"', 'паспорт, "%s", "cold"' % поле),
            "переприсвоєння": базовий.replace('        записати(', '        поле = "%s"\n        записати(' % поле),
            "словник": базовий + '\n\ndef додати(паспорт):\n'
            '    паспорт["картка"]["%s"] = {"опори": [{"уривок": "х"}]}\n' % поле,
            "копія": базовий + '\n\ndef додати(паспорт, давній):\n'
            '    факт = {"опори": давній.get("опори")}\n    паспорт["картка"]["%s"] = факт\n' % поле,
            "прямий_ключ": базовий + '\n\ndef додати(паспорт, давній):\n'
            '    паспорт["картка"]["%s"]["опори"] = давній.get("опори")\n' % поле,
        }
        for ім, текст in форми.items():
            yield ім + "_" + поле, текст, пункти
    yield "переприсвоєння_з_погоди", (_ПИСАЧ_ОПОР % '("смуга_погоди",)') \
        .replace('        записати(', '        поле = "бажання"\n        записати('), set()
    yield "типове_порожнє", базовий.replace("опори=None", "опори=()"), set()
    yield "невідоме_розпакування", базовий.replace('опори=[{"уривок": "х"}]', '**внутрішня') \
        .replace('паспорт, поле, внутрішня[поле]', 'паспорт, "смуга_погоди", внутрішня[поле]'), {2}
    yield "умовне_переприсвоєння", базовий.replace('        записати(',
        '        if внутрішня:\n            поле = "смуга_погоди"\n        записати('), {2}
    yield "умовне_зняття_погоди", (_ПИСАЧ_ОПОР % '("смуга_погоди",)').replace('        записати(',
        '        if внутрішня:\n            поле = "бажання"\n        записати('), {2}
    yield "іменовані_параметри", базовий.replace('уривок, опори=None', 'уривок, *, цитата=True, опори=None') \
        .replace('паспорт, поле, внутрішня[поле]', 'паспорт, "смуга_погоди", внутрішня[поле]'), {2}


def _прогін(штучні, очікувані, префікс=""):
    """[(назва, так/ні)]: кожна позначка штучних файлів — очікуваний набір пунктів; вивід — однаковий двічі."""
    тека = tempfile.mkdtemp(prefix="е2_смуга_")
    try:
        позначки = {}
        for шлях, текст in штучні.items():
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
        for ім, очікуване in очікувані.items():
            if ім not in позначки:
                підсумок.append((префікс + ім + " (позначки нема)", False))
                continue
            є = місця.get(позначки[ім], {}).get("пункти", set())
            ок = set(є) == очікуване
            підсумок.append((префікс + ("%s — %s" % (ім, "п." + ",".join(map(str, sorted(є))) if є else "не місце")
                                        if ок else "%s — є %s, чекали %s" % (ім, sorted(є), sorted(очікуване))), ок))
        підсумок.append((префікс + "позначки без очікуваного: %s" % (", ".join(sorted(set(позначки) - set(очікувані)))
                                                                   or "нема"), not (set(позначки) - set(очікувані))))
        підсумок.append((префікс + "вивід детермінований", друк(*перший) == друк(*другий)))
        return підсумок
    finally:
        shutil.rmtree(тека, ignore_errors=True)


def самоперевірка():
    """[(назва, так/ні)]: основне штучне дерево, потім кожне з `ДЕРЕВА_ОПОР`."""
    підсумок = _прогін(ШТУЧНІ, ОЧІКУВАНІ)
    for ім, (штучні, очікувані) in ДЕРЕВА_ОПОР.items():
        підсумок += _прогін(штучні, очікувані, ім + ": ")
    for ім, текст, пункти in випадки_писачів_опор():
        підсумок += _прогін({"джерела/ш_поля.py": _ЧИТАЧ_ОПОР, "джерела/ш_запис.py": текст},
                           {"опори_читач": пункти}, ім + ": ")
    return підсумок


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
    лише = "вітер" if "--вітер" in арг else "градуси" if "--градуси" in арг else None
    місця, стан, звіт, лік, читачі = лічити(корінь, лише=лише)
    print(друк(місця, стан, звіт, лік, читачі, тихо="--тихо" in арг, імена="--імена" in арг,
               з_читачами="--читачі" in арг))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
