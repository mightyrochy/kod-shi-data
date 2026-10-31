# -*- coding: utf-8 -*-
"""прилади/корінь_е2_частина_дня.py — прилад кореня Е2-частина-дня: година дня нагоди в коді продукту.

Клас — `аудит/корені/Е2-частина-дня.md` («Клас місць»): місце — кожна точка коду продукту (`джерела/` на будь-якій
глибині: Python, JS, HTML і промпти в них; проби, прилади й тести — ні), де година дня нагоди (година, хвилини,
годинник рядком) — поле, ключ, число, код чи текст показу. Тривалість і дата — не година. Пункти класу:
  1  мовну модель просять годину чи хвилини (схема, опис поля, промпт) чи код приймає їх із її відповіді;
  2  код читає, пише, зберігає чи передає годину (паспорт, картка, сцена, кеш, правила, погода, світло, бриф, промпт,
     протокол стилістки);
  3  код перетворює годину на частину дня чи частину дня на годину, зокрема ставить типову годину;
  4  панель дає ввести годину руками, картка показує годину полем;
  5  правило стилю з бази знань, що судить днем і вечором (ошатність за рівнем події, відкриті зони, рух, блиск,
     світло), не бере частини дня з паспорта чи діє не так, як записано в базі знань; вечір, що підіймає рівень
     ошатності весілля, — теж місце.

ВІД ЗНАЧЕННЯ, НЕ ВІД ІМЕН. Прилад не має переліку полів: імена, що несуть годину, він виводить сам.
  Звідки година приходить (зерна — ознаки самого значення):
    · схема числа 0–23 (`minimum=0, maximum=23` у виклику чи dict схеми) — ключ запису, до якого вона належить;
    · опис поля словами годинника («start hour», «24-hour clock», «clock time», «start time», «24-годинн…»,
      «година доби»), що стоїть значенням ключа;
    · формат годинника (`"%02d:%02d" % (г, х)`, f-рядок `{г:02d}:{х:02d}`, JS `String(г).padStart(2,'0') + ':'`);
    · арифметика доби (`г % 24`);
    · перетворювач: функція, що порівнює параметр із числами доби й повертає частину дня (`ранок/день/вечір/ніч`,
      `morning/day/evening/night`), і таблиця «частина дня → число 0–23»;
    · поле панелі `<input min="0" max="23">` (його `id`).
  Куди тече (до нерухомої точки, через усі файли): присвоєння, ключ dict і `dict(...)`, іменований аргумент,
  параметр функції продукту, повернення функції, пари ключів у таблицях відповідності (`(("hour", "година"), …)`),
  поріг, з яким годину порівнюють (`година >= РЕЄСТР["вечір_від"]["val"]` → ключ `вечір_від`), і назад — до
  джерел значення, що йде в місце години (`г = next(… in _СЛОВА_ГОДИНИ)` → таблиця слів годин).
  Вечір із години (п.5): прапорець, який код рахує порівнянням години з межею дня (`вечірнє_світло(година)`,
  `година >= 18`), і все, що його читає.
  Правила бази знань (п.5): таблиця `ПРАВИЛА_БАЗИ` — кожне правило дня й вечора з бази знань (якір у файлі
  бази звіряється при запуску) і знак у коді (ід правила, ключ реєстру); правило в коді, яке частини дня з
  паспорта не бере чи діє не так, як у базі, — місце в кожній точці коду зі знаком; правила в коді нема зовсім —
  місце на якорі бази.

ЩО НЕ МІСЦЕ: коментарі й докстрінги; тривалість (`duration_h`, «how many hours … lasts», «пів години») і дата;
годинник журналу й звітів (час прогону, `getHours`) — не година нагоди; частина дня (`part_of_day`, `пора`), що
йде як є, без години.

Вивід детермінований: перелік `файл:рядок · п.N[,M] · доказ`, підсумки за пунктами, файлами й правилами бази,
імена, які прилад вивів (з першою точкою виводу), останній рядок `місць: <N>` (N — різних `файл:рядок`), код 0.
Запуск з кореня репозиторію (чи `--корінь <шлях>`):
    python3 джерела/прилади/корінь_е2_частина_дня.py [--тихо] [--імена] [--самоперевірка]
"""
import ast
import os
import re
import shutil
import sys
import tempfile
import warnings

warnings.simplefilter("ignore", SyntaxWarning)

# ── межі обходу ─────────────────────────────────────────────────────────────────────────────────────────────────
ПОЗА_ТЕКИ = {"проби", "прилади", "node_modules", "__pycache__"}
ТЕСТ = re.compile(r"^(тест|test|стенд|батарея|gate_|pair_test|проба)|(_test|_тест)\.|\.test\.", re.IGNORECASE)
РОЗШИРЕННЯ = (".py", ".js", ".mjs", ".html")

# ── словник значень ─────────────────────────────────────────────────────────────────────────────────────────────
# Слова частини дня — область значення перетворювача (що він повертає), не імена полів.
СЛОВА_ПОРИ = {"ранок", "день", "вечір", "ніч", "обід", "morning", "day", "afternoon", "evening", "night", "noon"}
# Імена без змісту: значення будь-якого поля, тож годину не несуть як ключ (лише як локальні змінні).
ЗАГАЛЬНІ = {
    "value", "val", "значення", "quote", "уривок", "key", "ключ", "поле", "field", "type", "тип", "data", "дані",
    "name", "ім", "імя", "id", "ід", "текст", "text", "джерело", "source", "код", "code", "вихід", "result",
    "items", "item", "row", "рядок", "запис", "default", "типове", "мітка", "label", "self", "cls", "args", "kwargs",
    "get", "число", "number", "num", "int", "float", "str", "round", "abs", "min", "max", "next", "len", "parseInt",
    "parseFloat", "Number", "String", "Math", "floor", "value", "textContent", "innerHTML", "true", "false", "null",
    "None", "True", "False", "this", "return", "const", "let", "var", "new", "typeof", "undefined", "update",
    "setdefault", "pop", "join", "format", "push", "map", "filter", "isFinite", "isNaN", "padStart", "slice",
    "split", "trim", "replace", "length", "keys", "values", "entries", "Object", "Array", "JSON", "parse",
    "stringify", "console", "log", "window", "document", "dict", "list", "tuple", "set", "sorted", "any", "all",
}
# Локальні імена загального вжитку (цикли полів, значення будь-якого ключа): назад у них година не йде.
ЗАГАЛЬНІ_ЛОКАЛЬНІ = {"v", "в", "x", "k", "к", "з", "п", "р", "і", "i", "j", "s", "с", "о", "д", "т", "e", "е", "a",
                     "а", "b", "б", "n", "н", "y", "у", "ч", "ф", "м", "л", "val", "знач", "сире", "raw", "поле_",
                     "елемент", "річ", "item", "obj", "об"}
ОБГОРТКИ_PY = {"int", "float", "round", "abs", "str", "next", "max", "min"}
ОБГОРТКИ_JS = {"parseInt", "parseFloat", "Number", "String", "Math", "round", "floor", "trunc"}

# Текст годинника: у рядках коду (промпти, описи, написи), не в коментарях.
ГОДИННИК_ЛІТЕРАЛ = re.compile(r"(?<![\d.:/\[])(?:[01]?\d|2[0-3]):[0-5]\d(?![\d:\]])")
ГОДИНА_EN = re.compile(r"\b(?:start(?:ing)? hour|start time|24-hour|clock time|o'clock|on a clock|"
                       r"hour of the day)\b", re.IGNORECASE)
ГОДИНА_СЛОВО_EN = re.compile(r"(?<!\ban )(?<!\bper )(?<!\ba )(?<!\bthe next )\bhour\b(?!s)(?!-)", re.IGNORECASE)
ГОДИНА_UK = re.compile(r"24-годинн\w*|годин[аиуі] (?:доби|початку)|"
                       r"\bо (?:першій|другій|третій|четвертій|п['ʼ]?ятій|шостій|сьомій|восьмій|дев['ʼ]?ятій|"
                       r"десятій|одинадцятій|дванадцятій)\b")
ХВИЛИНИ_EN = re.compile(r"\bminutes of the start\b", re.IGNORECASE)
ДІАПАЗОН_ДОБИ = re.compile(r"(?<![\d.])0\s?[–-]\s?23(?![\d.])")
ФОРМАТ_ГОДИННИКА = re.compile(r"%0?2?d:%02d|\{:02d\}:\{:02d\}")
ДОВГА = re.compile(r"\b(?:how many hours|hours? long|lasts?)\b", re.IGNORECASE)


def ідентоподібне(р):
    """Рядок, схожий на ключ чи ід (без пробілів), — кандидат у ключі відповідності."""
    return bool(re.fullmatch(r"[\w-]{3,}", р or "")) and not р.isdigit()


def значуще(ім):
    """Ім'я, що може нести годину як ключ (не загальне, довше двох знаків)."""
    return isinstance(ім, str) and len(ім) > 2 and ім not in ЗАГАЛЬНІ and ім not in СЛОВА_ПОРИ


def значуще_е(ім):
    """Ім'я прапорця вечора з години: слова пори тут — ключі прапорця (`вечір=`), не значення."""
    return isinstance(ім, str) and len(ім) > 2 and ім not in ЗАГАЛЬНІ


def текст_години(т):
    """Причини, чому рядок тексту згадує годину дня (порожньо — не згадує)."""
    причини = []
    if ГОДИННИК_ЛІТЕРАЛ.search(т):
        причини.append("годинник «%s»" % ГОДИННИК_ЛІТЕРАЛ.search(т).group(0))
    for шаблон, імя in ((ГОДИНА_EN, "опис годинника"), (ГОДИНА_UK, "година словами"), (ХВИЛИНИ_EN, "хвилини початку"),
                        (ДІАПАЗОН_ДОБИ, "діапазон години")):
        м = шаблон.search(т)
        if м:
            причини.append("%s «%s»" % (імя, м.group(0)))
    if not причини:
        м = ГОДИНА_СЛОВО_EN.search(т)
        if м and not ДОВГА.search(т[max(0, м.start() - 40):м.end() + 40]):
            причини.append("година в тексті «%s»" % т[max(0, м.start() - 12):м.end() + 12].strip())
    return причини


def токени_носіїв(т, носії):
    """Ключі-носії, названі в рядку тексту як ключ коду (з `_`/`-`, не ASCII-слово, чи в лапках/`=`/`:`)."""
    знайдені = []
    for м in re.finditer(r"\w+(?:-\w+)*", т):
        с = м.group(0)
        if с not in носії:
            continue
        if "_" in с or "-" in с:
            знайдені.append(с)
            continue
        до, після = т[max(0, м.start() - 1):м.start()], т[м.end():м.end() + 2]
        if т.strip() == с or до in ('"', "'", "`", "{", "<") or після[:1] in ('"', "'", "=", ":", "|", ">") \
                or після.startswith("->") or re.match(r"\s+\d", т[м.end():м.end() + 3]):
            знайдені.append(с)
    return знайдені


# ── спільний стан виводу ────────────────────────────────────────────────────────────────────────────────────────
class Стан:
    """Імена, які прилад вивів: носії години, перетворювачі, вечір із години, частина дня; звідки кожне."""

    def __init__(self):
        self.Г = set()        # носії години: ключі, атрибути, глобальні імена, функції, ід полів
        self.КОНВ = set()     # перетворювачі година ↔ частина дня (функції й таблиці)
        self.Е = set()        # вечір із години: функції, ключі, параметри
        self.П = set()        # ключі частини дня (з перетворювача чи слова пори)
        self.С = set()        # прапорці походження години (`година_з_пори`): місця, але не значення години
        self.ПЕР = set()      # функції переводу години в частину дня (повертають результат перетворювача)
        self.Л = {}           # локальні носії: (файл, ід області) → імена
        self.ЛЕ = {}          # локальний вечір із години
        self.звідки = {}      # ім'я → «файл:рядок · правило»
        self.порядок = []     # порядок виводу (для відладки)
        self.змінено = True

    def додати(self, множина, ім, де, чому):
        """Додає ім'я до множини (зі звідки); повертає, чи нове."""
        if ім in множина:
            return False
        множина.add(ім)
        self.звідки.setdefault(ім, "%s · %s" % (де, чому))
        self.порядок.append((ім, де, чому))
        self.змінено = True
        return True

    def додати_л(self, словник, ключ, ім):
        """Локальний носій в області."""
        м = словник.setdefault(ключ, set())
        if ім not in м:
            м.add(ім)
            self.змінено = True
            self.порядок.append(("Л:" + ім, ключ[0], ""))


# ── Python ──────────────────────────────────────────────────────────────────────────────────────────────────────
ОБЛАСТІ = (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)


def рядок_константи(в):
    """Значення str-константи чи None."""
    return в.value if isinstance(в, ast.Constant) and isinstance(в.value, str) else None


def ціле(в):
    """Значення int-константи (не bool) чи None."""
    if isinstance(в, ast.Constant) and isinstance(в.value, int) and not isinstance(в.value, bool):
        return в.value
    if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.USub) and ціле(в.operand) is not None:
        return -ціле(в.operand)
    return None


class Пі:
    """Модуль Python: дерево, області, локальні імена, вузли за видом."""

    def __init__(self, шлях, текст):
        self.шлях = шлях
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
                # аргументи й типові значення функції належать зовнішній області, тіло — її
                стек.append((д, нова if not (isinstance(в, ОБЛАСТІ) and isinstance(д, (ast.arguments,))) else обл))
        self.локальні = {}
        self.параметри = {}
        self.функції = []
        for в in self.вузли:
            if isinstance(в, ОБЛАСТІ):
                пар = [а.arg for а in (в.args.posonlyargs + в.args.args + в.args.kwonlyargs)]
                пар += [а.arg for а in (в.args.vararg, в.args.kwarg) if а]
                self.параметри[id(в)] = пар
                self.локальні[id(в)] = set(пар)
                if not isinstance(в, ast.Lambda):
                    self.функції.append(в)
        глобальні = {}
        for в in self.вузли:
            обл = self.обл[id(в)]
            if обл is None:
                continue
            if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store):
                self.локальні[id(обл)].add(в.id)
            elif isinstance(в, (ast.Global, ast.Nonlocal)):
                глобальні.setdefault(id(обл), set()).update(в.names)
        for обл, імена in глобальні.items():
            self.локальні[обл] -= імена
        # усі присвоєння локальних імен: (ід області, ім'я) → значення; None — цикл, складене чи += (не одне значення)
        self.присвоєння = {}
        for в in self.вузли:
            обл = self.обл[id(в)]
            if обл is None:
                continue
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and в.value is not None:
                for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                    if isinstance(ц, ast.Name):
                        self.присвоєння.setdefault((id(обл), ц.id), []).append(в.value)
                    elif isinstance(ц, ast.Tuple):
                        пари = zip(ц.elts, в.value.elts) if isinstance(в.value, ast.Tuple) and \
                            len(в.value.elts) == len(ц.elts) else \
                            ((е, в.value if і == 0 and isinstance(в.value, ast.Call) else None)
                             for і, е in enumerate(ц.elts))
                        for е, з in пари:
                            if isinstance(е, ast.Name):
                                self.присвоєння.setdefault((id(обл), е.id), []).append(з)
            elif isinstance(в, (ast.For, ast.AsyncFor, ast.comprehension, ast.withitem, ast.AugAssign, ast.NamedExpr)):
                ціль = getattr(в, "target", None) or getattr(в, "optional_vars", None)
                for е in (ast.walk(ціль) if ціль is not None else ()):
                    if isinstance(е, ast.Name):
                        self.присвоєння.setdefault((id(обл), е.id), []).append(None)
        self.за_видом = {}
        for в in self.вузли:
            self.за_видом.setdefault(type(в).__name__, []).append(в)

    def вид(self, *імена):
        """Вузли даних видів."""
        for ім in імена:
            yield from self.за_видом.get(ім, ())

    def ключ_обл(self, в):
        """Ключ області вузла для локальних носіїв (None — модуль)."""
        обл = self.обл.get(id(в))
        return None if обл is None else (self.шлях, id(обл))

    def функція_області(self, в):
        """FunctionDef, що містить вузол (без лямбд), чи None."""
        б = self.батько.get(id(в))
        while б is not None and not isinstance(б, (ast.FunctionDef, ast.AsyncFunctionDef)):
            б = self.батько.get(id(б))
        return б


class АналізПі:
    """Правила виводу й пошуку місць для Python поверх спільного `Стан`."""

    def __init__(self, модулі, стан):
        self.модулі = модулі
        self.с = стан
        self.визначення = {}
        self.під_ключі = set()    # (ключ поля години, під-ключ запису), які читають у носій години
        self.геттери = set()      # функції з одним параметром-ключем: `def _з(k): … п.get(k) …` — значення поля
        for м in модулі:
            for ф in м.функції:
                self.визначення.setdefault(ф.name, []).append((м, ф))
                пар = [а.arg for а in ф.args.args]
                if len(пар) == 1 and any(
                        (isinstance(х, ast.Subscript) and isinstance(х.slice, ast.Name) and х.slice.id == пар[0])
                        or (isinstance(х, ast.Call) and isinstance(х.func, ast.Attribute) and х.func.attr == "get"
                            and х.args and isinstance(х.args[0], ast.Name) and х.args[0].id == пар[0])
                        for х in ast.walk(ф)):
                    self.геттери.add(ф.name)
        # ключі, що повторюються в dict-записах модуля (поля запису реєстру), — не ключ поля години
        self.повторні = {}
        for м in модулі:
            лік = {}
            for д in м.вид("Dict"):
                for к in д.keys:
                    р = рядок_константи(к) if к is not None else None
                    if р:
                        лік[р] = лік.get(р, 0) + 1
            self.повторні[м.шлях] = {к for к, н in лік.items() if н >= 3}

    # ── носії ──
    def носій_ім(self, м, ім, вузол, множина="Г"):
        """Чи ім'я в цій області несе годину (вечір із години): локальне — за виводом в області чи параметр з
        ім'ям ключа-носія; глобальне — за спільною множиною."""
        глоб, лок, знач = (self.с.Г, self.с.Л, значуще) if множина == "Г" else (self.с.Е, self.с.ЛЕ, значуще_е)
        к = м.ключ_обл(вузол)
        if к is not None and ім in м.локальні.get(к[1], ()):
            if ім in лок.get(к, ()):
                return True
            return ім in м.параметри.get(к[1], ()) and знач(ім) and ім in глоб
        return знач(ім) and ім in глоб

    def однозначний(self, м, к, ім, множина="Г", назад=False):
        """Локальне ім'я має одне призначення: не змінна циклу й не `+=`, а всі присвоєння — година (для виводу
        вперед) чи не більше двох (для виводу назад): змінна, яку цикл чи гілки наповнюють різними полями, годину
        не несе."""
        значення = м.присвоєння.get((к[1], ім), [])
        if any(з is None for з in значення):
            return False
        if назад:
            return len(значення) <= 2
        перевірка = self.є_година if множина == "Г" else self.є_вечір
        сам = lambda з: any(isinstance(х, ast.Name) and х.id == ім for х in ast.walk(з))   # `г = int(г)` — те саме
        return all(перевірка(м, з) or сам(з) or (isinstance(з, ast.Constant) and з.value in (None, "", False))
                   for з in значення)

    def ключі_ланцюга(self, в):
        """Str-ключі ланцюга підписок `а["к1"]["к2"]` і `.get("к")`."""
        ключі = []
        while True:
            if isinstance(в, ast.Subscript):
                р = рядок_константи(в.slice)
                if р is not None:
                    ключі.append(р)
                в = в.value
            elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "pop", "setdefault") \
                    and в.args and рядок_константи(в.args[0]) is not None:
                ключі.append(рядок_константи(в.args[0]))
                в = в.func.value
            else:
                return ключі

    def ім_виклику(self, в):
        """Ім'я функції виклику (Name чи атрибут) чи None."""
        if isinstance(в.func, ast.Name):
            return в.func.id
        if isinstance(в.func, ast.Attribute):
            return в.func.attr
        return None

    def є_година(self, м, в):
        """Чи вираз дає годину дня (число, рядок годинника чи носій)."""
        if в is None:
            return False
        if isinstance(в, ast.Name):
            return self.носій_ім(м, в.id, в)
        if isinstance(в, ast.Attribute):
            return в.attr in self.с.Г and значуще(в.attr)
        if isinstance(в, ast.Subscript) or (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                                             and в.func.attr in ("get", "pop", "setdefault")):
            if any(к in self.с.Г for к in self.ключі_ланцюга(в)):
                return True
            if isinstance(в, ast.Subscript) and isinstance(в.value, ast.Name) and в.value.id in self.с.КОНВ:
                return True     # таблиця «частина дня → година»
            if isinstance(в, ast.Call) and isinstance(в.func.value, ast.Name) and в.func.value.id in self.с.КОНВ:
                return True
            return False
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if ім in ОБГОРТКИ_PY:
                return any(self.є_година(м, а) for а in в.args)
            if ім and ім in self.с.Г and ім not in self.с.КОНВ:
                return True
            # доступ до поля за назвою: `_пара("hour", с, в.get("hour"))` — значення названого поля години;
            # геттер за самою назвою поля: `_з("година")` (усі аргументи — рядки, один — ключ години)
            if any(рядок_константи(а) in self.с.Г for а in в.args) \
                    and any(self.є_година(м, а) for а in list(в.args) + [к.value for к in в.keywords]):
                return True
            if len(в.args) == 1 and not в.keywords and рядок_константи(в.args[0]) in self.с.Г \
                    and ім in self.геттери:
                return True
            return False
        if isinstance(в, ast.BinOp):
            if isinstance(в.op, ast.Mod) and ціле(в.right) == 24:
                return True
            if isinstance(в.op, ast.Mod) and рядок_константи(в.left) and ФОРМАТ_ГОДИННИКА.search(рядок_константи(в.left)):
                return True
            if isinstance(в.op, (ast.Add, ast.Sub, ast.Mod)):
                return self.є_година(м, в.left) or (isinstance(в.op, (ast.Add, ast.Sub)) and self.є_година(м, в.right))
            return False
        if isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or):
            return any(self.є_година(м, з) for з in в.values)
        if isinstance(в, ast.IfExp):
            return self.є_година(м, в.body) or self.є_година(м, в.orelse)
        р = рядок_константи(в)
        if р is not None:
            return bool(re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", р))
        if isinstance(в, ast.JoinedStr):
            return self.годинник_f(в) is not None
        return False

    def годинник_f(self, в):
        """f-рядок годинника `{г:02d}:{х:02d}` → (вираз години, вираз хвилин) чи None."""
        ч = в.values
        for і in range(len(ч) - 2):
            if isinstance(ч[і], ast.FormattedValue) and рядок_константи(ч[і + 1]) == ":" \
                    and isinstance(ч[і + 2], ast.FormattedValue) and self.дві_цифри(ч[і + 2]):
                return ч[і].value, ч[і + 2].value
        return None

    def дві_цифри(self, в):
        """Формат f-рядка — ціле двома цифрами з нулем (`02d`, `02`): хвилини годинника, а не дріб чи частка."""
        сп = в.format_spec
        текст = "".join(рядок_константи(х) or "" for х in сп.values) if isinstance(сп, ast.JoinedStr) else ""
        return текст in ("02d", "02")

    def є_вечір(self, м, в):
        """Чи вираз — вечір (день), який код рахує з години: порівняння з межею дня чи прапорець із нього."""
        if в is None:
            return False
        if isinstance(в, ast.Compare) and len(в.ops) == 1 and isinstance(в.ops[0], (ast.Gt, ast.GtE, ast.Lt, ast.LtE)):
            а, б = в.left, в.comparators[0]
            for х, у in ((а, б), (б, а)):
                if self.є_година(м, х):
                    ч = ціле(у)
                    if (ч is not None and 12 <= ч <= 22) or (ч is None and рядок_константи(у) is None
                                                               and not isinstance(у, ast.Constant)):
                        return True
            return False
        if isinstance(в, ast.BoolOp):
            return any(self.є_вечір(м, з) for з in в.values)
        if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.Not):
            return self.є_вечір(м, в.operand)
        if isinstance(в, ast.Name):
            return self.носій_ім(м, в.id, в, "Е")
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if ім == "bool":
                return any(self.є_вечір(м, а) for а in в.args)
            if ім in ("get",) and в.args and рядок_константи(в.args[0]) in self.с.Е:
                return True
            return bool(ім) and ім in self.с.Е
        if isinstance(в, ast.Subscript):
            return рядок_константи(в.slice) in self.с.Е
        if isinstance(в, ast.Attribute):
            return в.attr in self.с.Е and значуще_е(в.attr)
        return False

    def джерела(self, м, в):
        """Прямі джерела значення виразу: (вид, ім'я, вузол) — для виводу назад."""
        if в is None:
            return []
        if isinstance(в, ast.Name):
            return [("ім", в.id, в)]
        if isinstance(в, ast.Attribute):
            return [("ключ", в.attr, в)]
        if isinstance(в, ast.Subscript) or (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                                             and в.func.attr in ("get", "pop", "setdefault")):
            вих = [("ключ", к, в) for к in self.ключі_ланцюга(в) if значуще(к)]
            if isinstance(в, ast.Call):
                вих += [д for а in в.args[1:2] for д in self.джерела(м, а)]
            return вих
        if isinstance(в, ast.Call):
            ім = self.ім_виклику(в)
            if ім in ОБГОРТКИ_PY:
                return [д for а in в.args for д in self.джерела(м, а)]
            return [("функція", ім, в)] if ім else []
        if isinstance(в, ast.BinOp):
            return self.джерела(м, в.left) + (self.джерела(м, в.right) if isinstance(в.op, (ast.Add, ast.Sub)) else [])
        if isinstance(в, ast.BoolOp):
            return [д for з in в.values for д in self.джерела(м, з)]
        if isinstance(в, ast.IfExp):
            return self.джерела(м, в.body) + self.джерела(м, в.orelse)
        if isinstance(в, (ast.GeneratorExp, ast.ListComp)):
            return [д for г in в.generators for д in self.джерела(м, г.iter)]
        return []

    def позначити_джерела(self, м, в, де, чому, глобальні=True):
        """Вивід назад: джерела значення, що йде в місце години, теж несуть годину.

        `глобальні=False` (значення ключа dict чи іменованого аргументу) — лише локальні імена й ключі: глобальне
        ім'я там — тип чи опис схеми (`{"година": ЦІЛЕ}`), а не джерело значення."""
        for вид, ім, вузол in self.джерела(м, в):
            if not глобальні and вид == "ім" and not (м.ключ_обл(вузол) and ім in м.локальні.get(м.ключ_обл(вузол)[1], ())):
                continue
            if вид == "функція":
                continue        # назад у функцію не йдемо: помічник загального вжитку ставав би годиною всюди
            if вид == "ім":
                к = м.ключ_обл(вузол)
                if к is not None and ім in м.локальні.get(к[1], ()):
                    if ім not in ЗАГАЛЬНІ and ім not in ЗАГАЛЬНІ_ЛОКАЛЬНІ and self.однозначний(м, к, ім, назад=True):
                        self.с.додати_л(self.с.Л, к, ім)
                elif значуще(ім):
                    self.с.додати(self.с.Г, ім, де, чому)
            elif значуще(ім) and ім not in self.с.КОНВ:
                self.с.додати(self.с.Г, ім, де, чому)

    def позначити_ціль(self, м, ц, де, чому, множина="Г"):
        """Ціль присвоєння несе годину (чи вечір із години)."""
        глоб, лок = (self.с.Г, self.с.Л) if множина == "Г" else (self.с.Е, self.с.ЛЕ)
        знач = значуще if множина == "Г" else значуще_е
        if isinstance(ц, ast.Name):
            к = м.ключ_обл(ц)
            if к is not None:
                if self.однозначний(м, к, ц.id, множина):
                    self.с.додати_л(лок, к, ц.id)
            elif знач(ц.id):
                self.с.додати(глоб, ц.id, де, чому)
        elif isinstance(ц, ast.Subscript):
            р = рядок_константи(ц.slice)
            if знач(р):
                self.с.додати(глоб, р, де, чому)
        elif isinstance(ц, ast.Attribute) and знач(ц.attr):
            self.с.додати(глоб, ц.attr, де, чому)

    def ціль_носій(self, м, ц):
        """Чи ціль присвоєння вже несе годину."""
        if isinstance(ц, ast.Name):
            return self.носій_ім(м, ц.id, ц)
        if isinstance(ц, ast.Subscript):
            return рядок_константи(ц.slice) in self.с.Г
        if isinstance(ц, ast.Attribute):
            return ц.attr in self.с.Г
        return False

    def ключі_записів(self, м, в):
        """Ключі dict-записів, у які вкладено вузол (без полів записів реєстру, що повторюються)."""
        ключі, д = [], в
        while д is not None:
            б = м.батько.get(id(д))
            if isinstance(б, ast.Dict):
                for к, з in zip(б.keys, б.values):
                    if з is д and к is not None and значуще(рядок_константи(к)) \
                            and рядок_константи(к) not in self.повторні[м.шлях]:
                        ключі.append(рядок_константи(к))
            elif isinstance(б, ast.keyword) and значуще(б.arg) and б.arg not in self.повторні[м.шлях]:
                ключі.append(б.arg)
            д = б
        return ключі

    # ── один прохід виводу ──
    def прохід(self, м):
        с = self.с
        де = lambda в: "%s:%d" % (м.шлях, getattr(в, "lineno", 0))
        # зерна: схема 0–23
        for в in м.вид("Call", "Dict"):
            if self.схема_доби(в):
                for к in self.ключі_записів(м, в):
                    с.додати(с.Г, к, де(в), "схема числа 0–23")
        # зерна: перетворювачі й таблиці частини дня
        for ф in м.функції:
            пар = self.перетворювач(м, ф)
            if пар is not None:
                с.додати(с.КОНВ, ф.name, де(ф), "перетворювач година → частина дня")
                for п in пар:
                    с.додати_л(с.Л, (м.шлях, id(ф)), п)
            if self.вечір_функція(м, ф):
                с.додати(с.Е, ф.name, де(ф), "вечір із години (поріг дня)")
        for в in м.вид("Assign"):
            if isinstance(в.value, ast.Dict) and self.таблиця_пори(в.value):
                for ц in в.targets:
                    if isinstance(ц, ast.Name):
                        с.додати(с.КОНВ, ц.id, де(в), "таблиця частина дня → година")
                        с.додати(с.Г, ц.id, де(в), "таблиця частина дня → година")
        # зерна: формат годинника й арифметика доби
        for в in м.вид("BinOp"):
            л = рядок_константи(в.left)
            if isinstance(в.op, ast.Mod) and л and ФОРМАТ_ГОДИННИКА.search(л):
                частини = в.right.elts[:2] if isinstance(в.right, ast.Tuple) else [в.right]
                for ч in частини:
                    self.позначити_джерела(м, ч, де(в), "формат годинника %02d:%02d")
            if isinstance(в.op, ast.Mod) and ціле(в.right) == 24:
                self.позначити_джерела(м, в.left, де(в), "арифметика доби % 24")
        for в in м.вид("JoinedStr"):
            пара = self.годинник_f(в)
            if пара:
                for ч in пара:
                    self.позначити_джерела(м, ч, де(в), "f-рядок годинника")
        for в in м.вид("Call"):
            if isinstance(в.func, ast.Attribute) and в.func.attr == "format" and рядок_константи(в.func.value) \
                    and ФОРМАТ_ГОДИННИКА.search(рядок_константи(в.func.value)):
                for а in в.args[:2]:
                    self.позначити_джерела(м, а, де(в), "формат годинника {:02d}:{:02d}")
        # зерна: опис поля словами годинника
        for в in м.вид("Dict"):
            for к, з in zip(в.keys, в.values):
                рк, рз = (рядок_константи(к) if к is not None else None), рядок_константи(з)
                поч = (рз or "")[:60]
                if значуще(рк) and рз and (ГОДИНА_EN.search(поч) or ГОДИНА_UK.search(поч) or ХВИЛИНИ_EN.search(поч)) \
                        and not ДОВГА.search(поч):
                    с.додати(с.Г, рк, де(з), "опис поля словами годинника")
        # функції переводу: повертають результат перетворювача від години (`_година_при_порі`)
        for ф in м.функції:
            if ф.name in с.КОНВ or ф.name in с.ПЕР:
                continue
            виклики = [х for х in ast.walk(ф) if isinstance(х, ast.Call) and self.ім_виклику(х) in с.КОНВ
                       and any(self.є_година(м, а) for а in х.args)]
            if not виклики:
                continue
            імена = {ц.id for х in ast.walk(ф) if isinstance(х, ast.Assign) and any(х.value is в for в in виклики)
                     for ц in х.targets if isinstance(ц, ast.Name)}
            for х in ast.walk(ф):
                if isinstance(х, ast.Return) and х.value is not None and any(
                        (isinstance(у, ast.Name) and у.id in імена) or any(у is в for в in виклики)
                        for у in ast.walk(х.value)):
                    с.додати(с.ПЕР, ф.name, де(ф), "повертає частину дня, переведену з години")
                    break
        # під-ключі записів поля години, які читають у носій години: `X["година"]["названа"]`
        for в in м.вид("Assign"):
            if len(в.targets) == 1 and self.є_година(м, в.value) and isinstance(в.value, ast.Subscript):
                ключі = self.ключі_ланцюга(в.value)
                for і in range(len(ключі) - 1):
                    if ключі[і + 1] in с.Г and ключі[і] not in с.Г:
                        self.під_ключі.add((ключі[і + 1], ключі[і]))
        # потік: присвоєння
        for в in м.вид("Assign", "AnnAssign"):
            цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
            if в.value is None:
                continue
            for ц in цілі:
                пари = list(zip(ц.elts, в.value.elts)) if isinstance(ц, ast.Tuple) and isinstance(в.value, ast.Tuple) \
                    and len(ц.elts) == len(в.value.elts) else [(ц, в.value)]
                if len(пари) > 1 and any(self.є_година(м, з) for _, з in пари):
                    for ціль, знач in пари:
                        if isinstance(знач, ast.Constant) and isinstance(знач.value, bool) \
                                and isinstance(ціль, ast.Subscript) and значуще(рядок_константи(ціль.slice)):
                            с.додати(с.С, рядок_константи(ціль.slice), де(в), "прапорець походження години")
                if isinstance(ц, ast.Tuple) and ц.elts and isinstance(в.value, ast.Call) and len(пари) == 1:
                    пари = [(ц.elts[0], в.value)]     # (значення, цитата) поля — година лише першим
                for ціль, знач in пари:
                    if self.є_година(м, знач):
                        self.позначити_ціль(м, ціль, де(в), "присвоєно годину")
                    elif self.ціль_носій(м, ціль):
                        self.позначити_джерела(м, знач, де(в), "джерело години")
                    if self.є_вечір(м, знач):
                        self.позначити_ціль(м, ціль, де(в), "присвоєно вечір із години", "Е")
        # потік: повернення
        for в in м.вид("Return"):
            ф = м.функція_області(в)
            if ф is None or в.value is None:
                continue
            if self.є_година(м, в.value) and ф.name not in с.КОНВ and значуще(ф.name):
                с.додати(с.Г, ф.name, де(в), "повертає годину")
            elif ф.name in с.Г and ф.name not in с.КОНВ:
                self.позначити_джерела(м, в.value, де(в), "джерело години, яку повертає функція")
            if isinstance(в.value, (ast.Compare, ast.BoolOp, ast.UnaryOp, ast.Name, ast.Call)) \
                    and self.є_вечір(м, в.value) and значуще_е(ф.name) and ф.name not in с.КОНВ:
                с.додати(с.Е, ф.name, де(в), "повертає вечір із години")
        # потік: виклики (іменовані аргументи, параметри)
        for в in м.вид("Call"):
            for кв in в.keywords:
                if not кв.arg:
                    continue
                if self.є_година(м, кв.value) and значуще(кв.arg):
                    с.додати(с.Г, кв.arg, де(в), "іменований аргумент з годиною")
                elif кв.arg in с.Г:
                    self.позначити_джерела(м, кв.value, де(в), "джерело години в аргументі", глобальні=False)
                if self.є_вечір(м, кв.value) and значуще_е(кв.arg):
                    с.додати(с.Е, кв.arg, де(в), "аргумент — вечір із години")
            ім = self.ім_виклику(в)
            if ім and значуще(ім) and ім in self.визначення:
                for мм, ф in self.визначення[ім]:
                    пар = [а.arg for а in ф.args.posonlyargs + ф.args.args]
                    if пар and пар[0] in ("self", "cls") and isinstance(в.func, ast.Attribute):
                        пар = пар[1:]
                    for і, а in enumerate(в.args):
                        if і < len(пар) and значуще(пар[і]):
                            if self.є_година(м, а):
                                с.додати_л(с.Л, (мм.шлях, id(ф)), пар[і])
                            if self.є_вечір(м, а):
                                с.додати_л(с.ЛЕ, (мм.шлях, id(ф)), пар[і])
        # потік: dict-літерали й таблиці відповідності ключів
        for в in м.вид("Dict"):
            for к, з in zip(в.keys, в.values):
                рк = рядок_константи(к) if к is not None else None
                if not значуще(рк):
                    continue
                if self.є_година(м, з):
                    с.додати(с.Г, рк, де(з), "ключ dict з годиною")
                elif рк in с.Г:
                    self.позначити_джерела(м, з, де(з), "джерело години в dict", глобальні=False)
        for в in м.вид("Tuple", "List"):
            if len(в.elts) >= 2 and all(isinstance(е, ast.Tuple) and len(е.elts) >= 2
                                        and all(рядок_константи(х) is not None for х in е.elts) for е in в.elts):
                for е in в.elts:
                    рр = [рядок_константи(х) for х in е.elts]
                    if any(р in с.Г for р in рр):
                        for р in рр:
                            if ідентоподібне(р) and значуще(р):
                                с.додати(с.Г, р, де(е), "пара ключів у таблиці відповідності")
        # поріг: з чим годину порівнюють
        for в in м.вид("Compare"):
            сторони = [в.left] + list(в.comparators)
            for і, оп in enumerate(в.ops):
                if not isinstance(оп, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)):
                    continue
                а, б = сторони[і], сторони[і + 1]
                for х, у in ((а, б), (б, а)):
                    if self.є_година(м, х) and not isinstance(у, ast.Constant) and not self.є_година(м, у):
                        self.позначити_джерела(м, у, де(в), "поріг, з яким порівнюють годину")
        # частина дня (для перевірки правил бази): ключі, яким дають слово пори чи перетворювач
        for в in м.вид("keyword"):
            if в.arg and (рядок_константи(в.value) in СЛОВА_ПОРИ or (isinstance(в.value, ast.Call)
                                                                     and self.ім_виклику(в.value) in с.КОНВ)):
                с.додати(с.П, в.arg, де(в.value), "ключ частини дня")
        for в in м.вид("Dict"):
            for к, з in zip(в.keys, в.values):
                рк = рядок_константи(к) if к is not None else None
                if значуще(рк) and рядок_константи(з) in СЛОВА_ПОРИ:
                    с.додати(с.П, рк, де(з), "ключ частини дня")

    def схема_доби(self, в):
        """Схема числа 0–23: `minimum=0, maximum=23|24` у виклику чи dict."""
        if isinstance(в, ast.Call):
            кв = {к.arg: ціле(к.value) for к in в.keywords if к.arg}
        else:
            кв = {рядок_константи(к): ціле(з) for к, з in zip(в.keys, в.values) if к is not None}
        return кв.get("minimum") == 0 and кв.get("maximum") in (23, 24)

    def схема_доби_в(self, запис, вузол):
        """Вузол лежить у схемі числа 0–23 всередині запису (опис поля для моделі)."""
        for х in ast.walk(запис):
            if isinstance(х, (ast.Call, ast.Dict)) and self.схема_доби(х) and any(у is вузол for у in ast.walk(х)):
                return True
        return False

    def перетворювач(self, м, ф):
        """Параметри, які функція порівнює з числами доби, коли повертає частину дня; None — не перетворювач."""
        пар = м.параметри.get(id(ф), [])
        if not пар:
            return None
        слова = {рядок_константи(в) for в in ast.walk(ф) if рядок_константи(в) in СЛОВА_ПОРИ}
        повертає = any(isinstance(в, ast.Return) and в.value is not None and any(
            рядок_константи(х) in СЛОВА_ПОРИ for х in ast.walk(в.value)) for в in ast.walk(ф))
        if len(слова) < 2 or not повертає:
            return None
        знайдені, числа = set(), set()
        for в in ast.walk(ф):
            if isinstance(в, ast.Compare) and any(isinstance(о, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)) for о in в.ops):
                сторони = [в.left] + list(в.comparators)
                імена = {х.id for х in сторони if isinstance(х, ast.Name) and х.id in пар}
                ч = {ціле(х) for х in сторони if ціле(х) is not None and 0 < ціле(х) < 24}
                if імена and ч:
                    знайдені |= імена
                    числа |= ч
        return sorted(знайдені) if знайдені and len(числа) >= 2 else None

    def є_поріг(self, х):
        """Вираз — поріг години (ключ реєстру чи ім'я, виведене як межа, з якою порівнюють годину)."""
        імена = self.ключі_ланцюга(х) if isinstance(х, (ast.Subscript, ast.Call)) else \
            [х.id] if isinstance(х, ast.Name) else [х.attr] if isinstance(х, ast.Attribute) else []
        return any("поріг" in self.с.звідки.get(і, "") for і in імена)

    def вечір_функція(self, м, ф):
        """Функція повертає порівняння години з межею дня (вечір із години)."""
        if ф.name in self.с.КОНВ:
            return False
        for в in ast.walk(ф):
            if isinstance(в, ast.Return) and isinstance(в.value, (ast.Compare, ast.BoolOp, ast.UnaryOp)) \
                    and self.є_вечір(м, в.value):
                return True
        return False

    def таблиця_пори(self, д):
        """Dict «частина дня → число 0–23» (≥2 записи)."""
        пари = [(рядок_константи(к) if к is not None else None, ціле(з)) for к, з in zip(д.keys, д.values)]
        добрі = [п for п in пари if п[0] in СЛОВА_ПОРИ and п[1] is not None and 0 <= п[1] <= 23]
        return len(добрі) >= 2 and len(добрі) == len(пари)

    # ── місця ──
    def місця(self, м, додати):
        с = self.с
        for в in м.вузли:
            р = getattr(в, "lineno", None)
            if р is None:
                continue
            if isinstance(в, ast.Call) and self.ім_виклику(в) in с.ПЕР:
                додати(м.шлях, р, 3, "виклик переводу години «%s»" % self.ім_виклику(в))
            if isinstance(в, ast.Subscript) and ціле(в.slice) == 0 and isinstance(в.value, ast.Call) \
                    and self.ім_виклику(в.value) == "split" and в.value.args and рядок_константи(в.value.args[0]) == ":":
                # година з рядка годинника: «18:00» → 18 — у гілці `":" in т`, і ліва частина далі стає числом
                п = м.батько.get(id(в))
                б = м.батько.get(id(п))
                ф = м.функція_області(в)
                ціль = п.targets[0].id if isinstance(п, ast.Assign) and isinstance(п.targets[0], ast.Name) else None
                if ціль and ф is not None and isinstance(б, ast.If) and any(
                        isinstance(х, ast.Compare) and any(isinstance(о, ast.In) for о in х.ops)
                        and рядок_константи(х.left) == ":" for х in ast.walk(б.test)) and any(
                        isinstance(х, ast.Call) and self.ім_виклику(х) in ("float", "int") and х.args
                        and isinstance(х.args[0], ast.Name) and х.args[0].id == ціль for х in ast.walk(ф)):
                    додати(м.шлях, р, 1, "година з рядка годинника відповіді split(':')[0] → число")
                    додати(м.шлях, б.test.lineno, 1, "рядок годинника «ГГ:ХХ» у відповіді моделі")
            if isinstance(в, ast.Name):
                if self.носій_ім(м, в.id, в):
                    додати(м.шлях, р, 2, "ім'я «%s» несе годину" % в.id)
                if в.id in с.КОНВ:
                    додати(м.шлях, р, 3, "перетворювач «%s»" % в.id)
                if self.є_вечір(м, в):
                    додати(м.шлях, р, 5, "вечір із години «%s»" % в.id)
            elif isinstance(в, ast.Attribute):
                if в.attr in с.Г and значуще(в.attr):
                    додати(м.шлях, р, 2, "атрибут «%s» несе годину" % в.attr)
                if в.attr in с.КОНВ:
                    додати(м.шлях, р, 3, "перетворювач «%s»" % в.attr)
                if в.attr in с.Е and значуще_е(в.attr):
                    додати(м.шлях, р, 5, "вечір із години «%s»" % в.attr)
            elif isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if в.name in с.ПЕР:
                    додати(м.шлях, р, 3, "функція «%s» переводить годину в частину дня" % в.name)
                    for х in ast.walk(в):
                        if isinstance(х, ast.Constant) and х.value in с.П and isinstance(м.батько.get(id(х)), ast.Call):
                            додати(м.шлях, х.lineno, 3, "частина дня проти години в «%s»" % в.name)
                if в.name in с.Г:
                    додати(м.шлях, р, 2, "функція «%s» дає годину" % в.name)
                if в.name in с.КОНВ:
                    додати(м.шлях, р, 3, "перетворювач «%s»" % в.name)
                if в.name in с.Е:
                    додати(м.шлях, р, 5, "функція «%s» — вечір із години" % в.name)
                к = (м.шлях, id(в))
                типові = в.args.defaults
                пар = в.args.posonlyargs + в.args.args
                for а, т in list(zip(пар[len(пар) - len(типові):], типові)) + \
                        list(zip(в.args.kwonlyargs, в.args.kw_defaults)):
                    if (а.arg in с.Г or а.arg in с.Л.get(к, ())) and ціле(т) is not None and 0 <= ціле(т) <= 23:
                        додати(м.шлях, т.lineno, 3, "типова година %d" % ціле(т))
            elif isinstance(в, ast.arg):
                обл = м.батько.get(id(м.батько.get(id(в))))
                к = (м.шлях, id(обл)) if обл is not None else None
                if (значуще(в.arg) and в.arg in с.Г) or (к and в.arg in с.Л.get(к, ())):
                    додати(м.шлях, р, 2, "параметр «%s» несе годину" % в.arg)
                if (значуще_е(в.arg) and в.arg in с.Е) or (к and в.arg in с.ЛЕ.get(к, ())):
                    додати(м.шлях, р, 5, "параметр «%s» — вечір із години" % в.arg)
            elif isinstance(в, ast.keyword):
                if в.arg and в.arg in с.Г:
                    додати(м.шлях, р, 2, "аргумент «%s=» несе годину" % в.arg)
                    if ціле(в.value) is not None and 0 <= ціле(в.value) <= 23:
                        додати(м.шлях, р, 3, "типова година %d" % ціле(в.value))
                if в.arg and в.arg in с.Е:
                    додати(м.шлях, р, 5, "аргумент «%s=» — вечір із години" % в.arg)
            elif isinstance(в, ast.alias):
                if в.name in с.Г or в.name in с.КОНВ or в.name in с.Е:
                    додати(м.шлях, р, 3 if в.name in с.КОНВ else 5 if в.name in с.Е else 2,
                           "імпорт «%s»" % в.name)
            elif isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in м.докстрінги:
                self.місця_рядка(м, в, додати)
            elif isinstance(в, ast.Compare):
                сторони = [в.left] + list(в.comparators)
                if any(self.є_година(м, х) for х in сторони):
                    if any(ціле(х) is not None and 0 < ціле(х) < 23 for х in сторони) or \
                            any(not isinstance(х, ast.Constant) and (not self.є_година(м, х) or self.є_поріг(х))
                                for х in сторони
                                if any(isinstance(о, (ast.Gt, ast.GtE, ast.Lt, ast.LtE)) for о in в.ops)):
                        додати(м.шлях, р, 3, "порівняння години з межею дня")
                    ф = м.функція_області(в)
                    if self.є_вечір(м, в) and not (ф is not None and ф.name in с.КОНВ):
                        додати(м.шлях, р, 5, "вечір рахує година, а не частина дня")
            elif isinstance(в, ast.BinOp):
                л = рядок_константи(в.left)
                if isinstance(в.op, ast.Mod) and ціле(в.right) == 24:
                    додати(м.шлях, р, 3, "арифметика доби % 24")
                if isinstance(в.op, ast.Mod) and л and ФОРМАТ_ГОДИННИКА.search(л):
                    додати(м.шлях, р, 4, "годинник рядком %02d:%02d")
            elif isinstance(в, ast.JoinedStr) and self.годинник_f(в):
                додати(м.шлях, р, 4, "годинник рядком (f-рядок)")
            elif isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or):
                if any(self.є_година(м, х) for х in в.values) and any(
                        ціле(х) is not None and 0 <= ціле(х) <= 23 for х in в.values):
                    додати(м.шлях, р, 3, "типова година (or N)")
            elif isinstance(в, ast.Call):
                if isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "setdefault") and len(в.args) >= 2 \
                        and рядок_константи(в.args[0]) in с.Г and ціле(в.args[1]) is not None:
                    додати(м.шлях, р, 3, "типова година в .get(…, %d)" % ціле(в.args[1]))
                ім = self.ім_виклику(в)
                if ім in с.КОНВ and any(self.є_година(м, а) for а in в.args):
                    додати(м.шлях, р, 3, "година → частина дня («%s»)" % ім)
                if self.схема_доби(в):
                    додати(м.шлях, р, 1, "схема числа 0–23")
                if isinstance(в.func, ast.Attribute) and в.func.attr in ("get",) and в.args \
                        and рядок_константи(в.args[0]) in с.Е:
                    додати(м.шлях, р, 5, "вечір із години «%s»" % рядок_константи(в.args[0]))
            elif isinstance(в, ast.Subscript):
                рк = рядок_константи(в.slice)
                if рк in с.Е and значуще_е(рк):
                    додати(м.шлях, р, 5, "вечір із години «%s»" % рк)
            elif isinstance(в, (ast.Assign, ast.AnnAssign)):
                цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                if в.value is not None and ціле(в.value) is not None and 0 <= ціле(в.value) <= 23 \
                        and any(self.ціль_носій(м, ц) for ц in цілі):
                    додати(м.шлях, р, 3, "типова година %d" % ціле(в.value))
            elif isinstance(в, ast.Dict):
                if self.таблиця_пори(в):
                    додати(м.шлях, р, 3, "таблиця частина дня → година")
                if self.схема_доби(в):
                    додати(м.шлях, р, 1, "схема числа 0–23")
                for к, з in zip(в.keys, в.values):
                    if к is not None and рядок_константи(к) in с.Г and ціле(з) is not None and 0 <= ціле(з) <= 23:
                        додати(м.шлях, з.lineno, 3, "типова година %d" % ціле(з))
                    if к is not None and рядок_константи(к) in с.Г and isinstance(з, ast.Dict):
                        # запис поля години в реєстрі: місце — під-ключ, який код читає ланцюгом від ключа години
                        # (`ПОЛЯ_ПАСПОРТА["година"]["названа"]` у носій години), а не кожен рядок запису
                        for пк, пз in zip(з.keys, з.values):
                            if пк is not None and (рядок_константи(к), рядок_константи(пк)) in self.під_ключі:
                                додати(м.шлях, пк.lineno, 2, "під-ключ «%s» поля «%s» читають у носій години"
                                       % (рядок_константи(пк), рядок_константи(к)))
            elif isinstance(в, ast.Tuple):
                рр = [рядок_константи(х) for х in в.elts]
                if any(р in с.Г for р in рр if р) and any(р and re.fullmatch(r"(?:[01]?\d|2[0-3])(?::00)?", р) for р in рр):
                    додати(м.шлях, р, 3, "типова година поля показу")

    def місця_рядка(self, м, в, додати):
        """Рядкова константа: ключ-носій як дані, текст годинника в промпті, описі чи написі."""
        с = self.с
        if в.value in с.Г:
            б = м.батько.get(id(в))
            ascii_читання = в.value.isascii() and (
                (isinstance(б, ast.Subscript) and isinstance(б.ctx, ast.Load))
                or (isinstance(б, ast.Call) and isinstance(б.func, ast.Attribute) and б.func.attr in ("get", "pop"))
                or isinstance(б, ast.Compare))
            додати(м.шлях, в.lineno, 1 if ascii_читання else 2,
                   "ключ «%s»%s" % (в.value, " читають із відповіді моделі" if ascii_читання else " як дані"))
            if "поріг" in с.звідки.get(в.value, ""):
                додати(м.шлях, в.lineno, 3, "поріг години «%s» (реєстр)" % в.value)
            return
        if в.value in с.С:
            додати(м.шлях, в.lineno, 3, "прапорець походження години «%s»" % в.value)
            return
        if в.value in с.Е and isinstance(м.батько.get(id(в)), (ast.Subscript,)):
            return
        if not в.value.strip() or re.search(r"(?m)^assert ", в.value):
            return      # порожнє; код гейта рядком (стенд збирання з `assert`) — тест, не продукт
        кінець = getattr(в, "end_lineno", в.lineno) or в.lineno
        схема = any(self.схема_доби(б) for б in self.предки(м, в) if isinstance(б, (ast.Call, ast.Dict)))
        for рядок in range(в.lineno, кінець + 1):
            сирий = м.рядки[рядок - 1] if рядок - 1 < len(м.рядки) else ""
            if в.lineno == кінець:
                сирий = в.value
            причини = текст_години(сирий)
            токени = токени_носіїв(сирий, с.Г)
            if not причини and not токени:
                continue
            англ = sum(ч.isascii() and ч.isalpha() for ч in сирий) > sum(not ч.isascii() and ч.isalpha() for ч in сирий)
            пункт = 1 if (англ or схема) else 2
            додати(м.шлях, рядок, пункт, "текст: " + "; ".join(причини + ["ключ «%s»" % т for т in токени[:2]]))

    def предки(self, м, в):
        """Батьки вузла до модуля."""
        б = м.батько.get(id(в))
        while б is not None:
            yield б
            б = м.батько.get(id(б))


# ── JS і HTML ───────────────────────────────────────────────────────────────────────────────────────────────────
ОП3 = ("===", "!==", "**=", "...", ">>>", "<<=", ">>=", "&&=", "||=", "??=")
ОП2 = ("==", "!=", "<=", ">=", "&&", "||", "??", "=>", "?.", "++", "--", "+=", "-=", "*=", "/=", "%=", "**",
       "<<", ">>", "|=", "&=", "^=")
ПЕРЕД_РЕГУЛЯРКОЮ = set("(,=:[!&|?{};+-*%<>~^") | {"return", "typeof", "case", "do", "else", "in", "of", "new",
                                                 "delete", "void", "throw", "=>", "&&", "||", "??", "==", "===",
                                                 "!=", "!==", "<=", ">="}


def лексер_js(т, перший_рядок=1):
    """Токени JS: (вид, значення, рядок); вид — ім, ряд, чис, оп. Коментарі відкинуто, шаблони розгорнуто."""
    токени, і, р, н = [], 0, перший_рядок, len(т)
    стек = []          # для `${`: глибина дужок у виразі шаблону

    def попередній():
        return токени[-1] if токени else None

    def шаблон(і, р):
        """Читає текст шаблону від `і` до «`» чи «${»; → (і, р, кінець_шаблону)."""
        поч, поч_р, буф = і, р, []
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
            п = попередній()
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
    """Файл JS (чи скрипти HTML): токени, верхні сегменти, локальні імена."""

    def __init__(self, шлях, токени, html=None):
        self.шлях = шлях
        self.т = токени
        self.html = html or []
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
        self.локальні = {}
        for і, (вид, зн, _) in enumerate(токени):
            if вид == "ім" and зн in ("const", "let", "var") and і + 1 < len(токени) and токени[і + 1][0] == "ім":
                self.локальні.setdefault(self.сегмент[і], set()).add(токени[і + 1][1])
        # параметри функцій
        for і, (вид, зн, _) in enumerate(токени):
            if вид == "ім" and зн == "function":
                j = і + 1
                while j < len(токени) and токени[j][1] != "(":
                    j += 1
                j += 1
                while j < len(токени) and токени[j][1] != ")":
                    if токени[j][0] == "ім":
                        self.локальні.setdefault(self.сегмент[j], set()).add(токени[j][1])
                    j += 1


class АналізДжс:
    """Правила виводу й місць для JS і HTML поверх спільного `Стан`."""

    def __init__(self, файли, стан):
        self.файли = файли
        self.с = стан

    def властивість(self, ф, і):
        """Токен — властивість після `.`/`?.`."""
        return і > 0 and ф.т[і - 1][0] == "оп" and ф.т[і - 1][1] in (".", "?.")

    def носій(self, ф, і):
        """Чи токен `і` (ім'я чи властивість) несе годину."""
        вид, зн, _ = ф.т[і]
        if вид != "ім":
            return False
        if self.властивість(ф, і):
            return зн in self.с.Г and значуще(зн)
        if значуще(зн) and зн in self.с.Г:
            return True
        return зн in self.с.Л.get((ф.шлях, ф.сегмент[і]), ())

    def кінець_виразу(self, ф, поч):
        """Індекс за кінцем виразу від `поч` (до `;`/`,`/закриття дужки на тій самій глибині)."""
        глиб, і = 0, поч
        while і < len(ф.т):
            вид, зн, _ = ф.т[і]
            if вид == "оп":
                if зн in "([{":
                    глиб += 1
                elif зн in ")]}":
                    if глиб == 0:
                        return і
                    глиб -= 1
                elif зн in (";", ",") and глиб == 0:
                    return і
            і += 1
        return і

    def розбити(self, ф, а, б, оп_набір):
        """Розбиває відрізок токенів за операторами верхнього рівня."""
        частини, глиб, поч = [], 0, а
        for і in range(а, б):
            вид, зн, _ = ф.т[і]
            if вид == "оп" and зн in "([{":
                глиб += 1
            elif вид == "оп" and зн in ")]}":
                глиб -= 1
            elif вид == "оп" and глиб == 0 and зн in оп_набір:
                частини.append((поч, і))
                поч = і + 1
        частини.append((поч, б))
        return частини

    def є_година(self, ф, а, б):
        """Чи відрізок токенів [а, б) — вираз години."""
        while а < б and ф.т[а][1] == "(" and self.парна(ф, а) == б - 1:
            а, б = а + 1, б - 1
        if а >= б:
            return False
        тернарні = self.розбити(ф, а, б, ("?",))
        if len(тернарні) > 1:
            гілки = self.розбити(ф, тернарні[1][0], б, (":",))
            return any(self.є_година(ф, x, y) for x, y in гілки)
        if len(self.розбити(ф, а, б, ("<", ">", "<=", ">=", "===", "!==", "==", "!="))) > 1:
            return False
        for ops in (("||", "??"), ("&&",), ("+", "-")):
            частини = self.розбити(ф, а, б, ops)
            if len(частини) > 1:
                if ops == ("&&",):
                    return self.є_година(ф, *частини[-1])
                return any(self.є_година(ф, x, y) for x, y in частини)
        return self.є_первинне_година(ф, а, б)

    def парна(self, ф, і):
        """Індекс парної дужки для `ф.т[і]`."""
        пари = {"(": ")", "[": "]", "{": "}"}
        відкр, закр, глиб = ф.т[і][1], пари.get(ф.т[і][1]), 0
        for j in range(і, len(ф.т)):
            if ф.т[j][0] == "оп" and ф.т[j][1] == відкр:
                глиб += 1
            elif ф.т[j][0] == "оп" and ф.т[j][1] == закр:
                глиб -= 1
                if глиб == 0:
                    return j
        return len(ф.т) - 1

    def є_первинне_година(self, ф, а, б):
        """Ланцюг `ім(.в|[..]|(..))*`, рядок годинника чи обгортка числа."""
        вид, зн, _ = ф.т[а]
        if вид == "ряд":
            return б - а == 1 and bool(re.fullmatch(r"(?:[01]?\d|2[0-3]):[0-5]\d", зн))
        if вид != "ім":
            return False
        if зн == "new" and а + 1 < б:
            return self.є_первинне_година(ф, а + 1, б)
        # обгортки числа й рядка
        if зн in ОБГОРТКИ_JS:
            j = а + 1
            while j < б and ф.т[j][1] in (".",) or (j < б and ф.т[j][0] == "ім" and ф.т[j - 1][1] == "."):
                j += 1
            if j < б and ф.т[j][1] == "(":
                к = self.парна(ф, j)
                арг = self.розбити(ф, j + 1, к, (",",))
                return bool(арг) and self.є_година(ф, *арг[0])
            return False
        # $('ід').value / getElementById('ід').value
        if зн in ("$", "getElementById", "querySelector") and а + 2 < б and ф.т[а + 1][1] == "(" \
                and ф.т[а + 2][0] == "ряд":
            ід = ф.т[а + 2][1].lstrip("#")
            к = self.парна(ф, а + 1)
            хвіст = [x[1] for x in ф.т[к + 1:б]]
            return ід in self.с.Г and хвіст[:2] in ([".", "value"], ["||", "{"]) or (
                ід in self.с.Г and ".value" in "".join(хвіст))
        носій = self.носій(ф, а)
        j = а + 1
        while j < б:
            з = ф.т[j][1]
            if з in (".", "?.") and j + 1 < б and ф.т[j + 1][0] == "ім":
                носій = ф.т[j + 1][1] in self.с.Г and значуще(ф.т[j + 1][1])
                j += 2
            elif з == "[":
                к = self.парна(ф, j)
                if к == j + 2 and ф.т[j + 1][0] == "ряд":
                    носій = ф.т[j + 1][1] in self.с.Г
                else:
                    носій = False
                j = к + 1
            elif з == "(":
                назва = ф.т[j - 1][1] if ф.т[j - 1][0] == "ім" else None
                носій = bool(назва) and значуще(назва) and назва in self.с.Г and назва not in self.с.КОНВ
                j = self.парна(ф, j) + 1
            else:
                return False
        return носій

    def джерела(self, ф, а, б):
        """Імена, властивості й ід полів у відрізку — джерела значення (вивід назад)."""
        вих = []
        for і in range(а, б):
            вид, зн, _ = ф.т[і]
            if вид == "ім" and зн not in ЗАГАЛЬНІ and зн not in ОБГОРТКИ_JS:
                вих.append(("властивість" if self.властивість(ф, і) else "ім", зн, і))
            elif вид == "ряд" and і >= 2 and ф.т[і - 1][1] == "(" and ф.т[і - 2][1] in ("$", "getElementById"):
                вих.append(("ід", зн.lstrip("#"), і))
        return вих

    def позначити_джерела(self, ф, а, б, де, чому):
        for вид, зн, і in self.джерела(ф, а, б):
            к = (ф.шлях, ф.сегмент[і])
            if вид == "ім" and зн in ф.локальні.get(ф.сегмент[і], ()):
                if зн not in ЗАГАЛЬНІ_ЛОКАЛЬНІ and зн not in ЗАГАЛЬНІ:
                    self.с.додати_л(self.с.Л, к, зн)
            elif значуще(зн) or вид == "ід":
                self.с.додати(self.с.Г, зн, де, чому)

    def прохід(self, ф):
        с, т = self.с, ф.т
        де = lambda і: "%s:%d" % (ф.шлях, т[і][2])
        for зерно in ф.html:
            с.додати(с.Г, зерно[0], "%s:%d" % (ф.шлях, зерно[1]), "поле панелі min=0 max=23")
        for і, (вид, зн, _) in enumerate(т):
            # формат годинника: String(X).padStart(2,'0') поруч із ':'
            if вид == "ім" and зн == "padStart" and і >= 2 and т[і - 1][1] == "." and т[і - 2][1] == ")":
                поч = self.відкрита(ф, і - 2)
                if поч is not None and поч >= 1 and т[поч - 1][1] in ("String",):
                    околиця = [x[1] for x in т[max(0, поч - 6):min(len(т), і + 12)] if x[0] == "ряд"]
                    if ":" in околиця:
                        self.позначити_джерела(ф, поч + 1, і - 2, де(і), "формат годинника padStart + ':'")
            # присвоєння: const|let|var X = …, X = …, об.в = …
            if вид == "оп" and зн == "=" and і >= 1:
                ціль = т[і - 1]
                кін = self.кінець_виразу(ф, і + 1)
                if ціль[0] == "ім":
                    нова = self.є_година(ф, і + 1, кін)
                    к = (ф.шлях, ф.сегмент[і])
                    локальна = ціль[1] in ф.локальні.get(ф.сегмент[і], ()) and not self.властивість(ф, і - 1)
                    if нова:
                        if локальна:
                            if self.однозначний(ф, і - 1):
                                с.додати_л(с.Л, к, ціль[1])
                        elif значуще(ціль[1]):
                            с.додати(с.Г, ціль[1], де(і), "присвоєно годину")
                    elif self.носій(ф, і - 1):
                        self.позначити_джерела(ф, і + 1, кін, де(і), "джерело години")
            # ключ об'єкта: { ключ: вираз }
            if вид == "оп" and зн == ":" and і >= 2 and т[і - 1][0] in ("ім", "ряд") and т[і - 2][1] in ("{", ","):
                ключ = т[і - 1][1]
                кін = self.кінець_виразу(ф, і + 1)
                if значуще(ключ):
                    if self.є_година(ф, і + 1, кін):
                        с.додати(с.Г, ключ, де(і), "ключ об'єкта з годиною")
                    elif ключ in с.Г:
                        self.позначити_джерела(ф, і + 1, кін, де(і), "джерело години в об'єкті")
            # повернення функції
            if вид == "ім" and зн == "return":
                назва = self.назва_функції(ф, і)
                кін = self.кінець_виразу(ф, і + 1)
                if назва and значуще(назва):
                    if self.є_година(ф, і + 1, кін):
                        с.додати(с.Г, назва, де(і), "повертає годину")
                    elif назва in с.Г:
                        self.позначити_джерела(ф, і + 1, кін, де(і), "джерело години, яку повертає функція")
            # стрілка-тіло: const f = () => вираз
            if вид == "оп" and зн == "=>" and і + 1 < len(т) and т[і + 1][1] != "{":
                назва = self.назва_стрілки(ф, і)
                кін = self.кінець_виразу(ф, і + 1)
                if назва and значуще(назва):
                    if self.є_година(ф, і + 1, кін):
                        с.додати(с.Г, назва, де(і), "повертає годину")
                    elif назва in с.Г:
                        self.позначити_джерела(ф, і + 1, кін, де(і), "джерело години, яку повертає функція")
            # параметри: виклик f(х) функції цього файлу з годиною
            # поріг: годину порівнюють з іменем
            if вид == "оп" and зн in ("<", ">", "<=", ">=") and і >= 1 and і + 1 < len(т):
                if self.носій(ф, і - 1) and т[і + 1][0] == "ім" and not self.носій(ф, і + 1):
                    if значуще(т[і + 1][1]) and т[і + 1][1] not in ф.локальні.get(ф.сегмент[і], ()):
                        с.додати(с.Г, т[і + 1][1], де(і), "поріг, з яким порівнюють годину")

    def однозначний(self, ф, і):
        """Усі присвоєння локального імені `ф.т[і]` у його сегменті — година (змінна одного призначення)."""
        ім, сег = ф.т[і][1], ф.сегмент[і]
        for j, (вид, зн, _) in enumerate(ф.т):
            if ф.сегмент[j] != сег or вид != "ім" or зн != ім or self.властивість(ф, j):
                continue
            if j + 1 < len(ф.т) and ф.т[j + 1][0] == "оп" and ф.т[j + 1][1] in ("=", "+=", "-=", "++", "--"):
                if ф.т[j + 1][1] != "=" or not self.є_година(ф, j + 2, self.кінець_виразу(ф, j + 2)):
                    return False
        return True

    def відкрита(self, ф, і):
        """Індекс відкритої дужки для закритої `ф.т[і]`."""
        глиб = 0
        for j in range(і, -1, -1):
            if ф.т[j][0] == "оп" and ф.т[j][1] == ")":
                глиб += 1
            elif ф.т[j][0] == "оп" and ф.т[j][1] == "(":
                глиб -= 1
                if глиб == 0:
                    return j
        return None

    def назва_функції(self, ф, і):
        """Ім'я `function NAME` верхнього сегмента, де стоїть токен."""
        сег = ф.сегмент[і]
        for j in range(і, -1, -1):
            if ф.сегмент[j] != сег:
                break
            if ф.т[j][1] == "function" and j + 1 < len(ф.т) and ф.т[j + 1][0] == "ім":
                return ф.т[j + 1][1] if ф.сегмент[j] == сег and self.верхня(ф, j) else None
        return None

    def верхня(self, ф, j):
        """`function` стоїть на початку сегмента (не вкладена)."""
        return j == 0 or ф.сегмент[j - 1] != ф.сегмент[j]

    def назва_стрілки(self, ф, і):
        """Ім'я `const NAME = (...) =>` для стрілки на `і`."""
        j = і - 1
        if j >= 0 and ф.т[j][1] == ")":
            j = (self.відкрита(ф, j) or 0) - 1
        elif j >= 0 and ф.т[j][0] == "ім":
            j -= 1
        if j >= 1 and ф.т[j][1] == "=" and ф.т[j - 1][0] == "ім":
            return ф.т[j - 1][1]
        return None

    def місця(self, ф, додати):
        с, т = self.с, ф.т
        for шлях_р, рядок, чому, пункт in ф.html_місця(с) if hasattr(ф, "html_місця") else ():
            додати(шлях_р, рядок, пункт, чому)
        for і, (вид, зн, р) in enumerate(т):
            if вид == "ім":
                if self.носій(ф, і):
                    додати(ф.шлях, р, 4, "%s «%s» несе годину" % ("властивість" if self.властивість(ф, і) else "ім'я", зн))
                    self.додаткові_пункти(ф, і, додати)
            elif вид == "ряд":
                if зн in с.Г:
                    додати(ф.шлях, р, 4, "ключ чи поле «%s»" % зн)
                    self.додаткові_пункти(ф, і, додати)
                    continue
                if not зн.strip():
                    continue
                for зсув, рядок_т in enumerate(зн.split("\n")):
                    причини = текст_години(рядок_т)
                    токени = токени_носіїв(рядок_т, с.Г)
                    if причини or токени:
                        англ = sum(ч.isascii() and ч.isalpha() for ч in рядок_т) > \
                            sum(not ч.isascii() and ч.isalpha() for ч in рядок_т)
                        додати(ф.шлях, р + зсув, 1 if англ else 4,
                               "текст: " + "; ".join(причини + ["ключ «%s»" % х for х in токени[:2]]))

    def додаткові_пункти(self, ф, і, додати):
        """п.3 (типова година, порівняння з межею дня) у тому самому виразі."""
        т = ф.т
        р = т[і][2]
        вікно = т[і + 1:і + 4]
        if len(вікно) >= 2 and вікно[0][1] in ("||", "??") and вікно[1][0] == "чис" and вікно[1][1].isdigit() \
                and 0 <= int(вікно[1][1]) <= 23:
            додати(ф.шлях, р, 3, "типова година (|| %s)" % вікно[1][1])
        if len(вікно) >= 2 and вікно[0][1] in ("<", ">", "<=", ">=") and вікно[1][0] == "чис" \
                and вікно[1][1].isdigit() and 0 < int(вікно[1][1]) < 23:
            додати(ф.шлях, р, 3, "порівняння години з межею дня")
        сусіди = [x for x in т[max(0, і - 4):і + 5] if x[0] == "ряд" and re.fullmatch(r"(?:[01]?\d|2[0-3])(?::00)?", x[1])]
        if сусіди and т[і][0] == "ряд":
            додати(ф.шлях, р, 3, "типова година поля показу «%s»" % сусіди[0][1])


class Хтмл(Джс):
    """HTML: поля панелі (`<input min=0 max=23>`), рядки з ід і ключами носіїв, вбудовані скрипти як JS."""

    ВХІД = re.compile(r"<input\b[^>]*>", re.IGNORECASE)

    def __init__(self, шлях, текст):
        self.рядки_html = текст.splitlines()
        токени, зерна = [], []
        for м in re.finditer(r"<script\b[^>]*>(.*?)</script>", текст, re.DOTALL | re.IGNORECASE):
            поч = текст.count("\n", 0, м.start(1)) + 1
            токени += лексер_js(м.group(1), поч)
        for м in self.ВХІД.finditer(текст):
            тег = м.group(0)
            мін = re.search(r"\bmin=[\"']?(-?\d+)", тег)
            макс = re.search(r"\bmax=[\"']?(\d+)", тег)
            ід = re.search(r"\bid=[\"']([^\"']+)", тег)
            if ід and ((мін and макс and int(мін.group(1)) == 0 and int(макс.group(1)) in (23, 24))
                       or re.search(r"type=[\"']?time", тег)):
                зерна.append((ід.group(1), текст.count("\n", 0, м.start()) + 1))
        super().__init__(шлях, токени, зерна)
        self.скрипти = {р for м in re.finditer(r"<script\b[^>]*>(.*?)</script>", текст, re.DOTALL | re.IGNORECASE)
                        for р in range(текст.count("\n", 0, м.start(1)) + 1, текст.count("\n", 0, м.end(1)) + 2)}

    def html_місця(self, с):
        """Рядки розмітки поза скриптами: атрибути з ід чи ключем носія, типове значення поля години."""
        for н, рядок in enumerate(self.рядки_html, 1):
            if н in self.скрипти:
                continue
            без_коментарів = re.sub(r"<!--.*?-->", "", рядок)
            for м in re.finditer(r"\b(?:id|for|name|data-[\w-]+)=[\"']([^\"']+)[\"']", без_коментарів):
                if м.group(1) in с.Г:
                    yield self.шлях, н, "розмітка: поле «%s»" % м.group(1), 4
                    if re.search(r"\bvalue=[\"']?\d", без_коментарів) and "type=\"hidden\"" not in без_коментарів:
                        yield self.шлях, н, "типове значення поля години", 3
                    break


# ── правила бази знань (п.5) ────────────────────────────────────────────────────────────────────────────────────
# Кожне правило дня й вечора з бази знань (п.5 класу): якір у базі (файл і рядок, що мусить там бути), знак у коді
# (ід правила, ключ реєстру — те, чим код називає саме це правило), і як звірити дію з базою: у функціях зі знаком
# частину дня бере паспорт (ключ частини дня, а не година) і є дія, яку пише база.
ПРАВИЛА_БАЗИ = (
    dict(вісь="ошатність за рівнем події (вечір підіймає щабель)",
         база=("джерела/тема-5_знання.md", r"^## 1\.3 The evening lift is graduated by tier"),
         знак=r"K-KOH-06", дія="підйом", межа=r"смуг|щабл|formality|ошатн", рішення=r"щабл|смуг"),
    dict(вісь="відкриті зони (удень одна, ввечері дві)",
         база=("джерела/тема-4_композиція-і-когерентність-EN.md", r"K-KOH-10\. One exposed zone.*evening contexts admit two"),
         знак=r"K-KOH-10", дія="друга_зона", межа=None, рішення=r"ліміт|ЗОНИ_ТИПОВО|відкриті_зони"),
    dict(вісь="рух (у вечірньому образі можна танцювати)",
         база=("джерела/тема-6_людина-профіль-і-діалог_v2.md", r"you must be able to dance"),
         знак=r"\bdanc\w*|\bтанц\w*", дія="є", межа=None, рішення=None),
    dict(вісь="блиск (ввечері більший бюджет)",
         база=("джерела/реєстр_константи.py", r'"блиск_вечір"'),
         знак=r"блиск_вечір|БЛИСК_ВЕЧІР", дія="є", межа=None, рішення=r"бюджет"),
    dict(вісь="світло (вечір — інше світло)",
         база=("джерела/тема-5_знання.md", r"After 6 p\.m\., err toward formality"),
         знак=r"вечір_від|вечірнє_світло", дія="є", межа=None, рішення=None),
)
ВЕСІЛЛЯ = re.compile(r"весілл|wedding")


def якір_бази(корінь, файл, шаблон):
    """Рядок якоря правила в базі знань; None — якоря нема (база змінилась, прилад теж мусить)."""
    шлях = os.path.join(корінь, файл)
    if not os.path.isfile(шлях):
        return None
    with open(шлях, encoding="utf-8") as ф:
        for н, рядок in enumerate(ф, 1):
            if re.search(шаблон, рядок):
                return н
    return None


def точки_знаку(модулі, шаблон):
    """Точки коду Python зі знаком правила (рядкова константа чи ім'я, не коментар): (модуль, функція, рядок)."""
    точки = []
    for м in модулі:
        for в in м.вузли:
            текст = None
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in м.докстрінги:
                текст = в.value
            elif isinstance(в, ast.Name):
                текст = в.id
            elif isinstance(в, ast.Attribute):
                текст = в.attr
            if текст and re.fullmatch(шаблон, текст):
                точки.append((м, м.функція_області(в), в.lineno, в))
    бачені, вихід = set(), []
    for т in sorted(точки, key=lambda т: (т[0].шлях, т[2], т[3].col_offset)):
        if (т[0].шлях, т[2]) not in бачені:
            бачені.add((т[0].шлях, т[2]))
            вихід.append(т)
    return вихід


def рішення_правила(м, вузол, шаблон):
    """Точка знаку стоїть у гілці рішення, яке за базою залежить від дня чи вечора: умова охопного `if` порівнює
    з межею цього рішення (`len(зони) > ліміт`), а не лише називає ід правила."""
    if not шаблон:
        return False
    в = м.батько.get(id(вузол))
    while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module, ast.ClassDef)):
        if isinstance(в, (ast.If, ast.While)) and any(isinstance(х, ast.Compare) for х in ast.walk(в.test)) \
                and re.search(шаблон, ast.get_source_segment("\n".join(м.рядки), в.test) or ""):
            return True
        в = м.батько.get(id(в))
    return False


def досягає(аналіз, м, вузол):
    """Значення години (чи вечора з години) доходить до точки правила: його читає сама інструкція з точкою або
    заголовок охопної гілки (`if`/`while` — умова, `for` — ітерований), не решта функції."""
    def читає(вираз):
        return any(isinstance(х, (ast.Name, ast.Attribute, ast.Subscript, ast.Call))
                   and (аналіз.є_година(м, х) or аналіз.є_вечір(м, х)) for х in ast.walk(вираз))
    в = вузол
    while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module, ast.ClassDef)):
        if isinstance(в, (ast.If, ast.While)):
            if читає(в.test):
                return True
        elif isinstance(в, (ast.For, ast.AsyncFor)):
            if читає(в.iter):
                return True
        elif isinstance(в, ast.stmt) and not isinstance(в, (ast.Try, ast.With, ast.AsyncWith)):
            if читає(в):
                return True
        в = м.батько.get(id(в))
    return False


def правила_бази(корінь, модулі, аналіз, додати, звіт, без_бази=False):
    """Звіряє правила дня й вечора з бази знань із кодом (п.5); місця — у `додати`, рядки — у `звіт`."""
    с = аналіз.с
    for правило in ПРАВИЛА_БАЗИ:
        якір = None if без_бази else якір_бази(корінь, *правило["база"])
        if not без_бази and якір is None:
            raise SystemExit("корінь_е2_частина_дня: якоря правила «%s» нема в %s — базу змінено, онови ПРАВИЛА_БАЗИ"
                             % (правило["вісь"], правило["база"][0]))
        точки = [т for т in точки_знаку(модулі, правило["знак"]) if not т[0].шлях.endswith(правило["база"][0])]
        if правило["межа"]:
            точки = [т for т in точки if т[1] is not None and re.search(
                правило["межа"], ast.get_source_segment("\n".join(т[0].рядки), т[1]) or "")]
        функції = {(т[0].шлях, id(т[1])): т for т in точки if т[1] is not None}
        бере_пору, дія, з_години = False, False, False
        for (шлях, _), (м, ф, _, _) in функції.items():
            пора = any((isinstance(в, ast.Constant) and в.value in с.П) or
                       (isinstance(в, ast.Compare) and any(рядок_константи(х) in СЛОВА_ПОРИ for х in в.comparators))
                       for в in ast.walk(ф))
            година = any(isinstance(в, (ast.Name, ast.Attribute, ast.Subscript, ast.Call)) and
                         (аналіз.є_година(м, в) or аналіз.є_вечір(м, в)) for в in ast.walk(ф))
            з_години = з_години or година
            бере_пору = бере_пору or (пора and not година)
            if правило["дія"] == "підйом":
                for в in ast.walk(ф):
                    if isinstance(в, ast.If) and any((isinstance(х, ast.Constant) and х.value in с.П) or
                                                     рядок_константи(х) in СЛОВА_ПОРИ for х in ast.walk(в.test)) \
                            and any(isinstance(х, ast.AugAssign) and isinstance(х.op, ast.Add) for х in ast.walk(в)):
                        дія = True
                        if not any(ВЕСІЛЛЯ.search(рядок_константи(х) or "") for х in ast.walk(в.test)):
                            додати(м.шлях, в.lineno, 5, "вечір підіймає ошатність і весіллю")
            elif правило["дія"] == "друга_зона":
                for в in ast.walk(ф):
                    if isinstance(в, ast.If) and any((isinstance(х, ast.Constant) and х.value in с.П) or
                                                     рядок_константи(х) in СЛОВА_ПОРИ for х in ast.walk(в.test)) \
                            and any(ціле(х) == 2 for х in ast.walk(в)):
                        дія = True
            else:
                дія = True
        гаразд = bool(функції) and бере_пору and дія
        if гаразд:
            звіт.append("правило бази «%s»: у коді є, частину дня бере з паспорта — не місце" % правило["вісь"])
            continue
        if not точки:
            звіт.append("правило бази «%s»: знаку в коді нема — рішення нема, місця нема (якір бази %s:%s)" % (
                правило["вісь"], правило["база"][0], якір))
            continue
        # місце правила — рішення, що за базою залежить від дня чи вечора: точка, до якої доходить значення години
        # (судить годиною), чи гілка рішення з межею цього правила (частини дня не бере); ід правила при іншому
        # рішенні місця не робить (клас п.5)
        з_години = [т for т in точки if досягає(аналіз, т[0], т[3])]
        досягнуті = [т for т in точки if т in з_години or рішення_правила(т[0], т[3], правило["рішення"])]
        чому = []
        if з_години:
            чому.append("судить годиною (вечір із години)")
        if not бере_пору:
            чому.append("частини дня з паспорта не бере")
        if not дія:
            чому.append("дії бази нема (%s)" % правило["дія"])
        for т in досягнуті:
            додати(т[0].шлях, т[2], 5, "правило бази «%s»: %s" % (
                правило["вісь"], ", ".join(чому if т in з_години else [ч for ч in чому if not ч.startswith("судить")])))
        звіт.append("правило бази «%s»: %s — точок знаку %d, рішень дня й вечора серед них %d (з годиною %d)%s" % (
            правило["вісь"], ", ".join(чому), len(точки), len(досягнуті), len(з_години),
            "" if досягнуті else "; рішення в коді нема — місця нема (якір бази %s:%s)" % (правило["база"][0], якір)))


# ── збирання ───────────────────────────────────────────────────────────────────────────────────────────────────
def файли_продукту(корінь):
    """(шлях від кореня, вид) файлів коду продукту і число файлів поза класом (тести й проби за іменем)."""
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
    """Повний обхід: → (місця {(файл, рядок): {пункти, доказ}}, стан, звіт, лік файлів)."""
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
        elif шлях.endswith(".html"):
            джс.append(Хтмл(шлях, текст))
        else:
            джс.append(Джс(шлях, лексер_js(текст)))
    стан = Стан()
    ап, адж = АналізПі(пі, стан), АналізДжс(джс, стан)
    проходів = 0
    while стан.змінено and проходів < 40:
        стан.змінено = False
        проходів += 1
        for м in пі:
            ап.прохід(м)
        for ф in джс:
            адж.прохід(ф)
    місця = {}

    def додати(файл, рядок, пункт, доказ):
        з = місця.setdefault((файл, рядок), {"пункти": set(), "докази": []})
        з["пункти"].add(пункт)
        if доказ not in з["докази"]:
            з["докази"].append(доказ)

    for м in пі:
        ап.місця(м, додати)
    for ф in джс:
        адж.місця(ф, додати)
    звіт = []
    правила_бази(корінь, пі, ап, додати, звіт, без_бази)
    лік = dict(py=sum(ф.endswith(".py") for ф in файли), js=sum(ф.endswith((".js", ".mjs")) for ф in файли),
               html=sum(ф.endswith(".html") for ф in файли), поза=поза, проходів=проходів, помилки=помилки)
    return місця, стан, звіт, лік


def друк(місця, стан, звіт, лік, тихо=False, імена=False):
    """Детермінований вивід; останній рядок — `місць: N`."""
    рядки = ["корінь Е2-частина-дня: година дня нагоди в коді продукту (клас — аудит/корені/Е2-частина-дня.md)",
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
    рядки.append("за файлами: " + "; ".join("%s — %d" % (ф, н) for ф, н in
                                            sorted(за_файлами.items(), key=lambda х: (-х[1], х[0]))))
    рядки += звіт
    if імена:
        рядки.append("")
        for назва, множина in (("носії години", стан.Г), ("перетворювачі", стан.КОНВ), ("прапорці походження", стан.С),
                               ("функції переводу", стан.ПЕР),
                               ("вечір із години", стан.Е), ("ключі частини дня", стан.П)):
            рядки.append("%s (%d):" % (назва, len(множина)))
            for ім in sorted(множина):
                рядки.append("  %s ← %s" % (ім, стан.звідки.get(ім, "?")))
    рядки.append("місць: %d" % len(місця))
    return "\n".join(рядки)


# ── самоперевірка на штучних випадках ───────────────────────────────────────────────────────────────────────────
ШТУЧНІ = {
    "джерела/опис.py": '''
ОПИСИ = {"hour": "start hour on a 24-hour clock, only when she names it",
         "duration_h": "how many hours the event lasts",
         "day_of_month": "the day of the month, 1-31"}
''',
    "джерела/паспорт.py": '''
from сцена import частина_доби
def з_відповіді(в):
    об = {}
    об["година"] = в.get("hour")          # година з відповіді
    об["тривалість_год"] = в.get("duration_h")
    об["дата"] = в.get("day_of_month")
    return об
def картка(п):
    return "%02d:%02d" % (п["година"], 0)
def пора(п):
    return частина_доби(п["година"] % 24)
def типова(п):
    п["година"] = 11
    return п
''',
    "джерела/сцена.py": '''
def частина_доби(г):
    """Година 0–23 → частина дня."""
    return "morning" if 5 <= г < 11 else "day" if г < 17 else "evening"
def лише_пора(п):
    return п.get("part_of_day") == "evening"
''',
    "джерела/світло.py": '''
РЕЄСТР = {"вечір_від": dict(val=18)}
def вечірнє_світло(година):
    return година >= РЕЄСТР["вечір_від"]["val"]
def бюджет(сц):
    вечір = вечірнє_світло(сц.get("година"))
    return 3 if вечір else 2
''',
    "джерела/показ/панель.js": '''
// година з поля — коментар, не місце
function годинаП(){ const г = parseInt($('поле-год').value, 10); return (г >= 0 && г <= 23) ? г : null; }
function рядокП(){ const г = годинаП(); return String(г).padStart(2, '0') + ':' + '00'; }
function тривалістьП(){ return 'пів години пішки'; }
''',
    "джерела/сторінка.html": '''<label for="поле-год">Година</label>
<input type="number" id="поле-год" value="11" min="0" max="23">
<input type="number" id="поле-темп" value="18" min="-30" max="45">
''',
    "джерела/тест_щось.py": '''ГОДИНА = {"hour": 7}
''',
    "джерела/правило.py": '''
def світлота(нагода):
    return ("K-KOH-06", "ошатність: світлота за нагодою")
def блиск_удень(година):
    if година is not None and година < 18:
        return ("K-KOH-06", "ошатність: блиск удень")
def зони(вибрані, ліміт=1):
    if len(вибрані) > ліміт:
        return ("K-KOH-10", "відкритих зон більше")
''',
    "джерела/поля.py": '''
ПОЛЯ = {
    "година": {
        "цитата": 'пара',
        "названа": ('named', 'clock_time'),
    },
}
_НАЗВАНА = ПОЛЯ["година"]["названа"]
''',
    "джерела/число.py": '''
def число(с, т):
    if с["type"] == "integer" and ":" in т:
        т = т.split(":")[0]
    return float(т)
def назва(н):
    if ":" in н:
        return н.split(":")[0]
''',
    "джерела/шов.py": '''
from сцена import частина_доби
def з_сцени(п):
    def _з(k):
        return п.get(k)
    година = _з("година")
    try: година = int(float(година))
    except (TypeError, ValueError): година = None
    return година
def пора_з_години(онов):
    г = онов.get("hour")
    пора = частина_доби(г)
    return dict(онов, part_of_day=пора)
def прийняти(онов):
    return пора_з_години(онов)
''',
}
ОЧІКУВАНІ = (
    ("опис поля «hour» — п.1", "джерела/опис.py", 1, 1),
    ("тривалість — не місце", "джерела/опис.py", 2, None),
    ("дата — не місце", "джерела/опис.py", 3, None),
    ("приймання hour з відповіді — п.1", "джерела/паспорт.py", 4, 1),
    ("запис ключа година — п.2", "джерела/паспорт.py", 4, 2),
    ("тривалість у паспорті — не місце", "джерела/паспорт.py", 5, None),
    ("дата в паспорті — не місце", "джерела/паспорт.py", 6, None),
    ("картка годинником — п.4", "джерела/паспорт.py", 9, 4),
    ("година → частина дня — п.3", "джерела/паспорт.py", 11, 3),
    ("типова година — п.3", "джерела/паспорт.py", 13, 3),
    ("перетворювач — п.3", "джерела/сцена.py", 3, 3),
    ("частина дня як є — не місце", "джерела/сцена.py", 5, None),
    ("частина дня як є (def) — не місце", "джерела/сцена.py", 4, None),
    ("поріг вечора з реєстру — п.2", "джерела/світло.py", 1, 2),
    ("вечір із години — п.5", "джерела/світло.py", 3, 5),
    ("правило судить вечором із години — п.5", "джерела/світло.py", 6, 5),
    ("поле панелі — п.4", "джерела/показ/панель.js", 2, 4),
    ("коментар — не місце", "джерела/показ/панель.js", 1, None),
    ("годинник рядком у JS — п.4", "джерела/показ/панель.js", 3, 4),
    ("тривалість у JS — не місце", "джерела/показ/панель.js", 4, None),
    ("поле години в розмітці — п.4", "джерела/сторінка.html", 1, 4),
    ("типова година в розмітці — п.3", "джерела/сторінка.html", 2, 3),
    ("поле температури — не місце", "джерела/сторінка.html", 3, None),
    ("тест — поза класом", "джерела/тест_щось.py", 0, None),
    ("знак правила без години — не місце", "джерела/правило.py", 2, None),
    ("знак правила, до якого доходить година, — п.5", "джерела/правило.py", 5, 5),
    ("рішення правила дня й вечора без частини дня (ліміт зон) — п.5", "джерела/правило.py", 8, 5),
    ("поріг вечора з реєстру — п.3", "джерела/світло.py", 1, 3),
    ("порівняння години з порогом реєстру — п.3", "джерела/світло.py", 3, 3),
    ("рядок запису поля години, що не година, — не місце", "джерела/поля.py", 3, None),
    ("під-ключ, який читають у носій години, — п.2", "джерела/поля.py", 4, 2),
    ("година з рядка годинника відповіді — п.1", "джерела/число.py", 3, 1),
    ("гілка «ГГ:ХХ» у відповіді — п.1", "джерела/число.py", 2, 1),
    ("split(':')[0] не в число — не місце", "джерела/число.py", 7, None),
    ("година з геттера поля в try — п.2", "джерела/шов.py", 6, 2),
    ("скидання години в except — п.2", "джерела/шов.py", 7, 2),
    ("функція переводу години в частину дня — п.3", "джерела/шов.py", 9, 3),
    ("виклик переводу години — п.3", "джерела/шов.py", 14, 3),
)


def самоперевірка():
    """Штучні випадки (`ШТУЧНІ`) → [(назва, так/ні)]."""
    тека = tempfile.mkdtemp(prefix="е2_частина_дня_")
    try:
        for шлях, текст in ШТУЧНІ.items():
            повний = os.path.join(тека, шлях)
            os.makedirs(os.path.dirname(повний), exist_ok=True)
            with open(повний, "w", encoding="utf-8") as ф:
                ф.write(текст.lstrip("\n"))
        місця, _, _, _ = лічити(тека, без_бази=True)
    finally:
        shutil.rmtree(тека, ignore_errors=True)
    вих = []
    for назва, файл, рядок, пункт in ОЧІКУВАНІ:
        з = місця.get((файл, рядок))
        вих.append((назва, з is None if пункт is None else (з is not None and пункт in з["пункти"])))
    return вих


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
    місця, стан, звіт, лік = лічити(корінь)
    print(друк(місця, стан, звіт, лік, тихо="--тихо" in арг, імена="--імена" in арг))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
