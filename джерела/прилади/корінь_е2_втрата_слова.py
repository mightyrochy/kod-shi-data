# -*- coding: utf-8 -*-
"""прилади/корінь_е2_втрата_слова.py — прилад кореня Е2-втрата-слова: місця за класом паспорта
`аудит/корені/Е2-втрата-слова.md` (пункти 1–4) і рішенням менеджера 31.10 (п.5 «читач бере не те значення»,
опис каталогу — не місце, поки розбір із цитатами зупинено).

Місце — точка коду продукту (`джерела/`, `zhnyvarka/` на будь-якій глибині: Python, JS і HTML; проби, прилади, тести,
стенди й батареї — ні), де значення від неї (її слова, репліки розмови, поля паспорта з її слів чи з її екрана), від
моделі (поле відповіді) чи від крамниці (поле запису каталогу) не доходить до читача-рішення, і втрату не видно.
Прилад іде ПОТОКОМ ЗНАЧЕННЯ, а не іменами змінних: джерела — значення реєстрів коду (`паспорт_поля.ПОЛЯ_ПАСПОРТА`,
схема виходу мовного шару `мовний_шар._ПОЛЯ_EN`, описи входів мосту `ЗОВНІШНІ_ВХОДИ`, `поля_виходу` оголошень задач,
схема розбору каталогу, теги складальника жниварки), далі — присвоєння, параметри, повернення, ключі словника й межа
Python/JS. Нічого не править; переліку місць руками не має.

ПУНКТИ (кожен — механічне правило; помилка правила видна в рядку `файл:рядок · пункт · чому`):
  1  ЗРІЗ ЇЇ СЛІВ. Python — `x[a:b]` зі сталою межею (число чи ІМʼЯ_СТАЛОЇ) на значенні, що походить від її слів:
     читання ключа поля «її мовою» (`її_мовою` у `ПОЛЯ_ПАСПОРТА` і його `поле` у схемі шару, далі — ключ дроту, у який
     його переносить словник-переклад) з обʼєкта-паспорта (у тій самій функції з нього читають і інше поле паспорта
     чи шару: `g["решта"]` групи речей — не паспорт), ключа входу мосту, чий опис у `ЗОВНІШНІ_ВХОДИ` після двокрапки
     починається з її питання, слів, репліки, листа чи стрічки чату (лише в модулі, що його оголошує). Потік —
     присвоєння (ужиток вище за присвоєння слів не несе), вирази, генератори (лише елементом від заражених ітерацій),
     параметри функцій продукту й повернення: виклик несе слова, коли функція повертає їх сама чи з параметра, якому
     цей виклик дає слова; рекурсивний виклик — ні. Слів не несуть: `len`, `bool`, хеш, порівняння, `not`, умова
     `… if … else …`, ключ таблиці (`Д[x]`, `Д.get(x)` — значення з таблиці), відоме поле без її слів зі зараженого
     обʼєкта (коди паспорта, тексти моделі). JS — `.slice/.substring/.substr` зі сталими межами на значенні від стрічки
     розмови `ЧАТ_П` (змінні, функції, що її повертають, параметри стрілок `.map/.filter/.forEach` над нею). Не
     місце: у тому самому реченні є «…»; функція лічить
     зняте (`len(база) - …`) чи кладе зріз у словник поруч із `len(основи)`; дві частини того самого значення
     складено назад (`x[:1] … x[1:]`); `.slice(0, -1)` знімає лише останню репліку (новий лист їде окремим полем) — у
     розділі «не місця». Межа зрізу — у рядку: число в коді чи стала з рядком визначення.
  2  ПЕРЕЛІК ПОЛІВ ПИСАЧА. Перелік, яким функція переносить поля з обʼєкта її полів далі (`{к: о.get(к) for к in П}`,
     цикл із `о.get(к)`, дозвіл ключів у `.items()`), у якому ≥2 її полів (ключі, що їх пише перекладач з її слів, чи
     плитки її екрана, `показ` у `ПОЛЯ_ПАСПОРТА`), і: (а) функція бере одну форму пари «те саме значення — інша
     форма», а другої не називає ніде (пара — зі схеми шару: опис поля каже «is Y and never X» чи «X then stays
     absent»), або (б) перелік бере щонайменше половину плиток її екрана, а решти функція не називає ніде. Місце —
     літерал переліку. Не місце: година й хвилини (інваріант `Е2-частина-дня`: коду їх не передають); перелік пар
     «поле → сусіднє поле» того самого простору (`_СУСІДИ_КОДІВ` — перекладка між полями шару).
  3  ПОЛЕ ВИХОДУ МОДЕЛІ БЕЗ ЧИТАЧА-РІШЕННЯ. (а) У функції, що читає текст моделі (виклик розбору протоколу), змінна
     тримає кортеж функції продукту, а від неї до наступного присвоєння береться лише `[0]` — решта (лічба, яку функція
     рахує з полів відповіді) губиться; функції самого протоколу (`розбір*`, `прочитати`) — не тут: їхня причина й
     нотатки — статус розбору (корінь `Е2-збій-без-сліду`). (б) Зліпок кількох полів в один текст, де щонайменше два
     ключі (і не менше двох третин зліпка) — поля `поля_виходу` під тим самим шляхом відповіді (`образи[].…`), а
     окремим ключем функція поле ніде не кладе: воно лишається хіба прозою для мовного гейту; пари-синоніми (`id`/`ід`)
     і поля речі каталогу під цю мірку не підпадають. (в) Поле схеми розбору каталогу, яке пише модель (без полів, що
     їх виводить код: `… if ш not in X` над `ПОЛЯ`), код безумовно пропускає, переносячи запис (`if к in (…):
     continue`, `… if к not in (…)` над `.items()`), а читача ключа поза модулями розбору нема.
  4  ПОЛЕ ЗАПИСУ КАТАЛОГУ. Тег, який пише складальник жниварки (`ТЕГИ`, `<description>`), а фід (`фід_розбір.py`)
     не бере (`findtext`/`findall`), з лічбою записів на `каталог_повний.xml.gz`. Не місце: опис у тегу
     `<description>` (рішення менеджера 31.10: до розбору з цитатами не підключається) і тег з одним значенням на всіх
     записах (значення не несе) — у розділі «не місця». Параметри `param` фід несе цілим словником (`параметри`).
  5  ЧИТАЧ БЕРЕ НЕ ТЕ ЗНАЧЕННЯ (рішення менеджера 31.10). (а) Виклик функції продукту дає те саме значення двом різним
     параметрам, з яких функція читає ключі (сама чи через копію `dict(п or {})`), а інші виклики тієї самої функції
     дають їм різні значення; (б) параметр, якому виклики дають поле її паспорта, а тіло функції його не читає.
     Функцію знаходить крізь ланцюг `from … import` (до шести ланок).

Вивід: перелік `файл:рядок · пункт · чому`, підсумки за пунктами, «не місця» з причиною, останній рядок
`місць: <N>` (N — різних `файл:рядок`), код 0. Запуск з кореня репозиторію (чи з `--корінь <шлях>`):
python3 джерела/прилади/корінь_е2_втрата_слова.py [--json] [--тихо]
"""
import ast
import gzip
import json
import os
import re
import sys
import warnings

warnings.simplefilter("ignore", SyntaxWarning)

# Файли поза продуктом (той самий перелік, що в `корінь_е2_межі.py`, і тести): проби, стенди, батареї, заміри.
НЕ_ПРОДУКТ = re.compile(r"^(тест|test_|gate_|audit_|build_|стенд|батарея_|measure_|pair_test|rule_genus|"
                        r"status_перевірки|скласти|склад$|мутанти|корпус$|таблиця_збирання|траса_петлі|звірка|"
                        r"зведення|рв\d|replay|проба)")
НЕ_ТЕКИ = {"проби", "прилади", "аудит", "лабораторія", "траса", "__pycache__", "node_modules", "тести", "tests",
           "розвідка", ".git"}
ТЕКИ_ПРОДУКТУ = ("джерела", "zhnyvarka")
# Розбір протоколу: їхній кортеж — (обʼєкт, причина, нотатки) — статус розбору, не поля відповіді.
РОЗБІР_ПРОТОКОЛУ = {"розбір", "розібрати_json", "розбір_останній", "розбір_за_схемою", "прочитати",
                    "виконати_розбір"}
# Вбудовані виклики, через які слово не тече (повертають число, істину чи тип).
НЕ_НЕСЕ = {"len", "bool", "isinstance", "int", "float", "any", "all", "sum", "hash", "id", "type", "callable",
           "hasattr", "issubclass", "round", "abs", "ord", "sha256", "sha1", "md5", "blake2b", "hexdigest", "digest"}
# Опис входу мосту, чий предмет — її слова: після першої двокрапки опис починається з її питання, слів, репліки чи
# листа, з реплік розмови чи стрічки чату («коди … з її питання» — коди, не слова).
ОПИС_ЇЇ_СЛІВ = re.compile(r"^[^:]*:\s*(?:УСІ\s+)?(?:\{нове — )?(?:її (?:питання|слова|реплік\w*|нов\w* лист|текст)|"
                          r"останні репліки розмови|стрічк\w* чату)")
ГОДИНИ = {"година", "хвилини", "hour", "minute", "start_hour", "clock_time"}
ПУНКТИ = {1: "зріз її слів без «…» і лічби знятого", 2: "перелік полів писача губить її поле",
          3: "поле виходу моделі без читача-рішення", 4: "поле запису каталогу без читача",
          5: "читач бере не те значення"}


def корінь_репозиторію():
    if "--корінь" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--корінь") + 1])
    return os.getcwd()


КОРІНЬ = корінь_репозиторію()


def прочитати(шлях):
    with open(шлях, encoding="utf-8", errors="replace") as ф:
        return ф.read()


def відн(шлях):
    return os.path.relpath(шлях, КОРІНЬ).replace(os.sep, "/")


def файли_продукту(розширення):
    вих = []
    for тека in ТЕКИ_ПРОДУКТУ:
        for д, теки, фф in os.walk(os.path.join(КОРІНЬ, тека)):
            теки[:] = sorted(т for т in теки if т not in НЕ_ТЕКИ and not т.startswith("дані"))
            for ф in sorted(фф):
                if ф.endswith(розширення) and not НЕ_ПРОДУКТ.match(ф.rsplit(".", 1)[0]):
                    вих.append(os.path.join(д, ф))
    return вих


def рядок_сталої(в):
    """Рядок із вузла: стала чи неявне склеювання; інакше None."""
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return в.value
    if isinstance(в, ast.JoinedStr):
        return "".join(ч.value for ч in в.values if isinstance(ч, ast.Constant) and isinstance(ч.value, str))
    return None


def ключ_читання(в):
    """`x.get("k")`, `x["k"]`, `x.pop("k")`, `x.setdefault("k")` → (обʼєкт, "k"); інакше None."""
    if isinstance(в, ast.Subscript) and not isinstance(в.slice, ast.Slice):
        к = рядок_сталої(в.slice)
        if к is not None:
            return в.value, к
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr in ("get", "pop", "setdefault") \
            and в.args:
        к = рядок_сталої(в.args[0])
        if к is not None:
            return в.func.value, к
    return None


def імʼя_виклику(в):
    if isinstance(в, ast.Call):
        в = в.func
    if isinstance(в, ast.Name):
        return в.id
    if isinstance(в, ast.Attribute):
        return в.attr
    return None


def батьки(дерево):
    б = {}
    for в in ast.walk(дерево):
        for д in ast.iter_child_nodes(в):
            б[д] = в
    return б


class Модуль:
    def __init__(self, шлях):
        self.шлях, self.ф = шлях, відн(шлях)
        self.ім = os.path.basename(шлях)[:-3]
        self.текст = прочитати(шлях)
        self.рядки = self.текст.splitlines()
        self.дерево = ast.parse(self.текст)
        self.б = батьки(self.дерево)
        self.псевдоніми = {}          # alias → модуль
        self.імпортовані = {}         # імʼя → (модуль, імʼя)
        self.функції = {}             # імʼя → вузол (верхній рівень і методи «Клас.м»)
        self.сталі = {}               # ІМʼЯ верхнього рівня → вузол значення
        for в in ast.walk(self.дерево):
            if isinstance(в, ast.Import):
                for а in в.names:
                    self.псевдоніми[а.asname or а.name] = а.name
            elif isinstance(в, ast.ImportFrom) and в.module and not в.level:
                for а in в.names:
                    self.імпортовані[а.asname or а.name] = (в.module, а.name)
        for в in self.дерево.body:
            if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.функції[в.name] = в
            elif isinstance(в, ast.ClassDef):
                for м in в.body:
                    if isinstance(м, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        self.функції["%s.%s" % (в.name, м.name)] = м
            elif isinstance(в, ast.Assign):
                for ц in в.targets:
                    if isinstance(ц, ast.Name):
                        self.сталі[ц.id] = в.value

    def функція_вузла(self, в):
        while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            в = self.б.get(в)
        while isinstance(в, ast.Lambda):
            в = self.б.get(в)
            while в is not None and not isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
                в = self.б.get(в)
        return в

    def речення(self, в):
        while в is not None and not isinstance(в, ast.stmt):
            в = self.б.get(в)
        return в


def зібрати_модулі():
    мм = {}
    for ш in файли_продукту(".py"):
        try:
            м = Модуль(ш)
        except (SyntaxError, ValueError):
            continue
        мм.setdefault(м.ім, м)
    return мм


# ── РЕЄСТРИ (усе — з AST, без імпорту продукту: прилад іде й на дереві бази храповика) ──────────────────────────

def літерал_словника(мм, модуль, імʼя):
    м = мм.get(модуль)
    в = м.сталі.get(імʼя) if м else None
    return в if isinstance(в, ast.Dict) else None


def поля_паспорта(мм):
    """`паспорт_поля.ПОЛЯ_ПАСПОРТА` → {ключ: {"поле": en, "її_мовою": bool, "показ": bool}}."""
    д = літерал_словника(мм, "паспорт_поля", "ПОЛЯ_ПАСПОРТА")
    вих = {}
    for к, v in zip(д.keys if д else [], д.values if д else []):
        ключ = рядок_сталої(к)
        if ключ is None or not isinstance(v, ast.Dict):
            continue
        оп = {"поле": None, "її_мовою": False, "показ": False}
        for кк, вв in zip(v.keys, v.values):
            ім = рядок_сталої(кк)
            if ім == "поле":
                оп["поле"] = рядок_сталої(вв)
            elif ім == "її_мовою":
                оп["її_мовою"] = isinstance(вв, ast.Constant) and вв.value is True
            elif ім == "показ":
                оп["показ"] = True
        вих[ключ] = оп
    return вих


def схема_шару(мм):
    """`мовний_шар._ПОЛЯ_EN` → {поле: опис} (опис — рядок, коли він сталий)."""
    д = літерал_словника(мм, "мовний_шар", "_ПОЛЯ_EN")
    вих = {}
    for к, v in zip(д.keys if д else [], д.values if д else []):
        ключ = рядок_сталої(к)
        if ключ is not None:
            вих[ключ] = рядок_сталої(v) or ""
    return вих


def пари_форм(схема):
    """Пари «те саме значення — інша форма» зі схеми шару: опис X каже «is Y and never X» чи «Y then stays absent»."""
    пари = set()
    for x, оп in схема.items():
        for y in re.findall(r"is (\w+),? (?:and )?never %s\b" % re.escape(x), оп):
            if y in схема and y != x:
                пари |= {(x, y), (y, x)}
        for y in re.findall(r"\b(\w+) then stays absent", оп):
            if y in схема and y != x:
                пари |= {(x, y), (y, x)}
    return {п for п in пари if not (set(п) & ГОДИНИ)}


def словники_перекладу(мм):
    """Літерали-словники «ключ → ключ» (усі значення — рядки, ≥3 пар): переклад ключа на ключ дроту."""
    вих = []
    for м in мм.values():
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.Dict) and len(в.keys) >= 3:
                пари = [(рядок_сталої(к), рядок_сталої(v)) for к, v in zip(в.keys, в.values) if к is not None]
                if len(пари) == len(в.keys) and all(а and б for а, б in пари):
                    вих.append(dict(пари))
    return вих


def входи_її_слів(мм):
    """Ключі входів мосту, чий опис у `ЗОВНІШНІ_ВХОДИ` називає її слова чи розмову."""
    вих = set()
    for м in мм.values():
        д = м.сталі.get("ЗОВНІШНІ_ВХОДИ")
        if isinstance(д, ast.Dict):
            for к, v in zip(д.keys, д.values):
                ключ, оп = рядок_сталої(к) if к is not None else None, рядок_сталої(v) or ""
                if ключ and ОПИС_ЇЇ_СЛІВ.search(оп):
                    вих.add(ключ)
    return вих


class Реєстри:
    def __init__(self, мм):
        self.паспорт = поля_паспорта(мм)
        self.схема = схема_шару(мм)
        en_ua = {оп["поле"]: к for к, оп in self.паспорт.items() if оп["поле"]}
        self.en_ua = en_ua
        # її поля: те, що перекладач пише з її слів (схема шару), і плитки її екрана
        self.її_en = set(self.схема) | {оп["поле"] for оп in self.паспорт.values() if оп["показ"] and оп["поле"]}
        self.її_ua = {en_ua[е] for е in self.схема if е in en_ua} | {к for к, оп in self.паспорт.items() if оп["показ"]}
        self.плитки_ua = {к for к, оп in self.паспорт.items() if оп["показ"]} - ГОДИНИ
        self.плитки_en = {self.паспорт[к]["поле"] for к in self.плитки_ua if self.паспорт[к]["поле"]} - ГОДИНИ
        пари_en = пари_форм(self.схема)
        self.пари = пари_en | {(en_ua[а], en_ua[б]) for а, б in пари_en if а in en_ua and б in en_ua}
        # її слова: поля «її мовою» (ключ і поле шару), ключі дроту, у які їх перекладає словник, входи мосту
        слова = set()
        for к, оп in self.паспорт.items():
            if оп["її_мовою"]:
                слова.add(к)
                if оп["поле"]:
                    слова.add(оп["поле"])
        for сл in словники_перекладу(мм):
            слова |= {v for к, v in сл.items() if к in слова and v not in self.її_ua}
        self.входи = входи_її_слів(мм)
        self.слова = слова
        # відомі поля, що її слів не несуть (коди, тексти моделі): читання їх зі зараженого обʼєкта — не її слова
        self.не_її = (set(self.паспорт) | {оп["поле"] for оп in self.паспорт.values() if оп["поле"]}
                      | set(self.схема)) - слова - self.входи


class Імена(dict):
    """Заражені імена функції → рядок, з якого імʼя несе слова: ужиток вище за присвоєння (те саме імʼя раніше
    тримало інше значення) слів не несе. Параметри й цілі циклів — з рядка 0."""

    def __init__(self, з=()):
        super().__init__()
        if isinstance(з, dict):
            self.update(з)
        else:
            for н in з:
                self[н] = 0

    def додати(self, нові, рядок=0):
        for н in нові:
            if н not in self or self[н] > рядок:
                self[н] = рядок

    def чинне(self, н, рядок):
        return н in self and self[н] <= рядок


# ── ПОТІК ЗНАЧЕННЯ PYTHON (п.1): заражене — те, що походить від її слів ────────────────────────────────────────

class ПотікСлів:
    """Потік її слів: джерела — читання ключів її слів (поля «її мовою» і ключі дроту, у які їх перекладено — у будь-
    якому модулі; входи мосту з описом її слів — лише в модулі, що їх оголошує). Повернення — залежне від виклику:
    виклик заражений, коли функція повертає слова сама чи з параметра, якому цей виклик дає слова."""

    def __init__(self, мм, рег):
        self.мм, self.рег = мм, рег
        self._ключі_обʼєктів = {}
        self.параметри = {}       # (модуль, функція) → {параметр}: хоч один виклик дає слова
        self.власне = set()       # (модуль, функція): повертає слова без заражених параметрів
        self.залежні = {}         # (модуль, функція) → {параметр}: слова параметра доходять до повернення
        self.імена = {}           # (модуль, функція) → {імʼя}
        self.входи = {м.ім: входи_модуля(м) for м in мм.values()}
        self.обчислити()

    def ціль(self, м, виклик):
        """Функція продукту, яку кличе виклик: локальна, імпортована чи через псевдонім модуля."""
        ф = виклик.func
        if isinstance(ф, ast.Name):
            if ф.id in м.функції:
                return (м.ім, ф.id)
            if ф.id in м.імпортовані:
                return self._реекспорт(*м.імпортовані[ф.id])
        if isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id in м.псевдоніми:
            return self._реекспорт(м.псевдоніми[ф.value.id], ф.attr)
        return None

    def _реекспорт(self, мод, ім):
        """Імʼя модуля → функція, де її визначено, крізь ланцюг `from … import` (до шести ланок)."""
        for _ in range(6):
            if мод not in self.мм:
                return None
            if ім in self.мм[мод].функції:
                return (мод, ім)
            if ім not in self.мм[мод].імпортовані:
                return None
            мод, ім = self.мм[мод].імпортовані[ім]
        return None

    def параметри_виклику(self, ц, виклик):
        цф = self.мм[ц[0]].функції[ц[1]]
        пар = [а.arg for а in цф.args.posonlyargs + цф.args.args]
        if "." in ц[1] and пар and пар[0] in ("self", "cls"):
            пар = пар[1:]
        вих = []
        for і, а in enumerate(виклик.args):
            if isinstance(а, ast.Starred):
                break
            if і < len(пар):
                вих.append((пар[і], а))
        вих += [(кв.arg, кв.value) for кв in виклик.keywords if кв.arg]
        return вих

    def заражене(self, м, вузол, імена, джерела=True):
        """Чи несе вираз її слова. Виклик функції продукту несе лише з параметра, що доходить до її повернення
        (чи коли вона повертає слова сама); вираз-генератор — лише своїм елементом, від цілей заражених ітерацій."""
        return self._з(м, вузол, імена, джерела, вузол)

    def _з(self, м, в, імена, джерела, межа):
        if isinstance(в, ast.Name):
            чинне = імена.чинне(в.id, в.lineno) if isinstance(імена, Імена) else в.id in імена
            return чинне and isinstance(в.ctx, ast.Load) and not self._під_ненесучим(м, в, межа) \
                and not self._читає_не_її(м, в)
        if джерела:
            кч = ключ_читання(в)
            if кч and (кч[1] in self.входи[м.ім] or кч[1] in self.рег.слова and self._паспорт(м, в, кч)) \
                    and not self._під_ненесучим(м, в, межа):
                return True
        if isinstance(в, ast.Call):
            ц = self.ціль(м, в)
            цф = self.мм[ц[0]].функції[ц[1]] if ц else None
            if цф is not None and not цф.args.vararg and not цф.args.kwarg \
                    and not any(isinstance(а, ast.Starred) for а in в.args) and not any(к.arg is None for к in в.keywords):
                if self._під_ненесучим(м, в, межа) or м.функція_вузла(в) is цф:
                    # рекурсивний виклик (ендпойнт мосту кличе сам себе на інший вхід) — інша гілка, не ці слова
                    return False
                if джерела and ц in self.власне:
                    return True
                зал = self.залежні.get(ц, set())
                return any(п in зал and self._з(м, а, імена, джерела, межа) for п, а in self.параметри_виклику(ц, в))
        if isinstance(в, (ast.ListComp, ast.SetComp, ast.GeneratorExp, ast.DictComp)):
            місцеві = Імена(імена)
            for г in в.generators:
                цілі = імена_цілі(г.target)
                if self._з(м, г.iter, місцеві, джерела, межа):
                    for н in цілі:
                        місцеві[н] = 0
                else:
                    for н in цілі:
                        місцеві.pop(н, None)
            елементи = [в.key, в.value] if isinstance(в, ast.DictComp) else [в.elt]
            return any(self._з(м, е, місцеві, джерела, межа) for е in елементи)
        if isinstance(в, ast.Lambda):
            return False
        return any(self._з(м, д, імена, джерела, межа) for д in ast.iter_child_nodes(в))

    def _паспорт(self, м, в, кч):
        """Чи обʼєкт, з якого читають ключ її слів, — паспорт: у тій самій функції з нього читають і інше поле
        паспорта чи схеми шару (`g["решта"]` групи речей — не паспорт)."""
        ф = м.функція_вузла(в) or м.дерево
        кеш = self._ключі_обʼєктів.get(id(ф))
        if кеш is None:
            кеш = {}
            for вв in ast.walk(ф):
                к = ключ_читання(вв)
                if к:
                    кеш.setdefault(ast.unparse(к[0]), set()).add(к[1])
            self._ключі_обʼєктів[id(ф)] = кеш
        поля = set(self.рег.паспорт) | set(self.рег.en_ua) | set(self.рег.схема)
        return bool((кеш.get(ast.unparse(кч[0]), set()) - {кч[1]}) & поля)

    def _читає_не_її(self, м, в):
        """`об["код"]` чи `об.get("код")` зі зараженого обʼєкта, де «код» — відоме поле без її слів."""
        п = м.б.get(в)
        if isinstance(п, ast.Attribute) and п.value is в:
            п = м.б.get(п)
        кч = ключ_читання(п) if п is not None else None
        return bool(кч) and кч[0] in (в, getattr(п, "func", None) and п.func.value) and кч[1] in self.рег.не_її

    def _під_ненесучим(self, м, в, межа):
        """Чи лежить вузол під викликом, що слова не несе (`len`, `bool`…), чи під порівнянням."""
        if в is межа:
            return False
        п = м.б.get(в)
        while п is not None:
            if isinstance(п, ast.Call) and імʼя_виклику(п) in НЕ_НЕСЕ:
                return True
            if isinstance(п, ast.Compare) or isinstance(п, ast.UnaryOp) and isinstance(п.op, ast.Not):
                return True
            if isinstance(п, ast.IfExp) and в in ast.walk(п.test):
                return True
            # `Д[x]`, `Д.get(x)`: значення — з таблиці Д, ключ x слова не переносить
            if isinstance(п, ast.Subscript) and в in ast.walk(п.slice):
                return True
            if isinstance(п, ast.Call) and isinstance(п.func, ast.Attribute) and п.func.attr == "get" and п.args \
                    and в in ast.walk(п.args[0]):
                return True
            if п is межа:
                break
            п = м.б.get(п)
        return False

    def поширити(self, м, ф, імена, джерела=True):
        імена = Імена(імена)
        for _ in range(6):
            до = dict(імена)
            for в in ast.walk(ф):
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                    if self.заражене(м, в.value, імена, джерела):
                        цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                        for ц in цілі:
                            імена.додати(імена_цілі(ц), в.lineno)
                elif isinstance(в, (ast.For, ast.AsyncFor)):
                    if self.заражене(м, в.iter, імена, джерела):
                        імена.додати(імена_цілі(в.target), в.lineno)
                elif isinstance(в, ast.comprehension):
                    if self.заражене(м, в.iter, імена, джерела):
                        імена.додати(імена_цілі(в.target), 0)
                elif isinstance(в, ast.NamedExpr) and self.заражене(м, в.value, імена, джерела):
                    імена.додати([в.target.id], в.lineno)
            if імена == до:
                break
        return імена

    def повертає(self, м, ф, імена, джерела=True):
        return any(isinstance(в, ast.Return) and в.value is not None and self.заражене(м, в.value, імена, джерела)
                   for в in ast.walk(ф))

    def обчислити(self):
        for _ in range(12):
            змінено = False
            for м in self.мм.values():
                for ім, ф in м.функції.items():
                    кл = (м.ім, ім)
                    пар = [а.arg for а in ф.args.posonlyargs + ф.args.args + ф.args.kwonlyargs]
                    # залежні параметри: слова лише з параметра (без джерел) доходять до повернення
                    зал = {п for п in пар if п not in self.залежні.get(кл, set())
                           and self.повертає(м, ф, self.поширити(м, ф, {п}, False), False)}
                    if зал:
                        self.залежні[кл] = self.залежні.get(кл, set()) | зал
                        змінено = True
                    if кл not in self.власне and self.повертає(м, ф, self.поширити(м, ф, set()), True):
                        self.власне.add(кл)
                        змінено = True
                    імена = self.поширити(м, ф, set(self.параметри.get(кл, ())))
                    if імена != self.імена.get(кл, Імена()):
                        self.імена[кл] = імена
                        змінено = True
                    for в in ast.walk(ф):
                        if isinstance(в, ast.Call):
                            ц = self.ціль(м, в)
                            if not ц:
                                continue
                            нові = {п for п, а in self.параметри_виклику(ц, в) if self.заражене(м, а, імена)}
                            if нові - self.параметри.get(ц, set()):
                                self.параметри[ц] = self.параметри.get(ц, set()) | нові
                                змінено = True
            if not змінено:
                break


def імена_цілі(ц):
    """Імена, які присвоєння заражає: імʼя й розпакування; `x[к] = …` і `x.а = …` контейнера не заражають — слово
    тече ключем (читання ключа її слів — джерело), а не цілим словником."""
    if isinstance(ц, ast.Name):
        return {ц.id}
    if isinstance(ц, (ast.Tuple, ast.List)):
        вих = set()
        for е in ц.elts:
            вих |= імена_цілі(е)
        return вих
    if isinstance(ц, ast.Starred):
        return імена_цілі(ц.value)
    return set()


def входи_модуля(м):
    """Ключі входів мосту цього модуля, чий опис у `ЗОВНІШНІ_ВХОДИ` називає її слова чи розмову."""
    д = м.сталі.get("ЗОВНІШНІ_ВХОДИ")
    вих = set()
    if isinstance(д, ast.Dict):
        for к, v in zip(д.keys, д.values):
            ключ = рядок_сталої(к) if к is not None else None
            if ключ and ОПИС_ЇЇ_СЛІВ.search(рядок_сталої(v) or ""):
                вих.add(ключ)
    return вих


def межа_сталої(в):
    if isinstance(в, ast.Constant) and isinstance(в.value, int) and not isinstance(в.value, bool):
        return str(в.value)
    if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.USub):
        м = межа_сталої(в.operand)
        return ("-" + м) if м else None
    if isinstance(в, ast.Name) and в.id.isupper():
        return в.id
    if isinstance(в, ast.Attribute) and в.attr.isupper():
        return ast.unparse(в)
    return None


def є_три_крапки(м, речення):
    if речення is None:
        return False
    for в in ast.walk(речення):
        с = рядок_сталої(в)
        if с and ("…" in с or "..." in с):
            return True
    return False


def доповнювальний(речення, зріз, база):
    """`x[:N] … x[N:]` в одному реченні: дві частини того самого значення складено назад — нічого не знято."""
    if речення is None:
        return False
    с = зріз.slice
    for в in ast.walk(речення):
        if в is зріз or not (isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Slice)) \
                or ast.unparse(в.value) != база:
            continue
        с2 = в.slice
        if с.lower is None and с2.upper is None and с.upper is not None and с2.lower is not None \
                and ast.unparse(с.upper) == ast.unparse(с2.lower):
            return True
        if с2.lower is None and с.upper is None and с2.upper is not None and с.lower is not None \
                and ast.unparse(с2.upper) == ast.unparse(с.lower):
            return True
    return False


def лічить_зняте(функція, база):
    """`len(база) - …` у тій самій функції: зняте полічено."""
    if функція is None or база is None:
        return False
    for в in ast.walk(функція):
        if isinstance(в, ast.BinOp) and isinstance(в.op, ast.Sub) and isinstance(в.left, ast.Call) \
                and імʼя_виклику(в.left) == "len" and в.left.args and ast.unparse(в.left.args[0]) == база:
            return True
    return False


def лічба_поруч(функція, основа, речення):
    """Зріз іде в поле поруч із лічбою всього: словник у тій самій функції має `len(N)` (N — імʼя з основи зрізу) і
    значення з імені, якому присвоєно зріз (`{"ходів": len(старші), "її_слова": … її}`)."""
    if функція is None or not isinstance(речення, ast.Assign):
        return False
    цілі = set().union(*(імена_цілі(ц) for ц in речення.targets))
    основи = {в.id for в in ast.walk(основа) if isinstance(в, ast.Name)}
    for д in ast.walk(функція):
        if not isinstance(д, ast.Dict):
            continue
        лічба = any(isinstance(v, ast.Call) and імʼя_виклику(v) == "len" and v.args and isinstance(v.args[0], ast.Name)
                    and v.args[0].id in основи for v in д.values)
        if лічба and any(isinstance(в, ast.Name) and в.id in цілі for v in д.values for в in ast.walk(v)):
            return True
    return False


def зрізи_python(мм, потік):
    місця, не_місця = [], []
    for м in мм.values():
        for ім, ф in м.функції.items():
            імена = потік.імена.get((м.ім, ім), Імена())
            for в in ast.walk(ф):
                if not (isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Slice)):
                    continue
                с = в.slice
                межі = [межа_сталої(б) for б in (с.lower, с.upper) if б is not None]
                if not межі or None in межі or с.step is not None:
                    continue
                if м.функція_вузла(в) is not ф and not isinstance(м.функція_вузла(в), ast.Lambda):
                    continue
                if not потік.заражене(м, в.value, імена):
                    continue
                речення = м.речення(в)
                база = ast.unparse(в.value)
                межа = ":".join(ast.unparse(б) if б is not None else "" for б in (с.lower, с.upper))
                if доповнювальний(речення, в, база):
                    continue
                if є_три_крапки(м, речення) or лічить_зняте(ф, база) or лічба_поруч(ф, в.value, речення):
                    не_місця.append((м.ф, в.lineno, 1, "зріз `%s[%s]` з «…» чи лічбою знятого" % (база[:50], межа)))
                    continue
                місця.append((м.ф, в.lineno, 1, "`%s[%s]` у `%s` — її слова без «…» і лічби знятого; межа: %s"
                              % (база[:60], межа, ім, опис_межі(м, с))))
    return місця, не_місця


def опис_межі(м, с):
    вих = []
    for б in (с.lower, с.upper):
        if isinstance(б, ast.Name) and б.id in м.сталі:
            р = next((в.lineno for в in м.дерево.body if isinstance(в, ast.Assign)
                      and any(isinstance(ц, ast.Name) and ц.id == б.id for ц in в.targets)), "?")
            вих.append("стала %s (%s:%s)" % (б.id, м.ф, р))
        elif б is not None:
            вих.append("число в коді %s" % ast.unparse(б))
    return ", ".join(вих)


# ── ПОТІК ЗНАЧЕННЯ JS (п.1): від стрічки розмови `ЧАТ_П` ───────────────────────────────────────────────────────

def без_коментарів_js(т):
    """Коментарі й рядки-шаблони без змісту → пробіли (номери рядків лишаються)."""
    вих, і, н = [], 0, len(т)
    while і < н:
        с = т[і]
        if т.startswith("/*", і):
            к = т.find("*/", і + 2)
            к = н if к < 0 else к + 2
            вих.append(re.sub(r"[^\n]", " ", т[і:к]))
            і = к
        elif т.startswith("//", і) and (і == 0 or т[і - 1] not in ":\\"):
            к = т.find("\n", і)
            к = н if к < 0 else к
            вих.append(" " * (к - і))
            і = к
        elif с in "'\"`":
            к = і + 1
            while к < н and т[к] != с:
                к += 2 if т[к] == "\\" else 1
            вих.append(т[і:к + 1])
            і = к + 1
        else:
            вих.append(с)
            і += 1
    return "".join(вих)


def файли_js():
    вих = []
    for ш in файли_продукту(".js"):
        вих.append((відн(ш), без_коментарів_js(прочитати(ш))))
    for ш in файли_продукту(".html"):
        т = прочитати(ш)
        частини = []
        for зб in re.finditer(r"<script\b[^>]*>(.*?)</script>", т, re.S):
            початок = т[:зб.start(1)].count("\n")
            частини.append((початок, зб.group(1)))
        if частини:
            рядки = [""] * (т.count("\n") + 1)
            тіло = "\n".join("" for _ in range(0))
            for п, ч in частини:
                for і, р in enumerate(ч.split("\n")):
                    if п + і < len(рядки):
                        рядки[п + і] = р
            тіло = "\n".join(рядки)
            вих.append((відн(ш), без_коментарів_js(тіло)))
    return вих


ІМʼЯ_JS = r"[A-Za-zА-Яа-яЇїІіЄєҐґ_$][\wА-Яа-яЇїІіЄєҐґ$]*"


def функції_js(т):
    """(імʼя, параметри, початок, кінець тіла) для `function N(...){}` і `const N = (...) => {...}|вираз;`."""
    вих = []
    for зб in re.finditer(r"\bfunction\s+(%s)\s*\(([^)]*)\)\s*\{" % ІМʼЯ_JS, т):
        к = кінець_дужки(т, зб.end() - 1)
        вих.append((зб.group(1), зб.group(2), зб.end(), к))
    for зб in re.finditer(r"\b(?:const|let|var)\s+(%s)\s*=\s*(?:async\s*)?(\([^)]*\)|%s)\s*=>\s*" % (ІМʼЯ_JS, ІМʼЯ_JS), т):
        п = зб.end()
        if п < len(т) and т[п] == "{":
            к = кінець_дужки(т, п)
            вих.append((зб.group(1), зб.group(2).strip("()"), п + 1, к))
        else:
            к = т.find(";", п)
            вих.append((зб.group(1), зб.group(2).strip("()"), п, len(т) if к < 0 else к))
    return вих


def кінець_дужки(т, і):
    пари = {"{": "}", "(": ")", "[": "]"}
    стек, к = [], і
    while к < len(т):
        с = т[к]
        if с in пари:
            стек.append(пари[с])
        elif стек and с == стек[-1]:
            стек.pop()
            if not стек:
                return к
        elif с in "'\"`":
            кк = к + 1
            while кк < len(т) and т[кк] != с:
                кк += 2 if т[кк] == "\\" else 1
            к = кк
        к += 1
    return len(т)


def приймач(т, крапка):
    """Вираз перед `.slice(`: ланцюг імен, крапок, викликів і індексів (назад від крапки)."""
    і = крапка
    while і > 0:
        с = т[і - 1]
        if с in ")]":
            пара = "(" if с == ")" else "["
            глиб, к = 0, і - 1
            while к >= 0:
                if т[к] in ")]":
                    глиб += 1
                elif т[к] in "([":
                    глиб -= 1
                    if глиб == 0:
                        break
                к -= 1
            і = к
            continue
        if re.match(r"[\wА-Яа-яЇїІіЄєҐґ$.]", с):
            і -= 1
            continue
        break
    return т[і:крапка]


def є_у(текст, імена):
    return any(re.search(r"(?<![\wА-Яа-яЇїІіЄєҐґ$.])%s(?![\wА-Яа-яЇїІіЄєҐґ$])" % re.escape(н), текст) for н in імена)


def зрізи_js():
    файли = файли_js()
    джерела, функції = {"ЧАТ_П"}, []
    for ф, т in файли:
        функції += [(ф, т) + ф_ for ф_ in функції_js(т)]
    повертають = set()
    for _ in range(8):
        до = len(повертають)
        for ф, т, ім, пар, п, к in функції:
            тіло = т[п:к]
            заражені = джерела | {н + "(" for н in повертають}
            рядки_повернення = re.findall(r"\breturn\b([^;]*)", тіло) if т[п - 1:п] == "{" else [тіло]
            if any(є_у(р, джерела) or any(н + "(" in р for н in повертають) for р in рядки_повернення):
                повертають.add(ім)
            del заражені
        if len(повертають) == до:
            break
    місця, не_місця = [], []
    for ф, т in файли:
        межі = [(п, к) for фф, тт, ім, пар, п, к in функції if фф == ф]
        for зб in re.finditer(r"\.(slice|substring|substr)\(\s*(-?\d+)\s*(?:,\s*(-?\d+)\s*)?\)", т):
            крапка = зб.start()
            пр = приймач(т, крапка)
            if not пр:
                continue
            # локальні заражені в найменшій функції, що містить місце
            обл = min(((п, к) for п, к in межі if п <= крапка <= к), key=lambda х: х[1] - х[0], default=(0, len(т)))
            тіло = т[обл[0]:обл[1]]
            імена = set(джерела)
            for _ in range(4):
                for з in re.finditer(r"\b(?:const|let|var)\s+(%s)\s*=\s*([^;]*)" % ІМʼЯ_JS, тіло):
                    if є_у(з.group(2), імена) or any(н + "(" in з.group(2) for н in повертають):
                        імена.add(з.group(1))
                for з in re.finditer(r"(%s)\s*\.\s*(?:map|filter|forEach|find|some|every|flatMap)\(\s*\(?\s*(%s)"
                                     % (r"[\wА-Яа-яЇїІіЄєҐґ$.()\[\]]+", ІМʼЯ_JS), тіло):
                    if є_у(з.group(1), імена) or any(н + "(" in з.group(1) for н in повертають):
                        імена.add(з.group(2))
            if not (є_у(пр, імена) or any(н + "(" in пр for н in повертають)):
                continue
            рядок = т[:крапка].count("\n") + 1
            поч = max(т.rfind(";", 0, крапка), т.rfind("\n", 0, т.rfind("\n", 0, крапка)))
            кін = т.find(";", зб.end())
            речення = т[поч + 1: кін if кін > 0 else len(т)]
            a, b = зб.group(2), зб.group(3)
            опис = "`%s.%s(%s%s)`" % (пр[-50:], зб.group(1), a, (", " + b) if b is not None else "")
            if a == "0" and b == "-1":
                не_місця.append((ф, рядок, 1, "%s знімає лише останню репліку (новий лист — окремим полем)" % опис))
            elif "…" in речення or "..." in речення:
                не_місця.append((ф, рядок, 1, "%s з «…»" % опис))
            else:
                місця.append((ф, рядок, 1, "%s — її слова чи репліки розмови без «…» і лічби знятого; межа: "
                              "число в коді" % опис))
    return місця, не_місця


# ── п.2: ПЕРЕЛІК ПОЛІВ ПИСАЧА ───────────────────────────────────────────────────────────────────────────────

def літерал_переліку(м, мм, в):
    """Вузол переліку ключів: літерал чи імʼя сталої (свого модуля чи `_Х.ІМʼЯ`) → (вузол, модуль)."""
    if isinstance(в, (ast.Tuple, ast.List, ast.Set, ast.Dict)):
        return в, м
    if isinstance(в, ast.Name) and isinstance(м.сталі.get(в.id), (ast.Tuple, ast.List, ast.Set, ast.Dict)):
        return м.сталі[в.id], м
    if isinstance(в, ast.Name) and в.id in м.імпортовані:
        мод, ім = м.імпортовані[в.id]
        if мод in мм and isinstance(мм[мод].сталі.get(ім), (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            return мм[мод].сталі[ім], мм[мод]
    if isinstance(в, ast.Attribute) and isinstance(в.value, ast.Name) and в.value.id in м.псевдоніми:
        мод = м.псевдоніми[в.value.id]
        if мод in мм and isinstance(мм[мод].сталі.get(в.attr), (ast.Tuple, ast.List, ast.Set, ast.Dict)):
            return мм[мод].сталі[в.attr], мм[мод]
    if isinstance(в, ast.Call) and імʼя_виклику(в) in ("frozenset", "set", "tuple") and в.args:
        return літерал_переліку(м, мм, в.args[0])
    return None, None


def ключі_переліку(вузол, позиція=0):
    елементи = вузол.keys if isinstance(вузол, ast.Dict) else вузол.elts
    вих = []
    for е in елементи:
        if isinstance(е, ast.Tuple) and len(е.elts) > позиція:
            е = е.elts[позиція]
        с = рядок_сталої(е) if е is not None else None
        if с is not None:
            вих.append(с)
    return вих


def переноситься(м, в, межа):
    """Чи йде прочитане значення в новий обʼєкт: присвоєння в ключ, словник, генератор словника, `dict(...)`."""
    п, д = м.б.get(в), в
    while п is not None and п is not межа:
        if isinstance(п, ast.Assign) and any(isinstance(ц, ast.Subscript) for ц in п.targets) and д is п.value:
            return True
        if isinstance(п, ast.Dict) and д in п.values:
            return True
        if isinstance(п, ast.DictComp):
            return True
        if isinstance(п, ast.keyword) and isinstance(м.б.get(п), ast.Call) and імʼя_виклику(м.б.get(п)) == "dict":
            return True
        if isinstance(п, ast.stmt):
            return False
        д, п = п, м.б.get(п)
    return False


def писачі(мм, рег):
    """Функції, що переносять поля з обʼєкта її полів: {(модуль, функція, обʼєкт): {"ключі", "перелік", "несе"}}."""
    вих = {}
    for м in мм.values():
        for ім, ф in м.функції.items():
            обʼєкти = {}

            def додати(обʼєкт, ключі, рядок_переліку, несе):
                if not isinstance(обʼєкт, ast.Name):
                    return
                з = обʼєкти.setdefault(обʼєкт.id, {"ключі": set(), "переліки": {}, "окремо": set()})
                з["ключі"] |= set(ключі)
                if рядок_переліку:
                    к0, н0 = з["переліки"].get(рядок_переліку, (set(), False))
                    з["переліки"][рядок_переліку] = (к0 | set(ключі), н0 or несе)
                elif несе:
                    з["окремо"] |= set(ключі)

            for в in ast.walk(ф):
                кч = ключ_читання(в)
                if кч:
                    додати(кч[0], [кч[1]], None, переноситься(м, в, ф))
                if isinstance(в, ast.Compare) and len(в.ops) == 1 and isinstance(в.ops[0], ast.In):
                    к = рядок_сталої(в.left)
                    if к is not None:
                        додати(в.comparators[0], [к], None, False)
                # for к in ПЕРЕЛІК / for а, б in ПЕРЕЛІК: … обʼєкт.get(к|а)
                if isinstance(в, (ast.For, ast.comprehension)):
                    перелік, мп = літерал_переліку(м, мм, в.iter)
                    тіло = в if isinstance(в, ast.For) else м.б.get(в)
                    if перелік is not None:
                        цілі = в.target.elts if isinstance(в.target, ast.Tuple) else [в.target]
                        for поз, ц in enumerate(цілі):
                            if not isinstance(ц, ast.Name):
                                continue
                            for вв in ast.walk(тіло):
                                if isinstance(вв, ast.Call) and isinstance(вв.func, ast.Attribute) \
                                        and вв.func.attr == "get" and вв.args and isinstance(вв.args[0], ast.Name) \
                                        and вв.args[0].id == ц.id:
                                    додати(вв.func.value, ключі_переліку(перелік, поз), (мп.ф, перелік.lineno),
                                           переноситься(м, вв, ф) or isinstance(тіло, ast.For))
                                elif isinstance(вв, ast.Subscript) and isinstance(вв.slice, ast.Name) \
                                        and вв.slice.id == ц.id and isinstance(вв.ctx, ast.Load):
                                    додати(вв.value, ключі_переліку(перелік, поз), (мп.ф, перелік.lineno),
                                           переноситься(м, вв, ф) or isinstance(тіло, (ast.For, ast.DictComp)))
                    # for к, v in обʼєкт.items(): if к not in ПЕРЕЛІК: continue / {к: v … if к in ПЕРЕЛІК}
                    if isinstance(в.iter, ast.Call) and isinstance(в.iter.func, ast.Attribute) \
                            and в.iter.func.attr == "items" and isinstance(в.target, ast.Tuple) \
                            and isinstance(в.target.elts[0], ast.Name):
                        к_ім = в.target.elts[0].id
                        умови = []
                        if isinstance(в, ast.comprehension):
                            умови = list(в.ifs)
                        else:
                            for с in в.body:
                                if isinstance(с, ast.If) and any(isinstance(х, ast.Continue) for х in с.body):
                                    умови.append(с.test)
                        for у in умови:
                            for пор in ast.walk(у):
                                if isinstance(пор, ast.Compare) and isinstance(пор.left, ast.Name) \
                                        and пор.left.id == к_ім and len(пор.ops) == 1:
                                    дозвіл = isinstance(в, ast.comprehension) and isinstance(пор.ops[0], ast.In) \
                                        or isinstance(в, ast.For) and isinstance(пор.ops[0], ast.NotIn)
                                    перелік, мп = літерал_переліку(м, мм, пор.comparators[0])
                                    if дозвіл and перелік is not None:
                                        несе = isinstance(м.б.get(в), ast.DictComp) or isinstance(в, ast.For) and any(
                                            isinstance(х, ast.Assign) and any(isinstance(ц, ast.Subscript)
                                                                               for ц in х.targets)
                                            for х in ast.walk(в))
                                        додати(в.iter.func.value, ключі_переліку(перелік), (мп.ф, перелік.lineno), несе)
            сталі = {в.value for в in ast.walk(ф) if isinstance(в, ast.Constant) and isinstance(в.value, str)}
            for обʼєкт, з in обʼєкти.items():
                з["сталі"] = сталі
                вих[(м.ф, ім, обʼєкт)] = з
    return вих


def сусіди(з, файл, рядок, мм, рег):
    """Перелік пар «поле → сусіднє поле» того самого простору (`_СУСІДИ_КОДІВ`: код з одного поля шару в інше):
    дві позиції кортежів несуть ключі шару — це перекладка між полями, а не перенос полів писачем."""
    м = next((м for м in мм.values() if м.ф == файл), None)
    if м is None:
        return False
    for в in ast.walk(м.дерево):
        if isinstance(в, (ast.Tuple, ast.List)) and getattr(в, "lineno", None) == рядок and в.elts \
                and all(isinstance(е, ast.Tuple) for е in в.elts):
            поз = [{рядок_сталої(е.elts[і]) for е in в.elts if len(е.elts) > і} for і in range(2)]
            return all(len(п & (рег.її_en | рег.її_ua)) >= 2 for п in поз) \
                and any(len(п & рег.її_en) >= 2 for п in поз) == all(len(п & рег.її_en) >= 2 for п in поз)
    return False


def переліки_писача(мм, рег):
    """Перелік, яким писач переносить поля обʼєкта її полів (`несе`: ключ іде далі значенням), губить її поле:
    у переліку одна форма пари, а другої нема ні в ньому, ні в окремому читанні того самого обʼєкта функцією; чи
    перелік бере щонайменше половину плиток її екрана, а решти не бере ніде."""
    місця, не_місця, бачені = [], [], set()
    for (ф, ім, обʼєкт), з in sorted(писачі(мм, рег).items()):
        for (файл, рядок), (ключі, несе) in sorted(з["переліки"].items()):
            if not несе or (файл, рядок) in бачені:
                continue
            простір_ua = len(ключі & рег.її_ua) >= len(ключі & рег.її_en)
            її = рег.її_ua if простір_ua else рег.її_en
            if len(ключі & її) < 2:
                continue
            # друга форма чи плитка «є», коли функція називає її будь-де (читає, пише, перелічує іншим переліком)
            є = ключі | з["ключі"] | з["сталі"]
            if сусіди(з, файл, рядок, мм, рег):
                continue
            плитки = рег.плитки_ua if простір_ua else рег.плитки_en
            губить = {б: "пара форм `%s`↔`%s`" % (а, б) for а, б in рег.пари if а in є and б not in є and б in її}
            if плитки and len(ключі & плитки) * 2 >= len(плитки):
                for п in sorted(плитки - є):
                    губить.setdefault(п, "плитка її екрана поза переліком (бере %d з %d плиток)"
                                      % (len(ключі & плитки), len(плитки)))
            губить = {к: v for к, v in губить.items() if к not in ГОДИНИ}
            if not губить:
                continue
            бачені.add((файл, рядок))
            чому = "; ".join("`%s` — %s" % (к, губить[к]) for к in sorted(губить))
            місця.append((файл, рядок, 2, "`%s` у `%s` переносить поля `%s` без: %s" % (обʼєкт, ім, обʼєкт, чому)
                          if файл == ф else "перелік, яким `%s` (`%s`) переносить `%s`, губить: %s"
                          % (ім, ф, обʼєкт, чому)))
    return місця, не_місця


# ── п.3: ПОЛЕ ВИХОДУ МОДЕЛІ БЕЗ ЧИТАЧА-РІШЕННЯ ─────────────────────────────────────────────────────────────────

def поля_виходу(мм):
    """Ключі `поля_виходу` усіх оголошень задач (останній сегмент шляху) → {ключ: [(файл, рядок, шлях)]}."""
    вих = {}

    def з_вузла(м, в):
        if isinstance(в, ast.Dict):
            for к in в.keys:
                с = рядок_сталої(к) if к is not None else None
                if с:
                    ост = re.split(r"[.\[\]]+", с.strip("[]."))[-1] if re.split(r"[.\[\]]+", с.strip("[].")) else с
                    вих.setdefault(ост, []).append((м.ф, к.lineno, с))
                elif к is None:
                    з_вузла(м, в.values[в.keys.index(к)])
        elif isinstance(в, ast.Call) and імʼя_виклику(в) == "dict":
            for а in в.args:
                з_вузла(м, а)
            for кв in в.keywords:
                з_вузла(м, кв.value)
        elif isinstance(в, ast.Name) and isinstance(м.сталі.get(в.id), ast.Dict):
            з_вузла(м, м.сталі[в.id])

    for м in мм.values():
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.keyword) and в.arg == "поля_виходу":
                з_вузла(м, в.value)
    return вих


def повертає_кортеж(ф):
    for в in ast.walk(ф):
        if isinstance(в, ast.Return) and isinstance(в.value, ast.Tuple) and len(в.value.elts) >= 2 \
                and any(not (isinstance(е, ast.Constant) and е.value is None) for е in в.value.elts[1:]):
            return True
    return False


def кортеж_лише_нуль(мм, потік):
    """(а) У функції, що читає текст моделі, від кортежу функції продукту береться лише `[0]`."""
    місця = []
    for м in мм.values():
        for ім, ф in м.функції.items():
            if not any(isinstance(в, ast.Call) and імʼя_виклику(в) in РОЗБІР_ПРОТОКОЛУ for в in ast.walk(ф)):
                continue
            присвоєння = {}
            for в in ast.walk(ф):
                if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name):
                    присвоєння.setdefault(в.targets[0].id, []).append(в.lineno)
            присвоєно = []
            for в in ast.walk(ф):
                if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name):
                    # змінна тримає сам кортеж: значення — виклик (чи виклик у гілці `… if … else …`)
                    гілки = [в.value.body, в.value.orelse] if isinstance(в.value, ast.IfExp) else [в.value]
                    for вв in гілки:
                        if isinstance(вв, ast.Call) and імʼя_виклику(вв) not in РОЗБІР_ПРОТОКОЛУ:
                            ц = потік.ціль(м, вв)
                            if ц and повертає_кортеж(мм[ц[0]].функції[ц[1]]):
                                присвоєно.append((в.targets[0].id, ц, в))
            for змінна, ц, присв in sorted(присвоєно, key=lambda х: (х[0], х[2].lineno)):
                наступне = min([р for р in присвоєння[змінна] if р > присв.lineno], default=10 ** 9)
                вжитки = [в for в in ast.walk(ф) if isinstance(в, ast.Name) and в.id == змінна
                          and isinstance(в.ctx, ast.Load) and присв.lineno <= в.lineno < наступне
                          and not (в.lineno == присв.lineno and в in ast.walk(присв.value))]
                нулі, інше = [], []
                for в in вжитки:
                    п = м.б.get(в)
                    if isinstance(п, ast.Subscript) and п.value is в and isinstance(п.slice, ast.Constant):
                        (нулі if п.slice.value == 0 else інше).append(п)
                    elif isinstance(п, (ast.If, ast.IfExp, ast.BoolOp)) and в is getattr(п, "test", None) \
                            or isinstance(п, ast.UnaryOp) and isinstance(п.op, ast.Not) \
                            or isinstance(п, ast.BoolOp) \
                            or isinstance(п, ast.Call) and імʼя_виклику(п) == "isinstance":
                        continue
                    elif isinstance(п, ast.IfExp) and в is п.test:
                        continue
                    else:
                        інше.append(в)
                if нулі and not інше:
                    рядок = min(н.lineno for н in нулі)
                    місця.append((м.ф, рядок, 3, "`%s` у `%s`: від кортежу `%s.%s` береться лише `[0]` — решта "
                                  "(що функція рахує з полів відповіді) губиться" % (змінна, ім, ц[0], ц[1])))
    return місця


def зліпок_у_прозу(мм, ключі_виходу):
    """(б) Поле виходу читається з обʼєкта відповіді лише в зліпку кількох полів в один текст."""
    місця = []
    for м in мм.values():
        for ім, ф in м.функції.items():
            кладе = set()
            for в in ast.walk(ф):
                if isinstance(в, ast.Assign):
                    for ц in в.targets:
                        if isinstance(ц, ast.Subscript):
                            к = рядок_сталої(ц.slice)
                            if к:
                                кладе.add(к)
                if isinstance(в, ast.Dict):
                    кладе |= {рядок_сталої(к) for к in в.keys if к is not None and рядок_сталої(к)}
                if isinstance(в, ast.Call) and імʼя_виклику(в) == "dict":
                    кладе |= {кв.arg for кв in в.keywords if кв.arg}
            for в in ast.walk(ф):
                if not isinstance(в, (ast.ListComp, ast.GeneratorExp)) or len(в.generators) != 1:
                    continue
                г = в.generators[0]
                перелік, _ = літерал_переліку(м, мм, г.iter)
                if перелік is None or not isinstance(г.target, ast.Name):
                    continue
                ключі = ключі_переліку(перелік)
                if len(ключі) < 2:
                    continue
                читає = [вв for вв in ast.walk(в.elt) if isinstance(вв, (ast.Subscript, ast.Call))
                         and ((isinstance(вв, ast.Subscript) and isinstance(вв.slice, ast.Name)
                               and вв.slice.id == г.target.id)
                              or (isinstance(вв, ast.Call) and isinstance(вв.func, ast.Attribute)
                                  and вв.func.attr == "get" and вв.args and isinstance(вв.args[0], ast.Name)
                                  and вв.args[0].id == г.target.id))]
                if not читає:
                    continue
                # зліпок полів ОДНІЄЇ відповіді: усі ключі — поля виходу під тим самим шляхом одного оголошення
                # (`образи[].підпис`, `образи[].чому`…); пари-синоніми (`id`/`ід`) і поля речі каталогу — ні
                лік = {}
                for к in ключі:
                    for пр in {д[2].rsplit(к, 1)[0] for д in ключі_виходу.get(к, [])}:
                        лік.setdefault(пр, set()).add(к)
                спільні = {пр: кк for пр, кк in лік.items() if len(кк) >= 2 and len(кк) * 3 >= len(ключі) * 2}
                if not спільні:
                    continue
                for к in sorted(set().union(*спільні.values())):
                    if к not in кладе:
                        де = next(д for д in ключі_виходу[к] if д[2].rsplit(к, 1)[0] in спільні)
                        місця.append((м.ф, в.lineno, 3, "поле виходу `%s` (%s:%s) `%s` читає лише в зліпку %s в один "
                                      "текст і окремим ключем не кладе" % (де[2], де[0], де[1], ім, ключі)))
    return місця


def поля_розбору_каталогу(мм):
    """Поля схеми розбору каталогу (`каталог_розбір`): перший елемент кортежів-описів (`("pattern", коди, "…")`)."""
    м = мм.get("каталог_розбір")
    вих = {}
    if not м:
        return вих, None
    for в in ast.walk(м.дерево):
        if isinstance(в, ast.Tuple) and len(в.elts) == 3 and (рядок_сталої(в.elts[2]) is not None
                                                            or isinstance(в.elts[2], ast.Name)):
            перше = в.elts[0]
            с = рядок_сталої(перше)
            if с is None and isinstance(перше, ast.BinOp) and isinstance(перше.op, ast.Mod):
                с = рядок_сталої(перше.left)
            if с:
                верх = re.split(r"[.\[%]", с)[0]
                if верх and re.match(r"^[a-z_]+$", верх):
                    вих.setdefault(верх, в.lineno)
    return вих, м


def не_пише_модель(мр, мм):
    """Поля схеми розбору, яких модель не пише: `[… for ш, … in ПОЛЯ if ш not in X]` у самому розборі."""
    вих = set()
    for в in ast.walk(мр.дерево):
        if isinstance(в, ast.comprehension):
            for у in в.ifs:
                if isinstance(у, ast.Compare) and len(у.ops) == 1 and isinstance(у.ops[0], ast.NotIn):
                    пр = у.comparators[0]
                    if isinstance(пр, ast.Name) and isinstance(мр.сталі.get(пр.id), ast.Call) \
                            and імʼя_виклику(мр.сталі[пр.id]) in ("frozenset", "set", "tuple") and мр.сталі[пр.id].args:
                        пр = мр.сталі[пр.id].args[0]
                    перелік, _ = літерал_переліку(мр, мм, пр)
                    if перелік is not None:
                        вих |= set(ключі_переліку(перелік))
    return вих


def пропускає(м, мм):
    """Ключі, які код безумовно пропускає, переносячи обʼєкт: `for к, v in X.items(): if к in ПЕРЕЛІК: continue`
    чи `{к: … for к, v in X.items() if к not in ПЕРЕЛІК}` → {ключ: рядок}."""
    вих = {}
    for в in ast.walk(м.дерево):
        if not (isinstance(в, (ast.For, ast.comprehension)) and isinstance(в.iter, ast.Call)
                and isinstance(в.iter.func, ast.Attribute) and в.iter.func.attr == "items"
                and isinstance(в.target, ast.Tuple) and isinstance(в.target.elts[0], ast.Name)):
            continue
        к_ім = в.target.elts[0].id
        умови = []
        if isinstance(в, ast.For):
            умови = [(с.test, ast.In) for с in в.body if isinstance(с, ast.If) and len(с.body) == 1
                     and isinstance(с.body[0], ast.Continue)]
        else:
            умови = [(у, ast.NotIn) for у in в.ifs]
        for у, оп in умови:
            if isinstance(у, ast.Compare) and isinstance(у.left, ast.Name) and у.left.id == к_ім \
                    and len(у.ops) == 1 and isinstance(у.ops[0], оп):
                перелік, _ = літерал_переліку(м, мм, у.comparators[0])
                if перелік is not None:
                    for к in ключі_переліку(перелік):
                        вих.setdefault(к, у.lineno)
    return вих


def знято_дротом(мм, рег):
    """(в) Поле, яке модель пише в розборі каталогу, код безумовно пропускає, переносячи запис, а читача ключа поза
    розбором нема (порівняння форми й стискач — не читачі)."""
    поля, мр = поля_розбору_каталогу(мм)
    місця = []
    if not мр:
        return місця
    поля = {к: р for к, р in поля.items() if к not in не_пише_модель(мр, мм)}
    js = "\n".join(т for _, т in файли_js())
    пропущені = {}
    for м in мм.values():
        if м.ім.startswith("каталог_розбір"):
            continue
        for к, р in пропускає(м, мм).items():
            if к in поля:
                пропущені.setdefault(к, (м.ф, р))
    for ключ, де in sorted(пропущені.items()):
        читачі = [(м.ф, в.lineno) for м in мм.values() if not м.ім.startswith("каталог_розбір")
                  for в in ast.walk(м.дерево) if (ключ_читання(в) or (None, None))[1] == ключ]
        if re.search(r"\.%s\b|\[['\"]%s['\"]\]" % (ключ, ключ), js):
            читачі.append(("js", 0))
        if not читачі:
            місця.append((мр.ф, поля[ключ], 3, "поле розбору каталогу `%s`: модель пише, код пропускає його завжди "
                          "(%s:%s), а читача ключа поза розбором нема" % (ключ, де[0], де[1])))
    return місця


# ── п.4: ПОЛЕ ЗАПИСУ КАТАЛОГУ ──────────────────────────────────────────────────────────────────────────────────

def теги_складальника(мм):
    м = мм.get("складальник")
    вих = {}
    if not м:
        return вих, None
    д = м.сталі.get("ТЕГИ")
    if isinstance(д, ast.Tuple):
        for е in д.elts:
            if isinstance(е, ast.Tuple) and len(е.elts) == 2 and рядок_сталої(е.elts[1]):
                вих[рядок_сталої(е.elts[1])] = е.lineno
    for в in ast.walk(м.дерево):
        с = рядок_сталої(в)
        if с:
            for тег in re.findall(r"<([a-zA-Z]+)>%s</\1>", с):
                вих.setdefault(тег, в.lineno)
    return вих, м


def поля_каталогу(мм):
    місця, не_місця = [], []
    теги, мс = теги_складальника(мм)
    мф = мм.get("фід_розбір")
    if not теги or not мф:
        return місця, не_місця
    бере = set()
    for в in ast.walk(мф.дерево):
        if isinstance(в, ast.Call) and імʼя_виклику(в) in ("findtext", "findall", "find", "iter") and в.args:
            с = рядок_сталої(в.args[0])
            if с:
                бере.add(с)
            elif isinstance(в.args[0], ast.Name):
                # `for поле, мітка in (("article", …), …): o.findtext(поле)` — поле з переліку циклу
                for цикл in ast.walk(мф.дерево):
                    if isinstance(цикл, ast.For) and в in ast.walk(цикл):
                        цілі = цикл.target.elts if isinstance(цикл.target, ast.Tuple) else [цикл.target]
                        for поз, ц in enumerate(цілі):
                            if isinstance(ц, ast.Name) and ц.id == в.args[0].id:
                                перелік, _ = літерал_переліку(мф, мм, цикл.iter)
                                if перелік is not None:
                                    бере |= set(ключі_переліку(перелік, поз))
    шлях = os.path.join(КОРІНЬ, "каталог_повний.xml.gz")
    лічба, значення, усього = {}, {}, 0
    if os.path.exists(шлях):
        with gzip.open(шлях, "rt", encoding="utf-8", errors="replace") as ф:
            текст = ф.read()
        оф = re.findall(r"<offer\b[^>]*>(.*?)</offer>", текст, re.S)
        усього = len(оф)
        for тег in теги:
            if тег in бере:
                continue
            зн = [з.strip() for о in оф for з in re.findall(r"<%s>(.*?)</%s>" % (тег, тег), о, re.S) if з.strip()]
            лічба[тег], значення[тег] = len(зн), len(set(зн))
    for тег, рядок in sorted(теги.items()):
        if тег in бере:
            continue
        н = лічба.get(тег, 0)
        if тег == "description":
            не_місця.append((мс.ф, рядок, 4, "тег `<%s>` (%d з %d записів) фід не бере — рішення менеджера 31.10: опис "
                             "до розбору з цитатами не підключається" % (тег, н, усього)))
        elif значення.get(тег, 0) <= 1:
            не_місця.append((мс.ф, рядок, 4, "тег `<%s>` має одне значення на всіх %d записах — значення не несе"
                             % (тег, н)))
        else:
            місця.append((мс.ф, рядок, 4, "тег `<%s>` пише складальник (%d з %d записів, %d значень), фід "
                          "(`фід_розбір.py`) його не бере" % (тег, н, усього, значення.get(тег, 0))))
    return місця, не_місця


# ── п.5: ЧИТАЧ БЕРЕ НЕ ТЕ ЗНАЧЕННЯ ─────────────────────────────────────────────────────────────────────────────

def виклики_функцій(мм, потік):
    """(модуль, функція) → [(модуль виклику, вузол)] для всіх викликів функцій продукту."""
    вих = {}
    for м in мм.values():
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.Call):
                ц = потік.ціль(м, в)
                if ц:
                    вих.setdefault(ц, []).append((м, в))
    return вих


def поле_паспорта_в(вузол, рег):
    for в in ast.walk(вузол):
        кч = ключ_читання(в)
        if кч and кч[1] in (рег.її_ua | рег.її_en) - ГОДИНИ:
            return кч[1]
    return None


def не_те_значення(мм, потік, рег):
    місця = []
    виклики = виклики_функцій(мм, потік)
    for ц, вв in sorted(виклики.items(), key=lambda х: х[0]):
        ф = мм[ц[0]].функції[ц[1]]
        пар = [а.arg for а in ф.args.posonlyargs + ф.args.args]
        if "." in ц[1] and пар and пар[0] in ("self", "cls"):
            пар = пар[1:]
        # (а) те саме значення двом параметрам, а інші виклики дають їм різне
        розклад = []
        for м, в in вв:
            арг = {}
            for і, а in enumerate(в.args):
                if isinstance(а, ast.Starred) or і >= len(пар):
                    break
                арг[пар[і]] = а
            for кв in в.keywords:
                if кв.arg:
                    арг[кв.arg] = кв.value
            розклад.append((м, в, арг))
        # обидва параметри — обʼєкти, з яких функція читає ключі (`.get`/`[…]`): різні носії полів
        носії = {кч[0].id for кч in (ключ_читання(в) for в in ast.walk(ф)) if кч and isinstance(кч[0], ast.Name)}
        носії |= {в.func.value.id for в in ast.walk(ф) if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute)
                  and в.func.attr == "get" and isinstance(в.func.value, ast.Name)}
        # копія параметра (`с = dict(сцен or {})`, `с, п = dict(а or {}), dict(б or {})`) несе його поля
        def джерело_копії(вир):
            while isinstance(вир, ast.Call) and імʼя_виклику(вир) == "dict" and len(вир.args) == 1:
                вир = вир.args[0]
            if isinstance(вир, ast.BoolOp) and isinstance(вир.op, ast.Or):
                вир = вир.values[0]
            return вир.id if isinstance(вир, ast.Name) and вир.id in пар else None
        for в in ast.walk(ф):
            if isinstance(в, ast.Assign) and len(в.targets) == 1:
                ц0, з0 = в.targets[0], в.value
                пари = list(zip(ц0.elts, з0.elts)) if isinstance(ц0, ast.Tuple) and isinstance(з0, ast.Tuple) \
                    and len(ц0.elts) == len(з0.elts) else [(ц0, з0)]
                for ціль_, знач in пари:
                    дж = джерело_копії(знач)
                    if дж and isinstance(ціль_, ast.Name) and ціль_.id in носії:
                        носії.add(дж)
        for м, в, арг in розклад:
            імена = sorted(п for п in арг if п in носії)
            for і, а in enumerate(імена):
                for б in імена[і + 1:]:
                    ва, вб = арг[а], арг[б]
                    if isinstance(ва, ast.Constant) or ast.unparse(ва) != ast.unparse(вб):
                        continue
                    інші = [1 for м2, в2, а2 in розклад if в2 is not в and а in а2 and б in а2
                            and ast.unparse(а2[а]) != ast.unparse(а2[б])]
                    if інші:
                        місця.append((м.ф, в.lineno, 5, "`%s(…)` дає те саме `%s` параметрам `%s` і `%s`, а %d інших "
                                      "викликів — різні значення" % (ц[1], ast.unparse(ва)[:40], а, б, len(інші))))
        # (б) параметр із полем її паспорта, якого тіло не читає
        читає = {в.id for в in ast.walk(ф) if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Load)}
        for п in пар:
            if п in читає or п.startswith("_") or п in ("self", "cls"):
                continue
            поля = sorted({поле_паспорта_в(арг[п], рег) for м, в, арг in розклад if п in арг} - {None})
            if поля:
                місця.append((мм[ц[0]].ф, ф.lineno, 5, "`%s` не читає параметра `%s`, а виклики дають у нього її поле "
                              "%s" % (ц[1], п, ", ".join("`%s`" % х for х in поля))))
    return місця


# ── ЗБІР І ВИВІД ───────────────────────────────────────────────────────────────────────────────────────────────

def зібрати():
    мм = зібрати_модулі()
    рег = Реєстри(мм)
    потік = ПотікСлів(мм, рег)
    місця, не_місця = [], []
    for м_, н_ in (зрізи_python(мм, потік), зрізи_js(), переліки_писача(мм, рег), поля_каталогу(мм)):
        місця += м_
        не_місця += н_
    ключі_виходу = поля_виходу(мм)
    місця += кортеж_лише_нуль(мм, потік) + зліпок_у_прозу(мм, ключі_виходу) + знято_дротом(мм, рег)
    місця += не_те_значення(мм, потік, рег)
    інфо = {"модулів": len(мм), "слова": sorted(рег.слова), "пари": sorted(рег.пари),
            "плитки": sorted(рег.плитки_ua), "входи": sorted(рег.входи)}
    return sorted(set(місця)), sorted(set(не_місця)), інфо


def main():
    місця, не_місця, інфо = зібрати()
    різні = sorted({(ф, р) for ф, р, _, _ in місця})
    if "--json" in sys.argv:
        print(json.dumps({"місця": місця, "не_місця": не_місця, "інфо": інфо}, ensure_ascii=False, indent=1))
    elif "--тихо" not in sys.argv:
        print("Корінь Е2-втрата-слова — прилад: модулів продукту %d" % інфо["модулів"])
        print("джерела її слів (ключі): %s" % ", ".join(інфо["слова"]))
        print("пари форм: %s; плиток її екрана: %d" % (", ".join("%s↔%s" % п for п in інфо["пари"] if п[0] < п[1]),
                                                       len(інфо["плитки"])))
        print()
        for ф, р, п, чому in місця:
            print("%s:%s · п.%d · %s" % (ф, р, п, чому))
        print()
        for п in sorted(ПУНКТИ):
            print("п.%d %s: %d" % (п, ПУНКТИ[п], len({(ф, р) for ф, р, пп, _ in місця if пп == п})))
        print()
        print("не місця (%d):" % len(не_місця))
        for ф, р, п, чому in не_місця:
            print("  %s:%s · п.%d · %s" % (ф, р, п, чому))
    print("місць: %d" % len(різні))
    return 0


if __name__ == "__main__":
    sys.exit(main())
