# -*- coding: utf-8 -*-
"""Прилад кореня Річ-запис-речі: місця за класом паспорта `аудит/корені/Річ-запис-речі.md`.

Місце — точка коду, що складає чи читає поле запису речі (тип, слот, комплект, склад, крій, довжина, рід, назва,
опис) і порушує інваріант: (1) читає слова регексом чи словником, щоб вивести код поля; (2) код поля — не з реєстру,
а зі свого переліку чи словника; (3) виводить поле удруге поза записом; (4) бере текст поля поза блоком товару.

Два шляхи (мірило наряду «а»):
  А — від полів до записувачів: усі записи в ключі поля й функції-виводники, звідти зворотним зрізом (дані й умови)
      до читачів слів;
  Б — від читачів слів до полів: усі словники, регекси й слівні перевірки, звідти вперед за потоком значення до
      коду реєстру чи ключа поля.
Місце, знайдене одним шляхом, друкується з позначкою шляху; розбіжність шляхів — окремий розділ у виводі.

Лічить синтаксичним розбором, не виконує код. Прилад читає лише дерево, яке йому дали (`--корінь`, за замовчуванням
поточна тека), тому кличеться на голові й на базі однаково. Вивід: `файл:рядок · пункт · чому`, підсумки за
пунктами, останній рядок `місць: <N>` (N — різні `файл:рядок`; місце з двома пунктами лічиться раз), код 0 —
формат храповика (`аудит/наряди/CI-храповик-кореня.md`).

Межі, які прилад називає, а не ховає: слова латиницею (hoodie, jeans) він як слова не бачить; текст, що не ходить
крізь імена функцій і змінних (`getattr`, рядкові імена), йому невидимий; назви функцій розв'язуються за кінцевим
іменем без типів, тож однойменні функції різних модулів зливаються (завищує, не занижує).
"""
import argparse
import ast
import os
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

warnings.filterwarnings("ignore")

КИРИЛИЦЯ = "а-яіїєґА-ЯІЇЄҐёЁъыэ"
СЛОВО_КИР = re.compile("[" + КИРИЛИЦЯ + "]{3,}")
ЛІТЕРА_КИР = re.compile("[" + КИРИЛИЦЯ + "]")
КОД_ЛАТ = re.compile(r"^[a-z][a-z0-9]*(?:_[a-z0-9]+)*$")

# ── Обсяг ────────────────────────────────────────────────────────────────────────────────────────────────────────
ТЕКИ_PY = ("джерела", "zhnyvarka")
ВИКЛЮЧЕНІ_ТЕКИ = ("проби", "прилади", "лабораторія", "__pycache__", "node_modules", "аудит", "дані_5191_5194",
                  "жнива_2026-09-18", "розвідка", "фікстури", "траса")
ВИКЛЮЧЕНІ_ІМЕНА = re.compile(r"^(?:тест_|test_|проба_|стенд_|pair_test|мутанти|батарея_|gate_|гейти_нові|доказ_|заміри_)")
# Реєстр кодів: звідси коди беруть, а не оголошують (п.2 класу). Окремі модулі, що ЛИШЕ перелічують поля реєстру
# (схеми, паспорт), сюди не входять: їхні переліки літералами — теж свій перелік.
РЕЄСТРИ = ("внутрішня_мова.py", "slots.py")        # каталог_коди.py — лише читач реєстру (рішення 11335)
ПЕРЕЛІКИ_ПОЛІВ_РЕЄСТРУ = ("item_type", "slot", "fabric", "fabric_kind", "material", "length", "shaft", "girth")

# Імена, якими мова коду сама називає слоти й поля: це коди, не слова крамниці.
ІМЕНА_РЕЄСТРУ = {"верх", "низ", "сукня", "комплект", "верхній_шар", "взуття", "сумка", "шарф", "головний_убір", "пояс",
                 "колготи", "шкарпетки", "прикраси", "сережки", "кольє", "намисто", "брошка", "браслет", "каблучка",
                 "окуляри", "рукавички", "годинник", "купальник", "білизна", "аксесуар", "слот", "тип", "склад", "крій",
                 "довжина", "рід", "назва", "опис", "колір", "ціна", "бренд", "фото", "статус", "розмір", "тканина"}

# Текстове походження: функція оперує текстом товару, якщо має параметр чи ключ із цього переліку.
ТЕКСТ_ПАРАМЕТРИ = {"назва", "name", "title", "опис", "description", "категорія", "category", "слаг", "slug", "url",
                   "hay", "haystack", "текст", "слово", "слова", "фраза", "рядок", "речення", "text", "word", "words",
                   "назви", "заголовок", "крихти", "offer", "оффер", "офер"}
ТЕКСТ_КЛЮЧІ = {"назва", "name", "title", "опис", "description", "категорія", "category", "розділ", "url", "слаг",
               "крихти", "назва_показу", "назва_суду", "param", "params", "параметри", "текст", "тип_оголошений",
               "категорія_крамниці", "хлібні_крихти", "заголовок", "h1"}

# ── Поля запису речі: ключі, якими їх зберігають ─────────────────────────────────────────────────────────────────
ПОЛЯ = {
    "тип": {"тип", "тип_речі", "item_type", "тип_набору", "вид", "вид_речі", "тип_верхнього", "типи"},
    "слот": {"слот", "slot", "слоти", "слоти_альт", "фото_слот", "підслот", "слоти_пулу"},
    "комплект": {"комплект", "склад_комплекту", "set_parts", "шар_у_комплекті", "склад_комплекту_джерело"},
    "склад": {"склад", "склад_тканини", "fabric", "composition", "матеріал", "material", "тканина", "волокно"},
    "крій": {"крій", "cut", "силует_речі", "крій_речі"},
    "довжина": {"довжина", "length", "довжина_речі", "довжина_клас"},
    "рід": {"рід", "рід_речі", "genus"},
    "назва": {"назва", "назва_показу", "name", "назва_суду"},
    "опис": {"опис", "description", "опис_речі"},
}
КОДОВІ_ПОЛЯ = {"тип", "слот", "комплект", "крій", "довжина", "рід"}
# імена полів/ключів у позиції значення — не коди
КОЛІРНИЙ_МОДУЛЬ = re.compile(r"колір|кольор|палітр")
ЧИТАЧ_ПОЗА = re.compile(r"кол[іо]р|кольор|мотив")
# читач тексту поля, що чистить/нормалізує назву чи опис (рішення 11335: чистка регексом чи словником — місце)
ЧИСТІЙ_ТЕКСТ = re.compile(r"назв|опис|чист|очист|прибр|нормал|текст")
НАЗВИ_ПОЛІВ = {"slot", "item_type", "kind", "type", "cut", "colour", "color", "length", "fabric", "unknown", "other", "none"}
КЛЮЧ_ПОЛЯ = {к: п for п, ключі in ПОЛЯ.items() for к in ключі}
ТЕКСТОВІ_ПОЛЯ = ("назва", "опис")          # текст, не код: слова в них чистять, коду з них не виводять
# Назви функцій-виводників: корінь слова в імені.
ВИВОДНИК = re.compile(
    r"^_?(?:тип|слот|комплект|набір|крій|довжин[аи]?|рід|вид|тканин[аи]?|склад|матеріал|предмет|іменник)(?:_|$)|_(?:типу|слота|слоту|виду|роду|крою|складу|тканини|набору|комплекту)$")
# Код-значення до поля: який перелік реєстру до якого поля належить.
ПЕРЕЛІК_ДО_ПОЛЯ = {"item_type": "тип", "slot": "слот", "fabric": "склад", "fabric_kind": "склад",
                   "material": "склад", "length": "довжина", "shaft": "довжина", "girth": "довжина"}

МЕТОДИ_РЕГЕКСУ = {"search", "match", "fullmatch", "findall", "finditer", "sub", "subn", "split"}
МЕТОДИ_РЯДКА = {"startswith", "endswith", "find", "rfind", "index", "count"}
ЗАГАЛЬНІ = {"get", "append", "items", "keys", "values", "lower", "upper", "strip", "split", "join", "format", "add",
            "update", "pop", "extend", "sort", "sorted", "len", "str", "int", "float", "list", "dict", "set", "tuple",
            "isinstance", "any", "all", "min", "max", "sum", "range", "enumerate", "zip", "map", "filter", "print",
            "open", "replace", "startswith", "endswith", "search", "match", "sub", "compile", "findall", "finditer",
            "fullmatch", "group", "groups", "setdefault", "copy", "bool", "getattr", "hasattr", "next", "iter",
            "reversed", "abs", "round", "repr", "type", "id", "ord", "chr", "write", "read", "close", "encode",
            "decode", "casefold", "title", "capitalize", "isdigit", "find", "index", "count", "rstrip", "lstrip",
            "partition", "rpartition", "splitlines", "zfill", "exists", "dumps", "loads", "load", "dump", "sleep"}


# ── Розбір дерева ────────────────────────────────────────────────────────────────────────────────────────────────
class Модуль:
    def __init__(self, шлях, відн, дерево, рядки):
        self.шлях, self.відн, self.дерево, self.рядки = шлях, відн, дерево, рядки
        self.реєстр = Path(відн).name in РЕЄСТРИ


def зібрати_файли(корінь):
    файли = []
    for тека in ТЕКИ_PY:
        for дір, піддіри, імена in os.walk(корінь / тека):
            піддіри[:] = sorted(д for д in піддіри if д not in ВИКЛЮЧЕНІ_ТЕКИ)
            for ім in sorted(імена):
                if ім.endswith(".py") and not ВИКЛЮЧЕНІ_ІМЕНА.match(ім):
                    файли.append(Path(дір) / ім)
    return файли


def прочитати_модулі(корінь, файли):
    модулі, помилки = [], []
    for ф in файли:
        відн = ф.relative_to(корінь).as_posix()
        try:
            текст = ф.read_text(encoding="utf-8")
            модулі.append(Модуль(ф, відн, ast.parse(текст), текст.split("\n")))
        except (SyntaxError, UnicodeDecodeError, ValueError) as е:
            помилки.append((відн, repr(е)[:80]))
    return модулі, помилки


def рядок_літерал(вузол):
    return вузол.value if isinstance(вузол, ast.Constant) and isinstance(вузол.value, str) else None


def слово_кир(рядок):
    """Слово крамниці: хоч три кириличні літери поспіль, без довгих речень, службових ідентифікаторів (`_`, цифри,
    великі літери всередині) і назв полів та імен слотів реєстру."""
    return (bool(рядок) and len(рядок) <= 40 and bool(СЛОВО_КИР.search(рядок)) and рядок.count(" ") <= 3
            and "_" not in рядок and not re.search(r"\d", рядок) and рядок not in ІМЕНА_РЕЄСТРУ)


КОДИ_ЛАТ_ГЛОБ = set()          # латинські коди реєстру; наповнює Аналіз


def латинський_візерунок(рядок):
    """Регекс із латинськими словами (слаг URL, транслітерація): ≥4 альтернативи і хоч одна — код реєстру чи його основа."""
    if not рядок or len(рядок) < 12 or "|" not in рядок or " " in рядок.strip():
        return False
    слова = [w for w in re.findall(r"[a-z]{3,}", re.sub(r"\\.|\(\?[^)]*\)", " ", рядок))]
    if len(слова) < 4:
        return False
    return any(w in КОДИ_ЛАТ_ГЛОБ or any(k.startswith(w) and len(w) >= 4 for k in КОДИ_ЛАТ_ГЛОБ) for w in слова)


def візерунок_має_слова(візерунок):
    без_класів = re.sub(r"\[(?:\\.|[^\]])*\]", "", візерунок)          # [а-яіїє] — клас символів, не слово
    без_класів = re.sub(r"\\[A-Za-z]", "", без_класів)
    return bool(СЛОВО_КИР.search(без_класів)) or латинський_візерунок(візерунок)


def ім_виклику(вузол):
    f = вузол.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def імена_в(вузол):
    """Усі імена (змінні й атрибути) у виразі."""
    вих = set()
    for н in ast.walk(вузол):
        if isinstance(н, ast.Name):
            вих.add(н.id)
        elif isinstance(н, ast.Attribute):
            вих.add(н.attr)
    return вих


def виклики_в(вузол):
    вих = set()
    for н in ast.walk(вузол):
        if isinstance(н, ast.Call):
            ім = ім_виклику(н)
            if ім:
                вих.add(ім)
    return вих


def ключ_у_підписі(вузол):
    """Підпис `x["ключ"]` / `x.get("ключ")` → ключ."""
    if isinstance(вузол, ast.Subscript):
        s = вузол.slice
        return рядок_літерал(s)
    if isinstance(вузол, ast.Call) and isinstance(вузол.func, ast.Attribute) and вузол.func.attr in (
            "get", "setdefault", "pop") and вузол.args:
        return рядок_літерал(вузол.args[0])
    return None


# ── Реєстр кодів (статично) ──────────────────────────────────────────────────────────────────────────────────────
def коди_реєстру(корінь):
    """{код: поле}: латинські коди з переліків реєстру і українські імена слотів. Нема реєстру — порожньо."""
    коди = {}
    мова = корінь / "джерела" / "внутрішня_мова.py"
    if мова.exists():
        дерево = ast.parse(мова.read_text(encoding="utf-8"))
        for н in дерево.body:
            if isinstance(н, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ТАБЛИЦЯ" for t in н.targets) \
                    and isinstance(н.value, ast.Dict):
                for к, з in zip(н.value.keys, н.value.values):
                    ім = рядок_літерал(к)
                    if ім in ПЕРЕЛІКИ_ПОЛІВ_РЕЄСТРУ and isinstance(з, ast.Dict):
                        for кк in з.keys:
                            код = рядок_літерал(кк)
                            if код:
                                коди.setdefault(код, ПЕРЕЛІК_ДО_ПОЛЯ[ім])
    слоти = корінь / "джерела" / "slots.py"
    if слоти.exists():
        for н in ast.walk(ast.parse(слоти.read_text(encoding="utf-8"))):
            с = рядок_літерал(н)
            if с and КОД_ЛАТ.match(с):
                коди.setdefault(с, "слот" if с in ("top", "bottom", "dress", "set", "outerwear", "shoes", "bag", "scarf",
                                                  "headwear", "belt", "tights", "socks", "jewelry", "earrings",
                                                  "collar_necklace", "necklace", "brooch", "bracelet", "ring",
                                                  "glasses", "gloves", "watch", "swimwear", "underwear",
                                                  "accessory") else "тип")
        for н in ast.walk(ast.parse(слоти.read_text(encoding="utf-8"))):
            if isinstance(н, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "КЛЮЧІ" for t in н.targets) \
                    and isinstance(н.value, ast.Dict):
                for з in н.value.values:
                    с = рядок_літерал(з)
                    if с:
                        коди.setdefault(с, "слот")
    return коди


def основи_матеріалів(корінь):
    """Перші 4 літери українських слів матеріалу й тканини з ТАБЛИЦІ реєстру: за ними пізнаємо перелік слів складу."""
    мова = корінь / "джерела" / "внутрішня_мова.py"
    основи = set()
    if not мова.exists():
        return основи
    for н in ast.parse(мова.read_text(encoding="utf-8")).body:
        if isinstance(н, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "ТАБЛИЦЯ" for t in н.targets) \
                and isinstance(н.value, ast.Dict):
            for к, з in zip(н.value.keys, н.value.values):
                if рядок_літерал(к) in ("material", "fabric") and isinstance(з, ast.Dict):
                    for в in з.values:
                        слово = рядок_літерал(в)
                        if слово and слово_кир(слово) and len(слово) >= 4:
                            основи.add(слово.lower()[:4])
    return основи


# ── Читачі слів (листки) ─────────────────────────────────────────────────────────────────────────────────────────
class Листок:
    """Місце, де код читає слова: словник/регекс (визначення) чи слівна перевірка (на місці)."""

    def __init__(self, модуль, рядок, вид, ім=None, слів=0, кодових_значень=0, вузол=None):
        self.модуль, self.рядок, self.вид, self.ім = модуль, рядок, вид, ім
        self.слів, self.вузол = слів, вузол
        self.кодових_значень, self.поля_кодів = кодових_значень if isinstance(кодових_значень, tuple) else (
            кодових_значень, frozenset())
        self.на_місці = ім is None
        self.слова_текст = []


def слів_у_вузлі(в, глибина=0):
    """Кириличні слова-елементи у літералі колекції; для dict — у ключах і у вкладених колекціях (до трьох рівнів)."""
    слова = []
    if глибина > 3:
        return слова
    if isinstance(в, ast.Dict):
        for к, з in zip(в.keys, в.values):
            if слово_кир(рядок_літерал(к)):
                слова.append(к)
            слова += слів_у_вузлі(з, глибина + 1) if isinstance(з, (ast.Tuple, ast.List, ast.Set, ast.Dict)) else []
    elif isinstance(в, (ast.Tuple, ast.List, ast.Set)):
        for e in в.elts:
            if isinstance(e, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
                слова += слів_у_вузлі(e, глибина + 1)
            elif слово_кир(рядок_літерал(e)) or латинський_візерунок(рядок_літерал(e)):
                слова.append(e)
    return слова


def кодів_у_значеннях(в, коди):
    """(скільки рядків-кодів реєстру в літералі і до яких полів вони належать): слово → код чи код → слова."""
    if not isinstance(в, (ast.Dict, ast.Tuple, ast.List, ast.Set)):
        return 0, frozenset()
    збіг = []
    for x in ast.walk(в):
        код = рядок_літерал(x)
        if код in коди:
            збіг.append(код)
    return len(збіг), frozenset(коди[к] for к in збіг)


class Функція:
    def __init__(self, модуль, вузол, клас=None):
        self.модуль, self.вузол, self.клас = модуль, вузол, клас
        self.ім = вузол.name
        self.рядок = вузол.lineno
        self.ключ = (модуль.відн, self.ім, self.рядок)


def функції_модуля(модуль):
    вих = []

    def обійти(тіло, клас):
        for н in тіло:
            if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef)):
                вих.append(Функція(модуль, н, клас))
                обійти(н.body, клас)
            elif isinstance(н, ast.ClassDef):
                обійти(н.body, н.name)
            elif isinstance(н, (ast.If, ast.Try, ast.With, ast.For, ast.While)):
                for ч in ("body", "orelse", "finalbody"):
                    обійти(getattr(н, ч, []) or [], клас)
                for о in getattr(н, "handlers", []) or []:
                    обійти(о.body, клас)
    обійти(модуль.дерево.body, None)
    return вих


def власні_вузли(ф):
    """Вузли тіла функції без вкладених функцій (вони окремі)."""
    стек = list(ф.вузол.body)
    while стек:
        н = стек.pop()
        yield н
        for д in ast.iter_child_nodes(н):
            if isinstance(д, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)) and д is not ф.вузол:
                if isinstance(д, ast.Lambda):
                    стек.append(д)
                continue
            стек.append(д)


def знайти_листки(модулі, коди):
    """Усі визначення словників, регексів і слівні перевірки на місці. Повертає (іменовані, листки на місці);
    іменований — (ім'я, листок, функція-область або None для модуля й класу)."""
    іменовані = []
    на_місці = []
    for м in модулі:
        # визначення module/class-level і в тілі функцій: Name = <літерал колекції | re.compile(...)>
        for н in ast.walk(м.дерево):
            if not isinstance(н, (ast.Assign, ast.AnnAssign)):
                continue
            значення = н.value
            цілі = н.targets if isinstance(н, ast.Assign) else [н.target]
            імена = [t.id for t in цілі if isinstance(t, ast.Name)]
            імена += [t.attr for t in цілі if isinstance(t, ast.Attribute)]
            if not імена or значення is None:
                continue
            лист = None
            if isinstance(значення, (ast.Dict, ast.Tuple, ast.List, ast.Set)):
                слова = слів_у_вузлі(значення)
                if len(слова) >= 3:
                    лист = Листок(м, н.lineno, "словник", імена[0], len(слова), кодів_у_значеннях(значення, коди))
                    лист.слова_текст = [рядок_літерал(w) or "" for w in слова]
            elif isinstance(значення, ast.Call) and ім_виклику(значення) in ("frozenset", "set", "tuple", "list",
                                                                             "dict") and значення.args:
                слова = слів_у_вузлі(значення.args[0])
                if len(слова) >= 3:
                    лист = Листок(м, н.lineno, "словник", імена[0], len(слова), 0)
                    лист.слова_текст = [рядок_літерал(w) or "" for w in слова]
            elif isinstance(значення, ast.Call) and ім_виклику(значення) == "compile" and значення.args:
                візерунок = текст_візерунка(значення.args[0], м)
                if візерунок and візерунок_має_слова(візерунок):
                    лист = Листок(м, н.lineno, "регекс", імена[0], len(СЛОВО_КИР.findall(візерунок)))
            elif isinstance(значення, (ast.Constant, ast.JoinedStr, ast.BinOp)):
                візерунок = текст_візерунка(значення, м)
                if візерунок and візерунок_має_слова(візерунок) and re.search(r"[|\\()\[\]?*+]", візерунок) and len(
                        візерунок) > 12:
                    лист = Листок(м, н.lineno, "візерунок", імена[0], len(СЛОВО_КИР.findall(візерунок)))
            if лист:
                область = н
                while область is not None and not isinstance(область, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    область = getattr(область, "_п", None)
                for ім in імена:
                    іменовані.append((ім, лист, область))
    # слівні перевірки на місці: регекс-виклик із літералом, `"слово" in x`, startswith("слово")
    for м in модулі:
        for н in ast.walk(м.дерево):
            if isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and isinstance(н.func.value, ast.Name) \
                    and н.func.value.id == "re" and н.func.attr in МЕТОДИ_РЕГЕКСУ | {"compile"} and н.args:
                візерунок = текст_візерунка(н.args[0], м)
                if візерунок and візерунок_має_слова(візерунок) and not (
                        н.func.attr == "compile" and ЗНИЗУ_Є_ПРИСВОЄННЯ(м, н)):
                    на_місці.append(Листок(м, н.lineno, "регекс на місці", None,
                                           len(СЛОВО_КИР.findall(візерунок)), 0, н))
            elif isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr in МЕТОДИ_РЯДКА and н.args:
                a = н.args[0]
                варіанти = a.elts if isinstance(a, ast.Tuple) else [a]
                if any(слово_кир(рядок_літерал(в)) and " " not in (рядок_літерал(в) or "") for в in варіанти):
                    на_місці.append(Листок(м, н.lineno, "префікс/підрядок", None, 1, 0, н))
            elif isinstance(н, ast.Compare) and any(isinstance(o, (ast.In, ast.NotIn)) for o in н.ops):
                ліве = н.left
                с = рядок_літерал(ліве)
                if с and слово_кир(с) and " " not in с and any(
                        not isinstance(к, (ast.Dict, ast.Set, ast.Tuple, ast.List)) for к in н.comparators):
                    на_місці.append(Листок(м, н.lineno, "слово в тексті", None, 1, 0, н))
                for к in н.comparators:
                    if isinstance(к, (ast.Tuple, ast.List, ast.Set)) and len(слів_у_вузлі(к)) >= 1 and not isinstance(
                            ліве, ast.Constant):
                        # `x in ("слово", ...)` — ключ зі слів, що ним порівнюють
                        на_місці.append(Листок(м, н.lineno, "слово у переліку", None, len(слів_у_вузлі(к)), 0, н))
    return іменовані, на_місці


def ЗНИЗУ_Є_ПРИСВОЄННЯ(модуль, виклик):
    """`re.compile` як значення присвоєння вже врахований як визначення — на місці його не дублюємо."""
    for н in ast.walk(модуль.дерево):
        if isinstance(н, (ast.Assign, ast.AnnAssign)) and getattr(н, "value", None) is виклик:
            return True
    return False


def текст_візерунка(вузол, модуль):
    """Літерал або склеєний літерал → текст; ім'я → не розв'язуємо (його визначення враховане окремо)."""
    if isinstance(вузол, ast.Constant) and isinstance(вузол.value, str):
        return вузол.value
    if isinstance(вузол, ast.JoinedStr):
        return "".join(ч.value for ч in вузол.values if isinstance(ч, ast.Constant) and isinstance(ч.value, str))
    if isinstance(вузол, ast.BinOp) and isinstance(вузол.op, ast.Add):
        л, п = текст_візерунка(вузол.left, модуль), текст_візерунка(вузол.right, модуль)
        return (л or "") + (п or "") or None
    return None


def імпорти_модуля(модуль):
    """{"імена": {локальне: (модуль, оригінальне)}, "модулі": {псевдонім: модуль}} для `import`/`from … import`."""
    імена, модулі = {}, {}
    for н in ast.walk(модуль.дерево):
        if isinstance(н, ast.ImportFrom) and н.module:
            for а in н.names:
                імена[а.asname or а.name] = (н.module.split(".")[-1], а.name)
                модулі[а.asname or а.name] = а.name if False else модулі.get(а.asname or а.name, "")
        elif isinstance(н, ast.Import):
            for а in н.names:
                модулі[а.asname or а.name.split(".")[0]] = а.name.split(".")[-1]
    return {"імена": імена, "модулі": {к: v for к, v in модулі.items() if v}}


# ── Аналіз функцій: потік слів до кодів ─────────────────────────────────────────────────────────────────────────
def поставити_батьків(дерево):
    for н in ast.walk(дерево):
        for д in ast.iter_child_nodes(н):
            д._п = н


class Аналіз:
    def __init__(self, корінь):
        self.корінь = корінь
        файли = зібрати_файли(корінь)
        self.модулі, self.помилки = прочитати_модулі(корінь, файли)
        self.коди = коди_реєстру(корінь)
        self.коди_лат = {к: п for к, п in self.коди.items() if КОД_ЛАТ.match(к)}
        КОДИ_ЛАТ_ГЛОБ.update(self.коди_лат)
        for м in self.модулі:
            поставити_батьків(м.дерево)
        self.функції = [ф for м in self.модулі for ф in функції_модуля(м)]
        self.за_ім = defaultdict(list)
        for ф in self.функції:
            self.за_ім[ф.ім].append(ф)
        модулі_слів = [м for м in self.модулі if not м.реєстр]
        іменовані, self.листки_на_місці = знайти_листки(модулі_слів, self.коди)
        self.листки_модуля, self.листки_локальні = defaultdict(list), defaultdict(list)
        self.усі_іменовані = []
        for ім, л, обл in іменовані:
            (self.листки_модуля[(л.модуль.відн, ім)] if обл is None else self.листки_локальні[(id(обл), ім)]).append(л)
            self.усі_іменовані.append(л)
        self.вузол_листка = {id(л.вузол): л for л in self.листки_на_місці if л.вузол is not None}
        self.імпорти = {м.відн: імпорти_модуля(м) for м in self.модулі}
        self.модуль_за_назвою = {Path(м.відн).stem: м.відн for м in self.модулі}
        self.псевдоніми()
        self.власні = {ф.ключ: list(власні_вузли(ф)) for ф in self.функції}
        self.статика = {ф.ключ: self.статично(ф) for ф in self.функції}
        self.присвоєння = {ф.ключ: self.присвоєння_функції(ф) for ф in self.функції}
        self.текстові = {}
        self.функція_за_ключем = {ф.ключ: ф for ф in self.функції}

    # ---- посилання на словники й регекси ----
    def листки_імені(self, модуль, ф, ім):
        """Листки, на які посилається просте ім'я: локальний, модульний або імпортований за `from M import X`."""
        знайдено = []
        if ф is not None:
            знайдено += self.листки_локальні.get((id(ф.вузол), ім), [])
        знайдено += self.листки_модуля.get((модуль.відн, ім), [])
        імп = self.імпорти[модуль.відн]["імена"].get(ім)
        if імп:
            відн = self.модуль_за_назвою.get(імп[0])
            if відн:
                знайдено += self.листки_модуля.get((відн, імп[1]), [])
        return знайдено

    def листки_атрибута(self, модуль, вузол):
        """`M.X` для імпортованого модуля M; `self.X`/`cls.X` — клас того самого модуля."""
        база = вузол.value
        if not isinstance(база, ast.Name):
            return []
        if база.id in ("self", "cls"):
            return self.листки_модуля.get((модуль.відн, вузол.attr), [])
        назва = self.імпорти[модуль.відн]["модулі"].get(база.id)
        відн = self.модуль_за_назвою.get(назва) if назва else None
        return self.листки_модуля.get((відн, вузол.attr), []) if відн else []

    def листки_вузла(self, модуль, ф, н):
        if isinstance(н, ast.Name):
            return self.листки_імені(модуль, ф, н.id)
        if isinstance(н, ast.Attribute):
            return self.листки_атрибута(модуль, н)
        return []

    def псевдоніми(self):
        """Ім'я верхнього рівня (модуль, клас), присвоєне виразом із ім'ям словника без викликів чужих функцій, — теж
        словник (похідні таблиці). Локальні змінні псевдонімів не дають: вони б заражали кожну однойменну змінну."""
        дозволені = {"dict", "set", "frozenset", "tuple", "list", "sorted", "items", "values", "keys", "reversed",
                     "enumerate", "zip", "len", "compile", "lower", "join", "map", "filter", "sum", "min", "max"}
        присвоєння = []
        for м in self.модулі:
            if м.реєстр:
                continue
            стек = list(м.дерево.body)
            while стек:
                н = стек.pop()
                if isinstance(н, ast.ClassDef):
                    стек += list(н.body)
                elif isinstance(н, ast.Assign) and not isinstance(н.value, ast.Constant):
                    цілі = [t.id for t in н.targets if isinstance(t, ast.Name)]
                    if цілі and not [в for в in ast.walk(н.value) if isinstance(в, ast.Call) and
                                     ім_виклику(в) not in дозволені]:
                        присвоєння.append((м, цілі, [x for x in ast.walk(н.value)
                                                     if isinstance(x, (ast.Name, ast.Attribute))]))
        змінилось = True
        кроків = 0
        while змінилось and кроків < 8:
            змінилось = False
            кроків += 1
            for м, цілі, вузли in присвоєння:
                посилання = [л for x in вузли for л in self.листки_вузла(м, None, x)]
                if not посилання:
                    continue
                for ц in цілі:
                    для_ц = self.листки_модуля[(м.відн, ц)]
                    for л in посилання:
                        if л not in для_ц:
                            для_ц.append(л)
                            змінилось = True

    # ---- статика функції ----
    def статично(self, ф):
        """Те, що не залежить від потоку: де функція читає листки, кого викликає, що пише в ключі полів."""
        читає, виклики, записи = [], [], []
        for н in self.власні[ф.ключ]:
            for л in self.листки_вузла(ф.модуль, ф, н):
                читає.append((л, н.lineno))
            if id(н) in self.вузол_листка:
                читає.append((self.вузол_листка[id(н)], н.lineno))
            if isinstance(н, ast.Call):
                ім = ім_виклику(н)
                if ім:
                    виклики.append((ім, н.lineno, н))
            записи += записи_поля(н)
        return {"читає": читає, "виклики": виклики, "записи_сирі": записи,
                "імена_викликів": {в[0] for в in виклики}}

    def присвоєння_функції(self, ф):
        """{змінна: [вирази, якими її заповнюють]} — присвоєння, цикли, записи `d[k] = …`, `d.attr = …`."""
        д = defaultdict(list)

        def цілі(т):
            for x in ast.walk(т):
                if isinstance(x, ast.Name):
                    yield x.id
        for н in self.власні[ф.ключ]:
            if isinstance(н, ast.Assign):
                for т in н.targets:
                    for ім in цілі(т):
                        д[ім].append(н.value)
            elif isinstance(н, (ast.AnnAssign, ast.AugAssign)) and н.value is not None:
                for ім in цілі(н.target):
                    д[ім].append(н.value)
            elif isinstance(н, (ast.For, ast.comprehension)):
                for ім in цілі(н.target):
                    д[ім].append(н.iter)
            elif isinstance(н, ast.NamedExpr):
                for ім in цілі(н.target):
                    д[ім].append(н.value)
        return д

    def текстова(self, ф):
        """Функція оперує текстом товару: параметр чи ключ із переліку (назва, опис, категорія, слаг, url…)."""
        ключ = ф.ключ
        if ключ not in self.текстові:
            аргс = ф.вузол.args
            імена = [а.arg for а in аргс.args + аргс.kwonlyargs + аргс.posonlyargs]
            так = bool(set(імена) & ТЕКСТ_ПАРАМЕТРИ)
            if not так:
                for н in self.власні[ключ]:
                    к = ключ_у_підписі(н)
                    if к in ТЕКСТ_КЛЮЧІ:
                        так = True
                        break
            self.текстові[ключ] = так
        return self.текстові[ключ]

    # ---- залежності значення від слів ----
    def залежності(self, вираз, ф, спуск, глибина, відвідані):
        """{(id листка, ключ функції-читача)}: від яких слівних джерел залежить значення виразу.

        Аргументи проєктної функції слова далі не несуть: код (чи слово) виходить із її повернення. Тому виклик
        `довжина(слот(о))` не робить слова слота джерелом довжини. `спуск` — чи йти в повернення викликаних функцій
        (шлях А); без нього (шлях Б) значення лишається в межах однієї функції."""
        вих = set()
        стек = [вираз]
        while стек:
            н = стек.pop()
            if id(н) in self.вузол_листка:
                вих.add((id(self.вузол_листка[id(н)]), ф.ключ))
            if isinstance(н, (ast.Name, ast.Attribute)):
                for л in self.листки_вузла(ф.модуль, ф, н):
                    вих.add((id(л), ф.ключ))
            if isinstance(н, ast.Name):
                ключ = (ф.ключ, н.id)
                if ключ not in відвідані:
                    відвідані.add(ключ)
                    for р in self.присвоєння[ф.ключ].get(н.id, ()):
                        стек.append(р)
                continue
            if isinstance(н, ast.Call):
                ім = ім_виклику(н)
                проєктна = bool(ім) and ім not in ЗАГАЛЬНІ and 0 < len(self.за_ім.get(ім, ())) <= 3
                if проєктна:
                    if спуск and глибина > 0:
                        for г in self.за_ім[ім]:
                            вих |= self.з_повернень(г, глибина - 1, відвідані)
                    if isinstance(н.func, ast.Attribute):
                        стек.append(н.func.value)
                    continue
                стек.append(н.func)
                стек += list(н.args) + [к.value for к in н.keywords]
                continue
            стек += list(ast.iter_child_nodes(н))
        return вих

    def з_повернень(self, г, глибина, відвідані):
        """Залежності всіх повернень функції; умови — лише коли повертається код реєстру (неявний потік)."""
        ключ = ("ф", г.ключ)
        if ключ in відвідані:
            return set()
        відвідані.add(ключ)
        вих = set()
        for н in self.власні[г.ключ]:
            if isinstance(н, ast.Return) and н.value is not None:
                вих |= self.залежності(н.value, г, True, глибина, відвідані)
                if self.код_реєстру(н.value, ВИВОДНИК.search(г.ім)):
                    for у in охоронці(н):
                        вих |= self.залежності(у, г, True, глибина, відвідані)
        return вих

    def код_реєстру(self, вираз, виводник=False, ключ=None):
        """Поле коду реєстру, якщо вираз — літерал-код (чи тернарний/кортеж із такими); інакше None."""
        for с in ast.walk(вираз):
            код = рядок_літерал(с)
            if not код:
                continue
            if код in self.коди_лат:
                return self.коди_лат[код]
            if код in self.коди and (виводник or ключ in КЛЮЧ_ПОЛЯ):
                return self.коди[код]
        return None


def записи_поля(н):
    """Усі записи в ключ поля на цьому вузлі: (поле, ключ, значення, рядок)."""
    вих = []
    if isinstance(н, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
        цілі = н.targets if isinstance(н, ast.Assign) else [н.target]
        for т in цілі:
            ключ = None
            if isinstance(т, ast.Subscript):
                ключ = рядок_літерал(т.slice)
            elif isinstance(т, ast.Attribute):
                ключ = т.attr
            if ключ in КЛЮЧ_ПОЛЯ and getattr(н, "value", None) is not None:
                вих.append((КЛЮЧ_ПОЛЯ[ключ], ключ, н.value, н.lineno))
    elif isinstance(н, ast.Dict):
        for к, з in zip(н.keys, н.values):
            ключ = рядок_літерал(к)
            if ключ in КЛЮЧ_ПОЛЯ and з is not None:
                вих.append((КЛЮЧ_ПОЛЯ[ключ], ключ, з, getattr(к, "lineno", н.lineno)))
    elif isinstance(н, ast.Call):
        ім = ім_виклику(н)
        if ім == "dict":
            for кв in н.keywords:
                if кв.arg in КЛЮЧ_ПОЛЯ:
                    вих.append((КЛЮЧ_ПОЛЯ[кв.arg], кв.arg, кв.value, н.lineno))
        if ім == "setdefault" and len(н.args) >= 2 and рядок_літерал(н.args[0]) in КЛЮЧ_ПОЛЯ:
            ключ = рядок_літерал(н.args[0])
            вих.append((КЛЮЧ_ПОЛЯ[ключ], ключ, н.args[1], н.lineno))
    return вих


# ── Поле, яке виводить функція за її іменем ──────────────────────────────────────────────────────────────────────
ІМ_ДО_ПОЛЯ = (("слот", "слот"), ("комплект", "комплект"), ("набір", "комплект"), ("крій", "крій"),
              ("довжин", "довжина"), ("рід", "рід"), ("тканин", "склад"), ("склад", "склад"), ("матеріал", "склад"),
              ("тип", "тип"), ("вид", "тип"), ("предмет", "тип"), ("іменник", "тип"), ("модифікатор", "тип"))


def поле_за_іменем(ім):
    чисте = ім.lstrip("_")
    for корінь, поле in ІМ_ДО_ПОЛЯ:
        if чисте.startswith(корінь) or ("_" + корінь) in чисте:
            return поле
    return "тип"


# ── Місця ────────────────────────────────────────────────────────────────────────────────────────────────────────
class Місця:
    def __init__(self):
        self.дані = defaultdict(dict)       # (файл, рядок) → {пункт: (чому, {шляхи})}

    def додати(self, модуль, рядок, пункт, чому, шлях):
        слот = self.дані[(модуль.відн, рядок)]
        if пункт in слот:
            слот[пункт][1].add(шлях)
            if чому < слот[пункт][0]:            # однаковий вивід за будь-якого порядку обходу
                слот[пункт][0] = чому
        else:
            слот[пункт] = [чому, {шлях}]

    def пункти(self):
        лічба = defaultdict(int)
        for ключ, за_пунктами in self.дані.items():
            for п in за_пунктами:
                лічба[п] += 1
        return лічба


def текстове(поля):
    return bool(поля) and set(поля) <= set(ТЕКСТОВІ_ПОЛЯ)


def охоронці(вузол):
    """Вирази умов, під якими стоїть вузол."""
    вих = []
    п = getattr(вузол, "_п", None)
    попередній = вузол
    while п is not None and not isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
        if isinstance(п, (ast.If, ast.While, ast.IfExp)) and попередній is not п.test:
            вих.append(п.test)
        elif isinstance(п, ast.comprehension) and попередній is not п.iter:
            вих += list(п.ifs)
        elif isinstance(п, ast.For) and попередній is not п.iter:
            вих.append(п.iter)
        попередній, п = п, getattr(п, "_п", None)
    return вих


def корені_полів(ан, ф):
    """Записувачі полів у функції: (поле, ключ, значення-вираз, умови, рядок). Умови враховуються для коду-літерала."""
    вих = []
    for н in ан.власні[ф.ключ]:
        for поле, ключ, значення, рядок in записи_поля(н):
            вих.append((поле, ключ, значення, охоронці(н), рядок))
    return вих


def шлях_б(ан):
    """Б: від читачів слів уперед за потоком значення, у межах функції, до коду реєстру чи ключа поля."""
    пари = set()                    # (id листка, ключ читача, поле, причина)
    поля_функції = defaultdict(set)
    for ф in ан.функції:
        ст = ан.статика[ф.ключ]
        if not ст["читає"] or not ан.текстова(ф):
            continue
        # (iii) запис у ключ поля значенням, що походить зі слів цієї функції
        for поле, ключ, значення, умови, рядок in корені_полів(ан, ф):
            залежні = ан.залежності(значення, ф, False, 0, set())
            if ан.код_реєстру(значення, False, ключ):
                for у in умови:                                   # (i) код за умовою зі словом
                    залежні |= ан.залежності(у, ф, False, 0, set())
            for лід, читач in залежні:
                пари.add((лід, читач, поле, f"запис у `{ключ}`"))
        for н in ан.власні[ф.ключ]:
            if isinstance(н, ast.Return) and н.value is not None:
                # (i) код реєстру, що повертається за умовою зі словом
                поле_коду = ан.код_реєстру(н.value, bool(ВИВОДНИК.search(ф.ім)))
                if поле_коду:
                    for у in охоронці(н):
                        for лід, читач in ан.залежності(у, ф, False, 0, set()):
                            пари.add((лід, читач, поле_коду, f"повертає код `{поле_коду}` за словом"))
                # (iv) виводник за іменем повертає значення, що походить зі слів
                if ВИВОДНИК.search(ф.ім):
                    for лід, читач in ан.залежності(н.value, ф, False, 0, set()):
                        пари.add((лід, читач, поле_за_іменем(ф.ім), "виводник за іменем"))
        # (ii) словник слово → код (чи код → слова) реєстру: хто його читає, виводить поле з кодів
        for лист, рядок in ст["читає"]:
            if лист.кодових_значень >= 3 and not лист.на_місці:
                for поле in лист.поля_кодів:
                    пари.add((id(лист), ф.ключ, поле, f"читає словник слово → код `{лист.ім}`"))
    for _, читач, поле, _ in пари:
        поля_функції[читач].add(поле)
    return пари, поля_функції


def шлях_а(ан):
    """А: від записувачів полів (записи в ключ поля, повернення виводників) зворотним зрізом, зі спуском у повернення
    викликаних функцій, до читачів слів."""
    вих = set()
    функції = {ф.ключ: ф for ф in ан.функції}
    for ф in ан.функції:
        for поле, ключ, значення, умови, рядок in корені_полів(ан, ф):
            залежні = ан.залежності(значення, ф, True, 4, set())
            if ан.код_реєстру(значення, False, ключ):
                for у in умови:
                    залежні |= ан.залежності(у, ф, True, 4, set())
            for лід, читач in залежні:
                if ан.текстова(функції[читач]):
                    вих.add((лід, читач, поле, f"запис у `{ключ}`"))
        if ВИВОДНИК.search(ф.ім):
            for лід, читач in ан.з_повернень(ф, 4, set()):
                if ан.текстова(функції[читач]):
                    вих.add((лід, читач, поле_за_іменем(ф.ім), "виводник за іменем"))
    return вих


# ── Пункти 2, 3, 4 ───────────────────────────────────────────────────────────────────────────────────────────────
def власні_переліки(ан, місця):
    """П.2 (клас 11335): місце — код поля, якого нема в реєстрі, або свій перелік/словник кодів поза реєстром, що
    задає групу, порядок чи властивість. Порогів нема: перелік чи словник із ≥2 кодів реєстру (латинських чи
    імен слотів) — місце; лише одне порівняння з одним кодом — читання. Вкладені й конкатеновані переліки лічаться
    кожен окремо."""
    for м in ан.модулі:
        if м.реєстр:
            continue
        for н in ast.walk(м.дерево):
            if isinstance(н, (ast.Tuple, ast.List, ast.Set)):
                ел = н.elts
            elif isinstance(н, ast.Dict):
                ел = [к for к in н.keys if к is not None] + list(н.values)
            else:
                continue
            лат = [рядок_літерал(e) for e in ел if рядок_літерал(e) in ан.коди_лат]
            укр = [рядок_літерал(e) for e in ел if рядок_літерал(e) in ан.коди and not КОД_ЛАТ.match(рядок_літерал(e) or "")]
            if len(лат) + len(укр) < 2:
                continue
            if len(лат) >= 2 or (лат and укр):
                поля = sorted({ан.коди_лат[к] for к in лат})
                місця.додати(м, н.lineno, 2, f"власний перелік {len(лат)} кодів ({'/'.join(поля)}), не з реєстру", "П")
            else:
                місця.додати(м, н.lineno, 2, f"власний перелік {len(укр)} імен слотів, не з реєстру", "П")
    # код поля запису, якого нема в реєстрі
    for ф in ан.функції:
        if ф.модуль.реєстр:
            continue
        for поле, ключ, значення, умови, рядок in корені_полів(ан, ф):
            for e in ast.walk(значення):
                код = рядок_літерал(e)
                if код and КОД_ЛАТ.match(код) and код not in ан.коди_лат and поле in ("тип", "слот") \
                        and код not in НАЗВИ_ПОЛІВ:
                    місця.додати(ф.модуль, рядок, 2, f"код `{код}` поля {поле} відсутній у реєстрі", "П")


def повторні_виводи(ан, місця):
    """П.3: виклик виводника поля з функції, що не складає запису, або другий виклик у записувачі.

    Виводник — функція з іменем виводника, з повернень якої (зі спуском) досяжні слівні джерела. Виводники, що
    кличуть виводників, — ланцюг одного виводу, а не повторний."""
    виводники = {ф.ключ for ф in ан.функції
                 if ВИВОДНИК.search(ф.ім) and not НЕ_РЕЧІ.search(ф.ім) and ан.з_повернень(ф, 4, set())}
    імена_виводників = {ан.функція_за_ключем[к].ім for к in виводники}
    записувачі = set()
    for ф in ан.функції:
        поля = {п for п, _, _, _ in ан.статика[ф.ключ]["записи_сирі"]}
        if len(поля) >= 3:
            записувачі.add(ф.ключ)
    for ф in ан.функції:
        if ф.ключ in виводники:
            continue
        бачені = defaultdict(list)
        for ім, рядок, вузол in ан.статика[ф.ключ]["виклики"]:
            if ім not in імена_виводників or ім == ф.ім:
                continue
            поле = поле_за_іменем(ім)
            if ф.ключ in записувачі:
                бачені[ім].append(рядок)
            else:
                місця.додати(ф.модуль, рядок, 3, f"`{ф.ім}` виводить {поле} удруге через `{ім}` поза записом", "П")
        for ім, рядки in бачені.items():
            for рядок in sorted(set(рядки))[1:]:
                місця.додати(ф.модуль, рядок, 3, f"запис виводить поле удруге: другий виклик `{ім}` у `{ф.ім}`", "П")
    return імена_виводників


# виводники, що не про тип/слот/склад речі: колір, метал, вологість, англомовна форма схеми, склад образу
НЕ_РЕЧІ = re.compile(r"кольору|_en$|вибору|повнота|металу|_слота$|слота_|_ранг_|інтервал_типу")
КОРІННЯ_СТОРІНКИ = {"суп", "soup", "html_текст", "html", "сторінка", "page", "дерево"}
МЕТОДИ_ЧИТАННЯ = {"get_text", "select", "select_one", "find", "find_all", "findAll", "itertext", "text"}
КЛЮЧІ_ТЕКСТУ_ПОЛЯ = (set(КЛЮЧ_ПОЛЯ) - {"крихти", "url", "URL", "посилання"}) | {"характеристики", "характеристики_сирі", "пари", "склад_джерело"}   # крихти й URL — розділ цього товару


def зліпок_dom(ан, місця):
    """П.4: JS у рядку Python (зліпок DOM жнив) збирає текст і пари для полів зі всього документа: `document.body` або
    `document.querySelectorAll` з `rows.push` у цьому ж чи двох наступних рядках."""
    for м in ан.модулі:
        for н in ast.walk(м.дерево):
            if not (isinstance(н, ast.Constant) and isinstance(н.value, str) and "document." in н.value):
                continue
            рядки = н.value.split("\n")
            for i, р in enumerate(рядки):
                вікно = " ".join(рядки[i:i + 3])
                if "document.body" in р:
                    місця.додати(м, н.lineno + i, 4, "зліпок DOM: текст поля з `document.body`, не з вузла товару", "П")
                elif "document.querySelectorAll" in р and "rows.push" in вікно:
                    місця.додати(м, н.lineno + i, 4, "зліпок DOM: пари поля з усього документа, не з вузла товару", "П")


def поза_блоком(ан, місця):
    """П.4: текст поля зі всієї сторінки (корінь розбору), а не з вузла товару."""
    зліпок_dom(ан, місця)
    for ф in ан.функції:
        читання = {}                                         # змінна → (рядок, метод) читання кореня сторінки
        вузли = ан.власні[ф.ключ]
        for н in вузли:
            if isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr in МЕТОДИ_ЧИТАННЯ:
                база = н.func.value
                while isinstance(база, ast.Attribute):
                    база = база.value
                якір = рядок_літерал(н.args[0]) if н.args else None
                if isinstance(база, ast.Name) and база.id in КОРІННЯ_СТОРІНКИ and якір not in ("h1", "title", "head") \
                        and "crumb" not in (якір or "") and "breadcrumb" not in (якір or ""):
                    читання[id(н)] = (н.lineno, база.id + "." + н.func.attr)
        if not читання:
            continue
        змінні = defaultdict(list)                           # змінна → читання, що її живлять
        for _ in range(5):
            for н in вузли:
                if isinstance(н, (ast.Assign, ast.AnnAssign)) and н.value is not None:
                    знайдено = [читання[id(x)] for x in ast.walk(н.value) if id(x) in читання]
                    знайдено += [r for x in ast.walk(н.value) if isinstance(x, ast.Name) for r in змінні.get(x.id, [])]
                    if знайдено:
                        for т in (н.targets if isinstance(н, ast.Assign) else [н.target]):
                            імена_цілі = [т] if isinstance(т, ast.Name) else (
                                [x for x in т.elts if isinstance(x, ast.Name)] if isinstance(т, ast.Tuple) else [])
                            for x in імена_цілі:
                                for r in знайдено:
                                    if r not in змінні[x.id]:
                                        змінні[x.id].append(r)
                elif isinstance(н, (ast.For, ast.comprehension)):
                    знайдено = [читання[id(x)] for x in ast.walk(н.iter) if id(x) in читання]
                    знайдено += [r for x in ast.walk(н.iter) if isinstance(x, ast.Name) for r in змінні.get(x.id, [])]
                    for x in ast.walk(н.target):
                        if isinstance(x, ast.Name):
                            for r in знайдено:
                                if r not in змінні[x.id]:
                                    змінні[x.id].append(r)
        for н in вузли:
            for ключ, значення, рядок in записи_будь_який_ключ(н):
                if ключ not in КЛЮЧІ_ТЕКСТУ_ПОЛЯ or значення is None:
                    continue
                джерела = [читання[id(x)] for x in ast.walk(значення) if id(x) in читання]
                джерела += [r for x in ast.walk(значення) if isinstance(x, ast.Name) for r in змінні.get(x.id, [])]
                for r_рядок, чим in джерела:
                    місця.додати(ф.модуль, r_рядок, 4, f"`{ключ}` бере текст із кореня сторінки `{чим}`, не з вузла товару", "П")


def записи_будь_який_ключ(н):
    вих = []
    if isinstance(н, (ast.Assign, ast.AnnAssign)):
        for т in (н.targets if isinstance(н, ast.Assign) else [н.target]):
            if isinstance(т, ast.Subscript) and рядок_літерал(т.slice) and getattr(н, "value", None) is not None:
                вих.append((рядок_літерал(т.slice), н.value, н.lineno))
    elif isinstance(н, ast.Dict):
        for к, з in zip(н.keys, н.values):
            if рядок_літерал(к) and з is not None:
                вих.append((рядок_літерал(к), з, getattr(к, "lineno", н.lineno)))
    elif isinstance(н, ast.Call):
        for кв in н.keywords:
            if кв.arg:
                вих.append((кв.arg, кв.value, н.lineno))
    return вих


# ── JS: слівні читачі коду поля та словники слово → код ──────────────────────────────────────────────────────────
JS_ТЕКИ = ("джерела",)
JS_ВИКЛЮЧЕНІ = re.compile(r"^(?:тест_|test_|worker\.js$|проби|node_modules)")
JS_ПОЛЕ = re.compile(r"item_type|\bslot\b|\.слот\b|['\"]слот['\"]|\.тип\b|['\"]тип['\"]|тип_речі|\bкрій\b|\bкомплект\b")
JS_СЛОВО = re.compile(r"/[^/\n*][^/\n]*?[" + КИРИЛИЦЯ + r"]{3,}[^/\n]*?/[gimsuy]*|"
                      r"\.(?:includes|indexOf|startsWith|endsWith|match|test|search)\(\s*['\"`][^'\"`\n]*["
                      + КИРИЛИЦЯ + r"]{3,}")
JS_СЛОВНИК = re.compile(r"['\"]([" + КИРИЛИЦЯ + r"_ -]{3,})['\"]\s*:\s*['\"]([a-z][a-z0-9_]*)['\"]")


def прибрати_коментарі_js(текст):
    текст = re.sub(r"/\*.*?\*/", lambda м: re.sub(r"[^\n]", " ", м.group(0)), текст, flags=re.S)
    return re.sub(r"(?<![:'\"\\])//[^\n]*", "", текст)


def js_місця(корінь, ан, місця):
    знайдено = 0
    for тека in JS_ТЕКИ:
        for дір, піддіри, імена in os.walk(корінь / тека):
            піддіри[:] = sorted(д for д in піддіри if д not in ВИКЛЮЧЕНІ_ТЕКИ and д != "node_modules")
            for ім in sorted(імена):
                if not ім.endswith(".js") or JS_ВИКЛЮЧЕНІ.match(ім):
                    continue
                ш = Path(дір) / ім
                відн = ш.relative_to(корінь).as_posix()
                м = Модуль(ш, відн, None, [])
                рядки = прибрати_коментарі_js(ш.read_text(encoding="utf-8")).split("\n")
                словник = [(i + 1, x.group(1), x.group(2)) for i, л in enumerate(рядки) for x in JS_СЛОВНИК.finditer(л)
                           if x.group(2) in ан.коди_лат]
                if len(словник) >= 3:
                    місця.додати(м, словник[0][0], 1, f"JS: словник {len(словник)} слів → коди реєстру", "JS")
                    місця.додати(м, словник[0][0], 2, "JS: власний словник слово → код, не з реєстру", "JS")
                    знайдено += 1
                for i, л in enumerate(рядки):
                    if JS_СЛОВО.search(л):
                        вікно = "\n".join(рядки[max(0, i - 2):i + 3])
                        коди_у_вікні = [к for к in re.findall(r"['\"]([a-z][a-z0-9_]*)['\"]", вікно) if к in ан.коди_лат]
                        if JS_ПОЛЕ.search(вікно) and коди_у_вікні:
                            місця.додати(м, i + 1, 1, "JS: слівна перевірка поруч із кодом поля", "JS")
                            знайдено += 1
    return знайдено


# ── Складання місць ──────────────────────────────────────────────────────────────────────────────────────────────
def перший_рядок(ан, ф, лист):
    рядки = sorted(р for л, р in ан.статика[ф.ключ]["читає"] if л is лист)
    return рядки[0] if рядки else None


def скласти(ан, корінь):
    місця = Місця()
    основи = основи_матеріалів(корінь)
    for лист in ан.усі_іменовані:                           # перелік слів складу й матеріалу — п.1 (рішення 11335)
        влучень = [w for w in лист.слова_текст if w and w.lower()[:4] in основи]
        if len(влучень) >= 2 and len(влучень) * 2 >= len(лист.слова_текст):
            місця.додати(лист.модуль, лист.рядок, 1,
                         f"словник `{лист.ім}`: слова складу/матеріалу ({len(влучень)} з {len(лист.слова_текст)})", "П")
    б_пари, поля_функції = шлях_б(ан)
    а_пари = шлях_а(ан)
    усі_листки = {}
    for л in ан.усі_іменовані:
        усі_листки[id(л)] = л
    for л in ан.листки_на_місці:
        усі_листки[id(л)] = л
    функції = {ф.ключ: ф for ф in ан.функції}

    # пари (листок, читач, поле) за шляхами
    пари = defaultdict(lambda: {"А": [], "Б": []})
    for лист, читач, поле, чому in а_пари:
        пари[(лист, читач, поле)]["А"].append(чому)
    for лист, читач, поле, чому in б_пари:
        пари[(лист, читач, поле)]["Б"].append(чому)

    код_пари = {}
    текст_пари = {}
    for (лист, читач, поле), шляхи in пари.items():
        if ЧИТАЧ_ПОЗА.search(функції[читач].ім):
            continue                                    # колір і мотив — не поля класу
        if поле in ТЕКСТОВІ_ПОЛЯ and not ЧИСТІЙ_ТЕКСТ.search(функції[читач].ім):
            текст_пари[(лист, читач, поле)] = шляхи
        else:
            код_пари[(лист, читач, поле)] = шляхи   # чистка тексту поля — теж п.1 (рішення 11335)

    читачі_листка = defaultdict(lambda: defaultdict(set))       # листок → читач → шляхи
    поля_листка = defaultdict(set)
    for (лист, читач, поле), шляхи in код_пари.items():
        for ш, чом in шляхи.items():
            if чом:
                читачі_листка[лист][читач].add(ш)
        поля_листка[лист].add(поле)

    # поза класом: схема палітри, теги YML-складальника (запис байтів), колір — корені Річ-колір-*
    поза_класом = {"СХЕМА", "ТЕГИ", "ПОЛЯ_ПАСПОРТА", "ВЕЧІРНІ_МІСЦЯ", "РЕЄСТРИ"}      # + сім'ї кольору (СІМ_Ї) за іменем нижче
    for лист_ід, читачі in читачі_листка.items():
        лист = усі_листки[лист_ід]
        if лист.ім in поза_класом or "СІМ_Ї" in (лист.ім or "") or КОЛІРНИЙ_МОДУЛЬ.search(лист.модуль.відн):
            continue
        поля = "/".join(sorted(поля_листка[лист_ід]))
        шляхи_листка = set().union(*читачі.values())
        шл = "".join(sorted(шляхи_листка))
        if лист.на_місці:
            місця.додати(лист.модуль, лист.рядок, 1, f"{лист.вид}: слова → поле {поля}", шл)
            continue
        імена_читачів = sorted({функції[к].ім for к in читачі})
        місця.додати(лист.модуль, лист.рядок, 1,
                     f"{лист.вид} `{лист.ім}` ({лист.слів} слів) → поле {поля}; читачі: {', '.join(імена_читачів[:4])}"
                     + ("…" if len(імена_читачів) > 4 else ""), шл)
        for ключ, шл_читача in читачі.items():
            ф = функції[ключ]
            рядок = перший_рядок(ан, ф, лист)
            if рядок:
                місця.додати(ф.модуль, рядок, 1, f"`{ф.ім}` читає {лист.вид} `{лист.ім}` → поле {поля}",
                             "".join(sorted(шл_читача)))
        if лист.кодових_значень >= 3:
            місця.додати(лист.модуль, лист.рядок, 2,
                         f"власний словник слово → код: {лист.кодових_значень} кодів реєстру в значеннях", "Б")

    власні_переліки(ан, місця)
    виводники = повторні_виводи(ан, місця)
    поза_блоком(ан, місця)
    js = js_місця(корінь, ан, місця)
    return місця, код_пари, текст_пари, усі_листки, функції, виводники, js


def розбіжність_шляхів(код_пари, усі_листки, функції):
    тільки_а, тільки_б, обидва = [], [], 0
    for (лист, читач, поле), шляхи in sorted(код_пари.items(), key=lambda x: str(x[0])):
        є_а, є_б = bool(шляхи["А"]), bool(шляхи["Б"])
        if є_а and є_б:
            обидва += 1
        elif є_а:
            тільки_а.append((лист, читач, поле, шляхи["А"][0]))
        else:
            тільки_б.append((лист, читач, поле, шляхи["Б"][0]))
    return обидва, тільки_а, тільки_б


def назва_листка(л):
    return f"{л.модуль.відн}:{л.рядок} {л.вид}" + (f" `{л.ім}`" if л.ім else "")


def головний():
    арг = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    арг.add_argument("--корінь", default=None, help="корінь дерева репозиторію (за замовчуванням — поточна тека)")
    арг.add_argument("--тихо", action="store_true", help="лише підсумки й останній рядок `місць: N`")
    арг.add_argument("--вибірка", type=int, default=0, help="надрукувати N випадкових місць і N файлів без місць")
    арг.add_argument("--насіння", type=int, default=29)
    а = арг.parse_args()
    корінь = Path(а.корінь).resolve() if а.корінь else Path.cwd()
    if not (корінь / "джерела").is_dir():
        корінь = Path(__file__).resolve().parents[2]
    ан = Аналіз(корінь)
    місця, код_пари, текст_пари, усі_листки, функції, виводники, js = скласти(ан, корінь)
    обидва, тільки_а, тільки_б = розбіжність_шляхів(код_пари, усі_листки, функції)

    рядки_місць = []
    for (файл, рядок), за_пунктами in sorted(місця.дані.items(), key=lambda x: (x[0][0], x[0][1])):
        for пункт in sorted(за_пунктами):
            чому, шляхи = за_пунктами[пункт]
            рядки_місць.append(f"{файл}:{рядок} · п.{пункт} · {чому} [{''.join(sorted(шляхи))}]")
    лічба = місця.пункти()
    N = len(місця.дані)

    if not а.тихо:
        print(f"# обсяг: Python-файлів {len(ан.модулі)}, функцій {len(ан.функції)}, листків-словників "
              f"{len(ан.усі_іменовані)}, слівних перевірок на місці "
              f"{len(ан.листки_на_місці)}, кодів реєстру {len(ан.коди)}")
        if ан.помилки:
            print(f"# не розібрано: {ан.помилки}")
        print(f"# шляхи: А й Б разом {обидва}, лише А {len(тільки_а)}, лише Б {len(тільки_б)} (пари листок × читач, коди)")
        for назва, список in (("лише А", тільки_а), ("лише Б", тільки_б)):
            for лист, читач, поле, чому in список[:60]:
                print(f"#   {назва}: {назва_листка(усі_листки[лист])} ← `{функції[читач].ім}`"
                      f" ({функції[читач].модуль.відн}:{функції[читач].рядок}) · {поле} · {чому}")
        текстові = sorted({(усі_листки[л].модуль.відн, усі_листки[л].рядок, п) for (л, ч, п) in текст_пари})
        print(f"# поза пунктами (слова чистять текст назви й опису, коду не виводять): {len(текстові)} листків")
        for ф, р, п in текстові[:80]:
            print(f"#   {ф}:{р} · {п}")
        for р in рядки_місць:
            print(р)
    for п in (1, 2, 3, 4):
        print(f"пункт {п}: {лічба.get(п, 0)}")
    if а.вибірка:
        import random
        ген = random.Random(а.насіння)
        ключі = sorted(місця.дані)
        print("# ВИБІРКА місць")
        for ключ in ген.sample(ключі, min(а.вибірка, len(ключі))):
            файл, рядок = ключ
            текст = (корінь / файл).read_text(encoding="utf-8").split("\n")
            print(f"## {файл}:{рядок} · {sorted(місця.дані[ключ])}")
            for i in range(max(0, рядок - 2), min(len(текст), рядок + 1)):
                print(f"   {i + 1}: {текст[i][:170]}")
        з_місцями = {ф for ф, _ in місця.дані}
        без = sorted(м.відн for м in ан.модулі if м.відн not in з_місцями)
        print("# ВИБІРКА файлів без місць")
        for ф in ген.sample(без, min(а.вибірка, len(без))):
            print(f"## {ф}")
    print(f"місць: {N}")
    return 0


if __name__ == "__main__":
    sys.exit(головний())
