# -*- coding: utf-8 -*-
"""прилади/корінь_е3_одна_величина.py — прилад кореня Е3-одна-величина: одна величина з кількома визначеннями.

Клас — `аудит/корені/Е3-одна-величина.md` («Клас місць» і «Стан і що лишилось»): величина — значення, яке система має
знати одне (межа виміру, значення входу правила чи моделі, типове значення поля, зміст ід правила); місце — точка коду
продукту (`джерела/` на будь-якій глибині: Python, JS, HTML; проби, прилади, стенди й тести — ні), що визначає таку
величину не з її одного джерела. Пункти:
  1  межу однієї величини ставить друге число: (а) голий літерал поруч із константою реєстру (та сама величина
     порівнюється й з константою, й з літералом); (б) пороги однієї величини в одному напрямку — константами ≥ 2
     реєстрів (модулів визначення): кожне вживання й кожен запис реєстру такого порога; (в) межа вмикання правила:
     пороги, що стережуть заяву того самого ід, — різні числа в одному напрямку;
  2  межу правила стилю поставлено числом сесії: (а) запис реєстру з тіром T3, чий опис — слово сесії («моє», «не
     калібровано», «середина між», «фольклорн…», «оцінка … не калібр…») без посилання на визнане джерело (автор і рік),
     і кожне порівняння з ним; (б) голий літерал у порозі, що стереже заяву правила стилю;
  3  одне значення входу правила чи моделі пишуть два писачі за різними умовами: (а) ключ виходу, який одна функція
     пише кодом таблиці (через кодувальник `внутрішня_мова.ТАБЛИЦЯ`), а інша — сирими словами (без кодувальника);
     (б) одна ознака «названо» (перелік ключів, які читають з того самого словника) — різними переліками: менший
     перелік ⊊ більшого, спільних ключів ≥ 3, у різних функціях;
  4  одне ід правила несе в коді ≥ 2 змісти: два тлумачення ід у таблицях коду без жодного спільного слова, ід має
     означення в корпусі (`правила.формулювання`); місце — кожна точка коду з цим ід (заява, рядок таблиці, запис
     реєстру `прав=`) і поріг, що стереже заяву;
  5  типове значення однієї величини записано в читанні чи підписі функції в ≥ 2 місцях: `x or <літерал>`,
     `.get(ключ, <літерал>)`, параметр `p=<літерал>` (JS: `||`, `??`, параметр з типовим).

ВІД ЗНАЧЕННЯ, НЕ ВІД ІМЕН. Величину прилад виводить потоком значення: присвоєння (і розпакування), ключ словника й
`dict(...)`, іменований аргумент, позиційний аргумент функції продукту (за її підписом), обгортки `float/int/round`,
`x.get("к")`, `x["к"]`, `x or …`, межа Python/JS — однаковий ключ. Локальні змінні — в межах своєї функції, ключі,
атрибути й параметри — спільні (ім'я входу); загальні імена (`value`, `код`, `x`…) потоку не несуть. Величина — компонента
об'єднання; рядкове типове ще й зливає компоненти за самим значенням (`"conventional"` — значення одного поля).
Кодувальник — функція, що читає `ТАБЛИЦЯ` чи повертає результат іншого кодувальника (нерухома точка).

ЧОГО ПРИЛАД НЕ ЛІЧИТЬ (паспорт, «Не місця» і рішення менеджера 31.10): величини інших коренів — градуси й погода
(`Е2-смуга-погоди`, Г3), година й частина дня (`Е2-частина-дня`), сила правила (`Е3-сила-правила`: `hard/strong/soft/
hint`), тривалість і дата; переклад слова ядра в код (Г2) — не писач (п.3 лише код проти сирого); порожні типові (`None`,
`""`, `0`, `False`, порожні колекції) — відсутність, не значення; поріг 0 — знак, не межа; коментарі й докстрінги.
Кількість цих поза класом друкується окремим рядком.

Вивід детермінований: перелік `файл:рядок · п.N[,M] · доказ`, підсумки за пунктами й файлами, останній рядок
`місць: <N>` (N — різних `файл:рядок`), код 0. Запуск з кореня репозиторію (чи `--корінь <шлях>`):
    python3 джерела/прилади/корінь_е3_одна_величина.py [--тихо] [--величини] [--самоперевірка]
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

# ── словник ─────────────────────────────────────────────────────────────────────────────────────────────────────
ІД_ПРАВИЛА = re.compile(r"^[KR]-[A-Z]+-\d+[A-Z]?(?:-[A-Z0-9]+)?$")
ЗАГАЛЬНІ = {
    "value", "val", "значення", "key", "ключ", "поле", "field", "type", "тип", "data", "дані", "name", "назва", "ім",
    "імя", "id", "ід", "текст", "text", "джерело", "source", "код", "code", "вихід", "вих", "result", "items", "item",
    "row", "рядок", "запис", "default", "типове", "мітка", "label", "self", "cls", "args", "kwargs", "get", "число",
    "number", "num", "int", "float", "str", "round", "abs", "min", "max", "next", "len", "dict", "list", "tuple", "set",
    "sorted", "any", "all", "out", "res", "ret", "obj", "об", "елемент", "річ", "речі", "сцен", "сцена", "паспорт",
    "суд", "вхід", "input", "inputs", "params", "options", "opts", "config", "cfg", "state", "стан", "info", "meta",
    "мета_", "x", "y", "v", "k", "i", "j", "n", "s", "e", "р", "к", "в", "с", "п", "о", "з", "т", "д", "м", "л", "ч",
    "val_", "знач", "сире", "raw", "this", "window", "document", "console", "event", "ev", "el", "node", "root",
    "parent", "child", "children", "length", "size", "count", "index", "idx", "ix", "pos", "start", "end", "kind",
    "mode", "режим", "what", "why", "missing", "statements", "чому", "note", "нота", "нотатки", "msg", "message", "повідомлення", "слова",
    "words", "word", "слово", "list_", "a", "b", "c", "lo", "hi", "low", "high", "від", "до", "межа", "поріг",
    "threshold", "limit", "ліміт", "мін", "макс", "сума", "total", "частка", "share", "ratio", "вага", "weight",
    "score", "бал", "бали", "крок", "step", "стор", "page", "path", "шлях", "file", "файл", "url",
    "lang", "мова", "format", "формат", "flag", "прапор", "on", "off", "enabled", "show", "hide",
}
ОБГОРТКИ = {"float", "int", "round", "abs", "str", "bool"}
ГЛИБИНА_СЛІДУ = 10     # кроків сліду джерела значення (параметр → виклик, ключ → писач, виклик → повернення)
ВУЗОЛ_ХАБ = 6          # різних імен-сусідів потоку понад це — ім'я несе різні значення, не одну величину
# Величини інших коренів (одиниця з імені чи константи — паспорт: «одиниці — з реєстру чи імені»).
ІНШІ_КОРЕНІ = (
    ("Е2-смуга-погоди", re.compile(r"темп|temp|градус|°|_c$|_c_|погод|weather|feel|відчутт|мороз|холод|тепл", re.I)),
    ("Е2-частина-дня", re.compile(r"годин|hour|хвилин|minute|частина_дня|part_of_day|пора\b", re.I)),
    ("тривалість і дата", re.compile(r"тривал|duration|дата|date|днів|days|місяц|month|рок|year|секунд|second|мс\b|ms$|"
                                      r"timeout|таймаут|_ms_|_мс", re.I)),
    ("Е3-сила-правила", re.compile(r"^сила|сила_|strength|^force|нп_межа", re.I)),
)
СЛІД_КЛЮЧЕМ = True     # ключ словника — слід лише після кроку через параметр чи виклик (не ключ самого писача)
КЛЮЧ_ДРОТУ = re.compile(r"^[a-z][a-z0-9_]*$")   # дріт моделі — англійські коди (п.12 ПРОДУКТ)
ТАБЛИЦЯ_МОВИ = "внутрішня_мова"        # одна таблиця кодів (п.17 ПРОДУКТ): слово ядра ↔ код
СИЛА = {"hard", "strong", "soft", "hint", "default"}
СЛОВА_ПОРИ = {"ранок", "день", "вечір", "ніч", "morning", "day", "afternoon", "evening", "night"}
СЛОВО_СЕСІЇ = re.compile(r"\bмо[яєїйю]\b|\bмоє\b|мого\b|моїм\b|\bМОЯ\b|\bМОЄ\b|не\s+калібр|НЕ\s+КАЛІБР|середин\w*\s+між|"
                         r"фольклорн|ФОЛЬКЛОРН|вигадан", re.I)
ПОСИЛАННЯ = re.compile(r"[A-Z][a-z]+(?:\s+et\s+al\.?|\s*(?:&|and|і)\s*[A-Z][a-z]+)?,?\s*\(?(?:19|20)\d\d\b")
СЛУЖБОВІ = {"або", "чи", "що", "без", "для", "його", "її", "їх", "тому", "щоб", "коли", "якщо", "this", "that",
            "with", "from", "into", "over", "under", "than", "not", "when", "then", "also", "only", "the", "and"}


# ── допоміжне ───────────────────────────────────────────────────────────────────────────────────────────────────
def іншого_кореня(*імена):
    """Назва іншого кореня, якому належить величина (за іменем чи ключем), або None."""
    for ім in імена:
        if not isinstance(ім, str):
            continue
        for корінь, шаблон in ІНШІ_КОРЕНІ:
            if шаблон.search(ім):
                return корінь
    return None


def загальне(ім):
    return not isinstance(ім, str) or ім.lower() in ЗАГАЛЬНІ or len(ім) < 2 or ім.startswith("__")


def число(в):
    """Числовий літерал (не bool) → значення, інакше None."""
    if isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) and not isinstance(в.value, bool):
        return в.value
    if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.USub):
        ч = число(в.operand)
        return -ч if ч is not None else None
    return None


def порожнє(в):
    """Типове-відсутність: None, "", 0, False, порожня колекція."""
    if isinstance(в, ast.Constant):
        return в.value in (None, "", 0, False) or в.value == 0
    if isinstance(в, (ast.List, ast.Tuple, ast.Set)) and not в.elts:
        return True
    if isinstance(в, ast.Dict) and not в.keys:
        return True
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ("dict", "list", "set", "tuple") \
            and not в.args and not в.keywords:
        return True
    return False


def літерал_типове(в):
    """Літерал типового (рядок, число, True) → значення, інакше None."""
    if порожнє(в):
        return None
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return в.value if re.search(r"\w", в.value) else None     # «?», «—», «.» — заповнювач показу, не значення
    if isinstance(в, ast.Constant) and isinstance(в.value, (int, float)):
        return в.value
    ч = число(в)
    return ч


def рядки_тексту(в):
    """Склеєний текст рядкових констант виразу (для опису реєстру)."""
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return в.value
    if isinstance(в, ast.JoinedStr):
        return "".join(рядки_тексту(з) for з in в.values)
    if isinstance(в, ast.BinOp):
        return рядки_тексту(в.left) + рядки_тексту(в.right)
    return ""


def основи(текст):
    """Основи змістових слів (перші 5 літер слів від 4 літер) — для порівняння тлумачень ід."""
    return {с[:5] for с in re.findall(r"[a-zа-яіїєґʼ']{4,}", текст.lower()) if с not in СЛУЖБОВІ}


class Обʼєднання:
    def __init__(self):
        self.б = {}

    def знайти(self, x):
        self.б.setdefault(x, x)
        while self.б[x] != x:
            self.б[x] = self.б[self.б[x]]
            x = self.б[x]
        return x

    def злити(self, a, b):
        if a is None or b is None:
            return
        ra, rb = self.знайти(a), self.знайти(b)
        if ra != rb:
            self.б[max(ra, rb)] = min(ra, rb)


# ── модуль Python ───────────────────────────────────────────────────────────────────────────────────────────────
class Модуль:
    """Розбір одного файлу: функції, реєстри, імпорти, батьки вузлів."""

    def __init__(self, шлях, текст):
        self.шлях = шлях
        self.ім = os.path.splitext(os.path.basename(шлях))[0]
        self.дерево = ast.parse(текст)
        self.батько = {}
        for в in ast.walk(self.дерево):
            for д in ast.iter_child_nodes(в):
                self.батько[д] = в
        self.псевдо = {}                       # псевдонім імпорту → модуль
        self.імпорт_імен = {}                  # ім'я → модуль (from X import ім)
        self.зірки = []                        # from X import *
        for в in ast.walk(self.дерево):
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.псевдо[а.asname or а.name] = а.name.split(".")[-1]
            elif isinstance(в, ast.ImportFrom) and в.module:
                for а in в.names:
                    if а.name == "*":
                        self.зірки.append(в.module.split(".")[-1])
                    else:
                        self.імпорт_імен[а.asname or а.name] = в.module.split(".")[-1]
        self.реєстри = {}                      # ім'я → {ключ: запис}
        self.сталі = {}                        # ВЕЛИКЕ_ІМ'Я → (значення, рядок)
        for в in self.дерево.body:
            ціль, знач = None, None
            if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name):
                ціль, знач = в.targets[0].id, в.value
            elif isinstance(в, ast.AnnAssign) and isinstance(в.target, ast.Name) and в.value is not None:
                ціль, знач = в.target.id, в.value
            if ціль is None:
                continue
            if isinstance(знач, ast.Dict):
                записи = {}
                for к, з in zip(знач.keys, знач.values):
                    if isinstance(к, ast.Constant) and isinstance(к.value, str) and isinstance(з, ast.Call) \
                            and isinstance(з.func, ast.Name) and з.func.id == "dict":
                        кв = {кл.arg: кл.value for кл in з.keywords if кл.arg}
                        if "val" in кв:
                            прав = кв.get("прав")
                            if isinstance(прав, (ast.List, ast.Tuple)):
                                прав = [е.value for е in прав.elts if isinstance(е, ast.Constant)]
                            elif isinstance(прав, ast.Constant):
                                прав = [прав.value]
                            else:
                                прав = []
                            записи[к.value] = dict(рядок=к.lineno, val=число(кв["val"]),
                                                   t=getattr(кв.get("t"), "value", None), прав=прав,
                                                   суть=рядки_тексту(кв.get("суть")) + " " + рядки_тексту(кв.get("джерело")))
                if записи:
                    self.реєстри[ціль] = записи
            if isinstance(знач, ast.DictComp):
                # `C = {k: РЕЄСТР[k]["val"] for k in РЕЄСТР}` — те саме визначення під іншим ім'ям
                джерело = next((п.id for п in ast.walk(знач) if isinstance(п, ast.Name) and п.id in self.реєстри), None)
                if джерело:
                    self.реєстри[ціль] = self.реєстри[джерело]
            ч = число(знач)
            if ч is not None and ціль.upper() == ціль and re.search(r"[A-ZА-ЯІЇЄҐ]", ціль):
                self.сталі[ціль] = (ч, в.lineno)

    def функція(self, вузол):
        """Найближча функція-власниця (FunctionDef/Lambda) або None (рівень модуля)."""
        в = self.батько.get(вузол)
        while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
            в = self.батько.get(в)
        return в

    def докстрінг(self, вузол):
        """Чи рядок — докстрінг чи вираз-коментар (не текст коду)."""
        б = self.батько.get(вузол)
        return isinstance(б, ast.Expr)


class Лічба:
    def __init__(self, корінь):
        self.корінь = корінь
        self.модулі = []
        self.js = []                            # (шлях, текст без коментарів)
        self.о = Обʼєднання()
        self.місця = {}                         # (файл, рядок) → {"пункти": set, "доказ": []}
        self.поза = {}                          # корінь → число відкинутих
        self.визначення = {}                    # ім'я функції → [(модуль, FunctionDef)]
        self.кодувальники = set()

    # ── збір файлів ──
    def зібрати(self):
        дж = os.path.join(self.корінь, "джерела")
        for тека, підтеки, файли in os.walk(дж):
            підтеки[:] = sorted(п for п in підтеки if п not in ПОЗА_ТЕКИ and not п.startswith("."))
            for ф in sorted(файли):
                if not ф.endswith(РОЗШИРЕННЯ) or ТЕСТ.search(ф):
                    continue
                повний = os.path.join(тека, ф)
                відн = os.path.relpath(повний, self.корінь).replace(os.sep, "/")
                with open(повний, encoding="utf-8", errors="replace") as д:
                    текст = д.read()
                if ф.endswith(".py"):
                    try:
                        self.модулі.append(Модуль(відн, текст))
                    except SyntaxError:
                        continue
                else:
                    self.js.append((відн, без_коментарів_js(текст)))
        for м in self.модулі:
            for в in ast.walk(м.дерево):
                if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.визначення.setdefault(в.name, []).append((м, в))

    # ── вузли величини ──
    def вузол_імені(self, м, ф, ім):
        if not isinstance(ім, str):
            return None
        if ф is not None:
            параметри = {а.arg for а in ф.args.args + ф.args.kwonlyargs + ф.args.posonlyargs}
            if ім in параметри and not загальне(ім):
                return ("к", ім.lower())
            if ім in параметри or ім in self.локальні(ф):
                return ("л", м.шлях, ф.name, ф.lineno, ім)
        if загальне(ім):
            return None
        return ("к", ім.lower())

    def локальні(self, ф):
        кеш = getattr(ф, "_локальні", None)
        if кеш is None:
            кеш = set()
            for в in ast.walk(ф):
                if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store):
                    кеш.add(в.id)
            ф._локальні = кеш
        return кеш

    def носій(self, м, ф, в):
        """Вузол величини, яку несе вираз, або None."""
        if isinstance(в, ast.Name):
            return self.вузол_імені(м, ф, в.id)
        if isinstance(в, ast.Attribute):
            return None if загальне(в.attr) else ("к", в.attr.lower())
        if isinstance(в, ast.Subscript):
            с = в.slice
            if isinstance(с, ast.Constant) and isinstance(с.value, str):
                return None if загальне(с.value) else ("к", с.value.lower())
            if isinstance(с, ast.Constant) and isinstance(с.value, int):
                return self.носій(м, ф, в.value)
            return None
        if isinstance(в, ast.Call):
            if isinstance(в.func, ast.Name) and в.func.id in ОБГОРТКИ and в.args:
                return self.носій(м, ф, в.args[0])
            if isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                    and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
                return None if загальне(в.args[0].value) else ("к", в.args[0].value.lower())
            return None
        if isinstance(в, ast.BoolOp):
            return self.носій(м, ф, в.values[0])
        return None

    def підпис(self, виклик, м):
        """Параметри функції продукту, яку кличе виклик (лише однозначна), або None."""
        f = виклик.func
        кандидати = []
        if isinstance(f, ast.Name):
            кандидати = [(мм, д) for мм, д in self.визначення.get(f.id, [])
                         if мм is м or м.імпорт_імен.get(f.id) == мм.ім]
        elif isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name):
            мод = м.псевдо.get(f.value.id)
            кандидати = [(мм, д) for мм, д in self.визначення.get(f.attr, []) if мод and мм.ім == мод]
        if len(кандидати) != 1:
            return None
        д = кандидати[0][1]
        return [а.arg for а in д.args.posonlyargs + д.args.args]

    def потік(self):
        """Ребра потоку значення → об'єднання вузлів. Вузол, що несе багато різних значень (сусідів понад
        `ВУЗОЛ_ХАБ`: ім'я циклу, загальний ключ, перевикористана змінна), — не величина: через нього не зливаємо."""
        ребра = []
        self.о.злити = lambda a, b: ребра.append((a, b)) if a is not None and b is not None and a != b else None
        self._ребра_потоку()
        del self.о.злити
        сусіди = {}
        for a, b in ребра:
            сусіди.setdefault(a, set()).add(str(b[-1]).lower().lstrip("_"))
            сусіди.setdefault(b, set()).add(str(a[-1]).lower().lstrip("_"))
        self.хаби = {в for в, с in сусіди.items() if len(с) > ВУЗОЛ_ХАБ}
        for a, b in ребра:
            if a not in self.хаби and b not in self.хаби:
                self.о.злити(a, b)

    def _ребра_потоку(self):
        for м in self.модулі:
            for в in ast.walk(м.дерево):
                ф = м.функція(в)
                if isinstance(в, (ast.Assign, ast.AnnAssign)):
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    if в.value is None:
                        continue
                    н = self.носій(м, ф, в.value)
                    for ц in цілі:
                        for ел in (ц.elts if isinstance(ц, (ast.Tuple, ast.List)) else [ц]):
                            if isinstance(ел, ast.Name):
                                self.о.злити(self.вузол_імені(м, ф, ел.id), н)
                            elif isinstance(ел, ast.Subscript) and isinstance(ел.slice, ast.Constant) \
                                    and isinstance(ел.slice.value, str) and not загальне(ел.slice.value):
                                self.о.злити(("к", ел.slice.value.lower()), н)
                elif isinstance(в, ast.Dict):
                    for к, з in zip(в.keys, в.values):
                        if isinstance(к, ast.Constant) and isinstance(к.value, str) and not загальне(к.value):
                            self.о.злити(("к", к.value.lower()), self.носій(м, ф, з))
                elif isinstance(в, ast.Call):
                    for кл in в.keywords:
                        if кл.arg and not загальне(кл.arg):
                            self.о.злити(("к", кл.arg.lower()), self.носій(м, ф, кл.value))
                    п = self.підпис(в, м)
                    if п:
                        for ім, арг in zip(п, в.args):
                            if not загальне(ім):
                                self.о.злити(("к", ім.lower()), self.носій(м, ф, арг))

    def величина(self, вузол):
        return self.о.знайти(вузол) if вузол is not None else None

    # ── константи ──
    def стала(self, м, ф, в, глибина=0):
        """Читання константи → (ім'я, значення, (файл, рядок) визначення, запис реєстру|None), інакше None."""
        if глибина > 3:
            return None
        if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id in ("float", "int") and в.args:
            return self.стала(м, ф, в.args[0], глибина + 1)
        if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and isinstance(в.slice.value, str):
            if в.slice.value == "val":
                return self.стала(м, ф, в.value, глибина + 1)
            ключ, база = в.slice.value, в.value
            мод, ім = None, None
            if isinstance(база, ast.Name):
                ім = база.id
                мод = м.ім if ім in м.реєстри else м.імпорт_імен.get(ім)
            elif isinstance(база, ast.Attribute) and isinstance(база.value, ast.Name):
                ім, мод = база.attr, м.псевдо.get(база.value.id)
            if ім is None:
                return None
            мм = self.модуль_реєстру(мод, ім)
            if мм is not None and ключ in мм.реєстри[ім]:
                з = мм.реєстри[ім][ключ]
                return ("%s.%s[%s]" % (мм.ім, ім, ключ), з["val"], (мм.шлях, з["рядок"]), з)
            # реєстр без модуля (C у локальному імені) — ключ однозначний серед усіх реєстрів
            знайдені = [(мм, р, з) for мм in self.модулі for р, зз in мм.реєстри.items() if р == ім
                        for к, з in зз.items() if к == ключ]
            if len(знайдені) == 1:
                мм, р, з = знайдені[0]
                return ("%s.%s[%s]" % (мм.ім, р, ключ), з["val"], (мм.шлях, з["рядок"]), з)
            return None
        if isinstance(в, ast.Name) and в.id.upper() == в.id and re.search(r"[A-ZА-ЯІЇЄҐ]", в.id):
            мод = м.ім if в.id in м.сталі else м.імпорт_імен.get(в.id)
            for мм in self.модулі:
                if мм.ім == мод and в.id in мм.сталі:
                    return ("%s.%s" % (мм.ім, в.id), мм.сталі[в.id][0], (мм.шлях, мм.сталі[в.id][1]), None)
            return None
        if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name) and в.attr.upper() == в.attr \
                and re.search(r"[A-ZА-ЯІЇЄҐ]", в.attr):
            мод = м.псевдо.get(в.value.id)
            for мм in self.модулі:
                if мм.ім == мод and в.attr in мм.сталі:
                    return ("%s.%s" % (мм.ім, в.attr), мм.сталі[в.attr][0], (мм.шлях, мм.сталі[в.attr][1]), None)
            return None
        if isinstance(в, ast.Name) and ф is not None:
            # локальний псевдонім константи: `поріг = C["…"]`
            for п in ast.walk(ф):
                if isinstance(п, ast.Assign) and len(п.targets) == 1 and isinstance(п.targets[0], ast.Name) \
                        and п.targets[0].id == в.id:
                    return self.стала(м, ф, п.value, глибина + 1)
        return None

    def модуль_реєстру(self, мод, ім, глибина=0):
        """Модуль, що визначає реєстр `ім`, видимий у модулі `мод` (з ланцюгом `from X import ім`)."""
        if мод is None or глибина > 4:
            return None
        for мм in self.модулі:
            if мм.ім == мод:
                if ім in мм.реєстри:
                    return мм
                return self.модуль_реєстру(мм.імпорт_імен.get(ім), ім, глибина + 1)
        return None

    # ── місце ──
    def додати(self, файл, рядок, пункт, доказ):
        з = self.місця.setdefault((файл, рядок), {"пункти": set(), "доказ": []})
        з["пункти"].add(пункт)
        if доказ not in з["доказ"]:
            з["доказ"].append(доказ)

    def відкинути(self, корінь):
        self.поза[корінь] = self.поза.get(корінь, 0) + 1

    def імена_величини(self, корінь_вузла):
        кеш = getattr(self, "_імена", None)
        if кеш is None:
            кеш = {}
            for x in list(self.о.б):
                кеш.setdefault(self.о.знайти(x), set()).add(x[-1] if isinstance(x[-1], str) else str(x[-1]))
            self._імена = кеш
        return кеш.get(корінь_вузла) or {str(корінь_вузла[-1])}


def без_коментарів_js(т):
    """JS/HTML без `//…` (не після `:` — адреса) і `/* … */`, зі збереженням рядків."""
    т = re.sub(r"/\*.*?\*/", lambda м: "\n" * м.group(0).count("\n"), т, flags=re.S)
    т = re.sub(r"(?<![:\\\"'])//[^\n]*", "", т)
    т = re.sub(r"<!--.*?-->", lambda м: "\n" * м.group(0).count("\n"), т, flags=re.S)
    return т


# ── аналіз ──────────────────────────────────────────────────────────────────────────────────────────────────────
НАПРЯМ = {ast.Lt: "верх", ast.LtE: "верх", ast.Gt: "низ", ast.GtE: "низ"}
ОБЕРНЕНО = {"верх": "низ", "низ": "верх"}
СИРІ_ОПЕРАЦІЇ = {"strip", "lstrip", "rstrip", "lower", "casefold", "split", "title"}


def назва_виклику(в):
    if isinstance(в, ast.Call):
        if isinstance(в.func, ast.Name):
            return в.func.id
        if isinstance(в.func, ast.Attribute):
            return в.func.attr
    return None


def повертає_значення(д):
    """Функція повертає саме значення (рядок чи код), а не збірку (словник, список, кортеж)."""
    повернення = [в.value for в in ast.walk(д) if isinstance(в, ast.Return) and в.value is not None]
    return bool(повернення) and not any(isinstance(п, (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.DictComp,
                                                       ast.ListComp, ast.SetComp, ast.GeneratorExp))
                                        for п in повернення)


def закодоване(в, коди, імена):
    """Вираз сам є кодом: виклик кодувальника, ім'я з нього, `a or b`, `a if c else b` з них."""
    if isinstance(в, ast.Call):
        return назва_виклику(в) in коди
    if isinstance(в, ast.Name):
        return в.id in імена
    if isinstance(в, ast.BoolOp):
        return any(закодоване(x, коди, імена) for x in в.values)
    if isinstance(в, ast.IfExp):
        return закодоване(в.body, коди, імена) or закодоване(в.orelse, коди, імена)
    return False


def кодувальники(л):
    """Нерухома точка: функція читає `ТАБЛИЦЯ` і повертає значення, чи повертає (прямо, через локальне ім'я,
    `or`, умовний вираз) виклик кодувальника — не збірку, в якій код лише одне з полів."""
    коди = set()
    for ім, визн in л.визначення.items():
        for м, д in визн:
            if any((isinstance(в, ast.Name) and в.id == "ТАБЛИЦЯ" and (м.ім == ТАБЛИЦЯ_МОВИ
                                                                   or м.імпорт_імен.get("ТАБЛИЦЯ") == ТАБЛИЦЯ_МОВИ))
                   or (isinstance(в, ast.Attribute) and в.attr == "ТАБЛИЦЯ" and isinstance(в.value, ast.Name)
                       and м.псевдо.get(в.value.id) == ТАБЛИЦЯ_МОВИ)
                   for в in ast.walk(д)) and повертає_значення(д):
                коди.add(ім)
    змінено = True
    while змінено:
        змінено = False
        for ім, визн in л.визначення.items():
            if ім in коди:
                continue
            for м, д in визн:
                закодовані = set()
                for в in ast.walk(д):
                    if isinstance(в, ast.Assign) and закодоване(в.value, коди, закодовані):
                        for ц in в.targets:
                            if isinstance(ц, ast.Name):
                                закодовані.add(ц.id)
                for в in ast.walk(д):
                    if isinstance(в, ast.Return) and в.value is not None and закодоване(в.value, коди, закодовані):
                        коди.add(ім)
                        змінено = True
                        break
                if ім in коди:
                    break
    return коди


def рампи(л):
    """Функції-рампи: `(x - від) / (до - від)` — параметр 0 мірять між параметрами-межами (порядок підпису)."""
    вих = {}
    for ім, визн in л.визначення.items():
        for м, д in визн:
            п = [а.arg for а in д.args.args]
            if len(п) < 3:
                continue
            пари = set()
            for в in ast.walk(д):
                if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Sub):
                    ліве = в.left.args[0] if isinstance(в.left, ast.Call) and в.left.args else в.left
                    if isinstance(ліве, ast.Name) and isinstance(в.right, ast.Name):
                        пари.add((ліве.id, в.right.id))
            межі = {i for i in range(1, len(п)) if (п[0], п[i]) in пари}
            межі |= {j for j in range(1, len(п)) for i in межі if (п[j], п[i]) in пари or (п[i], п[j]) in пари}
            if len(межі) >= 2:
                вих[(м.шлях, ім)] = sorted(межі)
    return вих


def пороги(л, рампа):
    """Усі пороги: порівняння величини з числом чи константою, межі рамп. → [поріг]."""
    вих = []
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            ф = None
            if isinstance(в, ast.Compare):
                ф = м.функція(в)
                ліві = [в.left] + в.comparators[:-1]
                for ліве, оп, праве in zip(ліві, в.ops, в.comparators):
                    н = НАПРЯМ.get(type(оп))
                    if н is None:
                        continue
                    for вел, пор, напр in ((ліве, праве, н), (праве, ліве, ОБЕРНЕНО[н])):
                        з = поріг_з(л, м, ф, вел, пор, напр, в)
                        if з:
                            вих.append(з)
            elif isinstance(в, ast.Call) and isinstance(в.func, (ast.Name, ast.Attribute)):
                ім = в.func.id if isinstance(в.func, ast.Name) else в.func.attr
                межі = next((мж for (шл, ір), мж in рампа.items() if ір == ім), None)
                if межі and в.args and len(в.args) > max(межі):
                    ф = м.функція(в)
                    for к, і in enumerate(межі):
                        з = поріг_з(л, м, ф, в.args[0], в.args[і], "верх" if к == 0 else "низ", в)
                        if з:
                            з["рампа"] = ім
                            вих.append(з)
    return вих


def поріг_з(л, м, ф, вел, пор, напр, вузол):
    ч = число(пор)
    ст = None if ч is not None else л.стала(м, ф, пор)
    if ч is None and ст is None:
        return None
    if ч in (0, 1):
        return None            # 0 — знак, 1 — повнота частки чи «хоч один»: не межа величини
    if число(вел) is not None or л.стала(м, ф, вел) is not None:
        return None
    if isinstance(вел, ast.Call) and назва_виклику(вел) in ("len", "sum", "count", "index", "find"):
        return None
    носій = л.носій(м, ф, вел)
    return dict(файл=м.шлях, рядок=вузол.lineno, м=м, ф=ф, вузол=вузол, вел=вел, носій=носій,
                q=л.величина(носій), напрям=напр, літ=ч, стала=ст,
                визн=("літ", ч) if ч is not None else ("стала", ст[0]),
                текст_вел=ast.unparse(вел)[:60])


def заяви_правил(л):
    """Точки ід правила: виклик з ід першим аргументом, кортеж з ід першим, ключ словника-ід, `id=`/`прав=`.
    → [(м, вузол, ід, вид)], тлумачення [(ід, файл, рядок, текст)]."""
    точки, тлумачення = [], []
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.Call):
                if в.args and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str) \
                        and ІД_ПРАВИЛА.match(в.args[0].value):
                    точки.append((м, в, в.args[0].value, "заява"))
                кв = {кл.arg: кл.value for кл in в.keywords if кл.arg}
                ід = кв.get("id")
                if isinstance(ід, ast.Constant) and isinstance(ід.value, str) and ІД_ПРАВИЛА.match(ід.value):
                    точки.append((м, в, ід.value, "означення"))
                    т = рядки_тексту(кв.get("суть")) or рядки_тексту(кв.get("зміст"))
                    if т:
                        тлумачення.append((ід.value, м.шлях, в.lineno, т))
            elif isinstance(в, ast.Tuple) and len(в.elts) >= 2 and isinstance(в.elts[0], ast.Constant) \
                    and isinstance(в.elts[0].value, str) and ІД_ПРАВИЛА.match(в.elts[0].value):
                б = м.батько.get(в)
                if isinstance(б, ast.Call) and б.args and б.args[0] is в:
                    pass
                точки.append((м, в, в.elts[0].value, "кортеж"))
                т = рядки_тексту(в.elts[1])
                if " " in т.strip():
                    тлумачення.append((в.elts[0].value, м.шлях, в.lineno, т))
            elif isinstance(в, ast.Dict):
                for к, з in zip(в.keys, в.values):
                    if isinstance(к, ast.Constant) and isinstance(к.value, str) and ІД_ПРАВИЛА.match(к.value):
                        точки.append((м, к, к.value, "рядок таблиці"))
                        т = рядки_тексту(з)
                        if " " in т.strip():
                            тлумачення.append((к.value, м.шлях, к.lineno, т))
        for ім, записи in м.реєстри.items():
            for ключ, з in записи.items():
                for ід in з["прав"]:
                    if isinstance(ід, str) and ІД_ПРАВИЛА.match(ід):
                        точки.append((м, з["рядок"], ід, "запис реєстру"))
    return точки, тлумачення


def вартові(м, вузол):
    """Умови, що стережуть вузол: тест `if`/`elif`/умовного виразу, у чиїй гілці `body` він стоїть, і `if` генератора."""
    вих = []
    в, попер = м.батько.get(вузол), вузол
    while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
        if isinstance(в, ast.If) and попер in в.body:
            вих.append(в.test)
        elif isinstance(в, ast.IfExp) and попер is в.body:
            вих.append(в.test)
        elif isinstance(в, ast.comprehension):
            вих.extend(в.ifs)
        в, попер = м.батько.get(в), в
    return вих


def означення_корпусу(корінь):
    """{ід} з означенням у корпусі: `правила.формулювання` дерева, інакше «**ід.» чи «ід.» на початку рядка теми."""
    дж = os.path.join(корінь, "джерела")
    try:
        sys.path.insert(0, дж)
        import importlib
        правила = importlib.import_module("правила")
        if os.path.abspath(os.path.dirname(правила.__file__)) == os.path.abspath(дж):
            return set(правила.формулювання())
    except Exception:
        pass
    finally:
        if sys.path and sys.path[0] == дж:
            sys.path.pop(0)
    вих = set()
    for ф in sorted(os.listdir(дж)) if os.path.isdir(дж) else []:
        if ф.startswith("тема-") and ф.endswith(".md"):
            with open(os.path.join(дж, ф), encoding="utf-8") as д:
                вих |= set(re.findall(r"(?:\*\*|^>?\s*)([KR]-[A-Z]+-\d+[A-Z]?)\.", д.read(), flags=re.M))
    return вих


ЩЕ_В_РОБОТІ = object()


def запам(функція):
    """Пам'ять сліду: вузол уже в роботі (цикл) — None; готовий — той самий клас (лічба детермінована)."""
    def обгортка(л, *арг):
        кеш = л.__dict__.setdefault("_слід_" + функція.__name__, {})
        ключ = tuple(id(а) if isinstance(а, ast.AST) else а for а in арг[:-1])
        if ключ in кеш:
            if кеш[ключ] is ЩЕ_В_РОБОТІ:
                л._цикл = True
                return None
            return кеш[ключ]
        кеш[ключ] = ЩЕ_В_РОБОТІ
        було, л._цикл = getattr(л, "_цикл", False), False
        вих = функція(л, *арг)
        if л._цикл and вих is None:
            del кеш[ключ]          # неповне через цикл — не пам'ятаємо
        else:
            кеш[ключ] = вих
        л._цикл = було or л._цикл
        return вих
    return обгортка


@запам
def класифікувати(л, м, ф, в, глибина=0):
    """Джерело значення, що пишеться: «код» (через кодувальник), «сире» (слова без кодувальника), інакше None."""
    if глибина > ГЛИБИНА_СЛІДУ or в is None:
        return None
    if any(назва_виклику(п) in л.кодувальники for п in ast.walk(в)):
        return "код" if глибина <= 1 else None
    if any(назва_виклику(п) in СИРІ_ОПЕРАЦІЇ or (назва_виклику(п) == "str" and isinstance(п.func, ast.Name))
           for п in ast.walk(в)):
        return "сире"
    if isinstance(в, ast.Call) and назва_виклику(в) in ("list", "tuple") and в.args \
            and isinstance(в.args[0], (ast.Name, ast.Subscript, ast.Call)):
        в = в.args[0]
    if isinstance(в, ast.Call) and назва_виклику(в) in л.визначення:
        # функція продукту: клас того, що вона повертає
        ім = назва_виклику(в)
        if isinstance(в.func, ast.Name):
            мод = м.імпорт_імен.get(ім, м.ім)
        elif isinstance(в.func.value, ast.Name):
            мод = м.псевдо.get(в.func.value.id)
        else:
            мод = None
        цілі = визначення_в(л, мод, ім)
        if len(цілі) == 1:
            мм, д = цілі[0]
            класи = {класифікувати(л, мм, д, п.value, глибина + 1) for п in ast.walk(д)
                     if isinstance(п, ast.Return) and п.value is not None and мм.функція(п) is д}
            класи.discard(None)
            return "код" if "код" in класи else ("сире" if класи else None)
    if isinstance(в, ast.BoolOp):
        класи = {класифікувати(л, м, ф, x, глибина + 1) for x in в.values}
        return "код" if "код" in класи else ("сире" if "сире" in класи else None)
    if СЛІД_КЛЮЧЕМ and глибина >= 2 and isinstance(в, ast.Call) and назва_виклику(в) == "get" and в.args \
            and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
        return клас_ключа(л, в.args[0].value, глибина + 1)
    if СЛІД_КЛЮЧЕМ and глибина >= 2 and isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) \
            and isinstance(в.slice.value, str):
        return клас_ключа(л, в.slice.value, глибина + 1)
    if isinstance(в, ast.Name) and ф is not None:
        if в.id in {а.arg for а in ф.args.posonlyargs + ф.args.args + ф.args.kwonlyargs}:
            return клас_параметра(л, ф, в.id, глибина + 1)
        класи = {класифікувати(л, м, ф, п.value, глибина + 1) for п in ast.walk(ф)
                 if isinstance(п, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == в.id for ц in п.targets)}
        класи.discard(None)
        return "код" if "код" in класи else ("сире" if класи else None)
    return None


def виклики(л):
    """(модуль, ім'я функції) → [(м, ф-викликач, Call)]: виклик за ім'ям у своєму модулі чи з `from M import`,
    за атрибутом псевдоніма модуля (кеш)."""
    кеш = getattr(л, "_виклики", None)
    if кеш is None:
        кеш = {}
        for м in л.модулі:
            for в in ast.walk(м.дерево):
                if isinstance(в, ast.Call):
                    ім = назва_виклику(в)
                    if ім not in л.визначення:
                        continue
                    if isinstance(в.func, ast.Name):
                        мод = м.імпорт_імен.get(ім, м.ім)
                    elif isinstance(в.func.value, ast.Name):
                        мод = м.псевдо.get(в.func.value.id)
                    else:
                        мод = None
                    кеш.setdefault((мод, ім), []).append((м, м.функція(в), в))
        л._виклики = кеш
    return кеш


def визначення_в(л, мод, ім, глибина=0):
    """Визначення функції `ім`, видимої в модулі `мод`: своє, з `from X import ім`, з `from X import *`."""
    if мод is None or глибина > 4:
        return []
    свої = [(мм, д) for мм, д in л.визначення.get(ім, []) if мм.ім == мод and мм.функція(д) is None]
    if свої:
        return свої
    м = next((мм for мм in л.модулі if мм.ім == мод), None)
    if м is None:
        return []
    if ім in м.імпорт_імен:
        return визначення_в(л, м.імпорт_імен[ім], ім, глибина + 1)
    for з in м.зірки:
        вих = визначення_в(л, з, ім, глибина + 1)
        if вих:
            return вих
    return []


def модуль_функції(л, ф):
    return next((м for м, д in л.визначення.get(ф.name, []) if д is ф), None)


@запам
def клас_ключа(л, ключ, глибина):
    """Клас значення ключа — за всіма його писачами (ключ словника несе величину між функціями)."""
    if глибина > ГЛИБИНА_СЛІДУ or загальне(ключ):
        return None
    класи = {класифікувати(л, м, ф, з, глибина + 1) for м, ф, з, _, _ in сирі_писачі(л).get(ключ, [])}
    класи.discard(None)
    return "код" if "код" in класи else ("сире" if класи else None)


@запам
def клас_параметра(л, ф, параметр, глибина):
    """Клас значення параметра — за аргументами в місцях виклику цієї функції."""
    м0 = модуль_функції(л, ф)
    if глибина > ГЛИБИНА_СЛІДУ or м0 is None:
        return None
    поз = [а.arg for а in ф.args.posonlyargs + ф.args.args]
    класи = set()
    for м, фв, в in виклики(л).get((м0.ім, ф.name), []):
        арг = next((кл.value for кл in в.keywords if кл.arg == параметр), None)
        if арг is None and параметр in поз:
            і = поз.index(параметр) - (1 if поз and поз[0] in ("self", "cls") else 0)
            арг = в.args[і] if 0 <= і < len(в.args) and not isinstance(в.args[і], ast.Starred) else None
        if арг is not None:
            класи.add(класифікувати(л, м, фв, арг, глибина))
    класи.discard(None)
    return "код" if "код" in класи else ("сире" if класи else None)


def писачі(л):
    """Записи ключів виходу з класом джерела → [(ключ, м, ф, рядок, клас)]."""
    вих = []
    for ключ, записи in сирі_писачі(л).items():
        for м, ф, знач, рядок, аргумент in записи:
            if аргумент:
                continue
            кл = класифікувати(л, м, ф, знач, 0)
            if кл:
                вих.append((ключ, м, ф, рядок, кл))
    return вих


def сирі_писачі(л):
    """Записи ключів виходу: `x["к"] = e`, `{"к": e}`, `dict(к=e)`, `f(к=e)` → {ключ: [(м, ф, e, рядок)]} (кеш)."""
    кеш = getattr(л, "_писачі", None)
    if кеш is not None:
        return кеш
    кеш = л._писачі = {}
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            пари = []
            if isinstance(в, ast.Assign):
                for ц in в.targets:
                    if isinstance(ц, ast.Subscript) and isinstance(ц.slice, ast.Constant) \
                            and isinstance(ц.slice.value, str):
                        пари.append((ц.slice.value, в.value, ц.lineno))
            elif isinstance(в, ast.Dict):
                пари = [(к.value, з, к.lineno) for к, з in zip(в.keys, в.values)
                        if isinstance(к, ast.Constant) and isinstance(к.value, str)]
            elif isinstance(в, ast.Call):
                пари = [(кл.arg, кл.value, кл.value.lineno) for кл in в.keywords if кл.arg]
            if not пари:
                continue
            ф = м.функція(в)
            аргумент = isinstance(в, ast.Call) and not (isinstance(в.func, ast.Name) and в.func.id == "dict")
            for ключ, знач, рядок in пари:
                кеш.setdefault(ключ, []).append((м, ф, знач, рядок, аргумент))
    return кеш


def переліки_ключів(л):
    """Переліки ключів, які читають разом: генератор над кортежем ≥ 3 рядків з `X.get(к)`/`X[к]` змінною циклу,
    словник ≥ 3 значень, кожне з яких читає `X.get("к")`/`X["к"]` того самого X. → [(м, ф, рядок, frozenset)]."""
    вих = []
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if isinstance(в, (ast.GeneratorExp, ast.ListComp, ast.SetComp)) and len(в.generators) == 1:
                г = в.generators[0]
                if isinstance(г.iter, (ast.Tuple, ast.List, ast.Set)) and isinstance(г.target, ast.Name) \
                        and len(г.iter.elts) >= 3 and all(isinstance(е, ast.Constant) and isinstance(е.value, str)
                                                          for е in г.iter.elts):
                    читає = any(
                        (isinstance(п, ast.Call) and назва_виклику(п) == "get" and п.args
                         and isinstance(п.args[0], ast.Name) and п.args[0].id == г.target.id)
                        or (isinstance(п, ast.Subscript) and isinstance(п.slice, ast.Name)
                            and п.slice.id == г.target.id)
                        for п in ast.walk(в.elt))
                    if читає:
                        вих.append((м, м.функція(в), в.lineno, frozenset(е.value for е in г.iter.elts)))
            elif isinstance(в, ast.Dict) and len(в.values) >= 3:
                ключі, бази = set(), set()
                for з in в.values:
                    читання = [п for п in ast.walk(з)
                               if (isinstance(п, ast.Call) and назва_виклику(п) == "get" and п.args
                                   and isinstance(п.args[0], ast.Constant) and isinstance(п.args[0].value, str)
                                   and isinstance(п.func.value, ast.Name))]
                    if len(читання) != 1:
                        ключі = None
                        break
                    ключі.add(читання[0].args[0].value)
                    бази.add(читання[0].func.value.id)
                if ключі and len(ключі) >= 3 and len(бази) == 1:
                    вих.append((м, м.функція(в), в.lineno, frozenset(ключі)))
    return вих


def типові_py(л):
    """Типові значення: `x or <літерал>`, `.get(к, <літерал>)`, параметр `p=<літерал>` → [(файл, рядок, вузол, знач, вид)]."""
    вих = []
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.BoolOp) and isinstance(в.op, ast.Or) and len(в.values) >= 2:
                зн = літерал_типове(в.values[-1])
                if зн is not None:
                    ф = м.функція(в)
                    носій = next((н for н in (л.носій(м, ф, x) for x in в.values[:-1]) if н), None)
                    вих.append((м.шлях, в.lineno, носій, зн, "or", ast.unparse(в.values[0])[:40]))
            elif isinstance(в, ast.Call) and назва_виклику(в) == "get" and isinstance(в.func, ast.Attribute) \
                    and len(в.args) == 2 and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
                зн = літерал_типове(в.args[1])
                if зн is not None:
                    к = в.args[0].value
                    вих.append((м.шлях, в.lineno, None if загальне(к) else ("к", к.lower()), зн, ".get", к))
            elif isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                поз = в.args.posonlyargs + в.args.args
                пари = list(zip(поз[len(поз) - len(в.args.defaults):], в.args.defaults)) + \
                    [(а, д) for а, д in zip(в.args.kwonlyargs, в.args.kw_defaults) if д is not None]
                for а, д in пари:
                    зн = літерал_типове(д)
                    if зн is not None:
                        вих.append((м.шлях, д.lineno, None if загальне(а.arg) else ("к", а.arg.lower()), зн,
                                    "параметр", а.arg))
    return вих


JS_ТИПОВЕ = re.compile(r"([A-Za-z_$А-Яа-яЇїІіЄєҐґ][\w$]*(?:\.[\w$]+|\[\s*['\"][^'\"\]]+['\"]\s*\])*)\s*(\|\||\?\?)\s*"
                       r"(\"[^\"\n]+\"|'[^'\n]+'|-?\d+(?:\.\d+)?)(?![\w.(])")
JS_ПАРАМЕТР = re.compile(r"(?:function\s*[\w$]*\s*\(|\(\s*)([^()]*?)\)\s*(?:=>|\{)")


def типові_js(л):
    вих = []
    for шлях, текст in л.js:
        рядки = текст.split("\n")
        for і, р in enumerate(рядки, 1):
            for м in JS_ТИПОВЕ.finditer(р):
                ліве, зн = м.group(1), м.group(3)
                знач = зн[1:-1] if зн[0] in "\"'" else float(зн)
                if знач in ("", 0) or (isinstance(знач, str) and not re.search(r"\w", знач)):
                    continue
                ім = re.findall(r"[\w$А-Яа-яЇїІіЄєҐґ]+", ліве)[-1]
                вих.append((шлях, і, None if загальне(ім) else ("к", ім.lower()), знач, "||", ліве[:40]))
        for м in JS_ПАРАМЕТР.finditer(текст):
            for п in re.finditer(r"([\w$]+)\s*=\s*(\"[^\"\n]+\"|'[^'\n]+'|-?\d+(?:\.\d+)?)", м.group(1)):
                зн = п.group(2)
                знач = зн[1:-1] if зн[0] in "\"'" else float(зн)
                if знач in ("", 0) or (isinstance(знач, str) and not re.search(r"\w", знач)):
                    continue
                і = текст.count("\n", 0, м.start(1) + п.start()) + 1
                вих.append((шлях, і, None if загальне(п.group(1)) else ("к", п.group(1).lower()), знач, "параметр",
                            п.group(1)))
    return вих


def лічити(корінь):
    л = Лічба(корінь)
    л.зібрати()
    л.потік()
    л.кодувальники = кодувальники(л)
    звіт = {}

    # ── п.5: типові ──
    типові = типові_py(л) + типові_js(л)
    for файл, рядок, носій, зн, вид, що in типові:
        if isinstance(зн, str) and re.fullmatch(r"[\w\-]{3,}", зн) and not зн.isdigit():
            л.о.злити(носій, ("знач", зн)) if носій else None
    групи = {}
    for файл, рядок, носій, зн, вид, що in типові:
        інший = іншого_кореня(що, *(л.імена_величини(л.величина(носій)) if носій else ()))
        if isinstance(зн, str) and (зн in СИЛА or зн in СЛОВА_ПОРИ):
            інший = інший or ("Е3-сила-правила" if зн in СИЛА else "Е2-частина-дня")
        if інший:
            л.відкинути(інший)
            continue
        q = л.величина(носій) if носій else (л.величина(("знач", зн)) if isinstance(зн, str)
                                             and re.fullmatch(r"[\w\-]{3,}", зн) and not зн.isdigit() else None)
        if q is None:
            continue
        # одна величина й те саме типове — двічі й більше: злиття потоку буває ширшим за величину, а однакове
        # значення в одній компоненті — ні (різні значення в одній компоненті — ще не доказ однієї величини)
        групи.setdefault((q, repr(зн)), []).append((файл, рядок, зн, вид, що))
    п5 = 0
    for (q, _), сайти in групи.items():
        if len({(ф, р) for ф, р, *_ in сайти}) < 2:
            continue
        ім = sorted(л.імена_величини(q) - {з for _, _, з, _, _ in сайти})[:3]
        for ф, р, з, вид, що in сайти:
            л.додати(ф, р, 5, "типове %r (%s %s) — величина [%s], те саме типове в %d місцях" % (
                з, вид, що, ", ".join(ім), len(сайти)))
            п5 += 1
    звіт["п.5 типових у групах"] = п5

    # ── пороги ──
    рампа = рампи(л)
    всі = []
    for п in пороги(л, рампа):
        інший = іншого_кореня(п["текст_вел"], п["стала"][0] if п["стала"] else None,
                              *(л.імена_величини(п["q"]) if п["q"] else ()))
        if інший:
            л.відкинути(інший)
            continue
        всі.append(п)

    # ── п.2(а): записи T3 сесії ──
    сесійні = {}
    for м in л.модулі:
        for ім, записи in м.реєстри.items():
            for ключ, з in записи.items():
                if з["t"] != "T3" or not СЛОВО_СЕСІЇ.search(з["суть"]) or ПОСИЛАННЯ.search(з["суть"]):
                    continue
                if not any(isinstance(і, str) and ІД_ПРАВИЛА.match(і) for і in з["прав"]):
                    continue
                if іншого_кореня(ключ):
                    л.відкинути(іншого_кореня(ключ))
                    continue
                назва = "%s.%s[%s]" % (м.ім, ім, ключ)
                сесійні[назва] = з
                л.додати(м.шлях, з["рядок"], 2, "запис T3 %s=%s (%s): опис сесії «%s», джерела нема" % (
                    назва, з["val"], "/".join(з["прав"]), СЛОВО_СЕСІЇ.search(з["суть"]).group(0)))
    for п in всі:
        if п["стала"] and п["стала"][0] in сесійні:
            л.додати(п["файл"], п["рядок"], 2, "%s %s %s — межа числом сесії (T3)" % (
                п["текст_вел"], "≤" if п["напрям"] == "верх" else "≥", п["стала"][0]))

    # ── п.1(а), (б): величина з константою й літералом; константи кількох реєстрів ──
    за_q = {}
    for п in всі:
        if п["q"] is not None:
            за_q.setdefault(п["q"], []).append(п)
    for q, сайти in за_q.items():
        сталі = [п for п in сайти if п["стала"]]
        if not сталі:
            continue
        ім = ", ".join(sorted(л.імена_величини(q))[:3])
        # (а) та сама межа в одному рішенні: функція, величина, напрям — і константа, і голе число
        for п in сайти:
            if п["літ"] is None:
                continue
            сусід = next((с for с in сталі if с["ф"] is п["ф"] and с["файл"] == п["файл"]
                          and с["напрям"] == п["напрям"] and с["стала"][1] != п["літ"]), None)
            if сусід:
                л.додати(п["файл"], п["рядок"], 1, "%s %s %s голим числом, а в тій самій функції та сама межа — %s=%s (:%d)" % (
                    п["текст_вел"], "≤" if п["напрям"] == "верх" else "≥", п["літ"], сусід["стала"][0],
                    сусід["стала"][1], сусід["рядок"]))
        # (б) одна межа — записами двох реєстрів, і опис одного називає другий
        for напрям in ("верх", "низ"):
            група = [п for п in сталі if п["напрям"] == напрям and п["стала"][3]]
            for п1 in група:
                for п2 in група:
                    с1, с2 = п1["стала"], п2["стала"]
                    if с1[2][0] == с2[2][0] or с1[1] == с2[1]:
                        continue
                    ключ2 = с2[0].split("[")[-1].rstrip("]")
                    ключ1 = с1[0].split("[")[-1].rstrip("]")
                    if ключ2 not in с1[3]["суть"] and ключ1 not in с2[3]["суть"]:
                        continue
                    доказ = "межа [%s] %s — двома реєстрами: %s=%s і %s=%s, опис одного називає другий" % (
                        ім, напрям, с1[0], с1[1], с2[0], с2[1])
                    for п in (п1, п2):
                        л.додати(п["файл"], п["рядок"], 1, доказ)
                        л.додати(п["стала"][2][0], п["стала"][2][1], 1, "запис: " + доказ)

    # ── заяви правил, вартові, п.1(в), п.2(б), п.4 ──
    точки, тлумачення = заяви_правил(л)
    корпус = означення_корпусу(корінь)
    пороги_вузла = {}
    for п in всі:
        пороги_вузла.setdefault(id(п["вузол"]), []).append(п)
    вартові_ід = {}
    for м, вузол, ід, вид in точки:
        if isinstance(вузол, int):
            continue
        for т in вартові(м, вузол):
            for п in (пп for в in ast.walk(т) for пп in пороги_вузла.get(id(в), [])):
                вартові_ід.setdefault(ід, []).append(п)
    for ід, сайти in sorted(вартові_ід.items()):
        унікальні = {(п["файл"], п["рядок"], п["визн"]): п for п in сайти}
        for п in унікальні.values():
            if п["літ"] is not None and п["q"] is not None:
                л.додати(п["файл"], п["рядок"], 2, "%s %s %s — межа правила %s голим числом" % (
                    п["текст_вел"], "≤" if п["напрям"] == "верх" else "≥", п["літ"], ід))
        for напрям in ("верх", "низ"):
            група = [п for п in унікальні.values() if п["напрям"] == напрям]
            значення = {п["стала"][1] if п["стала"] else п["літ"] for п in група}
            if len(значення) >= 2:
                for п in група:
                    л.додати(п["файл"], п["рядок"], 1, "межа вмикання %s %s різними числами: %s" % (
                        ід, напрям, ", ".join(str(з) for з in sorted(значення, key=str))))
    за_ід = {}
    for ід, файл, рядок, текст in тлумачення:
        за_ід.setdefault(ід, []).append((файл, рядок, текст))
    двозначні = {}
    for ід, тт in за_ід.items():
        if ід not in корпус:
            continue
        for і in range(len(тт)):
            for j in range(і + 1, len(тт)):
                а, б = основи(тт[і][2]), основи(тт[j][2])
                if len(а) >= 2 and len(б) >= 2 and not (а & б) and тт[і][0] != тт[j][0]:
                    двозначні.setdefault(ід, (тт[і], тт[j]))
    for ід, (т1, т2) in sorted(двозначні.items()):
        доказ = "ід %s — два змісти без спільного слова: «%s» (%s:%d) і «%s» (%s:%d)" % (
            ід, т1[2][:50], т1[0].split("/")[-1], т1[1], т2[2][:50], т2[0].split("/")[-1], т2[1])
        for м, вузол, і, вид in точки:
            if і == ід:
                л.додати(м.шлях, вузол if isinstance(вузол, int) else вузол.lineno, 4, "%s: %s" % (вид, доказ))
        for п in вартові_ід.get(ід, []):
            л.додати(п["файл"], п["рядок"], 4, "вартовий заяви %s: %s %s" % (ід, п["текст_вел"], п["визн"][1]))
    звіт["п.4 ід з двома змістами"] = sorted(двозначні)

    # ── п.3(а): код проти сирого ──
    за_ключем = {}
    for ключ, м, ф, рядок, кл in писачі(л):
        if загальне(ключ) or іншого_кореня(ключ) or not КЛЮЧ_ДРОТУ.match(ключ):
            continue
        за_ключем.setdefault(ключ, []).append((м.шлях, ф.name if ф else "<модуль>", рядок, кл))
    for ключ, сайти in sorted(за_ключем.items()):
        функції = {}
        for файл, фн, рядок, кл in сайти:
            функції.setdefault(кл, set()).add((файл, фн))
        if "код" in функції and "сире" in функції and (функції["код"] ^ функції["сире"]):
            for файл, фн, рядок, кл in сайти:
                л.додати(файл, рядок, 3, "ключ «%s» пише %s (%s), а %d інш. функцій — %s" % (
                    ключ, фн, "кодом таблиці" if кл == "код" else "сирими словами",
                    len(функції["сире" if кл == "код" else "код"]), "сирими словами" if кл == "код" else "кодом"))

    # ── п.3(б): переліки ключів ──
    пер = переліки_ключів(л)
    for м1, ф1, р1, г1 in пер:
        for м2, ф2, р2, г2 in пер:
            if г1 < г2 and len(г1) >= 3 and (м1.шлях, ф1) != (м2.шлях, ф2):
                різниця = ", ".join(sorted(г2 - г1))
                л.додати(м1.шлях, р1, 3, "ознака з ключів {%s} — менший перелік, ніж %s:%d (без: %s)" % (
                    ", ".join(sorted(г1)), м2.шлях.split("/")[-1], р2, різниця))
                л.додати(м2.шлях, р2, 3, "ознака з ключів {%s} — більший перелік, ніж %s:%d (понад: %s)" % (
                    ", ".join(sorted(г2)), м1.шлях.split("/")[-1], р1, різниця))
    звіт["кодувальників"] = len(л.кодувальники)
    return л, звіт


def друк(л, звіт, тихо=False, величини=False):
    вих = []
    if not тихо:
        for (ф, р), з in sorted(л.місця.items()):
            вих.append("%s:%d · п.%s · %s" % (ф, р, ",".join(str(п) for п in sorted(з["пункти"])), " | ".join(з["доказ"])))
    за_п = {}
    for з in л.місця.values():
        for п in з["пункти"]:
            за_п[п] = за_п.get(п, 0) + 1
    вих.append("за пунктами: " + ", ".join("п.%d — %d" % (п, н) for п, н in sorted(за_п.items())))
    за_ф = {}
    for (ф, р) in л.місця:
        за_ф[ф] = за_ф.get(ф, 0) + 1
    вих.append("за файлами: " + ", ".join("%s %d" % (ф.split("/")[-1], н)
                                          for ф, н in sorted(за_ф.items(), key=lambda x: (-x[1], x[0]))))
    вих.append("поза класом (інший корінь, не лічено): " + (", ".join("%s — %d" % (к, н) for к, н in sorted(л.поза.items()))
                                                             or "нема"))
    for к, з in звіт.items():
        вих.append("%s: %s" % (к, з))
    вих.append("місць: %d" % len(л.місця))
    return "\n".join(вих)


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
    л, звіт = лічити(корінь)
    print(друк(л, звіт, тихо="--тихо" in арг, величини="--величини" in арг))
    return 0


def самоперевірка():
    return []


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
