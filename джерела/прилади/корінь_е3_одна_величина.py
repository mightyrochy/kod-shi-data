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
     (г) та сама величина (однаковий вираз з тих самих полів після підстановки одноразових локальних присвоєнь) у
     двох функціях: одна зве її бік порівнянням з ненульовою межею, друга в інструкції з цією величиною пише
     «невідомо»/«unknown» — місце кожне таке порівняння й кожен такий рядок; функції, що кличуть першу (читачі її
     відповіді), — не місця;
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
  6  порівняння двох боків (річ і тіло, два виміри) без похибки обох боків чи вимір мінус оцінка іншої величини.
     Боки — значенням: тіло — поля запису, який повертає функція, що ділить на π чи кличе таку (`fit.тіло`):
     `профіль` (рядки; позиція 2 — ширина як обхват/π), контейнери (`обхвати`, `висоти`) і скаляри; річ — ключ з
     одиницею (`_см`, `_мм`) не з реєстру; похибка — мітка, чиє імʼя каже «розкид/похибка/допуск/шум». Мітки йдуть
     потоком через присвоєння, параметри (обʼєднання з усіх викликів), повернення (позиційно для кортежів) і ключі
     з одиницею; різниця чи частка двох різних вимірів дістає мітку «два боки», добуток частки на вимір — ні
     (інтерполяція профілю — вимір у точці). (а) порівняння `< <= > >=`, де операнди несуть різні виміри чи один —
     різницю двох, а похибки обох боків нема; (б) віднімання, де один бік — вимір речі, а другий — оцінка тіла через
     π; (в) заява правила з силою вироку, яку стереже лише наявність обох боків (`if річ is None or тіло is None`
     з виходом чи з `else`); (г) читач «невідомо» з порівняння (рішення менеджера 07.11): від кожного порівняння
     п.6 з похибкою (місця й виправлені) відповідь іде потоком (повернення, кортеж, поле словника, перелік,
     відфільтрований нею) до умови `if`/`elif`/`while`/виразу-вибору; місце — читач, що на «невідомо» виходить з правила
     без «утримано» й заяви (`continue`, `break`, `return`, `pass`), дає вирок чи мовчить умовою на істинність (вирок
     лише на «так», далі нема «утримано»), — одне на читача; де потік не розрізняє — таблиця вердиктів у приладі, читач
     поза нею — «п.?». За керуванням (рішення 07.11, 13967): перелік, поле чи імʼя, яке пише лише гілка «так» умови на
     відповідь, коли гілка «невідомо» нічого не пише, несе відповідь порожнечею; наповнювач — не місце, місце — умова,
     що на порожнечі мовчить без заяви «не судить», і поле, що несе порожнечу назовні (код продукту його не читає).
     Не місця (окремий розділ виводу з причиною): похибку обох боків враховано; гілка
     лише кидає виняток (межа області визначення даних); порівняння вибирає силу правила (корінь
     `Е3-сила-правила`) чи належить іншому кореню за текстом. Лише Python: JS і HTML `джерела/` вимірів см не
     порівнюють (06.11).
  7  орієнтир величини тіла (менеджер 06.11, 13854–13856) задає не означення бази знань (тема-1 §2.1 — груди,
     талія, високе стегно, стегна; коліно — «bisect the kneecap», щиколотка — «narrowest point» з рішення), а де його
     нема — не джерело з посиланням, чи форма, шаблон і правила під одним іменем мають різні орієнтири. Місце — точка,
     що означує орієнтир: (а) рівень шаблону — частка зросту в таблиці (імʼя, частка), яку код множить на зріст, без
     посилання (0 і 1 — межі зросту); похідний рівень — точка тіла, названа словом, як середина двох рівнів; поле
     обхвату форми (HTML, ключ — пара JS) без орієнтира чи з ознакою без бази й джерела; питання жінці «обхват
     <рівня> <де>» так само; (б) ознака орієнтира (найширше, найвужче, природна талія, наколінок, відстань…) не та,
     що в базі, чи слово таблиці орієнтирів читає рівень, а його код — інша точка тіла (`upper_thigh` на високе
     стегно); (в) точка чи слово речі на рівні тіла (менеджер 06.11, #3233): таблиця «слово речі → рівень» (довжина,
     посадка, клас шкали довжини, що позичає імена рівнів, і його точки на тілі — тотожний клас теж) і вбудована
     відповідність (`IfExp` з рівнем поряд із такою таблицею) без означення бази чи джерела з посиланням, чи з
     означенням бази, що кладе цю точку речі деінде (`midi` — «narrowest point of the calf»). Означення бази — будь-яке
     місце бази знань, що називає точку тіла (ознака + іменник, «at its widest», `mid-<іменник>`); одне імʼя з двома
     точками в базі (литка: K-SHO-05 найширша, K-SIL-10 найвужча) — дві величини, друкуються окремим рядком.
     Читач рівня (порівнює з рівнем уже покладену точку), таблиця «рівень → слово тіла» і `__main__` — не місця.

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
`місць: <N>` (N — різних `файл:рядок`), код 0; перед ним — розбивка «за файлами й пунктами» (для частин
без спільних файлів) і не місця п.1(г), п.6 і п.7 з причиною. Запуск з кореня репозиторію (чи `--корінь <шлях>`):
    python3 джерела/прилади/корінь_е3_одна_величина.py [--тихо] [--величини] [--самоперевірка]
"""
import ast
import math
import os
import re
import shutil
import sys
import tempfile
import warnings

import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

# ── межі обходу ─────────────────────────────────────────────────────────────────────────────────────────────────
# `лабораторія/` — код без входу на живому шляху (її `__init__`: ядро звідти не імпортує нічого) — значення звідти не
# доходить ні до правила, ні до моделі
ПОЗА_ТЕКИ = {"проби", "прилади", "node_modules", "__pycache__", "лабораторія"}
# Стенди, аудити й прогони поза продуктом (`status.МОДУЛІ_ПРОДУКТУ` їх не має; `status` сам називає `audit_contracts`,
# `gate_reach`, `pair_test`, `rule_genus`, `run_outfit` приладами): паспорт — «проби, прилади, стенди й тести — ні».
ТЕСТ = re.compile(r"^(тест|test|стенд|батарея|gate_|pair_test|проба|audit_|аудит_|measure_|мутант|звірка|досяжність"
                  r"|гейти_|run_outfit|rule_genus|status_перевірки|траса_|відбиток|зведення)|(_test|_тест)\.|\.test\.",
                  re.IGNORECASE)
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
    "скільки", "кількість", "лишити", "top", "topk", "top_k", "lang", "мова", "format", "формат", "flag", "прапор", "on", "off", "enabled", "show", "hide",
}
ОБГОРТКИ = {"float", "int", "round", "abs", "str", "bool"}
ГЛИБИНА_СЛІДУ = 10     # кроків сліду джерела значення (параметр → виклик, ключ → писач, виклик → повернення)
ВУЗОЛ_ХАБ = 6          # різних імен-сусідів потоку понад це — ім'я несе різні значення, не одну величину
# Величини інших коренів (одиниця з імені чи константи — паспорт: «одиниці — з реєстру чи імені»).
ІНШІ_КОРЕНІ = (
    ("Е2-смуга-погоди", re.compile(r"темп|temp|градус|°|_c$|_c_|погод|weather|feel|відчутт|мороз|холод|тепл", re.I)),
    ("Е2-частина-дня", re.compile(r"годин|hour|хвилин|minute|частина_дня|part_of_day|пора\b", re.I)),
    ("тривалість і дата", re.compile(r"тривал|duration|дата|date|днів|days|місяц|month|рок|year|секунд|second|мс\b|ms$|"
                                      r"timeout|тайм|_ms_|_мс", re.I)),
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
    """Літерал типового (рядок чи число) → значення, інакше None.

    Не величина: прапор (True/False — вибір поведінки виклику, не значення поля чи межі), нейтраль 0 і 1 (порожня
    сума, множник «без зміни», запобіжник ділення `or 1`) і заповнювач («?», «—», «null» — показ відсутності)."""
    if порожнє(в) or (isinstance(в, ast.Constant) and isinstance(в.value, bool)):
        return None
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return в.value if значуще_типове(в.value) else None
    ч = в.value if isinstance(в, ast.Constant) and isinstance(в.value, (int, float)) else число(в)
    return None if ч is None or ч in (0, 1) else ч


ШИРОКА = 6   # вузол, що з'єднує понад стільки імен, — не одна величина
КОД_СЛОВНИКА = re.compile(r"[a-z][a-z0-9_]{2,}")
ЗАПОВНЮВАЧІ = {"null", "undefined", "none", "nan", "нема", "немає", "жодного", "жодної", "жодних", "порожньо"}


def значуще_типове(зн):
    if isinstance(зн, str):
        return bool(re.search(r"\w", зн)) and зн.strip().lower() not in ЗАПОВНЮВАЧІ
    return зн not in (0, 1)


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
                            сире = кв["val"]
                            межі = [число(сире)] if not isinstance(сире, (ast.Tuple, ast.List)) else \
                                [число(е) for е in сире.elts]
                            записи[к.value] = dict(рядок=к.lineno, val=число(сире),
                                                   межа=bool(межі) and all(ч is not None for ч in межі),
                                                   val_текст=ast.unparse(сире)[:30],
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
                    except SyntaxError as е:
                        ОБСЯГ.непрочитано(відн, "SyntaxError: %s" % е)
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


def вимкнені_правила(м, словник):
    """Таблиця «ід → чому правило вимкнено» (`ВИМКНЕНІ_ПРАВИЛА`): текст у ній — причина, не дія правила. Прилад
    порівнює дії під ідом, не слова описів (рішення менеджера 01.11, K-CRA-04: під ід одна дія — крок редагування)."""
    б = м.батько.get(словник)
    цілі = б.targets if isinstance(б, ast.Assign) else [б.target] if isinstance(б, ast.AnnAssign) else []
    return any(isinstance(ц, ast.Name) and ц.id.startswith("ВИМКНЕНІ") for ц in цілі)


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
                        if " " in т.strip() and not вимкнені_правила(м, в):
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
    except Exception as е:
        ОБСЯГ.непрочитано_модуль(дж, "правила", "формулювання(): %s: %s" % (type(е).__name__, е))
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
                    цілі = визначення_в(л, мод, ім)     # повторний експорт (`pipeline` → `повнота_образу`)
                    if len(цілі) == 1:
                        мод = цілі[0][0].ім
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
                        вих.append((м, м.функція(в), в.lineno, frozenset(е.value for е in г.iter.elts), frozenset()))
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
                    дротові = frozenset(к.value for к in в.keys if isinstance(к, ast.Constant) and isinstance(к.value, str))
                    вих.append((м, м.функція(в), в.lineno, frozenset(ключі), дротові))
    return вих


# ── п.3: ключ пари, другий писач запису, читач відсутності ─────────────────────────────────────────────────────
def _get_поле(в):
    """`X.get("F")` / `X["F"]` → F, інакше None."""
    if isinstance(в, ast.Call) and назва_виклику(в) == "get" and isinstance(в.func, ast.Attribute) and в.args \
            and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
        return в.args[0].value
    if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and isinstance(в.slice.value, str):
        return в.slice.value
    return None


def _читає_поле(в, ім=None):
    """Поля, які вираз читає `X.get("F")` (X — ім'я `ім`, коли задано)."""
    вих = set()
    for п in ast.walk(в):
        f = _get_поле(п)
        if f is None:
            continue
        база = п.func.value if isinstance(п, ast.Call) else п.value
        if ім is None or (isinstance(база, ast.Name) and база.id == ім):
            вих.add(f)
    return вих


def джерело_збірки(л, м, ф, в, глибина=0, з_батьком=False):
    """Поле, з якого походить збірка: `X.get("образи")`, перелік над ним, локальне ім'я чи параметр (через виклики
    свого модуля) → «образи», інакше None."""
    if в is None or глибина > ГЛИБИНА_СЛІДУ:
        return None
    f = _get_поле(в)
    if f is not None:
        return f if not з_батьком else (обʼєкт_збірки(л, м, ф, в.func.value if isinstance(в, ast.Call) else в.value,
                                                     глибина + 1), f)
    if isinstance(в, (ast.BoolOp, ast.IfExp)):
        гілки = в.values if isinstance(в, ast.BoolOp) else (в.body, в.orelse)
        return next((д for д in (джерело_збірки(л, м, ф, x, глибина + 1, з_батьком) for x in гілки) if д), None)
    if isinstance(в, (ast.ListComp, ast.GeneratorExp, ast.SetComp)):
        # елемент — з останнього генератора: `[z for о in обр for z in о["знахідки"]]` — знахідки, не образи
        return джерело_збірки(л, м, ф, в.generators[-1].iter, глибина + 1, з_батьком)
    if isinstance(в, ast.Call) and назва_виклику(в) in ("enumerate", "list", "tuple", "sorted", "reversed") and в.args:
        return джерело_збірки(л, м, ф, в.args[0], глибина + 1, з_батьком)
    if isinstance(в, ast.Call) and назва_виклику(в) == "range" and в.args and isinstance(в.args[0], ast.Call) \
            and назва_виклику(в.args[0]) == "len" and в.args[0].args:
        return джерело_збірки(л, м, ф, в.args[0].args[0], глибина + 1, з_батьком)
    if isinstance(в, ast.Name):
        while ф is not None:
            if isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                присв = [п.value for п in ast.walk(ф) if isinstance(п, ast.Assign)
                         and any(isinstance(ц, ast.Name) and ц.id == в.id for ц in п.targets)]
                if присв:
                    return next((д for д in (джерело_збірки(л, м, ф, x, глибина + 1, з_батьком) for x in присв) if д), None)
                параметри = [а.arg for а in ф.args.posonlyargs + ф.args.args]
                if в.id in параметри:
                    і = параметри.index(в.id)
                    for мм, фф, виклик in виклики(л).get((м.ім, ф.name), []):
                        if і < len(виклик.args):
                            д = джерело_збірки(л, мм, фф, виклик.args[і], глибина + 1, з_батьком)
                            if д:
                                return д
                    return None
            ф = м.функція(ф)
    return None


def обʼєкт_збірки(л, м, ф, в, глибина=0):
    """Чий це перелік: ключ, з якого взято обʼєкт (`d.get("попередній_вердикт")` → «попередній_вердикт»), через
    локальне ім'я чи параметр (аргументи викликів свого модуля); ключа нема ні на одному шляху — ім'я параметра."""
    return _обʼєкт(л, м, ф, в, глибина, False) or _обʼєкт(л, м, ф, в, глибина, True)


def _обʼєкт(л, м, ф, в, глибина, запасне):
    if в is None or глибина > ГЛИБИНА_СЛІДУ:
        return None
    f = _get_поле(в)
    if f is not None:
        return f
    if isinstance(в, (ast.BoolOp, ast.IfExp)):
        гілки = в.values if isinstance(в, ast.BoolOp) else (в.body, в.orelse)
        return next((д for д in (_обʼєкт(л, м, ф, x, глибина + 1, запасне) for x in гілки
                                 if not isinstance(x, (ast.Dict, ast.Constant))) if д), None)
    if isinstance(в, ast.Name):
        while ф is not None:
            if isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                присв = [п.value for п in ast.walk(ф) if isinstance(п, ast.Assign)
                         and any(isinstance(ц, ast.Name) and ц.id == в.id for ц in п.targets)]
                if присв:
                    return next((д for д in (_обʼєкт(л, м, ф, x, глибина + 1, запасне) for x in присв) if д), None)
                параметри = [а.arg for а in ф.args.posonlyargs + ф.args.args]
                if в.id in параметри:
                    і = параметри.index(в.id)
                    for мм, фф, виклик in виклики(л).get((м.ім, ф.name), []):
                        if і < len(виклик.args):
                            д = _обʼєкт(л, мм, фф, виклик.args[і], глибина + 1, запасне)
                            if д:
                                return д
                    return в.id if запасне else None
            ф = м.функція(ф)
    return None


def пари_збірок(л):
    """Місця, де елементу однієї збірки шукають пару в іншій: індекс `{f(x.get("F")): x for x in C}` і його
    читання, `next(… for x in C if x.get("F") == o.get("F"))`, `max(C, key=… len(A & B) …)` →
    [(файл, рядок, поле збірки, вид пари)]."""
    вих = []
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            ф = м.функція(в)
            if isinstance(в, ast.DictComp) and len(в.generators) == 1 and isinstance(в.generators[0].target, ast.Name):
                ц = в.generators[0].target.id
                if isinstance(в.value, ast.Name) and в.value.id == ц and _читає_поле(в.key, ц):
                    зб = джерело_збірки(л, м, ф, в.generators[0].iter, з_батьком=True)
                    if not зб or not зб[0]:
                        continue
                    вид = "полем «%s»" % ", ".join(sorted(_читає_поле(в.key, ц)))
                    батько = м.батько.get(в)
                    читання = []
                    if isinstance(батько, ast.Assign) and isinstance(батько.targets[0], ast.Name):
                        ім = батько.targets[0].id
                        обл = ф if ф is not None else м.дерево
                        читання = sorted({п.lineno for п in ast.walk(обл)
                                          if (isinstance(п, ast.Call) and назва_виклику(п) == "get"
                                              and isinstance(п.func, ast.Attribute)
                                              and isinstance(п.func.value, ast.Name) and п.func.value.id == ім)
                                          or (isinstance(п, ast.Subscript) and isinstance(п.value, ast.Name)
                                              and п.value.id == ім and isinstance(п.ctx, ast.Load))})
                    for р in читання or [в.lineno]:
                        вих.append((м.шлях, р, зб, вид))
            elif isinstance(в, (ast.GeneratorExp, ast.ListComp)) and len(в.generators) == 1:
                г = в.generators[0]
                цілі = [г.target.id] if isinstance(г.target, ast.Name) else \
                    [е.id for е in getattr(г.target, "elts", []) if isinstance(е, ast.Name)]
                for умова in г.ifs:
                    for п in ast.walk(умова):
                        if isinstance(п, ast.Compare) and len(п.ops) == 1 and isinstance(п.ops[0], ast.Eq):
                            ліве, праве = _читає_поле(п.left), _читає_поле(п.comparators[0])
                            спільне = ліве & праве
                            свої = set().union(*(_читає_поле(п.left, ц) | _читає_поле(п.comparators[0], ц)
                                                 for ц in цілі)) if цілі else set()
                            if спільне and спільне & свої:
                                зб = джерело_збірки(л, м, ф, г.iter, з_батьком=True)
                                if зб and зб[0]:
                                    вих.append((м.шлях, п.lineno, зб, "полем «%s»" % ", ".join(sorted(спільне))))
            elif isinstance(в, ast.Call) and назва_виклику(в) in ("max", "min") and isinstance(в.func, ast.Name) \
                    and в.args:
                ключ = next((кл.value for кл in в.keywords if кл.arg == "key"), None)
                if ключ is not None and any(isinstance(п, ast.Call) and назва_виклику(п) == "len" and п.args
                                            and isinstance(п.args[0], ast.BinOp)
                                            and isinstance(п.args[0].op, ast.BitAnd) for п in ast.walk(ключ)):
                    зб = джерело_збірки(л, м, ф, в.args[0], з_батьком=True)
                    if зб and зб[0]:
                        вих.append((м.шлях, в.lineno, зб, "найбільшим перетином складу"))
    return вих


def записи_поверх(л):
    """Другий писач запису: `D = dict(X.get("F") or {})`, далі `D["K"] = …` чи цикл `for к, з in (("K", …), …):
    D[к] = з` → {F: {K: (файл, рядок)}}."""
    вих = {}
    for м in л.модулі:
        for ф in ast.walk(м.дерево):
            if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            копії = {}
            for п in ast.walk(ф):
                if isinstance(п, ast.Assign) and len(п.targets) == 1 and isinstance(п.targets[0], ast.Name) \
                        and isinstance(п.value, ast.Call) and назва_виклику(п.value) == "dict" and п.value.args:
                    а = п.value.args[0]
                    а = а.values[0] if isinstance(а, ast.BoolOp) else а
                    f = _get_поле(а)
                    if f:
                        копії[п.targets[0].id] = f
            if not копії:
                continue
            for п in ast.walk(ф):
                if isinstance(п, ast.Assign) and len(п.targets) == 1 and isinstance(п.targets[0], ast.Subscript) \
                        and isinstance(п.targets[0].value, ast.Name) and п.targets[0].value.id in копії:
                    сл = п.targets[0].slice
                    f = копії[п.targets[0].value.id]
                    if isinstance(сл, ast.Constant) and isinstance(сл.value, str):
                        вих.setdefault(f, {}).setdefault(сл.value, (м.шлях, п.lineno))
                    elif isinstance(сл, ast.Name):
                        цикл = м.батько.get(п)
                        while цикл is not None and not isinstance(цикл, ast.For):
                            цикл = м.батько.get(цикл)
                        if цикл is not None and isinstance(цикл.iter, (ast.Tuple, ast.List)) \
                                and isinstance(цикл.target, ast.Tuple) and isinstance(цикл.target.elts[0], ast.Name) \
                                and цикл.target.elts[0].id == сл.id:
                            for е in цикл.iter.elts:
                                if isinstance(е, ast.Tuple) and isinstance(е.elts[0], ast.Constant) \
                                        and isinstance(е.elts[0].value, str):
                                    вих.setdefault(f, {}).setdefault(е.elts[0].value, (м.шлях, цикл.lineno))
    return вих


def мапи_замін(л):
    """Мапа «поле одного писача → поле другого про той самий факт»: сталий словник рядок→рядок (≥ 3), який
    обходять `for к, з in М.items()` і читають `D.get(з)`, де D походить з `X.get("F")` → {F: [(файл, рядок, ім'я,
    значення)]}."""
    вих = {}
    for м in л.модулі:
        мапи = {}
        for в in м.дерево.body:
            if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name) \
                    and isinstance(в.value, ast.Dict) and len(в.value.keys) >= 3 \
                    and all(isinstance(к, ast.Constant) and isinstance(к.value, str) for к in в.value.keys) \
                    and all(isinstance(з, ast.Constant) and isinstance(з.value, str) for з in в.value.values):
                мапи[в.targets[0].id] = (в.lineno, {з.value for з in в.value.values})
        if not мапи:
            continue
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.For) and isinstance(в.iter, ast.Call) and назва_виклику(в.iter) == "items" \
                    and isinstance(в.iter.func, ast.Attribute) and isinstance(в.iter.func.value, ast.Name) \
                    and в.iter.func.value.id in мапи and isinstance(в.target, ast.Tuple) \
                    and isinstance(в.target.elts[1], ast.Name):
                з = в.target.elts[1].id
                for п in ast.walk(в):
                    if isinstance(п, ast.Call) and назва_виклику(п) == "get" and isinstance(п.func, ast.Attribute) \
                            and isinstance(п.func.value, ast.Name) and п.args and isinstance(п.args[0], ast.Name) \
                            and п.args[0].id == з:
                        f = джерело_збірки(л, м, м.функція(в), п.func.value)
                        if f:
                            рядок, значення = мапи[в.iter.func.value.id]
                            вих.setdefault(f, []).append((м.шлях, рядок, в.iter.func.value.id, значення))
                        break
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
                if not значуще_типове(знач):
                    continue
                ім = re.findall(r"[\w$А-Яа-яЇїІіЄєҐґ]+", ліве)[-1]
                вих.append((шлях, і, None if загальне(ім) else ("к", ім.lower()), знач, "||", ліве[:40]))
        for м in JS_ПАРАМЕТР.finditer(текст):
            for п in re.finditer(r"([\w$]+)\s*=\s*(\"[^\"\n]+\"|'[^'\n]+'|-?\d+(?:\.\d+)?)", м.group(1)):
                зн = п.group(2)
                знач = зн[1:-1] if зн[0] in "\"'" else float(зн)
                if not значуще_типове(знач):
                    continue
                і = текст.count("\n", 0, м.start(1) + п.start()) + 1
                вих.append((шлях, і, None if загальне(п.group(1)) else ("к", п.group(1).lower()), знач, "параметр",
                            п.group(1)))
    return вих


# ── п.6 і п.1(г): два боки однієї величини ────────────────────────────────────────────────────────────────────
ПОХИБКА = re.compile(r"розкид|похибк|допуск|toleran|spread|шум|noise", re.I)
ОДИНИЦЯ = re.compile(r"_(см|мм|cm|mm)$")
НЕВІДОМО = re.compile(r"unknown|невідом", re.I)
Ø = frozenset()
ВБУДОВАНІ = {"float", "int", "round", "abs", "min", "max", "sum", "next", "sorted", "list", "tuple", "fsum",
             "reversed", "iter"}
РЯДОК_ДОВЖИНА = 3
ЛОКАЛЬНИХ_ПРОХОДІВ = 40   # межа нерухомої точки потоку в одній функції


def на_пі(в):
    if not (isinstance(в, ast.BinOp) and isinstance(в.op, ast.Div)):
        return False
    п = в.right
    return (isinstance(п, ast.Attribute) and п.attr == "pi") or (isinstance(п, ast.Name) and п.id in ("pi", "π")) \
        or (isinstance(п, ast.Constant) and isinstance(п.value, float) and abs(п.value - math.pi) < 0.01)


def ключ_рядка(в):
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return в.value
    return None


def сторони(мітки):
    """Виміри без похибок: {'Т': {ід}, 'Р': {ід}}; похибки: {'Т'|'Р'}."""
    вим, пох = {"Т": set(), "Р": set()}, set()
    for м in мітки:
        if м[:2] in ("Т:", "Р:"):
            if ПОХИБКА.search(м):
                пох.add(м[0])
            else:
                вим[м[0]].add(м[2:])
    return вим, пох


def виміри(мітки):
    return {м for м in мітки if м[:2] in ("Т:", "Р:") and not ПОХИБКА.search(м)}


def різні(а, б):
    """Два операнди несуть різні виміри: обидва непорожні й без спільного (`X.?` — будь-який рівень X)."""
    ва, вб = виміри(а), виміри(б)
    if not ва or not вб or ва & вб:
        return False
    дикі = {в[:-2] for в in ва | вб if в.endswith(".?")}
    return not any(в.startswith(д + ".") for д in дикі for в in (ва if any(x == д + ".?" for x in вб) else вб))


class Боки:
    def __init__(self, л, назва_виклику, визначення_в):
        self.л, self.нв, self.вв = л, назва_виклику, визначення_в
        self.функції = []            # (м, ф|None)
        for м in л.модулі:
            self.функції.append((м, None))
            for в in ast.walk(м.дерево):
                if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    self.функції.append((м, в))
        self.вузли = {}              # id(ф або м) → [вузли цієї функції без вкладених]
        for м, ф in self.функції:
            корінь = ф if ф is not None else м.дерево
            стек, вих = list(ast.iter_child_nodes(корінь)), []
            while стек:
                в = стек.pop()
                вих.append(в)
                if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                    continue
                стек.extend(ast.iter_child_nodes(в))
            self.вузли[id(корінь)] = вих
        self.лок, self.пар, self.пов, self.кл = {}, {}, {}, {}
        self.ціль = {}
        self.тіло_ключі = {}
        self.сталі = {к for м in л.модулі for р in м.реєстри.values() for к in р}
        self.крок_ф = {}             # id(функції з кроком вибору) → «модуль.функція»
        self.крок_ключі = {}         # id(функції з кроком) → поля її словників з кроком; порожньо — усе повернення
        self.крок_імена = {}         # «модуль.функція» → ті самі поля (для читання обʼєкта)
        self.об_ключі = {}           # «@файл:рядок:колонка» словника → {поле: мітки кроку «⊗…» його значення}
        self._ключі_тіла()

    # ── виклик → визначення ──
    def ціль_виклику(self, м, в):
        к = id(в)
        if к in self.ціль:
            return self.ціль[к]
        ім = self.нв(в)
        вих = None
        if ім in self.л.визначення:
            if isinstance(в.func, ast.Name):
                мод = м.імпорт_імен.get(ім, м.ім)
            elif isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                мод = м.псевдо.get(в.func.value.id)
            else:
                мод = None
            цілі = self.вв(self.л, мод, ім)
            if len(цілі) == 1:
                вих = цілі[0]
        self.ціль[к] = вих
        return вих

    # ── тіло: ключі запису, що несе профіль (обхват через π) ──
    def _ключі_тіла(self):
        пі = {id(ф) for м, ф in self.функції if ф is not None and any(на_пі(в) for в in self.вузли[id(ф)])}
        self.пі_функції = пі
        for м, ф in self.функції:
            if ф is None:
                continue
            кличе_пі = id(ф) in пі or any(isinstance(в, ast.Call) and (lambda ц: ц is not None and id(ц[1]) in пі)(
                self.ціль_виклику(м, в)) for в in self.вузли[id(ф)])
            if not кличе_пі:
                continue
            for в in self.вузли[id(ф)]:
                if isinstance(в, ast.Return) and isinstance(в.value, ast.Call) and self.нв(в.value) == "dict":
                    for кл in в.value.keywords:
                        if кл.arg:
                            з = кл.value
                            вид = "контейнер" if isinstance(з, (ast.Dict, ast.DictComp)) or (
                                isinstance(з, ast.Call) and self.нв(з) == "dict") else "скаляр"
                            self.тіло_ключі.setdefault(кл.arg, вид)
                            if isinstance(з, ast.Name):
                                self.тіло_ключі[кл.arg] = ("ім", id(ф), з.id, вид)

    def вид_ключа(self, к):
        в = self.тіло_ключі.get(к)
        if isinstance(в, tuple):
            _, іф, ім, вид = в
            мітки = self.лок.get(іф, {}).get(ім, Ø)
            if "ряд" in мітки:
                return "ряд", мітки
            return вид, мітки
        return в, Ø

    # ── мітки виразу ──
    def читання(self, об, ключ, індекс):
        # значення, що пройшло крізь крок вибору, несе його в елемент за номером (`лок[2]`, `відр[0][0]`); обʼєкт
        # функції з кроком (`⊗о:`) — лише в полях з числом крізь крок (`м["близькість"]`, `з["припуск"]`, а
        # `з["еластан"]` — ні). Поле не літералом лишає обʼєкт обʼєктом: потік по імені параметра зливає всіх
        # викликачів, і крок тік би у кожне поле кожного словника (виміряно: 120 функцій поза кроками)
        вих = self._читання(об, ключ, індекс)
        if isinstance(індекс, int):
            вих = вих | frozenset(м for м in об if м.startswith("⊗"))
        for мм in об:
            if not мм.startswith("⊗о:") or ключ is None:
                continue
            ім = мм[3:]
            if ім.startswith("@"):
                вих = вих | self.об_ключі.get(ім, {}).get(ключ, Ø)
            elif ключ in self.крок_імена.get(ім, ()):
                вих = вих | {"⊗" + ім}
        return вих

    def _читання(self, об, ключ, індекс):
        if ключ is not None:
            вид, мітки = self.вид_ключа(ключ)
            if вид == "ряд":
                return frozenset({"ряд", "Т~:" + ключ} | {м for м in мітки if м.startswith("π@")})
            if вид == "контейнер":
                return frozenset({"Т*:" + ключ})
            if вид:
                return frozenset({"Т:" + ключ})
            конт = [м for м in об if м.startswith("Т*:")]
            if конт:
                return frozenset("Т:%s.%s" % (к[3:], ключ) for к in конт)
            if not ОДИНИЦЯ.search(ключ) or ключ in self.сталі:
                return Ø
            return frozenset({м for м in self.кл.get(ключ, Ø) if м.startswith("⊕")} | {"Р:" + ключ})
        if "ряд" in об:
            return frozenset((об - {"ряд"}) | {"рядок"})
        if "рядок" in об and isinstance(індекс, int):
            return self.елемент(об, індекс)
        конт = [м for м in об if м.startswith("Т*:")]
        if конт:
            return frozenset("Т:%s.?" % к[3:] for к in конт)
        return об

    def елемент(self, рядок, і):
        і = і % РЯДОК_ДОВЖИНА
        баз = [м[3:] for м in рядок if м.startswith("Т~:")]
        вих = {"Т:%s[%d]" % (б, і) for б in баз}
        if "π@%d" % і in рядок:
            вих.add("π")
        return frozenset(вих)

    def т(self, м, в, env, гл=0):
        if в is None or гл > 30:
            return Ø
        т = lambda x: self.т(м, x, env, гл + 1)
        if isinstance(в, ast.Name):
            return env.get(в.id, Ø)
        if isinstance(в, ast.BinOp):
            л, п = т(в.left), т(в.right)
            вих = л | п
            if isinstance(в.op, (ast.Sub, ast.Div)) and різні(л, п):
                вих = вих | {"⊕" + "".join(sorted({в_[0] for в_ in виміри(л) | виміри(п)}))}
            elif isinstance(в.op, ast.Mult) and виміри(л) and виміри(п):
                # частка, помножена на вимір, — вимір у точці (інтерполяція профілю), не різниця двох боків
                вих = frozenset(м_ for м_ in вих if not м_.startswith("⊕"))
            return вих | {"π"} if на_пі(в) else вих
        if isinstance(в, ast.UnaryOp):
            return т(в.operand)
        if isinstance(в, ast.BoolOp):
            return frozenset().union(*(т(x) for x in в.values))
        if isinstance(в, ast.IfExp):
            return т(в.body) | т(в.orelse)
        if isinstance(в, ast.Subscript):
            с = в.slice
            і = с.value if isinstance(с, ast.Constant) and isinstance(с.value, int) else \
                (-с.operand.value if isinstance(с, ast.UnaryOp) and isinstance(с.op, ast.USub)
                 and isinstance(с.operand, ast.Constant) and isinstance(с.operand.value, int) else None)
            return self.читання(т(в.value), ключ_рядка(с), і)
        if isinstance(в, ast.Call):
            ім = self.нв(в)
            if ім == "dict" and isinstance(в.func, ast.Name):
                # як і досі, `dict(…)` інших міток не несе; несе лише поля з кроком (обʼєкт «⊗о:@…»)
                return self.словник(м, в, [(к.arg, к.value) for к in в.keywords], env, гл, усе=False)
            if ім == "get" and isinstance(в.func, ast.Attribute) and в.args:
                вих = self.читання(т(в.func.value), ключ_рядка(в.args[0]), None)
                return вих | (т(в.args[1]) if len(в.args) > 1 else Ø)
            if isinstance(в.func, ast.Name) and ім in ВБУДОВАНІ:
                return frozenset().union(Ø, *(т(x) for x in в.args))
            ц = self.ціль_виклику(м, в)
            if ц is not None:
                п = self.пов.get(id(ц[1]), Ø)
                return frozenset().union(*п) if isinstance(п, tuple) else п
            return Ø
        if isinstance(в, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            env2 = dict(env)
            for г in в.generators:
                self.звʼязати(м, г.target, т2 := self.т(м, г.iter, env2, гл + 1), env2, ітерація=True)
            if isinstance(в, ast.DictComp):
                return self.т(м, в.value, env2, гл + 1)
            if isinstance(в.elt, ast.Tuple) and not isinstance(в, ast.GeneratorExp):
                елт = [self.т(м, е, env2, гл + 1) for е in в.elt.elts]
                return frozenset({"ряд"} | {"π@%d" % і for і, е in enumerate(елт) if "π" in е}
                                 | {мм for е in елт for мм in е if мм != "π"})
            return self.т(м, в.elt, env2, гл + 1)
        if isinstance(в, ast.Dict):
            return self.словник(м, в, [(ключ_рядка(к) if к is not None else None, з) for к, з in zip(в.keys, в.values)],
                                env, гл, усе=True)
        if isinstance(в, (ast.Tuple, ast.List, ast.Set)):
            return frozenset().union(Ø, *(т(x) for x in в.elts))
        if isinstance(в, ast.Starred):
            return т(в.value)
        return Ø

    def словник(self, м, в, пари, env, гл, усе):
        """Мітки словника: поле зі значенням крізь крок несе крок лише в своєму полі — обʼєкт «⊗о:@місце», поля якого
        в `об_ключі` (читання `з["нахил"]` дає крок, `з["еластан"]` — ні). `усе` — решта міток значень, як досі."""
        вих, поля = set(), {}
        for к, з in пари:
            л = self.т(м, з, env, гл + 1)
            крок = frozenset(x for x in л if x.startswith("⊗"))
            if усе:
                вих |= л - крок
            if not крок:
                continue
            if к is None:                     # `**інший` чи поле не літералом: обʼєкт несе все
                вих |= крок
            else:
                поля[к] = поля.get(к, Ø) | крок
        if поля:
            місце = "@%s:%d:%d" % (м.шлях, в.lineno, в.col_offset)
            стар = self.об_ключі.setdefault(місце, {})
            for к, л in поля.items():
                стар[к] = стар.get(к, Ø) | л
            вих.add("⊗о:" + місце)
        return frozenset(вих)

    def звʼязати(self, м, ціль, мітки, env, ітерація=False, значення=None, мітки_поз=None):
        if isinstance(ціль, ast.Name):
            if ітерація and "ряд" in мітки:
                мітки = frozenset((мітки - {"ряд"}) | {"рядок"})
            env[ціль.id] = env.get(ціль.id, Ø) | мітки
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            for і, е in enumerate(ціль.elts):
                if мітки_поз is not None and і < len(мітки_поз):
                    мм = мітки_поз[і]
                elif ітерація and "ряд" in мітки:
                    мм = self.елемент(мітки, і)
                elif "рядок" in мітки:
                    мм = self.елемент(мітки, і)
                else:
                    мм = мітки
                self.звʼязати(м, е, мм, env)
        elif isinstance(ціль, ast.Starred):
            self.звʼязати(м, ціль.value, мітки, env)

    # ── прохід функції ──
    def прохід(self, м, ф):
        корінь = ф if ф is not None else м.дерево
        env = dict(self.пар.get(id(корінь), {}))
        вузли = self.вузли[id(корінь)]
        # до нерухомої точки (а не 3 проходи): вузли йдуть у зворотному порядку, і ланцюг присвоєнь, довший за 3,
        # губив боки — `fit.зони` δ = (ст − верх)/верх ішов без `верх` (знахідка частини 13, наряд п.6)
        for _ in range(ЛОКАЛЬНИХ_ПРОХОДІВ):
            знімок = sum(len(v) for v in env.values())
            for в in вузли:
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    for ц in цілі:
                        if isinstance(ц, (ast.Tuple, ast.List)) and isinstance(в.value, (ast.Tuple, ast.List)) \
                                and len(ц.elts) == len(в.value.elts):
                            for е, з in zip(ц.elts, в.value.elts):
                                self.звʼязати(м, е, self.т(м, з, env), env)
                        elif isinstance(ц, (ast.Tuple, ast.List)) and isinstance(в.value, ast.Call) \
                                and isinstance(self.пов.get(id((self.ціль_виклику(м, в.value) or (0, None))[1]), Ø), tuple):
                            self.звʼязати(м, ц, Ø, env,
                                          мітки_поз=self.пов[id(self.ціль_виклику(м, в.value)[1])])
                        else:
                            self.звʼязати(м, ц, self.т(м, в.value, env), env)
                elif isinstance(в, (ast.For, ast.AsyncFor, ast.comprehension)):
                    self.звʼязати(м, в.target, self.т(м, в.iter, env), env, ітерація=True)
                elif isinstance(в, ast.NamedExpr):
                    self.звʼязати(м, в.target, self.т(м, в.value, env), env)
                elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.args \
                        and в.func.attr in ("append", "extend", "add", "insert") and isinstance(в.func.value, ast.Name):
                    # перелік, складений `append`, несе крок своїх елементів (інших міток, як і досі, — ні)
                    крок = frozenset(x for x in self.т(м, в.args[-1], env) if x.startswith("⊗"))
                    if крок:
                        env[в.func.value.id] = env.get(в.func.value.id, Ø) | крок
            if sum(len(v) for v in env.values()) == знімок:
                break
        self.лок[id(корінь)] = env
        # повернення
        if ф is not None:
            пов = [в.value for в in вузли if isinstance(в, ast.Return) and в.value is not None]
            крок = Ø
            if id(ф) in self.крок_ф:
                ім = self.крок_ф[id(ф)]
                ключі = self.крок_ключі.get(id(ф))
                self.крок_імена[ім] = ключі or set()
                # обʼєкт зі словниками несе крок лише в полях з числом крізь крок; інше повернення — увесь
                крок = frozenset({("⊗о:" if ключі else "⊗") + ім})
            if пов and all(isinstance(п, ast.Tuple) for п in пов) and len({len(п.elts) for п in пов}) == 1:
                self.пов[id(ф)] = tuple(frozenset().union(крок, *(self.т(м, п.elts[і], env) for п in пов))
                                        for і in range(len(пов[0].elts)))
            else:
                self.пов[id(ф)] = frozenset().union(крок, *(self.т(м, п, env) for п in пов))
        # ключі й параметри
        for в in вузли:
            if isinstance(в, ast.Assign):
                for ц in в.targets:
                    к = ключ_рядка(ц.slice) if isinstance(ц, ast.Subscript) else None
                    if к and ОДИНИЦЯ.search(к):
                        self.кл[к] = self.кл.get(к, Ø) | self.т(м, в.value, env)
            elif isinstance(в, ast.Dict):
                for к, з in zip(в.keys, в.values):
                    к = ключ_рядка(к)
                    if к and ОДИНИЦЯ.search(к):
                        self.кл[к] = self.кл.get(к, Ø) | self.т(м, з, env)
            elif isinstance(в, ast.Call):
                if self.нв(в) == "dict":
                    for кл in в.keywords:
                        if кл.arg and ОДИНИЦЯ.search(кл.arg):
                            self.кл[кл.arg] = self.кл.get(кл.arg, Ø) | self.т(м, кл.value, env)
                ц = self.ціль_виклику(м, в)
                if ц is None:
                    continue
                д = ц[1]
                поз = [а.arg for а in д.args.posonlyargs + д.args.args]
                п = self.пар.setdefault(id(д), {})
                for і, а in enumerate(в.args):
                    if isinstance(а, ast.Starred) or і >= len(поз):
                        continue
                    мм = self.т(м, а, env)
                    if мм:
                        п[поз[і]] = п.get(поз[і], Ø) | мм
                for кл in в.keywords:
                    if кл.arg:
                        мм = self.т(м, кл.value, env)
                        if мм:
                            п[кл.arg] = п.get(кл.arg, Ø) | мм

    def два_боки(self, м, в, env):
        """Мітки операндів порівняння і чи несуть вони два боки (різні виміри чи різницю двох)."""
        оп = [self.т(м, x, env) for x in [в.left] + в.comparators]
        мітки = frozenset().union(*оп)
        два = any(мм.startswith("⊕") for мм in мітки) or any(
            різні(оп[і], оп[j]) for і in range(len(оп)) for j in range(і + 1, len(оп)))
        return оп, мітки, два

    def кроки(self):
        """Функції з кроком вибору між двома боками (рівень речі проти рівнів профілю тіла): їхні повернення несуть
        мітку «⊗модуль.функція» далі потоком — до порівняння, що дає відповідь (рішення 06.11 п.6, #3222)."""
        нові = {}
        for м, ф in self.функції:
            if ф is None:
                continue
            env = self.лок.get(id(ф), {})
            for в in self.вузли[id(ф)]:
                if isinstance(в, ast.Compare) and any(isinstance(о, ПОРІВНЯННЯ) for о in в.ops):
                    оп, мітки, два = self.два_боки(м, в, env)
                    if два and крок_вибору(м, в, сторони(мітки)[0]):
                        нові.setdefault(id(ф), (м, ф, []))[2].append(в)
        змін = set(нові) - set(self.крок_ф)
        for іф, (м, ф, кроки) in нові.items():
            if іф in змін:
                self.крок_ф[іф] = "%s.%s" % (м.шлях.split("/")[-1].rsplit(".", 1)[0], ф.name)
        for іф, (м, ф, кроки) in нові.items():
            self.крок_ключі[іф] = self.ключі_кроку(м, ф, кроки)
        return змін

    def ключі_кроку(self, м, ф, кроки):
        """Поля словників, які будує функція з кроком, з числом, що пройшло крізь крок: імена, присвоєні в тому, що
        крок стереже (і в їхньому потоці), чи з виклику іншої функції з кроком; поле — число (арифметика, `round`,
        `float`…), а не ярлик чи властивість речі (`еластан=ел`, `носій=хто` — ні)."""
        вузли = self.вузли[id(ф)]
        стер = set()
        for в in кроки:
            р = регіон_кроку(м, в)
            if р is None:
                continue
            вид, стережене = р
            if вид == "вкл":
                с = м.батько.get(стережене[0])
                while с is not None and not isinstance(с, ast.stmt):
                    с = м.батько.get(с)
                стережене = [с] if с is not None else []
            for с in стережене:
                for x in ast.walk(с):
                    if isinstance(x, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                        for ц in (x.targets if isinstance(x, ast.Assign) else [x.target]):
                            стер |= {н.id for н in ast.walk(ц) if isinstance(н, ast.Name)}
                    elif isinstance(x, (ast.For, ast.comprehension)):
                        стер |= {н.id for н in ast.walk(x.target) if isinstance(н, ast.Name)}
                    elif isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) \
                            and x.func.attr in ("append", "extend", "add", "insert") \
                            and isinstance(x.func.value, ast.Name):
                        стер.add(x.func.value.id)
        def з_кроку(вираз):
            return any((isinstance(x, ast.Name) and x.id in стер) or (
                isinstance(x, ast.Call) and (lambda ц: ц is not None and id(ц[1]) in self.крок_ф)(
                    self.ціль_виклику(м, x))) for x in ast.walk(вираз))
        for _ in range(ЛОКАЛЬНИХ_ПРОХОДІВ):
            до = len(стер)
            for в in вузли:
                if isinstance(в, (ast.Assign, ast.AugAssign, ast.AnnAssign)) and в.value is not None \
                        and з_кроку(в.value):
                    for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                        стер |= {н.id for н in ast.walk(ц) if isinstance(н, ast.Name)}
                elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) \
                        and в.func.attr in ("append", "extend", "add", "insert") \
                        and isinstance(в.func.value, ast.Name) and any(з_кроку(а) for а in в.args):
                    стер.add(в.func.value.id)
            if len(стер) == до:
                break
        def число(вираз):
            return any(isinstance(x, ast.BinOp) or (isinstance(x, ast.Call) and isinstance(x.func, ast.Name)
                                                     and x.func.id in ("round", "float", "abs", "min", "max", "sum"))
                       or (isinstance(x, ast.Call) and (lambda ц: ц is not None and id(ц[1]) in self.крок_ф)(
                           self.ціль_виклику(м, x))) for x in ast.walk(вираз))
        ключі = set()
        for в in вузли:
            пари = []
            if isinstance(в, ast.Call) and self.нв(в) == "dict":
                пари = [(к.arg, к.value) for к in в.keywords if к.arg]
            elif isinstance(в, ast.Dict):
                пари = [(ключ_рядка(к), з) for к, з in zip(в.keys, в.values) if к is not None]
            for к, з in пари:
                if к and з_кроку(з) and число(з):
                    ключі.add(к)
        return ключі

    def обчислити(self, проходів=8):
        for н in range(проходів):
            знімок = (sum(len(v) for e in self.лок.values() for v in e.values()), sum(len(v) for v in self.кл.values()),
                      sum(len(v) for e in self.пар.values() for v in e.values()),
                      sum(len(v) for e in self.об_ключі.values() for v in e.values()))
            for м, ф in self.функції:
                self.прохід(м, ф)
            нов = (sum(len(v) for e in self.лок.values() for v in e.values()), sum(len(v) for v in self.кл.values()),
                   sum(len(v) for e in self.пар.values() for v in e.values()),
                   sum(len(v) for e in self.об_ключі.values() for v in e.values()))
            if нов == знімок and н:
                return н
        return проходів


ПОРІВНЯННЯ = (ast.Lt, ast.LtE, ast.Gt, ast.GtE)


def опис(вим, пох):
    return "річ {%s}, тіло {%s}; похибка: %s" % (", ".join(sorted(вим["Р"]))[:80], ", ".join(sorted(вим["Т"]))[:80],
                                                   "/".join("річ" if п == "Р" else "тіло" for п in sorted(пох)) or "нема")


def стереже_виняток(м, в):
    """Порівняння — умова `if`, чия гілка лише кидає виняток: межа області визначення даних, не відповідь."""
    б, п = м.батько.get(в), в
    while isinstance(б, (ast.BoolOp, ast.UnaryOp)):
        б, п = м.батько.get(б), б
    return isinstance(б, ast.If) and б.test is п and all(isinstance(с, ast.Raise) for с in б.body)


ІД_ВИРОКУ = re.compile(r"^[KR]-[A-Z]+-\d+")   # початок рядка — ід правила у вироку


def вирок_у(вузли):
    """Гілка дає вирок правила: рядок-ід правила (`K-FIT-03`) у її коді."""
    return any(isinstance(x, ast.Constant) and isinstance(x.value, str) and ІД_ВИРОКУ.match(x.value)
               for в in вузли for x in ast.walk(в))


def регіон_кроку(м, в):
    """Порівняння — крок вибору за будовою (рішення 06.11 п.6, #3222): фільтр включення (`[y for y in рівні if y <
    край]`), умова циклу `while`, чи умова `if` прямо в тілі циклу, чия гілка лише пропускає елемент
    (`continue`/`break`) чи повертає число з обраного відрізка, а не слово. → (вид, вузли, що їх стереже крок) чи None.
    Вид: «вкл» — включення (стережене — сам вираз включення), «цикл» — тіло `while`, «далі» — решта тіла циклу після
    `if … continue`, «гілка» — тіло `if`, що повертає."""
    б, п = м.батько.get(в), в
    while isinstance(б, ast.BoolOp) or (isinstance(б, ast.UnaryOp) and isinstance(б.op, ast.Not)):
        б, п = м.батько.get(б), б
    if isinstance(б, ast.comprehension) and п in б.ifs:
        return "вкл", [м.батько.get(б)]
    if isinstance(б, ast.While) and б.test is п:
        return "цикл", list(б.body)
    if isinstance(б, ast.If) and б.test is п and б.body:
        цикл = м.батько.get(б)
        if not (isinstance(цикл, (ast.For, ast.AsyncFor, ast.While)) and б in цикл.body):
            return None
        кін = б.body[-1]
        if isinstance(кін, (ast.Continue, ast.Break)):
            return "далі", цикл.body[цикл.body.index(б) + 1:]
        if isinstance(кін, ast.Return) and кін.value is not None \
                and not any(isinstance(x, ast.Constant) and isinstance(x.value, str) for x in ast.walk(кін.value)):
            return "гілка", list(б.body)
    return None


def крок_вибору(м, в, вим):
    """Крок обчислення, що лише вибирає відрізок інтерполяції чи межі вікна між рівнями профілю: крок за будовою
    (`регіон_кроку`), між рівнем речі й рівнем тіла (обидва боки в операндах), і те, що він стереже, вироку правила
    не дає. Відповіді він не дає — її дає порівняння, яке він живить (мітка «⊗» у потоці)."""
    if not (вим["Р"] and вим["Т"]):
        return False
    р = регіон_кроку(м, в)
    if р is None:
        return False
    вид, стережене = р
    if вид == "вкл":
        return True
    return not вирок_у(стережене)


СИЛА_Т = re.compile(r"^сила|сила_|strength", re.I)


def сила_від(м, в):
    """Порівняння вибирає силу правила: `"strong" if … else …` чи гілка, що лише пише `сила_*`."""
    б, п = м.батько.get(в), в
    while isinstance(б, (ast.BoolOp, ast.UnaryOp)):
        б, п = м.батько.get(б), б
    if isinstance(б, ast.IfExp) and б.test is п:
        return any(isinstance(x, ast.Constant) and x.value in ("hard", "strong", "soft", "hint", "default")
                   for x in (б.body, б.orelse))
    if isinstance(б, ast.If) and б.test is п and б.body:
        цілі = [ц for с in б.body if isinstance(с, (ast.Assign, ast.AugAssign))
                for ц in (с.targets if isinstance(с, ast.Assign) else [с.target])]
        return len(цілі) == len(б.body) and all(
            СИЛА_Т.search(ast.unparse(ц.slice) if isinstance(ц, ast.Subscript) else ast.unparse(ц)) for ц in цілі)
    return False


СИЛА_КРІЗЬ = re.compile(r"\bнп\b|_нп\b|вага_знахідок")   # неперервна сила правила (`сила_нп`) і її сума


def джерела_імен(корінь, в):
    """Тексти присвоєнь імен порівняння в тій самій функції (один крок назад), коли значення — читання поля чи
    арифметика вбудованими (`z.get("сила_нп")`, `max(0.0, сила_переваги * впевненість)`): звідки взято величину.
    Виклик іншої функції — ні: його аргументи називають інші величини (`метрики_образу(…, смуга_погоди=…)`)."""
    імена = {x.id for x in ast.walk(в) if isinstance(x, ast.Name)}
    вих = []
    for с in ast.walk(корінь):
        if isinstance(с, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id in імена for ц in с.targets) \
                and all(not isinstance(x, ast.Call) or (isinstance(x.func, ast.Name) and x.func.id in ВБУДОВАНІ)
                        or (isinstance(x.func, ast.Attribute) and x.func.attr == "get") for x in ast.walk(с.value)):
            вих.append(ast.unparse(с.value)[:200])
    return вих


def в_assert(м, в):
    б = м.батько.get(в)
    while б is not None and not isinstance(б, ast.stmt):
        б = м.батько.get(б)
    return isinstance(б, ast.Assert)


def вартовий_нуля(м, в):
    """`(w − w_min)/w if w > 0 else 0.0`, `if сер <= 0: return None`: величина проти нуля, а гілка — вартовий ділення
    на неї чи порожньої відповіді. Лише для порівнянь «крізь крок»; знак величини, що вибирає відповідь
    (`if дизайн < 0: назва = "close-fitting"`), — відповідь, не вартовий."""
    оп = [в.left] + в.comparators
    if len(оп) != 2 or not any(isinstance(x, ast.Constant) and x.value == 0 and not isinstance(x.value, bool)
                               for x in оп):
        return False
    вел = next(x for x in оп if not (isinstance(x, ast.Constant) and x.value == 0))
    текст = ast.unparse(вел)
    б, п = м.батько.get(в), в
    while isinstance(б, (ast.BoolOp, ast.UnaryOp)):
        б, п = м.батько.get(б), б
    if isinstance(б, ast.IfExp) and б.test is п:
        return any(isinstance(x, ast.BinOp) and isinstance(x.op, ast.Div) and ast.unparse(x.right) == текст
                   for гілка in (б.body, б.orelse) for x in ast.walk(гілка))
    if isinstance(б, ast.If) and б.test is п and len(б.body) == 1 and isinstance(б.body[0], ast.Return):
        з = б.body[0].value
        return з is None or (isinstance(з, ast.Constant) and з.value in (None, 0, 0.0, False)) or (
            isinstance(з, (ast.List, ast.Dict, ast.Tuple))
            and not (getattr(з, "elts", None) or getattr(з, "keys", None)))
    return False


def заява_сили(в):
    """Виклик заяви правила з силою вироку другим аргументом: (ід, сила) чи None."""
    if isinstance(в, ast.Call) and len(в.args) >= 2 and all(isinstance(а, ast.Constant) and isinstance(а.value, str)
                                                          for а in в.args[:2]) \
            and re.match(r"^[KR]-[A-Z]+-\d+", в.args[0].value) and в.args[1].value in ("hard", "strong", "soft", "hint"):
        return в.args[0].value, в.args[1].value
    return None


def п6_місця(б, іншого_кореня=lambda т: None, виробники=None):
    """→ місця [(файл, рядок, підпункт, текст, доказ)], не місця [(файл, рядок, текст, причина)]. `виробники` —
    перелік, куди дописати порівняння п.6(а) з похибкою хоч одного боку, місця й виправлені (м, функція, вузол,
    чи один операнд — сама похибка): у межах похибки їхня відповідь — «невідомо» (п.6(г))."""
    місця, не = [], []
    виробники = [] if виробники is None else виробники
    for м, ф in б.функції:
        корінь = ф if ф is not None else м.дерево
        env = б.лок.get(id(корінь), {})
        for в in б.вузли[id(корінь)]:
            if isinstance(в, ast.Compare) and any(isinstance(о, ПОРІВНЯННЯ) for о in в.ops):
                оп, мітки, два = б.два_боки(м, в, env)
                # крізь крок: операнд несе значення, обчислене кроком вибору між двома боками (`⊗…`), — відповідь,
                # яку живить крок, і похибка її — обох боків крізь цей крок (рішення 06.11 п.6, #3222)
                кроки = sorted({мм[1:] for мм in мітки if мм.startswith("⊗") and not мм.startswith("⊗о:")})
                if not два and not кроки:
                    continue
                вим, пох = сторони(мітки)
                текст = ast.unparse(в)[:70]
                інший = іншого_кореня(текст) or (сила_від(м, в) and "Е3-сила-правила")
                if not інший and not два:
                    # крізь крок значення тече далі в силу правила (`нп = z.get("сила_нп")`, `вага_вікна = …
                    # сила_переваги …`): сила — інший корінь, і за джерелом імені, не лише за текстом порівняння
                    інший = (СИЛА_КРІЗЬ.search(ast.unparse(в)) and "Е3-сила-правила") or іншого_кореня(
                        *джерела_імен(корінь, в))
                обидві = ("Р" in пох and "Т" in пох) if (вим["Р"] and вим["Т"]) else len(пох) >= 2
                if інший:
                    не.append((м.шлях, в.lineno, текст, "інший корінь: " + інший))
                elif стереже_виняток(м, в):
                    не.append((м.шлях, в.lineno, текст, "межа області визначення: гілка лише кидає виняток "
                                                        "даних, відповіді про величину нема"))
                elif в_assert(м, в):
                    не.append((м.шлях, в.lineno, текст, "перевірка коду (`assert`): відповіді правилу, моделі, "
                                                        "каталогу чи людині не дає"))
                elif два and крок_вибору(м, в, вим):
                    не.append((м.шлях, в.lineno, текст, "крок обчислення: лише вибирає відрізок інтерполяції чи "
                                                        "межі вікна, відповіді не дає — прилад веде вимір до "
                                                        "відповіді, яку він живить (рішення 06.11 п.6)"))
                elif not два and вартовий_нуля(м, в):
                    не.append((м.шлях, в.lineno, текст, "вартовий ділення: величина крізь крок проти нуля, "
                                                        "відповіді не дає"))
                elif обидві:
                    не.append((м.шлях, в.lineno, текст, "похибку обох боків враховано"))
                    виробники.append((м, ф, в, any(сторони(о)[1] and not виміри(о) for о in оп)))
                else:
                    if пох:
                        виробники.append((м, ф, в, any(сторони(о)[1] and not виміри(о) for о in оп)))
                    місця.append((м.шлях, в.lineno, "а", текст, опис(вим, пох) + (
                        "; крізь крок %s" % ", ".join(кроки) if кроки else "")))
            elif isinstance(в, ast.BinOp) and isinstance(в.op, ast.Sub):
                л, п = б.т(м, в.left, env), б.т(м, в.right, env)
                вл, _ = сторони(л)
                вп, _ = сторони(п)
                for а, ва, бб, вб in ((л, вл, п, вп), (п, вп, л, вл)):
                    if ва["Р"] and not ва["Т"] and "π" not in а and вб["Т"] and not вб["Р"] and "π" in бб:
                        місця.append((м.шлях, в.lineno, "б", ast.unparse(в)[:70],
                                      "вимір речі {%s} мінус оцінка тіла через π {%s}" % (
                                          ", ".join(sorted(ва["Р"])), ", ".join(sorted(вб["Т"])))))
            elif isinstance(в, ast.If):
                # (в) вирок, умова якого — лише наявність обох боків: `if річ is None or тіло is None` з виходом
                # чи з `else`; сила вироку стоїть на різниці, похибки якої код не знає
                нема = [б.т(м, к.left, env) for к in ast.walk(в.test) if isinstance(к, ast.Compare)
                        and len(к.ops) == 1 and isinstance(к.ops[0], ast.Is)
                        and isinstance(к.comparators[0], ast.Constant) and к.comparators[0].value is None]
                if not any(різні(нема[і], нема[j]) for і in range(len(нема)) for j in range(і + 1, len(нема))):
                    continue
                вим, _ = сторони(frozenset().union(*нема))
                гілки = list(в.orelse)
                if в.body and isinstance(в.body[-1], ast.Return):
                    бат = м.батько.get(в)
                    for поле in ("body", "orelse"):
                        с = getattr(бат, поле, None)
                        if isinstance(с, list) and в in с:
                            гілки += с[с.index(в) + 1:]
                for с in гілки:
                    for к in ast.walk(с):
                        зс = заява_сили(к)
                        if зс:
                            місця.append((м.шлях, к.lineno, "в", "%s %s" % зс,
                                          "вирок «%s» стоїть лише на наявності обох боків (річ {%s}, тіло {%s}): "
                                          "умова — різниця без похибки обох" % (
                                              зс[1], ", ".join(sorted(вим["Р"])), ", ".join(sorted(вим["Т"])))))
    return місця, не


# ── п.6(г): читач «невідомо» з порівняння (рішення менеджера 07.11, 13933, 13962) ───────────────────────────────────
# Виробник — порівняння п.6 з похибкою хоч одного боку (місце й виправлене): у межах похибки воно дає «невідомо» (None
# чи False «не доведено»). Відповідь іде потоком значення — повернення, кортеж (позиція), поле словника (ключ),
# перелік, параметр — до читача: умови `if`/`elif`/`while`/`… if … else …`, що бере її на істинність. Мітка — (виробник,
# шлях): шлях — позиції й ключі, які ще треба прочитати; `∅` — перелік, відфільтрований відповіддю чи дописаний
# лише гілкою «так» умови на неї, 13967 (його порожнеча —
# та сама відповідь).
ПОРОЖНЯ = "∅"
ПРОЗОРІ = {"list", "tuple", "set", "frozenset", "sorted", "reversed", "iter", "next", "bool", "any", "all", "filter"}
СИЛА_ВИРОКУ = {"hard", "strong", "soft", "hint"}
ОБЛІК = {"утримано", "питання"}
ДОПИСУВАННЯ = ("append", "extend", "add", "insert")
# Читачі, яких потік не розрізняє (умова не зводиться до «невідомо» → гілка: порівняння з числом, `while`, вираз-вибір
# не з None): вердикт сесії лічби з рядком читача, як `ВЕРДИКТИ` приладу Е2-збій-без-сліду. Ключ — файл, функція,
# номер такого читача в ній (рядки зсуваються). Читач без вердикту — місце «п.?»: новий читач не проходить мовчки.
# файл | функція#номер | М (місце) чи Н (не місце) | чому
_ТАБЛИЦЯ_Г = """
"""


def _вердикти_г(таблиця):
    вих = {}
    for р in таблиця.strip().splitlines():
        ф, фн, в, чому = [ч.strip() for ч in р.split(" | ", 3)]
        функція, номер = фн.rsplit("#", 1)
        вих[("джерела/" + ф, функція, int(номер))] = (в, чому)
    return вих


ВЕРДИКТИ_Г = _вердикти_г(_ТАБЛИЦЯ_Г)


def _вибрати(мітки, крок):
    """Мітки після читання позиції (int) чи ключа (str): шлях, що починається цим кроком, коротшає; інший крок того
    самого роду — інше значення; перелік (шлях без кроку чи з ключем під позицією) — елемент того самого."""
    вих = set()
    for о, ш in мітки:
        if ш and ш[0] == крок:
            вих.add((о, ш[1:]))
        elif ш and isinstance(крок, int) and isinstance(ш[0], str) and ш[0] != ПОРОЖНЯ:
            вих.add((о, ш))
    return frozenset(вих)


def _з_кроком(мітки, крок):
    return frozenset((о, (крок,) + ш) for о, ш in мітки)


def _відповідь(мітки):
    """Мітки, що несуть саму відповідь (шлях вичерпано) чи порожнечу відфільтрованого нею переліку."""
    return frozenset(о for о, ш in мітки if not ш or ш == (ПОРОЖНЯ,))


НЕ_СУДИТЬ = re.compile(r"not_judged")


def _не_судить(в):
    """Облік «невідомо» після умови: «утримано», «питання» чи заява, що правило не судить (`…not_judged…`)."""
    return (isinstance(в, ast.Constant) and в.value in ОБЛІК) or (
        isinstance(в, ast.Call) and назва_виклику(в) == "заява" and в.args and isinstance(в.args[0], ast.Constant)
        and isinstance(в.args[0].value, str) and bool(НЕ_СУДИТЬ.search(в.args[0].value)))


def _заява_в(б, м, вузли, гл=0):
    """Гілка каже слово правила — заяву (`заява(…)`) у собі чи у функціях продукту, які кличе (два кроки)."""
    for с in вузли:
        for x in ast.walk(с):
            if isinstance(x, ast.Call) and назва_виклику(x) == "заява" and not _не_судить(x):
                return True
            if isinstance(x, ast.Call) and гл < 2 and м is not None:
                ц = б.ціль_виклику(м, x)
                if ц is not None and _заява_в(б, ц[0], ц[1].body, гл + 1):
                    return True
    return False


class Відповіді:
    """Потік відповіді виробника п.6 до читача: та сама нерухома точка, що в `Боки`, з мітками (виробник, шлях)."""

    def __init__(self, б, виробники):
        self.б = б
        self.лок, self.пар, self.пов = {}, {}, {}
        self.насіння = {}            # id(Compare) → виробник «файл:рядок»: відповідь — саме порівняння
        self.виробники = set()       # id(Compare) усіх виробників: вони не читачі
        self.імена = {}              # id(функції) → {імʼя: мітки} — імена, присвоєні в гілках виробника
        self.повертає = {}           # id(функції) → мітки, які несе кожне її повернення (гілка виробника повертає)
        for м, ф, в, пряма in виробники:
            о = "%s:%d" % (м.шлях, в.lineno)
            self.виробники.add(id(в))
            корінь = ф if ф is not None else м.дерево
            вузли = self.б.вузли[id(корінь)]
            # «невідомо» є там, де функція його має: імʼя, якому присвоєно й None (`на = важіль = None`), повернення
            # None; порівняння, чий операнд — сама похибка (`різниця > похибка`), — хиба «не доведено» й у межах похибки
            ніщо = {ц.id for x in вузли if isinstance(x, ast.Assign) and isinstance(x.value, ast.Constant)
                    and x.value.value is None for ц in x.targets if isinstance(ц, ast.Name)}
            поверне_ніщо = any(isinstance(x, ast.Return) and (x.value is None or (
                isinstance(x.value, ast.Constant) and x.value.value is None)) for x in вузли)
            if пряма:
                self.насіння[id(в)] = о
            б_, п = м.батько.get(в), в
            while isinstance(б_, ast.BoolOp) or (isinstance(б_, ast.UnaryOp) and isinstance(б_.op, ast.Not)):
                б_, п = м.батько.get(б_), б_
            if isinstance(б_, ast.If) and б_.test is п:
                for с in б_.body + б_.orelse:
                    for x in ast.walk(с):
                        if isinstance(x, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
                            for ц in (x.targets if isinstance(x, ast.Assign) else [x.target]):
                                if isinstance(ц, ast.Name) and ц.id in ніщо:
                                    self.імена.setdefault(id(корінь), {}).setdefault(ц.id, set()).add((о, ()))
                        elif isinstance(x, ast.Return) and ф is not None and поверне_ніщо:
                            self.повертає.setdefault(id(ф), set()).add((о, ()))

    def т(self, м, в, env, гл=0):
        if в is None or гл > 30:
            return Ø
        т = lambda x: self.т(м, x, env, гл + 1)
        if isinstance(в, ast.Name):
            return env.get(в.id, Ø)
        if isinstance(в, ast.Compare):
            о = self.насіння.get(id(в))
            return frozenset({(о, ())}) if о else Ø
        if isinstance(в, ast.BoolOp):
            return frozenset().union(*(т(x) for x in в.values))
        if isinstance(в, ast.UnaryOp) and isinstance(в.op, ast.Not):
            return т(в.operand)
        if isinstance(в, ast.IfExp):
            return т(в.body) | т(в.orelse) | (т(в.test) if isinstance(в.test, ast.Compare) else Ø)
        if isinstance(в, ast.NamedExpr):
            return т(в.value)
        if isinstance(в, ast.Starred):
            return т(в.value)
        if isinstance(в, ast.Subscript):
            с = в.slice
            if isinstance(с, ast.Constant) and isinstance(с.value, (int, str)) and not isinstance(с.value, bool):
                return _вибрати(т(в.value), с.value)
            return Ø
        if isinstance(в, ast.Tuple):
            return frozenset().union(Ø, *(_з_кроком(т(x), і) for і, x in enumerate(в.elts)))
        if isinstance(в, (ast.List, ast.Set)):
            return frozenset().union(Ø, *(т(x) for x in в.elts))
        if isinstance(в, ast.Dict):
            вих = set()
            for к, з in zip(в.keys, в.values):
                if к is None:
                    вих |= т(з)
                elif isinstance(к, ast.Constant) and isinstance(к.value, str):
                    вих |= _з_кроком(т(з), к.value)
            return frozenset(вих)
        if isinstance(в, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
            env2 = dict(env)
            фільтр = set()
            for г in в.generators:
                self.звʼязати(г.target, frozenset(x for x in self.т(м, г.iter, env2, гл + 1)
                                                   if x[1] != (ПОРОЖНЯ,)), env2)
                for у in г.ifs:
                    фільтр |= {(о, (ПОРОЖНЯ,)) for о in _відповідь(self.т(м, у, env2, гл + 1))}
            вих = self.т(м, в.value if isinstance(в, ast.DictComp) else в.elt, env2, гл + 1)
            return вих | frozenset(фільтр)
        if isinstance(в, ast.Call):
            ім = назва_виклику(в)
            if isinstance(в.func, ast.Name) and ім == "dict":
                return frozenset().union(Ø, *(т(а) for а in в.args), *(
                    _з_кроком(т(к.value), к.arg) if к.arg else т(к.value) for к in в.keywords))
            if isinstance(в.func, ast.Name) and ім in ПРОЗОРІ:
                return frozenset().union(Ø, *(т(а) for а in в.args))
            ц = self.б.ціль_виклику(м, в)
            if ц is not None:
                return self.пов.get(id(ц[1]), Ø)
            if isinstance(в.func, ast.Attribute):
                if ім == "get" and в.args and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
                    return _вибрати(т(в.func.value), в.args[0].value) | (т(в.args[1]) if len(в.args) > 1 else Ø)
                if ім in ("pop", "copy", "values", "items"):
                    return т(в.func.value)
            return Ø
        return Ø

    def звʼязати(self, ціль, мітки, env):
        if isinstance(ціль, ast.Name):
            env[ціль.id] = env.get(ціль.id, Ø) | мітки
        elif isinstance(ціль, (ast.Tuple, ast.List)):
            for і, е in enumerate(ціль.elts):
                self.звʼязати(е, _вибрати(мітки, і), env)
        elif isinstance(ціль, ast.Starred):
            self.звʼязати(ціль.value, мітки, env)
        elif isinstance(ціль, ast.Subscript) and isinstance(ціль.value, ast.Name) \
                and isinstance(ціль.slice, ast.Constant) and isinstance(ціль.slice.value, str) and мітки:
            env[ціль.value.id] = env.get(ціль.value.id, Ø) | _з_кроком(мітки, ціль.slice.value)

    def прохід(self, м, ф):
        корінь = ф if ф is not None else м.дерево
        env = dict(self.пар.get(id(корінь), {}))
        for ім, мм in self.імена.get(id(корінь), {}).items():
            env[ім] = env.get(ім, Ø) | frozenset(мм)
        вузли = self.б.вузли[id(корінь)]
        ніщо = _порожні_імена(вузли)
        for _ in range(ЛОКАЛЬНИХ_ПРОХОДІВ):
            знімок = sum(len(v) for v in env.values())
            for в in вузли:
                if isinstance(в, ast.If):
                    self.керування(м, в, env, ніщо)
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign)) and в.value is not None:
                    for ц in (в.targets if isinstance(в, ast.Assign) else [в.target]):
                        if isinstance(ц, (ast.Tuple, ast.List)) and isinstance(в.value, (ast.Tuple, ast.List)) \
                                and len(ц.elts) == len(в.value.elts):
                            for е, з in zip(ц.elts, в.value.elts):
                                self.звʼязати(е, self.т(м, з, env), env)
                        else:
                            self.звʼязати(ц, self.т(м, в.value, env), env)
                elif isinstance(в, (ast.For, ast.AsyncFor)):
                    self.звʼязати(в.target, frozenset(x for x in self.т(м, в.iter, env) if x[1] != (ПОРОЖНЯ,)), env)
                elif isinstance(в, ast.NamedExpr):
                    self.звʼязати(в.target, self.т(м, в.value, env), env)
                elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.args \
                        and в.func.attr in ДОПИСУВАННЯ and isinstance(в.func.value, ast.Name):
                    мм = self.т(м, в.args[-1], env)
                    if мм:
                        env[в.func.value.id] = env.get(в.func.value.id, Ø) | мм
            if sum(len(v) for v in env.values()) == знімок:
                break
        self.лок[id(корінь)] = env
        if ф is not None:
            пов = frozenset().union(Ø, *(self.т(м, в.value, env) for в in вузли
                                         if isinstance(в, ast.Return) and в.value is not None))
            if id(ф) in self.повертає:
                пов = пов | frozenset(self.повертає[id(ф)])
            self.пов[id(ф)] = пов
        for в in вузли:
            if not isinstance(в, ast.Call):
                continue
            ц = self.б.ціль_виклику(м, в)
            if ц is None:
                continue
            д = ц[1]
            поз = [а.arg for а in д.args.posonlyargs + д.args.args]
            п = self.пар.setdefault(id(д), {})
            for і, а in enumerate(в.args):
                if isinstance(а, ast.Starred) or і >= len(поз):
                    continue
                мм = self.т(м, а, env)
                if мм:
                    п[поз[і]] = п.get(поз[і], Ø) | мм
            for кл in в.keywords:
                if кл.arg:
                    мм = self.т(м, кл.value, env)
                    if мм:
                        п[кл.arg] = п.get(кл.arg, Ø) | мм

    def несуть(self, м, т, env):
        """Операнди умови, що несуть відповідь (не порівняння самого виробника), і їхні виробники."""
        вих = [(к, _відповідь(self.т(м, к, env))) for к, _ in _кандидати(т) if id(к) not in self.виробники]
        return [(к, о) for к, о in вих if о]

    def керування(self, м, в, env, ніщо):
        """Залежність за керуванням (рішення 07.11, 13967): гілка «так» умови на відповідь, коли на «невідомо» інша
        гілка нічого не пише (порожня, `pass`, `continue`, `break`), — перелік, який вона дописує, і поле чи імʼя з
        порожнім початковим значенням, яке вона пише, несуть відповідь порожнечею, як відфільтрований перелік."""
        несуть = self.несуть(м, в.test, env)
        if not несуть:
            return
        зн = _при_невідомому(в.test, {id(к) for к, _ in несуть})
        if зн is None:
            return
        так, інша = (в.orelse, в.body) if зн else (в.body, в.orelse)
        if not так or not all(isinstance(с, (ast.Pass, ast.Continue, ast.Break)) for с in інша):
            return
        мітка = frozenset((о, (ПОРОЖНЯ,)) for _, оо in несуть for о in оо)
        сама = frozenset((о, ()) for _, оо in несуть for о in оо)
        for с in так:
            for x in ast.walk(с):
                if isinstance(x, ast.Call) and isinstance(x.func, ast.Attribute) and x.func.attr in ДОПИСУВАННЯ \
                        and isinstance(x.func.value, ast.Name):
                    env[x.func.value.id] = env.get(x.func.value.id, Ø) | мітка
                elif isinstance(x, ast.Assign) and not (isinstance(x.value, ast.Constant) and x.value.value is None):
                    for ц in x.targets:
                        if isinstance(ц, ast.Name) and ц.id in ніщо:
                            env[ц.id] = env.get(ц.id, Ø) | сама
                        elif isinstance(ц, ast.Subscript) and isinstance(ц.value, ast.Name) \
                                and isinstance(ц.slice, ast.Constant) and isinstance(ц.slice.value, str):
                            env[ц.value.id] = env.get(ц.value.id, Ø) | _з_кроком(мітка, ц.slice.value)

    def обчислити(self, проходів=10):
        def розмір():
            return (sum(len(v) for e in self.лок.values() for v in e.values()),
                    sum(len(v) for v in self.пов.values()),
                    sum(len(v) for e in self.пар.values() for v in e.values()))
        for н in range(проходів):
            знімок = розмір()
            for м, ф in self.б.функції:
                self.прохід(м, ф)
            if розмір() == знімок and н:
                break


def _порожні_імена(вузли):
    """Імена функції, яким присвоєно й порожнє: None, порожній перелік, словник чи множину."""
    def порожнє_(з):
        return (isinstance(з, ast.Constant) and з.value is None) or (
            isinstance(з, (ast.List, ast.Dict, ast.Set, ast.Tuple)) and not getattr(з, "elts", getattr(з, "keys", None)))
    вих = set()
    for x in вузли:
        if not isinstance(x, ast.Assign):
            continue
        for ц in x.targets:
            if isinstance(ц, ast.Name) and порожнє_(x.value):
                вих.add(ц.id)
            elif isinstance(ц, ast.Tuple) and isinstance(x.value, ast.Tuple) and len(ц.elts) == len(x.value.elts):
                вих |= {е.id for е, з in zip(ц.elts, x.value.elts) if isinstance(е, ast.Name) and порожнє_(з)}
    return вих


def _літерал(x):
    """Літерал умови: `1`, `None`, `-1` (мінус перед числом)."""
    return isinstance(x, ast.Constant) or (isinstance(x, ast.UnaryOp) and isinstance(x.op, ast.USub)
                                           and isinstance(x.operand, ast.Constant))


def _кандидати(т):
    """Операнди рішення умови: крізь `and`/`or`/`not`; порівняння з одним літералом — його другий бік (з оператором і
    літералом); решта — сам вираз."""
    if isinstance(т, ast.BoolOp):
        return [к for x in т.values for к in _кандидати(x)]
    if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
        return _кандидати(т.operand)
    if isinstance(т, ast.Compare) and len(т.ops) == 1:
        л, п = т.left, т.comparators[0]
        if _літерал(п) and not _літерал(л):
            return [(л, т)]
        if _літерал(л) and not _літерал(п):
            return [(п, т)]
    return [(т, None)]


def _при_невідомому(т, невідомі):
    """Значення умови, коли кожен операнд з `невідомі` — «невідомо» (None, порожній перелік), а решта не вирішує
    (`and` — істина, `or` — хиба): True, False чи None — потік не розрізняє."""
    if id(т) in невідомі:
        return False
    if isinstance(т, ast.BoolOp):
        зн = [_при_невідомому(x, невідомі) if any(id(у) in невідомі for у in ast.walk(x))
              else isinstance(т.op, ast.And) for x in т.values]
        if isinstance(т.op, ast.And):
            return False if False in зн else (None if None in зн else True)
        return True if True in зн else (None if None in зн else False)
    if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
        з = _при_невідомому(т.operand, невідомі)
        return None if з is None else not з
    if isinstance(т, ast.Compare) and len(т.ops) == 1 and any(id(x) in невідомі for x in [т.left] + т.comparators):
        оп, л = т.ops[0], next(x for x in [т.left] + т.comparators if id(x) not in невідомі)
        if not _літерал(л):
            return None
        л = л if isinstance(л, ast.Constant) else ast.Constant(-л.operand.value)
        if isinstance(оп, (ast.In, ast.NotIn)):        # `None in відповіді`: «невідомо» серед відповідей
            return (л.value is None) == isinstance(оп, ast.In)
        if isinstance(оп, (ast.Is, ast.Eq)):           # «невідомо» — None: дорівнює лише None
            return л.value is None
        if isinstance(оп, (ast.IsNot, ast.NotEq)):
            return л.value is not None
    return None


def _вирок(в):
    """Виклик вироку правила: ід правила й сила вироку першими двома аргументами (`_зн("K-FIT-03", "soft", …)`)."""
    return isinstance(в, ast.Call) and len(в.args) >= 2 and all(
        isinstance(а, ast.Constant) and isinstance(а.value, str) for а in в.args[:2]) \
        and bool(ІД_ВИРОКУ.match(в.args[0].value)) and в.args[1].value in СИЛА_ВИРОКУ


def _облік(в):
    """Знахідка «утримано» чи «питання» або заява (`заява(…)`): правило каже, що не судить."""
    return (isinstance(в, ast.Constant) and в.value in ОБЛІК) or (
        isinstance(в, ast.Call) and назва_виклику(в) == "заява")


def _гілка(б, м, вузли, гл=0):
    """→ ('облік'|'вирок'|None) для коду гілки: вирок правила чи облік «невідомо» в ній чи у функціях продукту, які
    вона кличе (до двох кроків)."""
    вирок = облік = False
    for с in вузли:
        for x in ast.walk(с):
            if _вирок(x):
                вирок = True
            elif _облік(x):
                облік = True
            elif isinstance(x, ast.Call) and гл < 2:
                ц = б.ціль_виклику(м, x) if м is not None else None
                if ц is not None:
                    р = _гілка(б, ц[0], ц[1].body, гл + 1)
                    вирок, облік = вирок or р == "вирок", облік or р == "облік"
    return "вирок" if вирок else ("облік" if облік else None)


def _вихід(вузли):
    """Гілка виходить з правила: кінчається `continue`/`break`/`return` чи лише `pass`."""
    return bool(вузли) and (isinstance(вузли[-1], (ast.Continue, ast.Break, ast.Return))
                            or all(isinstance(с, ast.Pass) for с in вузли))


def _далі(м, с):
    """Інструкції після `с` до кінця тіла циклу чи функції, у яких вона стоїть (вкладені блоки — їхній хвіст)."""
    вих = []
    while с is not None and not isinstance(с, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Module)):
        бат = м.батько.get(с)
        for поле in ("body", "orelse", "finalbody"):
            блок = getattr(бат, поле, None)
            if isinstance(блок, list) and с in блок:
                вих += блок[блок.index(с) + 1:]
                break
        if isinstance(бат, (ast.For, ast.AsyncFor, ast.While)):
            break
        с = бат
    return вих


def _читані_ключі(л):
    """Ключі, які код продукту читає: `x["к"]`, `x.get("к")` у Python, `.к` чи `"к"` у JS і HTML."""
    вих = set()
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if isinstance(в, ast.Subscript) and isinstance(в.ctx, ast.Load) and isinstance(в.slice, ast.Constant) \
                    and isinstance(в.slice.value, str):
                вих.add(в.slice.value)
            elif isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" and в.args \
                    and isinstance(в.args[0], ast.Constant) and isinstance(в.args[0].value, str):
                вих.add(в.args[0].value)
    тексти = "\n".join(т for _, т in л.js)
    return вих, тексти


def _поля_назовні(б, в_, м, корінь, env, читані):
    """Поле словника, що несе порожнечу відповіді (перелік, який пише лише гілка «так» чи фільтр відповіді), а код
    продукту його не читає — воно йде моделі, людині чи звіту без «невідомо» (рішення 07.11, 13967)."""
    ключі, тексти = читані
    вих = []
    for в in б.вузли[id(корінь)]:
        пари = []
        if isinstance(в, ast.Dict):
            пари = [(к.value, з) for к, з in zip(в.keys, в.values)
                    if isinstance(к, ast.Constant) and isinstance(к.value, str)]
        elif isinstance(в, ast.Call) and isinstance(в.func, ast.Name) and в.func.id == "dict":
            пари = [(к.arg, к.value) for к in в.keywords if к.arg]
        for ключ, з in пари:
            оо = {о for о, ш in в_.т(м, з, env) if ш == (ПОРОЖНЯ,)}
            if not оо or ключ in ключі or re.search(r"[.'\"`]%s\b" % re.escape(ключ), тексти):
                continue
            вих.append((з.lineno, "%s=…" % ключ, оо))
    return вих


def п6г_місця(б, виробники, вердикти=None):
    """→ місця [(файл, рядок, текст, доказ)], не місця [(файл, рядок, текст, причина)] читачів «невідомо»."""
    вердикти = ВЕРДИКТИ_Г if вердикти is None else вердикти
    в_ = Відповіді(б, виробники)
    в_.обчислити()
    читані = _читані_ключі(б.л)
    місця, не = [], []
    for м, ф in б.функції:
        корінь = ф if ф is not None else м.дерево
        env = в_.лок.get(id(корінь), {})
        ім = ф.name if ф is not None else "<модуль>"
        номер = 0
        відомо = {}                  # id(вузла) → виробники, чия відповідь там відома (гілка «так» читача)
        читачі = []                  # (рядок, текст, виробники, вид, «умова на істинність»)
        for в in sorted(б.вузли[id(корінь)], key=lambda x: (getattr(x, "lineno", 0), getattr(x, "col_offset", 0))):
            if not isinstance(в, (ast.If, ast.While, ast.IfExp)) or _під_main(м, в):
                continue
            # умова самого виробника (`if а - б > похибка: return 1`) — не читач: вона і є відповідь
            несуть = [(к, порівн) for к, порівн in _кандидати(в.test)
                      if id(к) not in в_.виробники and _відповідь(в_.т(м, к, env))]
            if not несуть:
                continue
            виробн = {о for к, _ in несуть for о in _відповідь(в_.т(м, к, env))}
            # усередині гілки «так» читача тієї самої відповіді вона відома — умова там не читає «невідомо»
            if виробн <= відомо.get(id(в), set()):
                continue
            зн = _при_невідомому(в.test, {id(к) for к, _ in несуть})
            if isinstance(в, ast.If) and зн is not None:
                for с in (в.orelse if зн else в.body):
                    for x in ast.walk(с):
                        відомо.setdefault(id(x), set()).update(виробн)
            вид, мовчить = None, False
            if isinstance(в, ast.IfExp):
                гілка = в.body if зн else в.orelse
                if зн is not None and isinstance(гілка, ast.Constant) and гілка.value is None:
                    вид = ("Н", "на «невідомо» вираз дає None — «невідомо» йде далі")
                elif зн is not None and isinstance(гілка, ast.Constant) and гілка.value in СИЛА_ВИРОКУ:
                    вид = ("М", "на «невідомо» вираз дає силу вироку «%s»" % гілка.value)
                elif зн is not None and isinstance(гілка, ast.IfExp):
                    вид = ("Н", "на «невідомо» вирішує наступна умова виразу")
            elif isinstance(в, ast.If) and зн is not None:
                гілка, інша = (в.body, в.orelse) if зн else (в.orelse, в.body)
                if len(гілка) == 1 and isinstance(гілка[0], ast.If) and any(
                        id(к) not in в_.виробники and _відповідь(в_.т(м, к, env)) for к, _ in _кандидати(гілка[0].test)):
                    вид = ("Н", "на «невідомо» вирішує наступна умова (`elif`), сама читач")
                elif гілка:
                    р = _гілка(б, м, гілка)
                    if р == "вирок":
                        вид = ("М", "на «невідомо» гілка дає вирок правила")
                    elif р == "облік":
                        вид = ("Н", "на «невідомо» — «утримано», «питання» чи заява")
                    elif _вихід(гілка):
                        вид = ("М", "на «невідомо» гілка виходить з правила (`%s`) без «утримано» й заяви"
                               % type(гілка[-1]).__name__.lower())
                    else:
                        вид = ("Н", "на «невідомо» гілка не виходить і вироку не дає")
                elif _гілка(б, м, інша) == "вирок" and _гілка(б, м, _далі(м, в)) != "облік":
                    вид, мовчить = ("М", "умова на істинність: вирок правила лише на «так», на «невідомо» — "
                                         "мовчання без «утримано» й заяви"), True
                elif _заява_в(б, м, інша) and not any(_не_судить(x) for с in _далі(м, в) for x in ast.walk(с)):
                    вид, мовчить = ("М", "умова на істинність: заява правила лише на «так», на «невідомо» — "
                                         "мовчання без «утримано» й заяви «не судить»"), True
                else:
                    вид = ("Н", "на «невідомо» гілка не виходить")
            if вид is None:
                номер += 1
                вер = вердикти.get((м.шлях, ім, номер))
                вид = ((вер[0], "за таблицею (%s#%d): %s" % (ім, номер, вер[1])) if вер
                       else ("М", "п.? — вердикту нема (%s#%d): потік не розрізняє, куди йде «невідомо»" % (ім, номер)))
            читачі.append((в.test.lineno, ast.unparse(в.test)[:70], виробн, вид, мовчить, в))
        # «невідомо» тієї самої відповіді вже обліковано іншим читачем у функції (`if б is None: утримано`, далі
        # `if б == 1: вирок`) — умова на істинність після нього не мовчить
        облік = [(р, вв, вуз) for р, _, вв, вид, _, вуз in читачі if вид[0] == "Н" and "утримано" in вид[1]]

        def після(вуз, в):
            """`в` стоїть у коді після умови `вуз` (не в іншій гілці тієї самої розвилки)."""
            с = м.батько.get(вуз) if isinstance(вуз, ast.IfExp) else вуз
            return any(x is в for с_ in _далі(м, с) for x in ast.walk(с_))
        for рядок, текст, виробн, вид, мовчить, в in читачі:
            # умова на істинність — після чи до обліку; вихід — лише після нього (`якщо is None: continue`)
            інший = next((р for р, вв, вуз in облік if вв & виробн and (мовчить and р != рядок or після(вуз, в))),
                         None) \
                if вид[0] == "М" else None
            if інший:
                вид = ("Н", "«невідомо» тієї самої відповіді обліковує читач рядка %d" % інший)
            звідки = "відповідь %s" % ", ".join(sorted(виробн)[:3]) + (" …" if len(виробн) > 3 else "")
            if вид[0] == "М":
                місця.append((м.шлях, рядок, текст, "%s — %s" % (вид[1], звідки)))
            else:
                не.append((м.шлях, рядок, текст, "читач «невідомо»: %s — %s" % (вид[1], звідки)))
        for рядок, текст, виробн in _поля_назовні(б, в_, м, корінь, env, читані):
            місця.append((м.шлях, рядок, текст, "поле несе порожнечу відповіді назовні (моделі, людині, звіту): "
                                               "код продукту його не читає, «невідомо» поряд нема — відповідь %s"
                                               % ", ".join(sorted(виробн)[:3])))
    return місця, не


НЕВІДОМО_Т = re.compile(r"unknown|невідом", re.I)


def канон(в, присв, гл=0):
    """Вираз з підставленими одноразовими локальними присвоєннями — та сама величина в різних функціях."""
    class Підст(ast.NodeTransformer):
        def visit_Name(self, н):
            if н.id in присв and гл < 4:
                return канон(присв[н.id], присв, гл + 1)
            return н

        def visit_IfExp(self, н):
            # `x if знаменник else 0.0` — та сама величина x з вартовим ділення (`ролі_зон` проти `fit.зони`)
            if isinstance(н.orelse, ast.Constant) and isinstance(н.orelse.value, (int, float)) \
                    and not isinstance(н.orelse.value, bool):
                return self.visit(н.body)
            return self.generic_visit(н)
    return Підст().visit(ast.parse(ast.unparse(в), mode="eval").body)


def п1г_місця(л, назва_виклику):
    """п.1(г): та сама величина (однаковий вираз з тих самих полів) — одна функція зве її бік за межею, друга —
    «невідомо». → місця [(файл, рядок, текст, доказ)], не місця [(файл, рядок, текст, причина)]."""
    групи = {}
    for м in л.модулі:
        for ф in ast.walk(м.дерево):
            if not isinstance(ф, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            присв, лік = {}, {}
            for в in ast.walk(ф):
                if isinstance(в, ast.Assign):
                    for ц in в.targets:
                        пари = zip(ц.elts, в.value.elts) if isinstance(ц, ast.Tuple) and isinstance(
                            в.value, ast.Tuple) and len(ц.elts) == len(в.value.elts) else [(ц, в.value)]
                        for ц1, з1 in пари:
                            if isinstance(ц1, ast.Name):
                                присв[ц1.id] = з1
                                лік[ц1.id] = лік.get(ц1.id, 0) + 1
            присв = {к: з for к, з in присв.items() if лік[к] == 1}
            for ім, з in присв.items():
                if not any(isinstance(к, ast.BinOp) and isinstance(к.op, (ast.Sub, ast.Div)) for к in ast.walk(з)):
                    continue
                к = канон(з, {і: зз for і, зз in присв.items() if і != ім})
                if sum(isinstance(x, ast.Subscript) for x in ast.walk(к)) < 2:
                    continue
                групи.setdefault(ast.dump(к), []).append((м, ф, ім))
    місця, не = [], []
    for ключ, сайти in групи.items():
        if len({id(ф) for _, ф, _ in сайти}) < 2:
            continue
        зве, невід = [], []
        for м, ф, ім in сайти:
            for в in ast.walk(ф):
                if isinstance(в, ast.Compare) and any(isinstance(о, ПОРІВНЯННЯ) for о in в.ops) and any(
                        isinstance(x, ast.Name) and x.id == ім for x in [в.left] + в.comparators) and not any(
                        isinstance(x, ast.Constant) and x.value == 0 for x in [в.left] + в.comparators):
                    зве.append((м, ф, в.lineno, ast.unparse(в)[:60]))
            for с in ast.walk(ф):
                if isinstance(с, ast.stmt) and not isinstance(с, (ast.FunctionDef, ast.If, ast.For, ast.While, ast.With,
                                                                    ast.Try)) \
                        and any(isinstance(x, ast.Name) and x.id == ім for x in ast.walk(с)):
                    for x in ast.walk(с):
                        if isinstance(x, ast.Constant) and isinstance(x.value, str) and НЕВІДОМО_Т.search(x.value):
                            невід.append((м, ф, x.lineno, x.value[:60]))
        if not зве or not невід or {id(ф) for _, ф, *_ in зве} == {id(ф) for _, ф, *_ in невід}:
            continue
        імена_зве = {ф.name for _, ф, *_ in зве}
        for м, ф, р, т in зве:
            if id(ф) in {id(ф2) for _, ф2, *_ in невід}:
                continue
            місця.append((м.шлях, р, т, "бік величини за межею тут, а %s — «невідомо» для тієї самої величини" % (
                ", ".join(sorted({"%s:%d" % (м2.шлях.split("/")[-1], р2) for м2, _, р2, _ in невід})))))
        for м, ф, р, т in невід:
            місця.append((м.шлях, р, т, "бік тієї самої величини — «невідомо», а %s зве його за межею" % (
                ", ".join(sorted({"%s:%d" % (м2.шлях.split("/")[-1], р2) for м2, _, р2, _ in зве})))))
        # читачі відповіді, що зве бік, — не місця: самі величини не визначають
        for м in л.модулі:
            for в in ast.walk(м.дерево):
                if isinstance(в, ast.Call) and назва_виклику(в) in імена_зве:
                    не.append((м.шлях, в.lineno, ast.unparse(в)[:60], "читає відповідь «%s», величини сам не "
                                                                      "визначає" % назва_виклику(в)))
    return місця, не


# ── п.7: орієнтир величини тіла — де жінка міряє обхват і яку точку тіла означає рівень шаблону ─────────────────
# Клас (менеджер 06.11, 13854–13856): орієнтир задає не означення бази знань, а де його нема — не визнане джерело з
# посиланням, чи форма, шаблон і правила під одним іменем мають різні орієнтири. Точки, що ОЗНАЧУЮТЬ орієнтир:
#   шаблон — таблиця (імʼя рівня, частка зросту), яку код множить на зріст (`areas.РІВНІ`): частка — точка тіла;
#   похідний рівень — точка тіла, названа словом, з висотою як середина двох рівнів шаблону;
#   форма — поле обхвату (`<input>` з одиницею, ключ — пара `['мр-…', 'ключ']` у JS) і текст, що каже, де міряти
#   (підказка `<i>` у підписі поля, інакше найближчий `<p>` перед ним у тому самому `<section>`);
#   питання жінці — рядок коду з «обхват <рівня> <де>», що питає («?») чи стоїть у сталій `…ПИТАННЯ`;
#   таблиця слів орієнтира — пари (слово про точку тіла, рівень шаблону), а код слова — зі словника тих самих слів;
#   точка речі на рівні тіла (менеджер 06.11 «точка речі», #3233): таблиця «слово чи точка речі → рівень» (довжина
#   «midi», посадка пояса, точка, від якої міряє крамниця, клас шкали довжини, що позичає імена рівнів) і вбудована
#   відповідність `IfExp` — місце без означення бази й джерела з посиланням чи з означенням бази деінде.
# Означення бази — будь-яке місце бази, що називає точку тіла під іменем рівня (`п7_точки_фрази`); два різні означення
# під одним іменем (литка: найширша K-SHO-05 і найвужча K-SIL-10) — дві величини: рівень шаблону бере те, що в записі
# його джерела, друге друкується окремим рядком і робить місцем точку, що на нього спирається.
# Читач рівня (`H["талія"]`, `висоти[…]`, `ТАБЛИЦЯ.get(слово)`) орієнтира не означує — не місце (як читач відповіді в
# п.1(г)). Не місця: таблиця «рівень → слово тіла» (`ХАЛЯВА_СЛОВОМ`: «коліно» → «коліна»); тотожне «слово → клас»;
# маківка й підлога (частки 1 і 0 — межі зросту за означенням); демонстрація під `if __name__ == "__main__"`.
П7_ОЗНАКИ = (
    ("найширше", re.compile(r"найширш|найповн|найбільш|fullest|largest|widest", re.I)),
    ("найвужче", re.compile(r"найвужч|найменш|smallest|narrowest", re.I)),
    ("природна талія", re.compile(r"природн\w*\s+тал|natural\s+waist", re.I)),
    ("наколінок", re.compile(r"наколін|kneecap|patella", re.I)),
    ("кісточка", re.compile(r"кісточ|malleol", re.I)),
    ("відстань", re.compile(r"\d+\s*(?:см|cm|inch\w*|″|\")\s*(?:\([^)]*\)\s*)?(?:нижче|вище|below|above)", re.I)),
    ("середина", re.compile(r"середин|\bmid", re.I)),
    ("верх", re.compile(r"верхн|\bupper", re.I)),
    ("під", re.compile(r"\bпід\s|\bunder", re.I)),
)
П7_ЗАПЕРЕЧЕННЯ = re.compile(r"\*?\bnot\b\*?|\bне\s+(?:є|по\s)", re.I)
# Означення бази знань (рішення 06.11 «орієнтири тіла» п.2–4): тема-1 §2.1 — назви вимірів формул FFIT; коліно й
# щиколотка — фрази, які рішення назвало; означення читається з тексту бази, зникне фраза — зникне й означення.
БАЗА_ТІЛА_2_1 = {"Bust": "груди", "Waist": "талія", "High hip": "високе_стегно", "Hip": "стегна"}
БАЗА_ТІЛА_ФРАЗИ = {"коліно": (r"bisect the kneecap", ("наколінок",), "knee"),
                   "щиколотка": (r"ankle strap cuts it at the narrowest point", ("найвужче",), "ankle")}
# Виміри поза профілем, які форма просить із підказкою, і фраза бази, що їх означує (тема-10).
БАЗА_ВИМІРІВ = {"голова_см": r"Head circumference is measured", "довжина_стопи_мм": r"Foot length\W+is defined"}
П7_ПОСИЛАННЯ = re.compile(ПОСИЛАННЯ.pattern + r"|ANSUR|ISO\s*\d{3,}")


# Будь-яке місце бази, що називає точку тіла під іменем рівня (рішення 06.11 «точка речі», п.3; 13870): ознака й
# англійський іменник тіла в одній фразі — «widest part of the calf», «narrowest point of the calf», «natural
# waist», «mid-hip». Іменник → рівень шаблону; «thigh» рівня не має (None): точка є, рівня під нею нема.
П7_ІМЕННИКИ = {"calf": "литка", "calves": "литка", "knee": "коліно", "knees": "коліно", "kneecap": "коліно",
              "ankle": "щиколотка", "ankles": "щиколотка", "waist": "талія", "bust": "груди", "hip": "стегна",
              "hips": "стегна", "shoulder": "плечі", "shoulders": "плечі", "crotch": "пах", "chin": "підборіддя",
              "thigh": None, "thighs": None}
_П7_ІМ = r"(?:" + "|".join(sorted(П7_ІМЕННИКИ, key=len, reverse=True)) + r")"
_П7_ОЗН = r"(?:widest|narrowest|fullest|largest|smallest|natural|middle)"
П7_ТОЧКА_БАЗИ = re.compile(
    r"\b(?P<о1>" + _П7_ОЗН + r")\s+(?:(?:part|point|place|circumference)\s+)?(?:(?:of|at|over)\s+(?:the|her|your)\s+)?"
    r"(?P<і1>" + _П7_ІМ + r")\b|\b(?P<і2>" + _П7_ІМ + r")\s+at\s+(?:its|the)\s+(?P<о2>" + _П7_ОЗН + r")\b"
    r"|\bmid-(?P<і3>" + _П7_ІМ + r")\b", re.I)
# Точка речі в базі: ще й прийменник перед іменником — «Above the Knee», «at the ankle» (вище, нижче, на).
П7_ПРИЙМЕННИК = re.compile(r"\b(?P<п>above|below|at|on|to|over)\s+the\s+(?P<mid>mid-)?(?P<і>" + _П7_ІМ + r")\b", re.I)
П7_ПРИЙМЕННИК_ОЗН = {"above": "вище", "below": "нижче"}


def п7_точки_фрази(фраза, з_прийменником=False):
    """Точки тіла, які називає фраза бази: [(позиція, рівень | None, ознаки, текст)]. Ознаки — ті самі імена, що в
    `П7_ОЗНАКИ`; «mid-» — середина; прийменник: above — вище, below — нижче, at/on/to/over — сама точка (без ознаки)."""
    вих = []
    for з in П7_ТОЧКА_БАЗИ.finditer(фраза):
        ім = (з.group("і1") or з.group("і2") or з.group("і3")).lower()
        озн = п7_ознаки(з.group(0)) | (frozenset({"середина"}) if з.group("і3") else frozenset())
        вих.append((з.start(), П7_ІМЕННИКИ[ім], озн, з.group(0)))
    if з_прийменником:
        for з in П7_ПРИЙМЕННИК.finditer(фраза):
            if any(п <= з.start("і") < п + len(т) for п, _, _, т in вих):
                continue
            озн = {П7_ПРИЙМЕННИК_ОЗН[з.group("п").lower()]} if з.group("п").lower() in П7_ПРИЙМЕННИК_ОЗН else set()
            if з.group("mid"):
                озн.add("середина")
            вих.append((з.start(), П7_ІМЕННИКИ[з.group("і").lower()], frozenset(озн), з.group(0)))
    return sorted(вих, key=lambda х: х[0])


def п7_фрази_бази(тексти):
    """Фрази бази (речення, пункт «·», рядок) без заперечення: [(файл, рядок, фраза)]."""
    вих = []
    for ф, т in тексти:
        for і, рядок in enumerate(т.split("\n"), 1):
            for фр in re.split(r"(?<=[.;!?])\s+|\s+·\s+", рядок):
                if фр.strip() and not П7_ЗАПЕРЕЧЕННЯ.search(фр):
                    вих.append((ф, і, фр))
    return вих


def п7_ознаки(текст):
    """Ознаки орієнтира в тексті (речення із запереченням — «not the widest point» — не означують)."""
    речення = [р for р in re.split(r"(?<=[.;])\s+", re.sub(r"\s+", " ", текст or "")) if not П7_ЗАПЕРЕЧЕННЯ.search(р)]
    т = " ".join(речення)
    return frozenset(ім for ім, рег in П7_ОЗНАКИ if рег.search(т))


def п7_база(корінь):
    """З `джерела/тема-*.md`: {рівень: (ознаки, іменник англійською, де в базі)} — §2.1 і фрази рішення;
    {вимір поза профілем: де в базі}; {рівень: [(ознаки, іменник, де)]} — кожне інше місце бази, що називає точку
    тіла під іменем рівня (`п7_точки_фрази`), у порядку файлів і рядків; [(файл, текст)] — тексти бази."""
    дж = os.path.join(корінь, "джерела")
    рівні, виміри, загальні, тексти = {}, {}, {}, []
    if not os.path.isdir(дж):
        return рівні, виміри, загальні, тексти
    for ф in sorted(os.listdir(дж)):
        if not (ф.startswith("тема-") and ф.endswith(".md")):
            continue
        with open(os.path.join(дж, ф), encoding="utf-8", errors="replace") as д:
            т = д.read()
        тексти.append((ф.split("_")[0], т))
        с = re.search(r"^###\s*2\.1\b[^\n]*\n(.*?)(?=^#)", т, re.M | re.S)
        if с:
            поч = т[:с.start(1)].count("\n") + 1
            for п in re.finditer(r"^- \*\*(.+?)\*\*\s*[—–-]\s*(.+?)(?=^- |^\s*$|\Z)", с.group(1), re.M | re.S):
                рівень = БАЗА_ТІЛА_2_1.get(п.group(1).strip())
                if рівень and рівень not in рівні:
                    рівні[рівень] = (п7_ознаки(п.group(2)), п.group(1).strip().split()[-1].lower(),
                                     "%s:%d §2.1 «%s — %s»" % (ф.split("_")[0], поч + с.group(1)[:п.start()].count("\n"),
                                                              п.group(1).strip(), " ".join(п.group(2).replace("*", "").split())[:60]))
        for рівень, (фраза, озн, іменник) in БАЗА_ТІЛА_ФРАЗИ.items():
            з = re.search(фраза, т)
            if з and рівень not in рівні:
                рівні[рівень] = (frozenset(озн), іменник, "%s:%d «%s»" % (ф.split("_")[0], т[:з.start()].count("\n") + 1,
                                                                        з.group(0)))
        for вимір, фраза in БАЗА_ВИМІРІВ.items():
            з = re.search(фраза, т)
            if з and вимір not in виміри:
                виміри[вимір] = "%s:%d" % (ф.split("_")[0], т[:з.start()].count("\n") + 1)
    for ф, і, фр in п7_фрази_бази(тексти):
        for _, рівень, озн, текст in п7_точки_фрази(фр):
            if рівень is not None and озн:
                загальні.setdefault(рівень, []).append((озн, текст.split()[-1].lower(), "%s:%d «%s»" % (ф, і, текст)))
    return рівні, виміри, загальні, тексти


def _під_main(м, в):
    б = м.батько.get(в)
    while б is not None:
        if isinstance(б, ast.If) and "__name__" in ast.unparse(б.test) and "__main__" in ast.unparse(б.test):
            return True
        б = м.батько.get(б)
    return False


def _коментар_над(рядки, рядок):
    """Коментар над рядком (суцільний блок `#`), без речень, що кажуть про відсутність джерела («ні в ANSUR»,
    «посилання НЕ мають», «без джерела»): згадка джерела в такому реченні — не посилання."""
    коментар, і = [], рядок - 2
    while і >= 0 and рядки[і].lstrip().startswith("#"):
        коментар.append(рядки[і].lstrip("# "))
        і -= 1
    речення = re.split(r"(?<=[.;])\s+", " ".join(reversed(коментар)))
    return " ".join(р for р in речення if not П7_БЕЗ_ДЖЕРЕЛА.search(р))


П7_БЕЗ_ДЖЕРЕЛА = re.compile(r"\bні\s+в\b|\bнема\b|\bбез\s+(?:джерел|посилан)|\bНЕ\b|\bне\s+мають\b|\bnot\b", re.I)


def _сталий_рядок(м, ім):
    """Текст модульної сталої-рядка `ім` у модулі `м` (для пошуку посилання), або ''."""
    for в in м.дерево.body:
        if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id == ім for ц in в.targets):
            return " ".join(р for р in (з.value for з in ast.walk(в.value) if isinstance(з, ast.Constant))
                            if isinstance(р, str))
    return ""


def _словник_модуля(м, ім):
    for в in м.дерево.body:
        if isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name) \
                and в.targets[0].id == ім and isinstance(в.value, ast.Dict):
            return в.value
    return None


def п7_словники_частки(л, м, ф, звʼязки, глибина=0):
    """Словники, з яких функція `ф` (модуль `м`) бере частку рівня за іменем рівня, — значенням: `D[рівень]` чи
    `D[<стала>][рівень]` модульного словника-літерала (сталу дає звʼязаний параметр), і те саме у функціях, які
    `ф` кличе (параметри звʼязуються сталими аргументами). → [(модуль, ast.Dict)]."""
    if глибина > 3 or ф is None:
        return []
    вих = []
    параметри = [а.arg for а in ф.args.posonlyargs + ф.args.args]
    for в in ast.walk(ф):
        б = м.батько.get(в)
        if isinstance(в, ast.Subscript) and isinstance(б, ast.Subscript) and б.value is в:
            continue                      # внутрішня ланка ланцюга `D[a][b]` — береться з зовнішньої
        if isinstance(в, ast.Subscript):
            ланцюг, к = [], в
            while isinstance(к, ast.Subscript):
                ланцюг.append(к.slice)
                к = к.value
            if not isinstance(к, ast.Name):
                continue
            ланцюг.reverse()
            д = _словник_модуля(м, к.id)
            if д is None or not (isinstance(ланцюг[-1], ast.Name) and ланцюг[-1].id in параметри
                                 and ланцюг[-1].id not in звʼязки):
                continue
            for сл in ланцюг[:-1]:
                ключ = сл.value if isinstance(сл, ast.Constant) else звʼязки.get(getattr(сл, "id", None))
                д = next((з for кк, з in zip(д.keys, д.values) if isinstance(кк, ast.Constant) and кк.value == ключ),
                         None) if д is not None else None
                if not isinstance(д, ast.Dict):
                    д = None
                    break
            if д is not None:
                вих.append((м, д))
        elif isinstance(в, ast.Call):
            ім = назва_виклику(в)
            if isinstance(в.func, ast.Name):
                мод = м.імпорт_імен.get(ім, м.ім)
            elif isinstance(в.func, ast.Attribute) and isinstance(в.func.value, ast.Name):
                мод = м.псевдо.get(в.func.value.id)
            else:
                continue
            цілі = визначення_в(л, мод, ім)
            if len(цілі) != 1:
                continue
            мц, фц = цілі[0]
            пц = [а.arg for а in фц.args.posonlyargs + фц.args.args]
            зв = {}
            рівень_передано = False
            for і, а in enumerate(в.args):
                if і >= len(пц):
                    break
                if isinstance(а, ast.Constant):
                    зв[пц[і]] = а.value
                elif isinstance(а, ast.Name) and а.id in параметри and а.id not in звʼязки:
                    рівень_передано = True
            if рівень_передано:
                вих += п7_словники_частки(л, мц, фц, зв, глибина + 1)
    return вих


def _частка_запису(м, з):
    """(частка | None, посилання?, текст запису) значення словника частки: число; виклик чи `dict(...)` — перший
    позиційний аргумент чи `середнє=`/`частка=`; посилання — у рядках запису й у сталих-рядках, які він читає."""
    ч = число(з)
    if ч is not None:
        return ч, False, ""
    if not isinstance(з, ast.Call):
        return None, False, ""
    сире = з.args[0] if з.args else next((к.value for к in з.keywords if к.arg in ("середнє", "частка")), None)
    тексти = [в.value for в in ast.walk(з) if isinstance(в, ast.Constant) and isinstance(в.value, str)]
    тексти += [_сталий_рядок(м, в.id) for в in ast.walk(з) if isinstance(в, ast.Name)]
    текст = " ".join(тексти)
    return (число(сире) if сире is not None else None), bool(П7_ПОСИЛАННЯ.search(текст)), текст


def п7_шаблони(л):
    """Таблиці рівнів шаблону: (модуль, вузол присвоєння, імʼя, [дані рівня]) — значенням: змінна-частка циклу по
    таблиці множиться в генераторі. Таблиця — пари (рядок, число в [0, 1]) ≥ 5, монотонні; або
    `[(nm, F(nm)) for nm in ПОРЯДОК]` з ≥ 5 імен рівнів, де частку дає функція F: словник-літерал і записи
    реєстру, з яких F бере частку за іменем рівня (`п7_словники_частки`). Дані рівня — dict(рівень, частка, файл,
    рядок, посилання, текст): кожне місце, де частку рівня записано числом; запис без числа (None) — частки не
    означує й не входить."""
    рез = []
    for м in л.модулі:
        for в in м.дерево.body:
            if not (isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name)):
                continue
            пари = []
            if isinstance(в.value, (ast.List, ast.Tuple)) and len(в.value.elts) >= 5:
                for е in в.value.elts:
                    if isinstance(е, ast.Tuple) and len(е.elts) == 2 and isinstance(е.elts[0], ast.Constant) \
                            and isinstance(е.elts[0].value, str) and число(е.elts[1]) is not None \
                            and 0 <= число(е.elts[1]) <= 1:
                        пари.append(dict(рівень=е.elts[0].value, частка=число(е.elts[1]), файл=м.шлях,
                                         рядок=е.lineno, посилання=None, текст=""))
                if len(пари) != len(в.value.elts):
                    continue
                ч = [п["частка"] for п in пари]
                if not (ч == sorted(ч) or ч == sorted(ч, reverse=True)):
                    continue
            elif isinstance(в.value, ast.ListComp) and len(в.value.generators) == 1:
                ген, елт = в.value.generators[0], в.value.elt
                if not (isinstance(ген.target, ast.Name) and isinstance(ген.iter, ast.Name)
                        and isinstance(елт, ast.Tuple) and len(елт.elts) == 2
                        and isinstance(елт.elts[0], ast.Name) and елт.elts[0].id == ген.target.id
                        and isinstance(елт.elts[1], ast.Call) and isinstance(елт.elts[1].func, ast.Name)):
                    continue
                порядок = next((п.value for п in м.дерево.body if isinstance(п, ast.Assign)
                                and any(isinstance(ц, ast.Name) and ц.id == ген.iter.id for ц in п.targets)), None)
                if not (isinstance(порядок, (ast.Tuple, ast.List)) and len(порядок.elts) >= 5
                        and all(isinstance(е, ast.Constant) and isinstance(е.value, str) for е in порядок.elts)):
                    continue
                рівні = [е.value for е in порядок.elts]
                ф = next((д for мм, д in визначення_в(л, м.ім, елт.elts[1].func.id)), None)
                словники = п7_словники_частки(л, м, ф, {})
                for р in рівні:
                    for мс, д in словники:
                        for к, з in zip(д.keys, д.values):
                            if not (isinstance(к, ast.Constant) and к.value == р):
                                continue
                            ч, посилання, текст = _частка_запису(мс, з)
                            if ч is not None and 0 <= ч <= 1:
                                пари.append(dict(рівень=р, частка=ч, файл=мс.шлях, рядок=к.lineno,
                                                 посилання=посилання, текст=текст))
                            elif ч is None and текст:
                                пари.append(dict(рівень=р, частка=None, файл=мс.шлях, рядок=к.lineno,
                                                 посилання=посилання, текст=текст))
                if not пари:
                    for р in рівні:
                        пари.append(dict(рівень=р, частка=None, файл=м.шлях, рядок=в.lineno, посилання=None,
                                         текст=""))
            else:
                continue
            ім = в.targets[0].id
            множить = False
            for г in ast.walk(м.дерево):
                if isinstance(г, (ast.ListComp, ast.GeneratorExp, ast.SetComp, ast.DictComp)):
                    for ген in г.generators:
                        if isinstance(ген.iter, ast.Name) and ген.iter.id == ім and isinstance(ген.target, ast.Tuple):
                            змінні = {н.id for н in ген.target.elts if isinstance(н, ast.Name)}
                            if any(isinstance(б, ast.BinOp) and isinstance(б.op, ast.Mult)
                                   and ({getattr(б.left, "id", None), getattr(б.right, "id", None)} & змінні)
                                   for б in ast.walk(г)):
                                множить = True
            if множить:
                рез.append((м, в, ім, пари))
    return рез


def _основи_рівня(рівень):
    return [ч[:4] for ч in рівень.split("_") if ч]


def п7_рівень_слова(слова, рівні):
    """Рівень шаблону, чиї основи всі є в словах (більше основ — точніше: «високого стегна» — високе стегно)."""
    сл = (слова or "").lower()
    кращий = None
    for р in рівні:
        осн = _основи_рівня(р)
        if осн and all(re.search(r"(?<!\w)" + re.escape(о), сл) for о in осн):
            if кращий is None or len(осн) > len(_основи_рівня(кращий)):
                кращий = р
    return кращий


def _п7_значення_речі(в, словник):
    """Значення запису таблиці «річ → рівень»: [імена] (рядок; кортеж 1–2 рядків; кортеж (кортеж рядків, число)),
    [] для None, або None — не той вигляд. Імена мають бути в словнику рівнів."""
    if isinstance(в, ast.Constant) and в.value is None:
        return []
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return [в.value] if в.value in словник else None
    if isinstance(в, ast.Tuple) and len(в.elts) == 2 and isinstance(в.elts[0], ast.Tuple) and число(в.elts[1]) is not None:
        в = в.elts[0]
    if isinstance(в, ast.Tuple) and 1 <= len(в.elts) <= 2 and all(isinstance(е, ast.Constant) and е.value in словник
                                                                   for е in в.elts):
        return [е.value for е in в.elts]
    return None


def _п7_ключ_речі(в):
    """Слова ключа таблиці «річ → рівень»: рядок; кортеж рядків; `re.compile(<рядок>)` — шаблон. Інакше None."""
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        return [в.value]
    if isinstance(в, ast.Tuple) and в.elts and all(isinstance(е, ast.Constant) and isinstance(е.value, str)
                                                    for е in в.elts):
        return [е.value for е in в.elts]
    if isinstance(в, ast.Call) and назва_виклику(в) == "compile" and в.args and isinstance(в.args[0], ast.Constant) \
            and isinstance(в.args[0].value, str):
        return [в.args[0].value]
    return None


def п7_таблиці_речі(л, рівні):
    """Таблиці, що кладуть слово чи точку речі на рівень тіла, — значенням: модульний словник чи кортеж пар
    (ключ → значення), де кожне значення — рівень шаблону, None чи 1–2 рівні (і число поруч), а ключі — слова речі
    (рядок, кортеж рядків, `re.compile`), не слова про точку тіла (таблиця орієнтирів — окремо). Шкала довжини, що
    позичає імена рівнів (`композитор_річ.РІВЕНЬ_ЗОНА`: клас «литка» → рівні тіла), сама стає словником: таблиця
    «слово → клас» (`ДОВЖИНА_PARAM`: «міді» → «литка») кладе слово на той самий рівень. Пари бувають і навпаки —
    (клас, (слова…)). → [(модуль, вузол, імʼя, [(рядок, слова ключа, [імена])], значення — рівні тіла?, навпаки?)]."""
    кандидати = []
    for м in л.модулі:
        for в in м.дерево.body:
            if not (isinstance(в, ast.Assign) and len(в.targets) == 1 and isinstance(в.targets[0], ast.Name)):
                continue
            сирі = []
            if isinstance(в.value, ast.Dict) and в.value.keys:
                сирі = [(к, з, к.lineno if к is not None else з.lineno, False) for к, з in zip(в.value.keys, в.value.values)]
            elif isinstance(в.value, (ast.Tuple, ast.List)) and в.value.elts \
                    and all(isinstance(е, ast.Tuple) and len(е.elts) == 2 for е in в.value.elts):
                сирі = [(е.elts[0], е.elts[1], е.lineno, None) for е in в.value.elts]
            if сирі:
                кандидати.append((м, в, в.targets[0].id, сирі))
    словник = set(рівні)
    прийнято = {}
    while True:
        нове = False
        for м, в, ім, сирі in кандидати:
            if (м.шлях, ім) in прийнято:
                continue
            for навпаки in (False, True):
                записи = []
                for к, з, рядок, _ in сирі:
                    if навпаки:
                        к, з = з, к
                    слова, значення = _п7_ключ_речі(к), _п7_значення_речі(з, словник)
                    if слова is None or значення is None:
                        break
                    записи.append((рядок, слова, значення))
                else:
                    if not записи or not any(з for _, _, з in записи):
                        continue
                    if all(len(с) == 1 and з == с for _, с, з in записи):
                        continue                  # тотожна таблиця імен — не відповідність
                    if all(п7_рівень_слова(с[0], рівні) for _, с, з in записи if з):
                        continue                  # слова про точку тіла — таблиця орієнтирів (окремий розділ)
                    тіла = all(set(з) <= set(рівні) for _, _, з in записи)
                    прийнято[(м.шлях, ім)] = (м, в, ім, записи, тіла, навпаки)
                    # шкала, що позичає імена рівнів: ключі таблиці «клас → рівні тіла» — теж імена рівня
                    if тіла and not навпаки:
                        ключі = {с[0] for _, с, з in записи if len(с) == 1}
                        if ключі & set(рівні) and not ключі <= словник:
                            словник |= ключі
                            нове = True
                    break
        if not нове:
            break
    return [прийнято[к] for к in sorted(прийнято)]


def п7_точки_речі(л, рівні, база, подвійні, тексти_бази, не):
    """Місця точки речі на рівні тіла: [(файл, рядок, доказ)]; не місця дописує в `не`. Відповідність «слово чи
    точка речі → рівень» без означення бази й без джерела з посиланням — місце; означення бази, що кладе цю точку
    речі деінде (`midi` — «narrowest point of the calf», а рівень «литка» — найширше), — теж. Означення речі в
    базі — фраза зі словом речі (ключ чи його код `внутрішня_мова.ТАБЛИЦЯ`), де за ним до 15 слів названо точку
    тіла (`п7_точки_фрази` з прийменником). Ще місце — вбудована відповідність: `IfExp`, одна гілка якого — імʼя
    рівня, а друга читає таку таблицю (`фід_атрибути.довжина_виробу`: «від талії» → «талія»)."""
    вих = []
    таблиці = п7_таблиці_речі(л, рівні)
    коди = {}
    for м in л.модулі:
        if м.ім != ТАБЛИЦЯ_МОВИ:
            continue
        д = _словник_модуля(м, "ТАБЛИЦЯ")
        for вісь in (д.values if д is not None else ()):
            if isinstance(вісь, ast.Dict):
                for к, з in zip(вісь.keys, вісь.values):
                    if isinstance(к, ast.Constant) and isinstance(з, ast.Constant) and isinstance(з.value, str):
                        коди.setdefault(з.value.lower(), set()).add(str(к.value))
    фрази = п7_фрази_бази(тексти_бази)
    клас_у_тіло = {}
    for м, в, ім, записи, тіла, навпаки in таблиці:
        if тіла and not навпаки:
            for _, с, з in записи:
                if len(с) == 1 and з:
                    клас_у_тіло.setdefault(с[0], з)

    def означення_речі(слова):
        for слово in слова:
            for код in sorted({слово} | коди.get(слово.lower(), set())):
                if not re.fullmatch(r"[A-Za-z][A-Za-z_ -]*", код):
                    continue
                тілом = код.lower() in П7_ІМЕННИКИ
                рег = re.compile(r"\b" + re.escape(код.replace("_", " ")) + (r"[- ](?:length|high)\b" if тілом
                                                                              else r"\b"), re.I)
                for ф, і, фр in фрази:
                    всередині = [(п, п + len(т_)) for п, _, _, т_ in п7_точки_фрази(фр, з_прийменником=True)]
                    з = next((з for з in рег.finditer(фр)
                              if not any(п <= з.start() < к for п, к in всередині)), None)
                    if not з:
                        continue
                    хвіст = " ".join(re.split(r"[,;]", фр[з.end():])[0].split()[:15])
                    точки = п7_точки_фрази(хвіст, з_прийменником=True)
                    if точки:
                        return код, ["%s %s" % ("тіла" if р is None else "«%s»" % р, т) for _, р, _, т in точки], \
                            [(р, о) for _, р, о, _ in точки], "%s:%d" % (ф, і)
        return None

    def як_база(рівень, точки):
        з = база.get(рівень)
        return any(р == рівень and (not о or (з and о & з[0])) for р, о in точки)

    for м, в, ім, записи, тіла, навпаки in таблиці:
        рядки = open(os.path.join(л.корінь, м.шлях), encoding="utf-8", errors="replace").read().split("\n")
        над = _коментар_над(рядки, в.lineno)
        за_рядком = {}
        for рядок, слова, значення in записи:
            if not значення:
                continue
            що = "«%s» → %s" % (" | ".join(слова)[:40], " + ".join("«%s»" % з for з in значення))
            if len(слова) == 1 and значення == слова and not тіла:
                не.append((м.шлях, рядок, "%s.%s %s" % (м.ім, ім, що), "клас шкали довжини сам у собі — точки не кладе"))
                continue
            if П7_ПОСИЛАННЯ.search(рядки[рядок - 1]) or П7_ПОСИЛАННЯ.search(над):
                не.append((м.шлях, рядок, "%s.%s %s" % (м.ім, ім, що), "відповідність з посиланням на джерело"))
                continue
            тілом = [клас_у_тіло.get(з, [з]) for з in значення]
            озн = означення_речі(слова)
            if len(значення) == 1 and len(тілом[0]) == 1 and озн and як_база(тілом[0][0], озн[2]):
                не.append((м.шлях, рядок, "%s.%s %s" % (м.ім, ім, що), "як база: %s «%s» — %s" % (
                    озн[3], озн[0], "; ".join(озн[1]))))
                continue
            if озн:
                рівень = тілом[0][0] if len(тілом[0]) == 1 else None
                з = база.get(рівень) if рівень else None
                друга = рівень and next((а for а in подвійні.get(рівень, ())
                                         if any(р == рівень and о & а[0] for р, о in озн[2])), None)
                доказ = "%s: база кладе «%s» деінде (%s: %s)%s" % (
                    що, озн[0], озн[3], "; ".join(озн[1]),
                    (", а рівень «%s» — %s: дві величини під одним іменем" % (рівень, з[2]) if друга and з
                     else ""))
            else:
                доказ = "%s: без означення бази й без джерела з посиланням" % що
            різні = ["«%s» = %s" % (з, " + ".join(т_)) for з, т_ in zip(значення, тілом) if [з] != т_]
            if різні:
                доказ += " (на тілі — %s)" % ", ".join(різні)
            за_рядком.setdefault(рядок, []).append(доказ)
        for рядок, що in sorted(за_рядком.items()):
            вих.append((м.шлях, рядок, "точка речі на рівні тіла %s.%s: %s" % (м.ім, ім, "; ".join(що))))

    # ── вбудована відповідність: гілка `IfExp` — імʼя рівня, друга гілка читає таблицю «річ → рівень» ──
    імена_таблиць = {}
    for м, в, ім, записи, тіла, навпаки in таблиці:
        імена_таблиць[ім] = {з for _, _, зн in записи for з in зн}
    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if not isinstance(в, ast.IfExp) or _під_main(м, в):
                continue
            for гілка, інша in ((в.body, в.orelse), (в.orelse, в.body)):
                if not (isinstance(гілка, ast.Constant) and isinstance(гілка.value, str)):
                    continue
                таблиця = next((н.id if isinstance(н, ast.Name) else н.attr for н in ast.walk(інша)
                                if (isinstance(н, ast.Name) and н.id in імена_таблиць)
                                or (isinstance(н, ast.Attribute) and н.attr in імена_таблиць)), None)
                if таблиця and гілка.value in імена_таблиць[таблиця]:
                    вих.append((м.шлях, в.lineno, "точка речі на рівні тіла: вбудована відповідність «%s» → «%s» "
                                "поряд із таблицею %s, без означення бази й без джерела з посиланням"
                                % (ast.unparse(в.test)[:60], гілка.value, таблиця)))
    return вих


def п7_місця(л):
    """Місця п.7 і не місця: ([(файл, рядок, доказ)], [(файл, рядок, текст, причина)])."""
    місця, не = [], []
    база, виміри_бази, загальні, тексти_бази = п7_база(л.корінь)
    подвійні = {}                       # рівень → [означення бази з іншою точкою під тим самим іменем]
    л.п7_подвійні = подвійні
    л.п7_база = база

    def текст_файлу(шлях):
        with open(os.path.join(л.корінь, шлях), encoding="utf-8", errors="replace") as д:
            return д.read().split("\n")

    def з_бази(рівень):
        з = база.get(рівень)
        return "база: %s" % з[2] if з else "у базі означення нема"

    def суд(рівень, озн, з_посиланням, де):
        """Вирок одному означенню орієнтира: (місце?, доказ)."""
        з = база.get(рівень)
        if з:
            if not озн:
                return True, "%s: орієнтир не названо, %s" % (де, з_бази(рівень))
            if not (озн & з[0]):
                друга = next((а for а in подвійні.get(рівень, ()) if озн & а[0]), None)
                if друга:
                    return True, ("%s: «%s» — як друга точка бази під тим самим іменем (%s), а рівень «%s» — %s: "
                                  "дві величини під одним іменем" % (де, ", ".join(sorted(озн)), друга[2], рівень,
                                                                     з_бази(рівень)))
                return True, "%s: «%s», а %s — різні орієнтири під одним іменем" % (де, ", ".join(sorted(озн)),
                                                                                    з_бази(рівень))
            return False, "%s: «%s» — як %s" % (де, ", ".join(sorted(озн)), з_бази(рівень))
        if з_посиланням:
            return False, "%s: орієнтир з посиланням на джерело" % де
        if not озн:
            return True, "%s: орієнтир не названо, у базі означення нема, джерела нема" % де
        return True, "%s: «%s» без означення бази й без джерела з посиланням" % (де, ", ".join(sorted(озн)))

    # ── шаблон рівнів ──
    шаблони = п7_шаблони(л)
    рівні = set()
    for м, в, ім, пари in шаблони:
        рівні |= {п["рівень"] for п in пари}
    for м, в, ім, пари in шаблони:
        над_таблицею = _коментар_над(текст_файлу(м.шлях), в.lineno)
        за_рядком = {}
        for п in пари:
            р, ч, файл, рядок = п["рівень"], п["частка"], п["файл"], п["рядок"]
            if ч is None:
                continue
            що = "%s.%s «%s» %g" % (м.ім, ім, р, ч)
            if ч in (0, 1):
                не.append((файл, рядок, що, "частка %g — межа зросту за означенням, не орієнтир" % ч))
                continue
            рядки = текст_файлу(файл)
            if п["посилання"] or П7_ПОСИЛАННЯ.search(рядки[рядок - 1]) \
                    or П7_ПОСИЛАННЯ.search(_коментар_над(рядки, рядок)) \
                    or (файл == м.шлях and П7_ПОСИЛАННЯ.search(над_таблицею)):
                не.append((файл, рядок, що, "рівень з посиланням на джерело"))
                continue
            з = база.get(р)
            за_рядком.setdefault((файл, рядок), []).append(
                "«%s» %.3f зросту" % (р, ч) + (" (база: %s%s)" % (
                    з[2], "; база ставить точку відстанню, не часткою зросту" if "відстань" in з[0] else "")
                    if з else ""))
        for (файл, рядок), що in sorted(за_рядком.items()):
            місця.append((файл, рядок, "рівень шаблону %s.%s — частка зросту без означення бази й без джерела: %s"
                          % (м.ім, ім, "; ".join(що))))
    if not рівні:
        return місця, не

    # ── означення бази поза §2.1 і фразами рішення (13870): рівень без них бере точку з будь-якого місця бази;
    # два місця з різними точками під одним іменем — дві величини. Точка рівня шаблону — та, що в записі його
    # джерела (литка — CALF HEIGHT, «рівень найбільшого обхвату»: найширше, K-SHO-05), інакше — перша в базі ──
    записи_рівня = {}
    for м, в, ім, пари in шаблони:
        for п in пари:
            записи_рівня[п["рівень"]] = записи_рівня.get(п["рівень"], "") + " " + п["текст"]
    for р, означення in sorted(загальні.items()):
        if р not in база:
            озн_запису = п7_ознаки(записи_рівня.get(р, ""))
            база[р] = next((о for о in означення if о[0] & озн_запису), означення[0])
        інші = [о for о in означення if not (о[0] & база[р][0])]
        if інші:
            подвійні[р] = інші

    # ── похідний рівень: точка тіла, названа словом, — середина двох рівнів шаблону ──
    def ключ_рівня(в):
        if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and в.slice.value in рівні:
            return в.slice.value
        return None

    for м in л.модулі:
        for в in ast.walk(м.дерево):
            if not (isinstance(в, ast.BinOp) and isinstance(в.op, ast.Div) and число(в.right) == 2
                    and isinstance(в.left, ast.BinOp) and isinstance(в.left.op, ast.Add)):
                continue
            а, б = ключ_рівня(в.left.left), ключ_рівня(в.left.right)
            if not (а and б) or а == б:
                continue
            кортеж, п = None, м.батько.get(в)
            while п is not None and not isinstance(п, ast.stmt):
                if isinstance(п, ast.Tuple):
                    кортеж = п
                    break
                п = м.батько.get(п)
            слово = next((е.value for е in (кортеж.elts if кортеж else ()) if isinstance(е, ast.Constant)
                          and isinstance(е.value, str) and п7_рівень_слова(е.value, рівні)
                          is not None), None) if кортеж else None
            if слово is None:
                continue
            if _під_main(м, в):
                не.append((м.шлях, в.lineno, "«%s» = (%s + %s) / 2" % (слово, а, б),
                           "демонстрація під __main__ — не шлях продукту"))
                continue
            місця.append((м.шлях, в.lineno, "похідний рівень «%s» = середина рівнів «%s» і «%s» — точка тіла без "
                                             "означення бази й без джерела" % (слово, а, б)))

    # ── таблиця слів орієнтира: (слово про точку тіла, рівень шаблону | None), код слова — зі словника тих самих слів ──
    словники = []
    for м in л.модулі:
        for в in м.дерево.body:
            if isinstance(в, ast.Assign) and isinstance(в.value, ast.Dict) and в.value.keys:
                пари = {к.value: з.value for к, з in zip(в.value.keys, в.value.values)
                        if isinstance(к, ast.Constant) and isinstance(к.value, str)
                        and isinstance(з, ast.Constant) and isinstance(з.value, str)}
                if len(пари) == len(в.value.keys):
                    словники.append(пари)
    for м in л.модулі:
        for в in м.дерево.body:
            if not (isinstance(в, ast.Assign) and isinstance(в.value, (ast.Tuple, ast.List)) and len(в.value.elts) >= 3):
                continue
            пари = []
            for е in в.value.elts:
                if isinstance(е, ast.Tuple) and len(е.elts) == 2 and all(isinstance(х, ast.Constant) for х in е.elts) \
                        and isinstance(е.elts[0].value, str) and (е.elts[1].value is None or е.elts[1].value in рівні):
                    пари.append((е.elts[0].value, е.elts[1].value, е.lineno))
            # слово про точку тіла — українське слово з основою рівня (код довжини речі «midi», «knee» — не воно)
            if len(пари) != len(в.value.elts) or not all(п7_рівень_слова(с, рівні) or р is None for с, р, _ in пари) \
                    or sum(р is not None for _, р, _ in пари) < 3:
                continue
            коди = next((с for с in словники if sum(сл in с for сл, _, _ in пари) >= len(пари) - 1), {})
            за_рядком = {}
            for слово, р, рядок in пари:
                if р is None:
                    continue
                озн, код = п7_ознаки(слово), коди.get(слово)
                з = база.get(р)
                if з and код and з[1] not in re.split(r"[_\W]+", код.lower()):
                    за_рядком.setdefault(рядок, []).append(
                        "«%s» (код %s) читає рівень «%s», а база: %s — різні точки тіла під одним іменем"
                        % (слово, код, р, з[2]))
                    continue
                if not озн:
                    не.append((м.шлях, рядок, "«%s» → «%s»" % (слово, р), "слово без ознаки — читач рівня"))
                    continue
                місце, доказ = суд(р, озн, False, "«%s» (код %s) → рівень «%s»" % (слово, код, р))
                if місце:
                    за_рядком.setdefault(рядок, []).append(доказ)
                else:
                    не.append((м.шлях, рядок, "«%s» → «%s»" % (слово, р), доказ))
            for рядок, що in sorted(за_рядком.items()):
                місця.append((м.шлях, рядок, "таблиця орієнтирів %s.%s: %s" % (м.ім, в.targets[0].id
                                                                            if isinstance(в.targets[0], ast.Name)
                                                                            else "?", "; ".join(що))))

    # ── питання жінці: «обхват <рівня> <де>» ──
    for м in л.модулі:
        сталі_питань = {id(в.value) for в in м.дерево.body if isinstance(в, ast.Assign)
                        and any(isinstance(ц, ast.Name) and "ПИТАННЯ" in ц.id for ц in в.targets)}
        for в in ast.walk(м.дерево):
            if not (isinstance(в, ast.Constant) and isinstance(в.value, str) and re.search(r"обхват", в.value, re.I)):
                continue
            if not ("?" in в.value or id(в) in сталі_питань) or м.докстрінг(в) or _під_main(м, в):
                continue
            докази, місце = [], False
            for к in re.finditer(r"обхват\w*\s+((?:[\w'ʼ]+\s+)?[\w'ʼ]+)(.*?)(?=\s+і\s+обхват|[?;]|\.\s|\.$|$)",
                                 в.value, re.I | re.S):
                р = п7_рівень_слова(к.group(1), рівні)
                if р is None:
                    continue
                м_, д = суд(р, п7_ознаки(к.group(2)), bool(П7_ПОСИЛАННЯ.search(в.value)),
                            "питання «%s»" % " ".join(("обхват %s %s" % (к.group(1), к.group(2))).split())[:70])
                місце |= м_
                докази.append((м_, д))
            if місце:
                місця.append((м.шлях, в.lineno, "; ".join(д for _, д in докази)))
            elif докази:
                не.append((м.шлях, в.lineno, "питання про обхват", "; ".join(д for _, д in докази)))

    # ── форма: поле обхвату й текст, де міряти ──
    ключі = {}
    for шлях, т in л.js:
        for к in re.finditer(r"\[\s*'([^']+)'\s*,\s*'([^']+)'\s*\]", т):
            ключі.setdefault(к.group(1), к.group(2))
    for шлях, т in л.js:
        if not шлях.endswith(".html"):
            continue
        рядки = т.split("\n")
        p_текст = None
        поле_за_рядком = {}
        for і, рядок in enumerate(рядки, 1):
            if re.search(r"<section\b", рядок):
                p_текст = None
            for п in re.finditer(r"<p\b[^>]*>(.*?)</p>", рядок):
                p_текст = (і, re.sub(r"<[^>]+>", " ", п.group(1)))
            for п in re.finditer(r"<input\b[^>]*\bid=\"([^\"]+)\"", рядок):
                ключ = ключі.get(п.group(1))
                if ключ is None or not (ключ in рівні or ключ in БАЗА_ВИМІРІВ):
                    continue
                # підпис поля — від поля до `</label>` (буває на два рядки: підказка `<i>` під полем)
                хвіст = "\n".join(рядки[і - 1:і + 3])[п.start():]
                підпис = хвіст.split("</label>")[0]
                if not re.search(r"<b>\s*(см|мм)\s*</b>", підпис):
                    continue
                підказка = re.search(r"<i>(.*?)</i>", підпис, re.S)
                if ключ in БАЗА_ВИМІРІВ:
                    if підказка and ключ in виміри_бази:
                        не.append((шлях, і, "поле «%s»" % ключ, "орієнтир названо підказкою, база означує вимір (%s)"
                                   % виміри_бази[ключ]))
                    else:
                        місця.append((шлях, і + (підпис[:підказка.start()].count("\n") if підказка else 0),
                                      "форма: поле «%s» — %s" % (ключ, "орієнтир не названо" if not підказка
                                                                 else "підказка без означення бази")))
                    continue
                if підказка:
                    де_рядок, текст = і + підпис[:підказка.start()].count("\n"), підказка.group(1)
                elif p_текст:
                    де_рядок, текст = p_текст
                    # абзац на всі поля («груди — по найповнішому місцю; талія — …; плечі — …»): полю — його відрізок
                    свій = [в for в in re.split(r"[;:]\s*", текст)
                            if re.match(r"\s*([\w'ʼ ]+?)\s+[—–-]\s", в)
                            and п7_рівень_слова(re.match(r"\s*([\w'ʼ ]+?)\s+[—–-]\s", в).group(1), {ключ}) == ключ]
                    if свій:
                        текст = " ".join(свій)
                else:
                    де_рядок, текст = і, ""
                озн = п7_ознаки(текст)
                if not підказка and not озн:
                    де_рядок = і              # текст перед полем місця не називає — місце в самому полі
                м_, д = суд(ключ, озн, bool(П7_ПОСИЛАННЯ.search(текст)), "форма, поле «%s»" % ключ)
                поле_за_рядком.setdefault(де_рядок, []).append((м_, д))
        for рядок, сайти in sorted(поле_за_рядком.items()):
            if any(м_ for м_, _ in сайти):
                місця.append((шлях, рядок, "; ".join(д for м_, д in сайти if м_)))
            if not any(м_ for м_, _ in сайти):
                for _, д in сайти:
                    не.append((шлях, рядок, "форма", д))
    # ── точка речі на рівні тіла (рішення 06.11 «точка речі», п.1–3; 13869) ──
    for файл, рядок, доказ in п7_точки_речі(л, рівні, база, подвійні, тексти_бази, не):
        місця.append((файл, рядок, доказ))
    return місця, не


def лічити(корінь, вердикти_г=None):
    л = Лічба(корінь)
    л.зібрати()
    л.потік()
    л.кодувальники = кодувальники(л)
    звіт = {}

    # ── п.5: типові ──
    типові = типові_py(л) + типові_js(л)
    for файл, рядок, носій, зн, вид, що in типові:
        # Код словника дроту («conventional», «uncontrolled») сам називає величину — його типове зводить читання
        # під різними іменами; слово показу («річ», «нема») величини не називає: ним зводить лише потік.
        if isinstance(зн, str) and КОД_СЛОВНИКА.fullmatch(зн):
            л.о.злити(носій, ("знач", зн)) if носій else None
    групи = {}
    for файл, рядок, носій, зн, вид, що in типові:
        # JS не веде потоку: його ключ — вузол, злитий з однойменними ключами Python. Вузол, що з'єднує понад ШИРОКА імен,
        # не одна величина: місце видно за власним іменем, а не за іменами сусідів по склейці (01.11:
        # `вх.імʼя || 'безіменна'` тонуло в склейці з температурою й було видно лише з `лабораторія/`).
        if носій and not файл.endswith(".py") and len(л.імена_величини(л.величина(носій))) > ШИРОКА:
            носій = ("ім", носій[-1])
        інший = іншого_кореня(що, *(sorted(л.імена_величини(л.величина(носій))) if носій else ()))
        if isinstance(зн, str) and (зн in СИЛА or зн in СЛОВА_ПОРИ):
            інший = інший or ("Е3-сила-правила" if зн in СИЛА else "Е2-частина-дня")
        if інший:
            л.відкинути(інший)
            continue
        q = л.величина(носій) if носій else (л.величина(("знач", зн)) if isinstance(зн, str)
                                             and КОД_СЛОВНИКА.fullmatch(зн) else None)
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
                              *(sorted(л.імена_величини(п["q"])) if п["q"] else ()))
        if інший:
            л.відкинути(інший)
            continue
        всі.append(п)

    # ── п.2(а): записи T3 сесії ──
    сесійні = {}
    for м in л.модулі:
        for ім, записи in м.реєстри.items():
            for ключ, з in записи.items():
                # межа — число чи пара чисел; таблиця ваг (`дистанція.РЕЄСТР["якорі"]`) — не межа
                if з["t"] != "T3" or not з["межа"] or not СЛОВО_СЕСІЇ.search(з["суть"]) \
                        or ПОСИЛАННЯ.search(з["суть"]):
                    continue
                if not any(isinstance(і, str) and ІД_ПРАВИЛА.match(і) for і in з["прав"]):
                    continue
                if іншого_кореня(ключ):
                    л.відкинути(іншого_кореня(ключ))
                    continue
                назва = "%s.%s[%s]" % (м.ім, ім, ключ)
                сесійні[назва] = з
                л.додати(м.шлях, з["рядок"], 2, "запис T3 %s=%s (%s): опис сесії «%s», джерела нема" % (
                    назва, з["val_текст"], "/".join(з["прав"]), СЛОВО_СЕСІЇ.search(з["суть"]).group(0)))
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
    читачі_відсутності = set()
    for м1, ф1, р1, г1, д1 in пер:
        for м2, ф2, р2, г2, _ in пер:
            if г1 < г2 and len(г1) >= 3 and (м1.шлях, ф1) != (м2.шлях, ф2):
                різниця = ", ".join(sorted(г2 - г1))
                if д1:
                    читачі_відсутності.add((м1, р1, д1, м2.шлях.split("/")[-1], р2, різниця))
                л.додати(м1.шлях, р1, 3, "ознака з ключів {%s} — менший перелік, ніж %s:%d (без: %s)" % (
                    ", ".join(sorted(г1)), м2.шлях.split("/")[-1], р2, різниця))
                л.додати(м2.шлях, р2, 3, "ознака з ключів {%s} — більший перелік, ніж %s:%d (понад: %s)" % (
                    ", ".join(sorted(г2)), м1.шлях.split("/")[-1], р1, різниця))
    # ── п.3(в): ключ пари — та сама збірка, різні способи знайти пару ──
    за_збіркою = {}
    for ф, р, зб, вид in пари_збірок(л):
        за_збіркою.setdefault(зб, []).append((ф, р, вид))
    for зб, сайти in за_збіркою.items():
        види = {вид for _, _, вид in сайти}
        if len(види) < 2 or len({ф for ф, _, _ in сайти}) < 2:
            continue
        for ф, р, вид in сайти:
            л.додати(ф, р, 3, "пара елемента «%s.%s» — %s, а деінде — %s" % (
                зб[0], зб[1], вид, "; ".join(sorted(види - {вид})) or "тим самим способом в іншому модулі"))

    # ── п.3(г): поле запису пишуть розбір і код — мапа заміни читає одного, запис поверх пише другий ──
    поверх = записи_поверх(л)
    for f, мапи in мапи_замін(л).items():
        for ф, р, ім, значення in мапи:
            спільні = sorted(значення & set(поверх.get(f, {})))
            if not спільні:
                continue
            л.додати(ф, р, 3, "%s бере поля {%s} з «%s» як є, а код пише їх поверх (%s)" % (
                ім, ", ".join(спільні), f, ", ".join(sorted({"%s:%d" % (поверх[f][к][0].split("/")[-1],
                                                                       поверх[f][к][1]) for к in спільні}))))
            for к in спільні:
                фф, рр = поверх[f][к]
                л.додати(фф, рр, 3, "поле «%s» запису «%s» пише код поверх розбору, а %s:%d (%s) бере його з «%s»" % (
                    к, f, ф.split("/")[-1], р, ім, f))

    # Модель читає відсутність ключа меншого переліку як «не названо» (`Поле("occasion", …, без=…)`): той самий
    # вхід, що суд рахує більшим переліком, — третє місце тієї самої ознаки.
    for м1, р1, д1, ім2, р2, різниця in sorted(читачі_відсутності, key=lambda з: (з[0].шлях, з[1])):
        for в in ast.walk(м1.дерево):
            if isinstance(в, ast.Call) and в.args and isinstance(в.args[0], ast.Constant) \
                    and в.args[0].value in д1 and any(кл.arg == "без" for кл in в.keywords):
                рядок = next(кл.value.lineno for кл in в.keywords if кл.arg == "без")
                л.додати(м1.шлях, рядок, 3, "модель читає відсутність «%s» (ознака з :%d) як «не названо», а %s:%d "
                                            "рахує ознаку й з {%s}" % (в.args[0].value, р1, ім2, р2, різниця))

    # ── п.6: порівняння двох боків; п.1(г): одна функція зве бік величини за межею, друга — «невідомо» ──
    б = Боки(л, назва_виклику, визначення_в)
    б.обчислити()
    while б.кроки():                 # функції з кроком вибору — мітка «⊗» на їхніх поверненнях, і потік наново
        б.обчислити()
    виробники = []
    місця6, не6 = п6_місця(б, іншого_кореня, виробники)
    for файл, рядок, під, текст, доказ in місця6:
        л.додати(файл, рядок, 6, "(%s) %s — %s" % (під, текст, доказ))
    # п.6(г): читач, що бере «невідомо» з порівняння п.6 за «ні», «рівно» чи «пройдено» (рішення 07.11)
    місця6г, не6г = п6г_місця(б, виробники, вердикти_г)
    for файл, рядок, текст, доказ in місця6г:
        л.додати(файл, рядок, 6, "(г) %s — %s" % (текст, доказ))
    не6 = не6 + не6г
    місця1г, не1г = п1г_місця(л, назва_виклику)
    for файл, рядок, текст, доказ in місця1г:
        л.додати(файл, рядок, 1, "(г) %s — %s" % (текст, доказ))
    for _, _, _, причина in не6:
        if причина.startswith("інший корінь: "):
            л.відкинути(причина[len("інший корінь: "):])
    # ── п.7: орієнтир величини тіла (форма, шаблон, правила) ──
    місця7, не7 = п7_місця(л)
    for файл, рядок, доказ in місця7:
        л.додати(файл, рядок, 7, доказ)
    л.не_місця = sorted(set(не6 + не1г + не7))

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
    # розбивка для частин без спільних файлів: файл → пункти
    вих.append("за файлами й пунктами:")
    за_фп = {}
    for (ф, р), з in л.місця.items():
        for п in з["пункти"]:
            за_фп.setdefault(ф, {}).setdefault(п, set()).add(р)
    for ф, пп in sorted(за_фп.items(), key=lambda x: (-len({р for рр in x[1].values() for р in рр}), x[0])):
        вих.append("  %s — %d: %s" % (ф, len({р for рр in пп.values() for р in рр}), ", ".join(
            "п.%d — %d" % (п, len(рр)) for п, рр in sorted(пп.items()))))
    не = getattr(л, "не_місця", [])
    вих.append("не місця п.1(г), п.6 і п.7 (знайдено, місцем не лічено): %d" % len(не))
    if not тихо:
        for ф, р, текст, причина in не:
            вих.append("  %s:%d · %s · %s" % (ф, р, текст, причина))
    подвійні = getattr(л, "п7_подвійні", {})
    вих.append("п.7 дві точки тіла під одним іменем у базі (дві величини): " + ("; ".join(
        "%s — %s і %s" % (р, л.п7_база[р][2], " і ".join(о[2] for о in оо)) for р, оо in sorted(подвійні.items()))
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


# ── самоперевірка: штучне дерево, у кожному рядку — позначка «МІСЦЕ:<пункт>» чи «НЕ» (не місце) ─────────────────
ШТУЧНІ = {
    "джерела/внутрішня_мова.py": '''
ТАБЛИЦЯ = {"refuse": {"сукня": "dress"}, "occasion": {"театр": "theatre"}, "place": {"зал": "hall"},
           "dress_code": {"вечірній": "evening"}, "item_type": {"сукня": "dress"}}
def код(вісь, слово):
    return ТАБЛИЦЯ.get(вісь, {}).get(слово)
''',
    "джерела/реєстр_а.py": '''
РЕЄСТР = {
    "межа_а": dict(t="T3", val=0.78, прав=["K-TST-01"], суть="моє число, не калібровано"),  # МІСЦЕ:2
    "межа_з_джерелом": dict(t="T3", val=0.5, прав=["K-TST-01"], суть="моє, за Lee 2007"),  # НЕ
    "ваги": dict(t="T3", val={"а": 1.0}, прав=["K-TST-01"], суть="моя таблиця ваг"),  # НЕ
}
C = {к: РЕЄСТР[к]["val"] for к in РЕЄСТР}
''',
    "джерела/реєстр_б.py": '''
РЕЄСТР = {
    "без_точки": dict(t="T1", val=0.90, прав=["K-TST-02"], суть="верх рампи; низ — межа_а"),  # МІСЦЕ:1
}
C = {к: РЕЄСТР[к]["val"] for к in РЕЄСТР}
''',
    "джерела/тіло.py": '''
from реєстр_а import C
import реєстр_б as Б


def зони(whr):
    вих = {}
    if whr <= C["межа_а"]:  # МІСЦЕ:2
        вих["виражена"] = True
    if whr <= 0.75:  # МІСЦЕ:1
        вих["ярлик"] = "X"
    if whr >= C["межа_а"]:  # МІСЦЕ:1
        вих["без"] = True
    return вих


def без_точки(whr):
    return whr >= Б.C["без_точки"]  # МІСЦЕ:1


def повна(частка, кількість):
    return частка >= 1 or кількість > 0  # НЕ
''',
    "джерела/бриф.py": '''
ПРАВИЛА_СЛОВАМИ = {"K-TST-03": "рівень події: жодна річ нижче щабля"}  # МІСЦЕ:4


def бриф(рівень, заява):
    if рівень >= 7:  # МІСЦЕ:1
        заява("K-TST-03", "нижче")  # МІСЦЕ:4


def вечір(година, заява):
    if година >= 18:  # НЕ
        заява("K-TST-05", "вечір")
''',
    "джерела/суд.py": '''
ПРАВИЛА = [dict(id="K-TST-03", суть="біле на чужому весіллі; перевершити господиню")]  # МІСЦЕ:4


def суд(рівень, заява):
    if рівень >= 6:  # МІСЦЕ:1
        заява("K-TST-03", "нижче")  # МІСЦЕ:4


def ранок(година, заява):
    if година >= 17:  # НЕ
        заява("K-TST-05", "вечір")
''',
    "джерела/тема-1_тест.md": "**K-TST-03.** A guest never outshines the host.\\n**K-TST-05.** Evening.\\n",
    "джерела/запити.py": '''
from внутрішня_мова import код


def вибір(с):
    return {"she_refuses": код("refuse", с.get("відмова"))}  # МІСЦЕ:3


def складання(с):
    return {"she_refuses": с.get("відмова_слова").strip()}  # МІСЦЕ:3


def суд_нагоди(сцен):
    return any(сцен.get(к) for к in ("нагода", "місце", "дрес_код", "ошатність"))  # МІСЦЕ:3
''',
    "джерела/оцінка.py": '''
import внутрішня_мова as ВМ


class Поле:
    def __init__(self, ключ, опис, без=None):
        self.ключ, self.опис, self.без = ключ, опис, без


def сцена_для_моделі(с):
    return {"occasion": ВМ.код("occasion", с.get("нагода")),  # МІСЦЕ:3
            "place": ВМ.код("place", с.get("місце")),
            "dress_code": ВМ.код("dress_code", с.get("дрес_код"))}


ВХІД = [Поле("occasion", "where she goes",
             без="She did not name the occasion: do not judge formality.")]  # МІСЦЕ:3
''',
    "джерела/вердикт.py": '''
def склад(о):
    return set(о.get("речі") or [])


def пара(о, попередній):
    поп = [п for п in (попередній.get("образи") or [])]
    return max(поп, key=lambda п: len(склад(о) & склад(п)), default=None)  # МІСЦЕ:3
''',
    "джерела/міст.py": '''
def злити(відповідь, попередній):
    за_ід = {str(о.get("ід")): о for о in (попередній.get("образи") or [])}
    return [за_ід.get(str(о.get("ід"))) for о in (відповідь.get("образи") or [])]  # МІСЦЕ:3


def знайти(речі, попередній):
    за_н = {str(р.get("н")): р for р in (попередній.get("речі") or [])}
    return [за_н.get(str(р.get("н"))) for р in речі]  # НЕ
''',
    "джерела/дріт.py": '''
ЗАМІНИ = {"type": "item_type", "cut": "cut", "len": "length"}  # МІСЦЕ:3


def запис(r):
    о = {"type": r.get("тип"), "cut": r.get("крій")}
    розб = r.get("розбір") or {}
    for к, з in ЗАМІНИ.items():
        if розб.get(з):
            о.pop(к, None)
    return о
''',
    "джерела/пакет.py": '''
import внутрішня_мова as ВМ


def пакет(r):
    розб = dict(r.get("розбір") or {})
    розб["item_type"] = ВМ.код("item_type", r.get("тип"))  # МІСЦЕ:3
    розб["note"] = r.get("нотатка")  # НЕ
    return розб
''',
    "джерела/типові.py": '''
def намір_а(intent="conventional"):  # МІСЦЕ:5
    return intent


def намір_б(д):
    return д.get("intent") or "conventional"  # МІСЦЕ:5


def показ_а(показ=True, множ=1.0):  # НЕ
    return показ, множ


def показ_б(показ=True, множ=1.0):  # НЕ
    return показ, множ


def чекати_а(тайм=120):  # НЕ
    return тайм


def чекати_б(тайм=120):  # НЕ
    return тайм


def сила_а(з):
    return з.get("сила", "soft")  # НЕ


def сила_б(з):
    return з.get("сила") or "soft"  # НЕ


def довжина(довжина_см=6):  # НЕ
    return довжина_см


def відступ(годин_сну=6):  # НЕ
    return годин_сну


def зони_а(к):
    return к.get("відкриті_зони") or "нема"  # НЕ


def зони_б(к):
    return к.get("відкриті_зони") or "нема"  # НЕ


ПЕРЕКЛАД_А = {"червоний": "red", "синій": "blue"}  # НЕ
ПЕРЕКЛАД_Б = {"червоний": "red", "синій": "blue"}  # НЕ
''',
    "джерела/показ/типові.js": '''
function а(в) { return в.чому || "no_reason"; }  // МІСЦЕ:5
function б(в) { return в.чому || "no_reason"; }  // МІСЦЕ:5
function в(х) { return х.ім || "null"; }  // НЕ
function г(х) { return х.ім || "null"; }  // НЕ
''',
    "джерела/вимкнено.py": '''
ПРАВИЛА = [dict(id="K-TST-05", суть="вечірній вихід: довжина не вище щиколотки")]  # НЕ
ВИМКНЕНІ_ПРАВИЛА = {"K-TST-05": "рішення власника: поле припуску в каталозі відсутнє"}  # НЕ
''',
    "джерела/склейка.py": '''
def склейка(а, к):
    ім = к["підпис"]
    а1 = ім
    а2 = ім
    а3 = ім
    а4 = ім
    а5 = ім
    а6 = ім
    а7 = ім
    return а1, а2, а3, а4, а5, а6, а7, а
''',
    "джерела/показ/склейка.js": '''
function а(в) { return в.підпис || "безіменна"; }  // МІСЦЕ:5
function б(в) { return в.підпис || "безіменна"; }  // МІСЦЕ:5
''',
    "джерела/тіло_штучне.py": '''
import math


def тіло(о, зріст):
    профіль = [(nm, зріст * 0.8, о[nm] / math.pi) for nm in о]
    return dict(профіль=профіль, обхвати=dict(о), зріст=зріст, похибка_см=0.5)


def плече(р, т):
    ш = р.get("ширина_плеча_см")
    w = next(w for nm, _, w in т["профіль"] if nm == "плечі")
    δ = float(ш) - w  # МІСЦЕ:6
    return δ


def довжина(р, т):
    надлишок = р.get("довжина_см") - т["зріст"] * 0.5
    if надлишок > р.get("розкид_см"):  # МІСЦЕ:6
        return 1
    return 0


def довжина_з_похибкою(р, т):
    надлишок = р.get("довжина_см") - т["зріст"] * 0.5
    if надлишок > р.get("розкид_см") + т["похибка_см"]:  # НЕ
        return 1
    return 0


def межа(р, т):
    if not (0 <= р.get("низ_см") <= т["зріст"]):  # НЕ
        raise ValueError("поза тілом")
    return 0


def сила(р, т):
    δ = р.get("довжина_см") - т["зріст"]
    return "strong" if δ > 3 else "hint"  # НЕ


def вирок(р, т):
    ш = р.get("ширина_плеча_см")
    w = next(w for nm, _, w in т["профіль"] if nm == "плечі")
    if ш is None or w is None:
        return [_зн("K-TST-07", "питання")]  # НЕ
    return [_зн("K-TST-07", "strong")]  # МІСЦЕ:6


def одна_річ(р):
    return р.get("довжина_см") > 100  # НЕ


def образ(о, зріст, р):
    т = тіло(о, зріст)
    return плече(р, т), довжина(р, т), довжина_з_похибкою(р, т), межа(р, т), сила(р, т), вирок(р, т), одна_річ(р)
''',
    # п.6(г) рішення 07.11: читач «невідомо» з порівняння з похибкою — місце, коли на «невідомо» виходить з правила
    # без «утримано» й заяви (`continue`, `return`), дає вирок чи мовчить умовою на істинність; облік «утримано», вираз
    # з None, умова, що «невідомо» пропускає далі, — не місця; читач без вердикту в таблиці — «п.?»
    "джерела/читач_штучний.py": '''
import math


def тіло(о, зріст):
    профіль = [(nm, зріст * 0.8, о[nm] / math.pi) for nm in о]
    return dict(профіль=профіль, обхвати=dict(о), зріст=зріст, похибка_см=0.5)


def _зн(ід, сила, текст):
    return dict(ід=ід, сила=сила, текст=текст)


def бік(а, похибка_а, б, похибка_б):
    if а is None or б is None or похибка_а is None or похибка_б is None:
        return None
    if а - б > похибка_а + похибка_б:  # НЕ
        return 1
    if б - а > похибка_а + похибка_б:  # НЕ
        return -1
    return None


def низ(р, т):
    return бік(р.get("низ_см"), р.get("розкид_см"), т["зріст"], т["похибка_см"])


def міра(р, т):
    на = None
    if р.get("низ_см") - т["зріст"] > р.get("розкид_см") + т["похибка_см"]:  # НЕ
        на = True
    return dict(на_максимумі=на, важіль_є=р.get("розкид_см") is not None)


def правило_вихід(р, т):
    if низ(р, т) != 1:  # МІСЦЕ:6
        return []
    return [_зн("K-TST-11", "soft", "нижче")]


def правило_вирок(р, т):
    if низ(р, т) != -1:  # МІСЦЕ:6
        return [_зн("K-TST-12", "soft", "не вище")]
    return []


def правило_мовчить(р, т):
    if низ(р, т) == 1:  # МІСЦЕ:6
        return [_зн("K-TST-13", "soft", "нижче")]
    return []


def правило_утримано(р, т):
    б_ = низ(р, т)
    if б_ is None:  # НЕ
        return [dict(ід="K-TST-14", стан="утримано")]
    if б_ == 1:  # НЕ
        return [_зн("K-TST-14", "soft", "нижче")]
    return []


def мітка(р, т):
    б_ = низ(р, т)
    return "нижче" if б_ == 1 else ("вище" if б_ == -1 else None)  # НЕ


def правило_поля(р, т):
    вих = []
    for м in [міра(р, т)]:
        if not (м["на_максимумі"] and м["важіль_є"]):  # МІСЦЕ:6
            continue
        вих.append(_зн("K-TST-15", "soft", "на максимумі"))
    return вих


def правило_переліку(р, т):
    _на = [м for м in [міра(р, т)] if м["на_максимумі"]]
    if not _на:  # МІСЦЕ:6
        return []
    return [_зн("K-TST-16", "soft", "на максимумі")]


def правило_get(речі):
    вих = []
    for x in речі:
        if not x.get("низ_см"):  # НЕ
            continue
        вих.append(x)
    return вих


def правило_без_вердикту(р, т):
    if низ(р, т) > 0:  # МІСЦЕ:6
        return [_зн("K-TST-17", "soft", "нижче")]
    return []


def заява(код, **дані):
    return dict(код=код, дані=дані)


def понад(р, т):
    return р.get("низ_см") - т["зріст"] > р.get("розкид_см") + т["похибка_см"]  # НЕ


def смуги(р, т):
    погані, поч = [], None
    for y in (1, 2, 3):
        зле = міра(р, т)["на_максимумі"]
        if зле and поч is None:  # НЕ
            поч = y
        if not зле and поч is not None:  # НЕ
            погані.append((поч, y))
            поч = None
    return погані


def смуги_з_невідомим(р, т):
    добрі, невідомі = [], []
    for y in (1, 2, 3):
        зле = міра(р, т)["на_максимумі"]
        if зле:  # НЕ
            добрі.append(y)
        else:
            невідомі.append(y)
    return добрі


def бриф(р, т):
    рядки = []
    с = смуги(р, т)
    if с:  # МІСЦЕ:6
        рядки.append(заява("no_hem_at", at=с))
    с2 = смуги_з_невідомим(р, т)
    if с2:  # НЕ
        рядки.append(заява("hem_at", at=с2))
    return рядки


def журнал(р, т):
    return dict(
        смуги_краю=смуги(р, т),  # МІСЦЕ:6
        смуги_відомі=смуги(р, т))  # НЕ


def показ(з):
    return з["смуги_відомі"]


def вето(р, т, речі):
    вих = []
    for e in речі:
        якщо = None
        if понад(р, т):  # НЕ
            якщо = "вище"
        if якщо is None and e.get("низ_см") is not None:  # НЕ
            вих.append(заява("hem_limit_not_judged"))
            continue
        if якщо is None:  # НЕ
            continue
        вих.append(_зн("K-TST-18", "hard", якщо))
    return вих


def правило_розвилка(р, т, точки):
    вих = []
    for x in точки:
        if x:
            _на = [м for м in [міра(р, т)] if м["на_максимумі"]]
            if not _на:  # НЕ
                вих.append(dict(стан="утримано"))
                continue
        elif not міра(р, т)["на_максимумі"]:  # МІСЦЕ:6
            continue
        вих.append(_зн("K-TST-19", "soft", "на максимумі"))
    return вих


def образ(о, зріст, р, речі):
    т = тіло(о, зріст)
    правило_розвилка(р, т, речі)
    return (правило_вихід(р, т), правило_вирок(р, т), правило_мовчить(р, т), правило_утримано(р, т), мітка(р, т),
            правило_поля(р, т), правило_переліку(р, т), правило_get(речі), правило_без_вердикту(р, т), бриф(р, т),
            показ(журнал(р, т)), вето(р, т, речі))
''',
    "джерела/пара_штучна.py": '''
C = {"перекос": 0.05}


def ролі(о):
    δ = (о["стегна"] - о["груди"]) / о["груди"]
    if δ >= C["перекос"]:  # МІСЦЕ:1
        return "низ"
    return "нейтраль"


def баланс(о):
    δ = (о["стегна"] - о["груди"]) / о["груди"]
    return dict(рядок=f"різниця {δ:.2f}", бік="невідомо")  # МІСЦЕ:1


def операції(о):
    return ролі(о)  # НЕ


def інша(о):
    д = (о["талія"] - о["груди"]) / о["груди"]
    return "невідомо" if д is None else д  # НЕ


def ярлик_пари(о):
    δ = ((о["стегна"] - о["груди"]) / о["груди"]) if о["груди"] else 0.0
    if δ >= 0.05:  # МІСЦЕ:1
        return "A"
    return "H"
''',
    # (а) рішення 06.11 п.6 (#3222): крок, що лише вибирає відрізок інтерполяції чи межі вікна, — не місце; місце —
    # порівняння, яке він живить (через повернення, поле словника); вартовий ділення — ні; `if … continue`, що стереже
    # вирок правила, — не крок
    "джерела/крок_штучний.py": '''
import math


def тіло(о, зріст):
    профіль = [(nm, зріст * ч, о[nm] / math.pi) for nm, ч in (("стегна", 0.5), ("коліно", 0.3))]
    return dict(профіль=профіль, висоти={nm: зріст * ч for nm, ч in (("стегна", 0.5), ("коліно", 0.3))},
                зріст=зріст)


def ширина_на(проф, см):
    for i in range(len(проф) - 1):
        (_, y1, w1), (_, y2, w2) = проф[i], проф[i + 1]
        if y2 <= см <= y1:  # НЕ
            t = (см - y2) / (y1 - y2)
            return w2 + (w1 - w2) * t
    return проф[-1][2]


def вікно(проф, край):
    нижче = [y for _, y, _ in проф if y < край]  # НЕ
    return max(нижче) if нижче else 0.0


def близько(р, т):
    край = р.get("низ_см")
    w = ширина_на(т["профіль"], край)
    w_лоу = ширина_на(т["профіль"], край - 10)
    звуження = (w - w_лоу) / w if w > 0 else 0.0  # НЕ
    return dict(звуження=звуження, на_межі=звуження >= 0.05)  # МІСЦЕ:6


def запас(р, т):
    край = р.get("низ_см")
    if край - вікно(т["профіль"], край) < 3:  # МІСЦЕ:6
        return "впритул"
    return "вільно"


def суд(р, т):
    м = близько(р, т)
    if м["звуження"] > 0.1:  # МІСЦЕ:6
        return "зсунути"
    return "лишити"


def краї(речі, т):
    вих = []
    for р in речі:
        if р.get("низ_см") <= т["висоти"]["коліно"]:  # МІСЦЕ:6
            continue
        вих.append(_зн("K-TST-09", "hint"))
    return вих


def образ(о, зріст, р):
    т = тіло(о, зріст)
    return суд(р, т), запас(р, т), краї([р], т)
''',
    # (б) рішення 06.11 п.6 (#3222): два виміри тіла — різниця обхватів проти межі FFIT, частка талії й зросту, бік
    # пари голим ±0.05 (ланцюг присвоєнь довший за 3 — як `fit.зони`, знахідка частини 13)
    "джерела/форма_штучна.py": '''
import math

C = {"талія_груди": 9}


def тіло(о, зріст):
    return dict(профіль=[(nm, зріст, о[nm] / math.pi) for nm in о], обхвати=dict(о), зріст=зріст)


def категорія(т):
    о = т["обхвати"]
    гт = о["груди"] - о["талія"]
    if гт >= C["талія_груди"]:  # МІСЦЕ:6
        return "Hourglass"
    return "Rectangle"


def статура(т):
    ч = т["обхвати"]["талія"] / т["зріст"]
    return "повна" if ч >= 0.6 else "середня"  # МІСЦЕ:6


def ярлик(т):
    о = т["обхвати"]
    пл, гр, ст = о["плечі"], о["груди"], о["стегна"]
    верх = max(пл, гр)
    δ = (ст - верх) / верх
    if δ >= 0.05:  # МІСЦЕ:6
        return "A"
    return "H"


def образ(о, зріст):
    т = тіло(о, зріст)
    return категорія(т), статура(т), ярлик(т)
''',
    # п.7 (менеджер 06.11, 13854–13856): орієнтир величини тіла — база знань (§2.1 і фраза коліна), шаблон рівнів
    # часткою зросту (0 і 1 — межі зросту; рівень з посиланням — не місце), похідний рівень зі словом точки тіла, таблиця
    # слів орієнтира з кодами (слово речі — не орієнтир тіла), питання жінці, форма: текст перед полями, поле без
    # орієнтира, підказка з посиланням, вимір поза профілем без означення бази; демонстрація під __main__ — не місце
    "джерела/тема-1_штучна.md": """# тема

### 2.1 Measurement definitions the formulas assume

- **Bust** — around the fullest part.
- **Waist** — smallest circumference at the natural waist.
- **High hip** — roughly 18 cm below the natural waist. This is *not* the widest point.
- **Hip** — largest circumference over the fullest part of the buttocks.

## Knee

The crease should bisect the kneecap.

## Hem

**K-TST-10.** A midi skirt's termination point is critical (narrowest point of the calf).
**K-TST-11.** A boot shaft that ends at the widest part of the calf widens the leg.
**K-TST-12.** Mini or Above the Knee on the Mid-Thigh.
**K-TST-13.** A knee-length hem stops at the kneecap.
**K-TST-14.** Ankle-length trousers end at the narrowest point of the ankle.
""",
    "джерела/рівні_штучні.py": '''
# Рівні тіла часткою зросту.
РІВНІ = [("маківка", 1.000), ("груди", 0.720),  # МІСЦЕ:7
         ("талія", 0.620),  # МІСЦЕ:7
         ("високе_стегно", 0.575), ("стегна", 0.520),  # МІСЦЕ:7
         ("коліно", 0.2756),  # ANSUR II, Gordon et al. 2014 # НЕ
         ("литка", 0.200),  # МІСЦЕ:7
         ("підлога", 0.000)]  # НЕ
ДОВЖИНИ_ЧАСТКИ = [("a", 0.1), ("b", 0.2), ("c", 0.3), ("d", 0.4), ("e", 0.5)]  # НЕ


def профіль(зріст, ш):
    return [(nm, доля * зріст, ш[nm]) for nm, доля in РІВНІ]


def частки():
    return [к for к, ч in ДОВЖИНИ_ЧАСТКИ]
''',
    "джерела/орієнтири_штучні.py": '''
ОРІЄНТИРИ = (("коліні", "коліно"),  # НЕ
             ("середині литки", "литка"),  # МІСЦЕ:7
             ("найширшій точці стегна", "стегна"),  # НЕ
             ("верхньому стегні", "високе_стегно"),  # МІСЦЕ:7
             ("талії", "талія"))  # НЕ
КОД_ОРІЄНТИРА = {"коліні": "knee", "середині литки": "mid_calf", "найширшій точці стегна": "widest_hip",
                 "верхньому стегні": "upper_thigh", "талії": "waist"}
ДОВЖИНИ_НИЗУ = (("mini", "коліно"), ("midi", "литка"), ("hip", "високе_стегно"))  # МІСЦЕ:7


def орієнтир(H, y):
    точки = [(abs(H["коліно"] - y), "коліні")]
    точки.append((abs((H["талія"] + H["груди"]) / 2 - y), "під грудьми"))  # МІСЦЕ:7
    точки.append((abs((H["талія"] + H["груди"]) / 2 - y), 0))  # НЕ
    return min(точки)


ВИСОКЕ_СТЕГНО_ПИТАННЯ = "Обхват високого стегна: 18 см нижче природної талії, по кістці тазу."  # НЕ
ПИТАННЯ_ТАЛІЇ = "Обхват талії — найвужче місце на природній талії."  # НЕ
ТІЛО = dict(литка=dict(питання="Який обхват литки в найширшому місці і обхват коліна?"))  # МІСЦЕ:7
ПОЯС = "обхват талії стрічкою"  # НЕ

if __name__ == "__main__":
    print(("середина литки", (H["коліно"] + H["литка"]) / 2))  # НЕ
''',
    "джерела/показ_штучний.js": '''
const ПОЛЯ = [['ш-груди','груди'],['ш-талія','талія'],['ш-коліно','коліно'],['ш-литка','литка'],
              ['ш-голова','голова_см'],['ш-зріст','зріст'],['ш-талія-2','талія']];
''',
    "джерела/показ_штучний.html": '''
<section id="мірки">
  <p>Обхвати — у сантиметрах, по найширшому місцю.</p>  <!-- МІСЦЕ:7 -->
  <label><span>Груди</span><input type="number" id="ш-груди"><b>см</b></label>  <!-- НЕ -->
  <label><span>Талія</span><input type="number" id="ш-талія"><b>см</b></label>  <!-- НЕ -->
  <p class="підказка">Необов'язково.</p>
  <label><span>Коліно</span><input type="number" id="ш-коліно"><b>см</b></label>  <!-- МІСЦЕ:7 -->
  <label><span>Литка</span><input type="number" id="ш-литка"><b>см</b>
    <i>по найширшому місцю литки (Gordon et al. 2014)</i></label>  <!-- НЕ -->
  <label><span>Голова</span><input type="number" id="ш-голова"><b>см</b>
    <i>на дюйм вище брів</i></label>  <!-- МІСЦЕ:7 -->
  <label><span>Зріст</span><input type="number" id="ш-зріст"><b>см</b></label>  <!-- НЕ -->
</section>
<section>
  <label><span>Талія</span><input type="number" id="ш-талія-2"><b>см</b>
    <i>найвужче місце на природній талії</i></label>  <!-- НЕ -->
</section>
''',
    # п.7 (менеджер 06.11 «точка речі», #3233): шаблон-комприхеншн, де частку дає запис реєстру з джерелом (не місце),
    # а запасний словник — без джерела (місце); слово чи точка речі на рівні тіла — словник, кортеж пар, пари навпаки,
    # `re.compile`, шкала класу, що позичає імена рівнів (і тотожний клас у ній), слово на клас шкали, вбудований
    # `IfExp`; означення речі в базі: як база (`ankle`, `knee` — код усередині точки «Above the Knee» не означення) —
    # не місце, деінде (`midi` — найвужче, а литка шаблону — найширше: друга точка під одним іменем) — місце; не місця —
    # тотожне «слово → клас», таблиця з посиланням, «рівень → слово тіла», читач таблиці
    "джерела/похибка_штучна.py": '''
def _рівень(середнє, джерело, місце):
    return dict(середнє=середнє, джерело=джерело, місце=місце)


РЕЄСТР = {
    "рівень": {
        "маківка": _рівень(1.0, "означення", "маківка — сам зріст"),  # НЕ
        "підборіддя": _рівень(None, None, ""),
        "пах": _рівень(0.4721, "ANSUR II, Gordon et al. 2014", "crotchheight / stature"),  # НЕ
        "щиколотка": _рівень(0.0451, "ANSUR II, Gordon et al. 2014", "lateralmalleolusheight / stature"),  # НЕ
        "литка": _рівень(0.2, "ANSUR II, Gordon et al. 2014", "CALF HEIGHT: рівень найбільшого обхвату литки"),  # НЕ
        "підлога": _рівень(0.0, "означення", "підлога"),  # НЕ
    },
}


def запис(вид, назва):
    return dict(РЕЄСТР[вид][назва])
''',
    "джерела/шаблон_штучний.py": '''
import похибка_штучна as _ПОХ

ПОРЯДОК = ("маківка", "підборіддя", "пах", "литка", "щиколотка", "підлога")
_БЕЗ_ДЖЕРЕЛА = {"підборіддя": 0.870}  # МІСЦЕ:7


def _частка(назва):
    с = _ПОХ.запис("рівень", назва)["середнє"]
    return с if с is not None else _БЕЗ_ДЖЕРЕЛА[назва]


РІВНІ_З = [(nm, _частка(nm)) for nm in ПОРЯДОК]


def висоти(зріст):
    return {nm: доля * зріст for nm, доля in РІВНІ_З}
''',
    "джерела/річ_штучна.py": '''
import re

# Клас довжини → рівні тіла.
РІВЕНЬ_ЗОНА = {"коліно": (("коліно",), 4.0),  # МІСЦЕ:7
               "литка": (("коліно", "щиколотка"), 7.0),  # МІСЦЕ:7
               "максі": (("щиколотка",), 5.0)}  # МІСЦЕ:7
ДОВЖИНА_PARAM = {"міді": "литка",  # МІСЦЕ:7
                 "максі": "максі"}  # НЕ
КЛЮЧІ = (("коліно", ("до колін", "по колін")),  # МІСЦЕ:7
         ("максі", ("максі", "в підлогу")))  # МІСЦЕ:7
ДОВЖИНИ = (("crop", "талія"),  # МІСЦЕ:7
           ("ankle", "щиколотка"),  # НЕ
           ("knee", "коліно"),  # НЕ
           ("midi", "литка"))  # МІСЦЕ:7
ТОЧКА = ((re.compile(r"кроков", re.I), "пах"),)  # МІСЦЕ:7
ТОЧКА_СЛОТА = {"верх": "груди",  # МІСЦЕ:7
               "низ": "талія"}  # МІСЦЕ:7
# Довжини за Kwon 2019, табл. 3.
ДОВЖИНИ_З_ДЖЕРЕЛОМ = {"mini": "коліно", "maxi": "щиколотка"}  # НЕ
ХАЛЯВА_СЛОВОМ = {"коліно": "коліна", "литка": "литки"}  # НЕ


def точка(уточнення, слот):
    return "талія" if "від талії" in уточнення else ТОЧКА_СЛОТА[слот]  # МІСЦЕ:7


def клас(слово):
    return ДОВЖИНА_PARAM.get(слово)  # НЕ
''',
    "джерела/тест_штучний.py": '''
def тест(intent="conventional"):  # НЕ
    return intent
''',
}


def самоперевірка():
    """Штучні випадки кожного пункту (1–7) і не-місць: п.7 — рівень шаблону без джерела, похідний рівень, слово
    таблиці орієнтирів з кодом іншої точки, ознака без бази, поле форми без орієнтира чи всупереч базі, питання; не
    місця п.7 — межі зросту 0 і 1, рівень з посиланням, читач рівня, питання як у базі, `__main__`; точка речі (#3233) —
    шаблон-комприхеншн із запасом без джерела, таблиці «річ → рівень» усіх видів, шкала класу, `IfExp`, означення речі в
    базі деінде; не місця — означення речі як база, посилання, тотожне «слово → клас», «рівень → слово тіла», читач;
    литка — дві точки бази; п.6 — вимір речі мінус обхват тіла через π, надлишок проти
    похибки лише речі, вирок на самій наявності обох боків; не місця п.6 — похибка обох боків, межа області
    визначення (виняток), вибір сили правила, один вимір проти числа; п.6(а) рішення 06.11 — крок вибору відрізка чи
    вікна не місце, а відповідь, яку він живить, — місце (повернення, поле словника), вартовий ділення — ні, `continue`
    перед вироком — не крок; п.6(г) рішення 07.11 — читач «невідомо» з порівняння з похибкою: вихід
    без «утримано», вирок, умова на істинність, поле словника, перелік, відфільтрований відповіддю, читач без вердикту
    («п.?»); не місця — облік «утримано» (і умова на істинність після нього), вираз з None, `.get` → `continue`;
    п.6(г) 13967 — перелік, який пише лише гілка «так» (наповнювач — не місце, з гілкою «невідомо» — його читач не
    місце), умова, що на порожнечі мовчить без заяви «не судить», поле, що несе порожнечу назовні, вихід після
    обліку — не місце; п.6(б) — два виміри тіла (FFIT, частка талії й зросту, бік пари голим числом); п.1(г) —
    бік за межею проти «невідомо» тієї самої величини (і з вартовим ділення), читач відповіді — не місце; ще не-місця:
    переклад слова ядра, година, тривалість, те саме число різних одиниць, сила правила, межі 0 і 1, прапор, нейтраль,
    заповнювач, межа з посиланням, таблиця ваг, тест."""
    import tempfile
    вих = []
    with tempfile.TemporaryDirectory() as тека:
        for шлях, текст in ШТУЧНІ.items():
            повний = os.path.join(тека, шлях)
            os.makedirs(os.path.dirname(повний), exist_ok=True)
            with open(повний, "w", encoding="utf-8") as д:
                д.write(текст.lstrip("\n"))
        л, _ = лічити(тека)
        for шлях, текст in sorted(ШТУЧНІ.items()):
            for і, рядок in enumerate(текст.lstrip("\n").split("\n"), 1):
                м = re.search(r"(?:#|//|<!--) (МІСЦЕ:(\d)|НЕ)\s*(?:-->)?\s*$", рядок)
                if not м:
                    continue
                знайдено = л.місця.get((шлях, і))
                if м.group(2):
                    вих.append(("%s:%d п.%s" % (шлях, і, м.group(2)),
                                bool(знайдено) and int(м.group(2)) in знайдено["пункти"]))
                else:
                    вих.append(("%s:%d не місце" % (шлях, і), not знайдено))
        чужі = sorted("%s:%d" % к for к in л.місця
                      if not re.search(r"(?:#|//|<!--) МІСЦЕ:\d\s*(?:-->)?\s*$",
                                       (ШТУЧНІ.get(к[0], "").lstrip("\n").split("\n") + [""] * к[1])[к[1] - 1]))
        подвійні = getattr(л, "п7_подвійні", {})
        вих.append(("п.7 литка — дві точки бази під одним іменем (найширша й найвужча)", "литка" in подвійні
                    and "найширше" in л.п7_база["литка"][0] and any("найвужче" in о[0] for о in подвійні["литка"])))
        к92 = next(і for і, р in enumerate(ШТУЧНІ["джерела/читач_штучний.py"].lstrip("\n").split("\n"), 1)
                   if "низ(р, т) > 0" in р)
        лв, _ = лічити(тека, {("джерела/читач_штучний.py", "правило_без_вердикту", 1): ("Н", "штучний вердикт")})
        вих.append(("п.6(г) читач з вердиктом таблиці — не місце, без вердикту — «п.?»",
                    ("джерела/читач_штучний.py", к92) not in лв.місця and "п.?" in str(л.місця.get(
                        ("джерела/читач_штучний.py", к92)))))
        вих.append(("місць без позначки нема%s" % (" (є: %s)" % ", ".join(чужі) if чужі else ""), not чужі))
    return вих


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
