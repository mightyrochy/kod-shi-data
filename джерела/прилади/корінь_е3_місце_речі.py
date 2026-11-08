# -*- coding: utf-8 -*-
"""прилади/корінь_е3_місце_речі.py — прилад кореня Е3-місце-речі (`аудит/корені/Е3-місце-речі.md`).

Клас — з паспорта («Клас місць», «Інваріант ПІСЛЯ», «Рішення» 06.11), не перелік прикладів. Місце — точка коду
продукту, де рахунок, знахідка, заміна чи порада залежить від того, де річ на ній (голова, обличчя, шия, тулуб,
руки, зона мети) чи що вона закриває (волосся, шию, виріз), а бере це не з одного запису місця з походженням, а
зі сталої класу чи під-слоту, з власної логіки правила чи з припущення, що волосся видно й його голоси перемішані.
Прилад коду не править і місць руками не перелічує: таблиці, читачі й обгортки — з AST усього обсягу.

ПУНКТИ (місце — `файл:рядок`; рядок з кількома пунктами — один, пункт — перший за номером):
  п.1  стала класу як місце речі. ТАБЛИЦЯ МІСЦЯ — названа стала (модуля чи функції), чиє ім'я каже про місце
       (`СЛОВНИК_ТАБЛИЦІ`: NEAR, обличчя, голова, волосся, шия, виріз, зона, тіло, торс, закриває, портрет, місце),
       а в літералі (з розкриттям сталих модуля, на які він посилається) є назва слота, під-слоту чи типу речі
       (`slots.py`, `внутрішня_мова.ТАБЛИЦЯ["item_type"]`): `SLOT_NEAR_FALLBACK`, `ЗОНА_МЕТИ_СЛОТИ`, … Стала
       модуля, чиє значення читає таблицю (`ДАЛЕКІ = [с for с, в in SLOT_NEAR_FALLBACK.items() …]`), — теж таблиця
       (похідна), хоч би як звалась. ОБГОРТКА — функція, що вертає значення таблиці чи іншої обгортки (повернення —
       читання, порівняння, логіка, арифметика, умовний вираз, `round`/`float`/`min`/`max`/… над ним, або локальне
       ім'я, якому таке присвоєно): `колір_річ.near_слота`, `композитор_річ.near_слота`, `річ_з_фото.біля_обличчя`,
       `регістр_уваги.на_мету`. Місце — кожне читання таблиці (крім визначення іншої таблиці) і кожен виклик
       обгортки, з розкриттям імпортів (`import М as А`, `from М import Х as У`, `А = __import__("М")`, повторний
       експорт). Таблиця, яка за ім'ям і літералом підходить, але місця речі на ній не несе, — у `НЕ_ТАБЛИЦІ` з
       причиною поіменно; запис без такої таблиці на дереві — рядок «застаріле» (не код 1).
  п.2  поле `near` елемента без походження: читання `x["near"]`/`x.get("near")` (Python) і `.near`/`["near"]` (JS
       показу), коли функція не читає походження (`near_виміряний`) і запису місця (п. «Запис»): поле несе сталу
       класу слота (`outfit.елементи`: `near_слота`, коли маски нема), і правило бере її як факт (K-CLR-02,
       `колір_світлота.біля_обличчя`). Не місце — копія: значення стоїть просто аргументом-ключем виклику чи
       значенням літерала словника (крізь `bool`/`float`/`round`/…), як `near=m[i]["near"]`: копія місця не
       вирішує, вирішує її читач.
  п.3  власна логіка правила: у функції, названій за місцем (слово імені — `СЛОВНИК_ФУНКЦІЇ`: обличчя, near,
       голова, волосся, шия, зона, місце, закриває, портрет), — порівняння слота чи типу речі з літералом
       слотів/типів (`слот in ("браслет", "каблучка")`, `слот == "верхній_шар"`). Функція, що лише має п.1, сюди
       не йде: поряд у ній слот вирішує й не місце (краї, крій) — така межа була б вигадана.
  п.4  волосся. (а) голоси волосся перемішано: числова згортка (`sum`/`max`/`min`/`mean`/`median`) світлоти L* по
       всіх голосах профілю — збірка за ключем `startswith("волосся")` чи `рід_риси(…) == "волосся"` (рішення
       06.11: середнє голосів для контрасту — місце); (б) волосся видно: світлота волосся в одному виразі зі
       світлотою шкіри (різниця, сума, виклик з обома) — власний контраст і «value обличчя» без знання, чи образ
       волосся закриває.

ЗАПИС (не місце; негативний бік проб). Функція, що читає запис місця з походженням — ключ `місце…`
(`місце`, `місце_джерело`, `місця`, `місце_речі`, …) чи походження `near` (`near_виміряний`, `near_джерело`,
`near_походження`) не лише в підписі (`"виміряно" if … else "запасне"`), — читач запису: її п.2–п.4 не лічаться (п.1 лічиться й там: підставити сталу класу запис не
дозволяє). Так уже живе місце аксесуара (`фід_атрибути.спосіб_носіння`, `композитор_річ.обрати_місце`:
`місце`+`місце_джерело`, None — «невідомо») і перенормування виміряного `near` (`outfit.елементи`).

ОБСЯГ. Python — `джерела/*.py` продукту без вимірників, стендів, тестів, лабораторії й руки 2 (`НЕ_ПРОДУКТ`); JS —
`джерела/показ/*.js`, `показ.html`, `показ_шаблон.js`, `worker_джерело.js` (п.1 — ім'я таблиці, п.2 — `near`).
Промпти — там, де їх складає код: читання таблиць і поля при складанні лічаться п.1–п.2. Нерозбірний файл, словник
слотів, що не читається, — `обсяг_приладу.непрочитано` (код 1, Д10).

ОБМЕЖЕННЯ (гіпотеза, не висновок): потоку значень між функціями, крім обгорток, прилад не простежує; методи класів
(`self.f`) обгортками не розкриває; п.3 бачить лише літерали слотів/типів, а не похідні множини без імені таблиці.

Вивід: `файл:рядок · п.N · чому · функція`, підсумок за пунктами, таблиці й обгортки, `НЕ_ТАБЛИЦІ`, самоперевірка
вибіркою паспорта (`ВІДОМІ` — місця, `НЕ_МІСЦЯ` — читачі запису й копії: не-місце серед місць — код 1), останній
рядок `місць: <N>` (різні `файл:рядок`), код 0. Запуск з кореня репозиторію (чи `--корінь <дерево>`):
python3 джерела/прилади/корінь_е3_місце_речі.py [--тихо]
"""
import argparse
import ast
import os
import re
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import обсяг_приладу as ОБСЯГ  # noqa: E402  Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

НЕ_ПРОДУКТ = re.compile(r"^(тест|стенд|батарея|проба|gate_|audit_|measure_|pair_test|жнива|мутанти|лабораторія|"
                        r"гейти|verify_|звірка|зведення|траса_петлі|status_перевірки|build_|покроковик|досяжність|"
                        r"відбиток|run_outfit|rule_genus|поломки|скласти$|корпус$|таблиця_збирання)")
JS_ПОКАЗУ = ("показ.html", "показ_шаблон.js", "worker_джерело.js")
СЛОВНИК_ТАБЛИЦІ = re.compile(r"NEAR|ПРИОБЛИЧЧ|ОБЛИЧЧ|ГОЛОВ|ВОЛОСС|ШИЯ|ШИЇ|ШИЮ|ДЕКОЛЬТЕ|ВИРІЗ|ЗОН[АИІУ]|ТІЛА|ТОРС|"
                             r"ЗАКРИВ|ПОРТРЕТ|МІСЦ")
СЛОВНИК_ФУНКЦІЇ = re.compile(r"^(обличч|near|голов|волосс|шия|шиї|шию|декольте|зон[аиі]|місц|закрива|портрет)",
                             re.IGNORECASE)   # до слова імені функції (`стан_металу_біля_обличчя`, не `мономісце`)
ЗАПИС = re.compile(r"^(місце\w*|місця|near_(виміряний|джерело|походження))$")
ОБГОРТКИ_ЗНАЧЕННЯ = {"round", "float", "int", "min", "max", "abs", "bool", "sum", "any", "all", "set", "frozenset",
                     "tuple", "list", "sorted", "len", "str"}
ЗГОРТКИ = {"sum", "max", "min", "mean", "median", "fmean"}

# Таблиці, що за ім'ям і літералом підходять, але місця речі на ній не несуть. Причина — поіменно; таблиця без
# причини лічиться (нове ім'я фіксера не зникає з лічби мовчки).
НЕ_ТАБЛИЦІ = {
    ("verify.py", "_ЗОНА_СЛОТА"): "зона іменника в тексті опису (верх ↔ низ) для звірки слів, не де річ на ній",
    ("композитор_слоти.py", "_ЗОНА_КРОЮ"): "який ярус кроїв тіла ранжує слот (K-BOD-02): слот «верх» за означенням "
                                          "шиється на торс — поділ слотів, не місце речі в образі",
    ("фід_атрибути.py", "ЗОНА_РОЗМІЩЕННЯ"): "ключі — основи слів опису принта (місце мотиву на самій речі); «низ» тут "
                                           "— основа слова «низ»/поділ, не слот",
    ("аксесуари_структура.py", "СЛОВА_МІСЦЯ"): "ключі — значення запису `місце` аксесуара (місце носіння з "
                                              "`місце_джерело`), «верх»/«сумка» — місця, не слоти: слова для жінки",
    ("аксесуари_структура.py", "МІСЦЕ_НАСЛІДКИ"): "ключі — значення запису `місце` аксесуара (місце носіння), не "
                                                 "слоти: наслідок обраного місця",
    ("аксесуари_структура.py", "МІСЦЕ_КОД"): "ключі — значення запису `місце` (у руці, кросбоді…), не слоти: код місця",
    ("аксесуари_структура.py", "МІСЦЯ_АСИМЕТРІЇ"): "члени — значення запису `місця` аксесуара (місця носіння), "
                                                  "«кросбоді» — місце, не тип: фільтр запису",
    ("силует_пропорції.py", "ЗОНИ_ПАРИ"): "зони тіла, які порівнює пара пропорції (плечі/груди проти стегон) — "
                                         "означення правила, не де річ на ній (межа — ЗНАХІДКА в PR приладу)",
    ("фід_взуття.py", "ВИРІЗ_ЗА_ТИПОМ"): "виріз (лінія підйому) взуття за типом — конструкція речі, не місце на ній",
}

# Самоперевірка вибіркою паспорта («Клас місць», приклади на `main` 06.11; номери рядків зсуваються — шукаємо за
# функцією й текстом рядка). Зникле — «нема» (виправлено чи прилад сліпий: звір), без коду 1.
ВІДОМІ = (
    ("п.1", "колір_річ.py", "near_слота", r"SLOT_NEAR_FALLBACK\.get\(слот"),
    ("п.1", "outfit.py", "елементи", r"near = near_слота\(s, дистанція\)"),
    ("п.2", "колір_світлота.py", "біля_обличчя", r'e\["near"\] >= NEAR_МІН'),
    ("п.4", "face_features.py", "_контраст", r"Lh = sum\("),
    ("п.4", "face_features.py", "_контраст", r"gap = round\(abs\(Lh"),
    ("п.4", "face_features.py", "_контраст_рис", r'_мішельсон\(шк\["L"\], sum\(вол\)'),
    ("п.1", "формальність.py", "нагода_палітра", r"in ПОВЕРХНІ_БІЛЯ_ОБЛИЧЧЯ_БІЛОГО"),
    ("п.2", "формальність.py", "нагода_палітра", r'e\.get\("near"\)'),
    ("п.1", "регістр_уваги.py", "на_мету", r"ЗОНА_МЕТИ_СЛОТИ\[з\]"),
    ("п.1", "траурний_регістр.py", "метал_біля_обличчя", r"in МЕТАЛ_БІЛЯ_ОБЛИЧЧЯ_СЛОТИ"),
)
НЕ_МІСЦЯ = (
    ("запис: обране місце аксесуара", "аксесуари_структура.py", "_займає", r'р\.get\("місце"\)'),
    ("запис: місце з походженням", "композитор_річ.py", "обрати_місце", r'r\.get\("місце"\)'),
    ("походження near: лише виміряний", "outfit.py", "елементи", r'if e\["near_виміряний"\]: по_речах'),
    ("копія виміру з масок", "pipeline.py", None, r'near=m\[i\]\["near"\]'),
    ("писач виміру з масок", "areas.py", None, r"near=near_share\("),
)


# ── обсяг і словники ──────────────────────────────────────────────────────────────────────────────────────────
def прочитати(шлях):
    """Текст файлу; не прочитано — запис Д10 і None."""
    try:
        with open(шлях, encoding="utf-8") as ф:
            return ф.read()
    except (OSError, UnicodeDecodeError) as е:
        ОБСЯГ.непрочитано(шлях, е)
        return None


def словник_речей(дж):
    """Назви слотів, під-слотів і типів речі: `slots.py` (ключі, значення, типи) і `внутрішня_мова.ТАБЛИЦЯ`
    (`item_type`). Без жодного з них лічба п.1/п.3 неповна — запис Д10."""
    слова = {"верхній_шар", "комплект"}
    шлях = os.path.join(дж, "slots.py")
    текст = прочитати(шлях)
    дерево = ОБСЯГ.розібрати(текст, "джерела/slots.py") if текст is not None else None
    знайдено = set()
    for в in (ast.walk(дерево) if дерево else ()):
        if isinstance(в, ast.Assign) and any(isinstance(ц, ast.Name) and ц.id in ("КЛЮЧІ", "_SLOT_TYPES")
                                            for ц in в.targets):
            знайдено.add(в.targets[0].id)
            слова |= {д.value for д in ast.walk(в.value) if isinstance(д, ast.Constant) and isinstance(д.value, str)}
    if дерево is not None and знайдено != {"КЛЮЧІ", "_SLOT_TYPES"}:
        ОБСЯГ.непрочитано("джерела/slots.py", "нема КЛЮЧІ чи _SLOT_TYPES — словник слотів неповний")
    шлях = os.path.join(дж, "внутрішня_мова.py")
    текст = прочитати(шлях)
    дерево = ОБСЯГ.розібрати(текст, "джерела/внутрішня_мова.py") if текст is not None else None
    типи = None
    for в in (ast.walk(дерево) if дерево else ()):
        if isinstance(в, ast.Dict):
            for к, з in zip(в.keys, в.values):
                if isinstance(к, ast.Constant) and к.value == "item_type" and isinstance(з, ast.Dict):
                    типи = {д.value for д in ast.walk(з) if isinstance(д, ast.Constant) and isinstance(д.value, str)}
    if дерево is not None and not типи:
        ОБСЯГ.непрочитано("джерела/внутрішня_мова.py", "нема ТАБЛИЦЯ[\"item_type\"] — словник типів неповний")
    return слова | (типи or set())


class Модуль:
    """Розібраний модуль продукту: дерево, батьки вузлів, функція кожного вузла, імпорти, сталі модуля."""

    def __init__(self, імя, файл, дерево, текст):
        self.імя, self.файл, self.дерево = імя, файл, дерево
        self.рядки = текст.splitlines()
        self.батько, self.функція = {}, {}
        self.імпорти = {}          # ім'я → ("мод", М) | ("обʼєкт", М, Х)
        self.сталі = {}            # ім'я сталої модуля → вузол присвоєння
        self.функції = {}          # ім'я функції модуля (і вкладеної) → вузол
        self._обійти(дерево, None, None)
        for в in дерево.body:
            for ім, знач in _цілі(в):
                self.сталі.setdefault(ім, в)

    def _обійти(self, вузол, батько, функція):
        self.батько[id(вузол)] = батько
        self.функція[id(вузол)] = функція
        if isinstance(вузол, (ast.FunctionDef, ast.AsyncFunctionDef)):
            self.функції.setdefault(вузол.name, вузол)
            функція = вузол
        if isinstance(вузол, ast.Import):
            for а in вузол.names:
                self.імпорти[(а.asname or а.name).split(".")[0]] = ("мод", а.name if а.asname else
                                                                   а.name.split(".")[0])
        elif isinstance(вузол, ast.ImportFrom) and not вузол.level and вузол.module:
            for а in вузол.names:
                self.імпорти[а.asname or а.name] = ("обʼєкт", вузол.module, а.name)
        elif isinstance(вузол, ast.Assign) and len(вузол.targets) == 1 and isinstance(вузол.targets[0], ast.Name) \
                and isinstance(вузол.value, ast.Call) and isinstance(вузол.value.func, ast.Name) \
                and вузол.value.func.id == "__import__" and вузол.value.args \
                and isinstance(вузол.value.args[0], ast.Constant) and isinstance(вузол.value.args[0].value, str):
            self.імпорти[вузол.targets[0].id] = ("мод", вузол.value.args[0].value)
        for дитина in ast.iter_child_nodes(вузол):
            self._обійти(дитина, вузол, функція)

    def рядок(self, н):
        return self.рядки[н - 1] if 0 < н <= len(self.рядки) else ""


def _цілі(вузол):
    """[(ім'я, значення)] простого присвоєння (`Х = …`, `Х: т = …`)."""
    if isinstance(вузол, ast.Assign):
        return [(ц.id, вузол.value) for ц in вузол.targets if isinstance(ц, ast.Name)]
    if isinstance(вузол, ast.AnnAssign) and вузол.value is not None and isinstance(вузол.target, ast.Name):
        return [(вузол.target.id, вузол.value)]
    return []


def сталої_ім(ім):
    """Ім'я сталої: великі літери, цифри, підкреслення (`_ТОРС`, `SLOT_NEAR_FALLBACK`)."""
    return bool(re.fullmatch(r"_*[A-ZА-ЯІЇЄҐ][A-ZА-ЯІЇЄҐ0-9_']*", ім))


# ── лічба ─────────────────────────────────────────────────────────────────────────────────────────────────────
class Прилад:
    def __init__(self, корінь):
        self.корінь = корінь
        self.дж = os.path.join(корінь, "джерела")
        self.модулі = {}
        self.місця = {}            # (файл, рядок) → (пункт, чому, функція)
        self.таблиці = {}          # (мод, ім'я) → dict(файл, рядок, ім'я, похідна, слова)
        self.не_таблиці = {}       # (файл, ім'я) → причина (знайдені на дереві)
        self.обгортки = {}         # (мод, ім'я функції) → рядок
        self.слова = set()

    # обсяг
    def завантажити(self):
        self.слова = словник_речей(self.дж)
        if not os.path.isdir(self.дж):
            ОБСЯГ.непрочитано("джерела", "теки нема")
            return
        for ф in sorted(os.listdir(self.дж)):
            if not ф.endswith(".py") or НЕ_ПРОДУКТ.match(ф):
                continue
            текст = прочитати(os.path.join(self.дж, ф))
            if текст is None:
                continue
            дерево = ОБСЯГ.розібрати(текст, "джерела/" + ф)
            if дерево is not None:
                self.модулі[ф[:-3]] = Модуль(ф[:-3], ф, дерево, текст)

    # розкриття імен
    def канон(self, мод, ім, глибина=0):
        """(модуль визначення, ім'я) з розкриттям `from М import Х` і повторного експорту."""
        м = self.модулі.get(мод)
        if м is None or глибина > 8:
            return (мод, ім)
        і = м.імпорти.get(ім)
        if і and і[0] == "обʼєкт" and ім not in м.функції:
            return self.канон(і[1], і[2], глибина + 1)
        return (мод, ім)

    def на_що(self, м, вузол):
        """Канон імені чи атрибута-модуля (`А.Х`) вузла; None — не ім'я модуля."""
        if isinstance(вузол, ast.Name):
            ф = м.функція.get(id(вузол))
            if ф is not None and (ф.name, вузол.id) in self._локальні.get(м.імя, {}):
                return (м.імя, ф.name + "." + вузол.id)
            if ф is not None and вузол.id in self._присвоєні(м, ф):
                return None
            і = м.імпорти.get(вузол.id)
            if і and і[0] == "обʼєкт":
                return self.канон(і[1], і[2])
            if вузол.id in м.сталі or вузол.id in м.функції:
                return (м.імя, вузол.id)
            return None
        if isinstance(вузол, ast.Attribute) and isinstance(вузол.value, ast.Name):
            і = м.імпорти.get(вузол.value.id)
            if і and і[0] == "мод" and not self._затінено(м, вузол.value):
                return self.канон(і[1], вузол.attr)
        return None

    def _присвоєні(self, м, ф):
        кеш = self._кеш_присвоєних.setdefault(м.імя, {})
        if ф.name not in кеш:
            імена = {а.arg for а in ф.args.args + ф.args.kwonlyargs + ф.args.posonlyargs}
            імена |= {а.arg for а in (ф.args.vararg, ф.args.kwarg) if а}
            for в in ast.walk(ф):
                if isinstance(в, ast.Name) and isinstance(в.ctx, ast.Store):
                    імена.add(в.id)
            кеш[ф.name] = імена
        return кеш[ф.name]

    def _затінено(self, м, ім_вузол):
        ф = м.функція.get(id(ім_вузол))
        return ф is not None and ім_вузол.id in self._присвоєні(м, ф) and ім_вузол.id not in м.імпорти

    # таблиці
    def знайти_таблиці(self):
        self._кеш_присвоєних, self._локальні = {}, {}
        for м in self.модулі.values():
            лок = self._локальні.setdefault(м.імя, {})
            for в in ast.walk(м.дерево):
                for ім, знач in _цілі(в):
                    if not сталої_ім(ім) or not СЛОВНИК_ТАБЛИЦІ.search(ім):
                        continue
                    слова = self._слова_значення(м, знач)
                    if not слова:
                        continue
                    if (м.файл, ім) in НЕ_ТАБЛИЦІ:
                        self.не_таблиці[(м.файл, ім)] = НЕ_ТАБЛИЦІ[(м.файл, ім)]
                        continue
                    ф = м.функція.get(id(в))
                    ключ = (м.імя, ім) if ф is None else (м.імя, ф.name + "." + ім)
                    if ф is not None:
                        лок[(ф.name, ім)] = в
                    self.таблиці[ключ] = dict(файл=м.файл, рядок=в.lineno, імя=ключ[1], похідна=False,
                                              слова=sorted(слова)[:6])
        # похідні: стала модуля, чиє значення читає таблицю
        змінено = True
        while змінено:
            змінено = False
            for м in self.модулі.values():
                for в in м.дерево.body:
                    for ім, знач in _цілі(в):
                        if (м.імя, ім) in self.таблиці or (м.файл, ім) in НЕ_ТАБЛИЦІ:
                            continue
                        if any(self.на_що(м, д) in self.таблиці for д in ast.walk(знач)
                               if isinstance(д, (ast.Name, ast.Attribute))):
                            self.таблиці[(м.імя, ім)] = dict(файл=м.файл, рядок=в.lineno, імя=ім, похідна=True,
                                                            слова=[])
                            змінено = True

    def _слова_значення(self, м, знач, глибина=0):
        """Назви речей у літералі: рядкові сталі, ключі, іменовані аргументи `dict(…)`, сталі модуля за іменем."""
        слова = set()
        # ім'я під індексом чи атрибутом (`ТАБЛИЦЯ["zone"]`) — частина іншої сталої, не вся вона: не розкриваємо
        під = {id(д.value) for д in ast.walk(знач) if isinstance(д, (ast.Subscript, ast.Attribute))}
        for д in ast.walk(знач):
            if id(д) in під:
                continue
            if isinstance(д, ast.Constant) and isinstance(д.value, str) and д.value in self.слова:
                слова.add(д.value)
            elif isinstance(д, ast.keyword) and д.arg in self.слова:
                слова.add(д.arg)
            elif isinstance(д, ast.Name) and глибина < 3 and д.id in м.сталі and д.id != getattr(знач, "id", None):
                for ім, з in _цілі(м.сталі[д.id]):
                    if ім == д.id:
                        слова |= self._слова_значення(м, з, глибина + 1)
        return слова

    # обгортки
    def несе(self, м, вираз, мітки):
        """Чи вираз несе значення таблиці чи обгортки (див. п.1)."""
        if вираз is None:
            return False
        if isinstance(вираз, (ast.Name, ast.Attribute)):
            if isinstance(вираз, ast.Name) and вираз.id in мітки:
                return True
            return self.на_що(м, вираз) in self.таблиці
        if isinstance(вираз, ast.Subscript):
            return self.несе(м, вираз.value, мітки)
        if isinstance(вираз, ast.Call):
            ф = вираз.func
            if self.на_що(м, ф) in self.обгортки:
                return True
            if isinstance(ф, ast.Attribute) and self.несе(м, ф.value, мітки):
                return True
            if isinstance(ф, ast.Name) and ф.id in ОБГОРТКИ_ЗНАЧЕННЯ:
                return any(self.несе(м, а, мітки) for а in вираз.args)
            return False
        if isinstance(вираз, ast.Compare):
            return any(self.несе(м, ч, мітки) for ч in [вираз.left] + вираз.comparators)
        if isinstance(вираз, ast.BoolOp):
            return any(self.несе(м, ч, мітки) for ч in вираз.values)
        if isinstance(вираз, ast.BinOp):
            return self.несе(м, вираз.left, мітки) or self.несе(м, вираз.right, мітки)
        if isinstance(вираз, ast.UnaryOp):
            return self.несе(м, вираз.operand, мітки)
        if isinstance(вираз, ast.IfExp):
            return any(self.несе(м, ч, мітки) for ч in (вираз.test, вираз.body, вираз.orelse))
        if isinstance(вираз, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self.несе(м, вираз.elt, мітки) or any(
                self.несе(м, г.iter, мітки) or any(self.несе(м, у, мітки) for у in г.ifs) for г in вираз.generators)
        if isinstance(вираз, ast.NamedExpr):
            return self.несе(м, вираз.value, мітки)
        return False

    def знайти_обгортки(self):
        змінено = True
        while змінено:
            змінено = False
            for м in self.модулі.values():
                for ф in [в for в in ast.walk(м.дерево) if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))]:
                    if (м.імя, ф.name) in self.обгортки:
                        continue
                    мітки = self._мітки(м, ф)
                    if any(isinstance(в, ast.Return) and м.функція.get(id(в)) is ф and self.несе(м, в.value, мітки)
                           for в in ast.walk(ф)):
                        self.обгортки[(м.імя, ф.name)] = ф.lineno
                        змінено = True

    def _мітки(self, м, ф):
        """Локальні імена функції, яким присвоєно значення таблиці чи обгортки (до нерухомої точки)."""
        мітки = set()
        while True:
            нові = set(мітки)
            for в in ast.walk(ф):
                if м.функція.get(id(в)) is not ф:
                    continue
                if isinstance(в, (ast.Assign, ast.AnnAssign, ast.AugAssign, ast.NamedExpr)) and в.value is not None:
                    цілі = в.targets if isinstance(в, ast.Assign) else [в.target]
                    if self.несе(м, в.value, мітки):
                        нові |= {д.id for ц in цілі for д in ast.walk(ц) if isinstance(д, ast.Name)}
            if нові == мітки:
                return мітки
            мітки = нові

    # місця
    def додати(self, м, рядок, пункт, чому, вузол):
        ф = м.функція.get(id(вузол))
        ключ = (м.файл, рядок)
        if ключ not in self.місця or пункт < self.місця[ключ][0]:
            self.місця[ключ] = (пункт, чому, ф.name if ф is not None else "<модуль>")

    def читає_запис(self, м, ф):
        if ф is None:
            return False
        for в in ast.walk(ф):
            if isinstance(в, ast.Constant) and isinstance(в.value, str) and ЗАПИС.match(в.value):
                п = м.батько.get(id(в))
                if isinstance(п, ast.Subscript) or (isinstance(п, ast.Call) and isinstance(п.func, ast.Attribute)
                                                     and п.func.attr in ("get", "pop", "setdefault")):
                    # походження лише в підписі («виміряно» / «запасне число») рахунку не править — не читач запису
                    в_тексті = м.батько.get(id(п))
                    if isinstance(в_тексті, ast.IfExp) and в_тексті.test is п and all(
                            isinstance(г, ast.Constant) and isinstance(г.value, str)
                            for г in (в_тексті.body, в_тексті.orelse)):
                        continue
                    return True
        return False

    def п1(self, м):
        визначення = set()
        for в in м.дерево.body:
            for ім, знач in _цілі(в):
                if (м.імя, ім) in self.таблиці:
                    визначення.add(id(знач))
        for в in ast.walk(м.дерево):
            if isinstance(в, (ast.Assign, ast.AnnAssign)) and м.функція.get(id(в)) is not None:
                for ім, знач in _цілі(в):
                    if (м.імя, м.функція[id(в)].name + "." + ім) in self.таблиці:
                        визначення.add(id(знач))
        for в in ast.walk(м.дерево):
            if self._під(м, в, визначення):
                continue
            if isinstance(в, (ast.Name, ast.Attribute)) and isinstance(getattr(в, "ctx", None), ast.Load):
                if isinstance(в, ast.Name) and isinstance(м.батько.get(id(в)), ast.Attribute):
                    pass
                к = self.на_що(м, в)
                if к in self.таблиці:
                    self.додати(м, в.lineno, 1, "стала класу: %s" % к[1], в)
            elif isinstance(в, ast.Call):
                к = self.на_що(м, в.func)
                if к in self.обгортки:
                    self.додати(м, в.lineno, 1, "обгортка сталої класу: %s.%s" % к, в)

    def _під(self, м, вузол, корені):
        п = вузол
        while п is not None:
            if id(п) in корені:
                return True
            п = м.батько.get(id(п))
        return False

    def п2(self, м):
        for в in ast.walk(м.дерево):
            читання = (isinstance(в, ast.Subscript) and isinstance(в.ctx, ast.Load)
                       and isinstance(в.slice, ast.Constant) and в.slice.value == "near") or \
                      (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get"
                       and в.args and isinstance(в.args[0], ast.Constant) and в.args[0].value == "near")
            if not читання:
                continue
            ф = м.функція.get(id(в))
            if self.читає_запис(м, ф) or self._копія(м, в):
                continue
            self.додати(м, в.lineno, 2, "поле near без походження (стала класу слота як факт)", в)

    def _копія(self, м, вузол):
        """Значення лише копіюється: аргумент-ключ виклику чи значення словника (крізь обгортки значення)."""
        поточний, п = вузол, м.батько.get(id(вузол))
        while isinstance(п, ast.Call) and isinstance(п.func, ast.Name) and п.func.id in ОБГОРТКИ_ЗНАЧЕННЯ \
                and поточний in п.args:
            поточний, п = п, м.батько.get(id(п))
        if isinstance(п, ast.keyword):
            return True
        return isinstance(п, ast.Dict) and поточний in п.values

    def п3(self, м):
        for в in ast.walk(м.дерево):
            if not isinstance(в, ast.Compare):
                continue
            ф = м.функція.get(id(в))
            if ф is None or not any(СЛОВНИК_ФУНКЦІЇ.match(сл) for сл in ф.name.split("_")) or \
                    self.читає_запис(м, ф):
                continue
            частини = [в.left] + в.comparators
            літерал = [ч for ч in частини if self._літерал_речей(ч)]
            if not літерал:
                continue
            інші = [ч for ч in частини if ч not in літерал]
            if any(re.search(r"слот|тип|\bсл\b|\bs\b|\bс\b", ast.unparse(ч)) for ч in інші):
                self.додати(м, в.lineno, 3, "власна логіка правила: слот/тип проти літерала (%s)"
                            % ast.unparse(літерал[0])[:50], в)

    def _літерал_речей(self, вираз):
        if isinstance(вираз, ast.Constant):
            return isinstance(вираз.value, str) and вираз.value in self.слова
        if isinstance(вираз, (ast.Tuple, ast.Set, ast.List)) and вираз.elts:
            return all(isinstance(е, ast.Constant) for е in вираз.elts) and any(
                isinstance(е.value, str) and е.value in self.слова for е in вираз.elts)
        return False

    def п4(self, м):
        for ф in [в for в in ast.walk(м.дерево) if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef))]:
            if self.читає_запис(м, ф):
                continue
            збірки, збірки_L, світлота_в, шкіра = set(), set(), set(), set()
            for _ in range(4):
                for в in ast.walk(ф):
                    if м.функція.get(id(в)) is not ф:
                        continue
                    for ім, знач in _цілі(в):
                        if self._збірка_волосся(знач):
                            збірки.add(ім)
                            if self._бере_L(знач.elt):     # хрома C — межа (ЗНАХІДКА), не L*
                                збірки_L.add(ім)
                        if self._світлота_волосся(знач, збірки, світлота_в, збірки_L):
                            світлота_в.add(ім)
                        if self._шкіра(знач, шкіра):
                            шкіра.add(ім)
            for в in ast.walk(ф):
                if м.функція.get(id(в)) is not ф:
                    continue
                if isinstance(в, ast.Call) and self._ім_виклику(в) in ЗГОРТКИ and any(
                        self._по_голосах(а, збірки, збірки_L) for а in в.args):
                    self.додати(м, в.lineno, 4, "голоси волосся перемішано: згортка L* усіх голосів", в)
                elif isinstance(в, (ast.BinOp, ast.Call)):
                    ч = [в.left, в.right] if isinstance(в, ast.BinOp) else list(в.args)
                    if any(self._світлота_волосся(х, збірки, світлота_в, збірки_L) for х in ч) and \
                            any(self._шкіра_L(х, шкіра) for х in ч):
                        self.додати(м, в.lineno, 4, "волосся видно: світлота волосся проти шкіри без знання, "
                                                    "чи образ його закриває", в)

    @staticmethod
    def _ім_виклику(в):
        return в.func.attr if isinstance(в.func, ast.Attribute) else в.func.id if isinstance(в.func, ast.Name) else ""

    @staticmethod
    def _фільтр_волосся(вираз):
        for д in ast.walk(вираз):
            if isinstance(д, ast.Call) and isinstance(д.func, ast.Attribute) and д.func.attr == "startswith" \
                    and д.args and isinstance(д.args[0], ast.Constant) and д.args[0].value == "волосся":
                return True
            if isinstance(д, ast.Compare) and any(isinstance(ч, ast.Constant) and ч.value == "волосся"
                                                 for ч in [д.left] + д.comparators) \
                    and any(isinstance(ч, ast.Call) for ч in [д.left] + д.comparators):
                return True
        return False

    def _збірка_волосся(self, вираз):
        return isinstance(вираз, (ast.ListComp, ast.SetComp, ast.GeneratorExp)) and any(
            any(self._фільтр_волосся(у) for у in г.ifs) for г in вираз.generators)

    @staticmethod
    def _бере_L(вираз):
        return any((isinstance(д, ast.Subscript) and isinstance(д.slice, ast.Constant) and д.slice.value == "L") or
                   (isinstance(д, ast.Call) and isinstance(д.func, ast.Attribute) and д.func.attr == "get" and д.args
                    and isinstance(д.args[0], ast.Constant) and д.args[0].value == "L") for д in ast.walk(вираз))

    def _по_голосах(self, вираз, збірки, збірки_L=()):
        """Аргумент згортки — L* по всіх голосах: збірка волосся з L, чи генератор над нею, що бере L."""
        if self._збірка_волосся(вираз) and self._бере_L(вираз):
            return True
        if isinstance(вираз, ast.Name) and вираз.id in збірки_L:
            return True
        if isinstance(вираз, (ast.ListComp, ast.SetComp, ast.GeneratorExp)):
            return self._бере_L(вираз.elt) and any(isinstance(г.iter, ast.Name) and г.iter.id in збірки
                                                    for г in вираз.generators)
        return False

    def _світлота_волосся(self, вираз, збірки, світлота_в, збірки_L=()):
        for д in ast.walk(вираз):
            if isinstance(д, ast.Name) and д.id in світлота_в:
                return True
            if isinstance(д, ast.Call) and self._ім_виклику(д) in ЗГОРТКИ and any(
                    self._по_голосах(а, збірки, збірки_L) for а in д.args):
                return True
            if isinstance(д, ast.Subscript) and isinstance(д.slice, ast.Constant) and д.slice.value == "L" and \
                    self._ключ_волосся(д.value):
                return True
        return False

    @staticmethod
    def _ключ_волосся(вираз):
        return any(isinstance(д, ast.Constant) and isinstance(д.value, str) and д.value.startswith("волосся")
                   for д in ast.walk(вираз))

    @staticmethod
    def _шкіра(вираз, шкіра):
        return any((isinstance(д, ast.Constant) and д.value == "шкіра") or (isinstance(д, ast.Name) and д.id in шкіра)
                   for д in ast.walk(вираз))

    def _шкіра_L(self, вираз, шкіра):
        """Світлота шкіри: `шк["L"]`, `F["шкіра"]["L"]`, `(F.get("шкіра") or {}).get("L")`, ім'я з неї."""
        for д in ast.walk(вираз):
            if (isinstance(д, ast.Subscript) and isinstance(д.slice, ast.Constant) and д.slice.value == "L") or \
                    (isinstance(д, ast.Call) and isinstance(д.func, ast.Attribute) and д.func.attr == "get"
                     and д.args and isinstance(д.args[0], ast.Constant) and д.args[0].value == "L"):
                if self._шкіра(д.value if isinstance(д, ast.Subscript) else д.func.value, шкіра):
                    return True
            if isinstance(д, ast.Name) and д.id in шкіра and isinstance(вираз, ast.Name):
                return False
        return False

    def js(self):
        файли = [os.path.join("показ", ф) for ф in sorted(os.listdir(os.path.join(self.дж, "показ")))
                 if ф.endswith(".js")] if os.path.isdir(os.path.join(self.дж, "показ")) else []
        файли += [ф for ф in JS_ПОКАЗУ if os.path.isfile(os.path.join(self.дж, ф))]
        імена = sorted({к[1].split(".")[-1] for к in self.таблиці}, key=len, reverse=True)
        таблиця = re.compile(r"\b(%s)\b" % "|".join(map(re.escape, імена))) if імена else None
        поле = re.compile(r"\.near\b(?!_)|\[\s*['\"]near['\"]\s*\]")
        for ф in файли:
            текст = прочитати(os.path.join(self.дж, ф))
            if текст is None:
                continue
            for н, р in enumerate(текст.splitlines(), 1):
                код = re.sub(r"//.*$", "", р)
                if код.lstrip().startswith(("*", "/*")):
                    continue
                if таблиця and таблиця.search(код):
                    self.місця.setdefault((ф, н), (1, "стала класу в показі: %s" % таблиця.search(код).group(1), "JS"))
                elif поле.search(код):
                    self.місця.setdefault((ф, н), (2, "поле near у показі без походження", "JS"))

    def лічити(self):
        self.завантажити()
        self.знайти_таблиці()
        self.знайти_обгортки()
        for м in self.модулі.values():
            self.п1(м)
        for м in self.модулі.values():
            self.п2(м)
            self.п3(м)
            self.п4(м)
        self.js()
        return self.місця

    # самоперевірка
    def самоперевірка(self):
        рядки, хиба = [], False
        за_файлом = {}
        for (ф, н), (п, _, фн) in self.місця.items():
            за_файлом.setdefault(ф, []).append((н, п, фн))
        for пункт, ф, фн, ре in ВІДОМІ:
            м = self.модулі.get(ф[:-3])
            знайдено = м is not None and any(
                фн_ == фн and re.search(ре, м.рядок(н)) and "п.%d" % п == пункт for н, п, фн_ in за_файлом.get(ф, ()))
            рядки.append("  %s %s %s:%s «%s»" % ("✓" if знайдено else "нема", пункт, ф, фн, ре))
        for чому, ф, фн, ре in НЕ_МІСЦЯ:
            м = self.модулі.get(ф[:-3])
            хибне = м is not None and any((фн is None or фн_ == фн) and re.search(ре, м.рядок(н))
                                         for н, п, фн_ in за_файлом.get(ф, ()))
            хиба |= хибне
            рядки.append("  %s не місце (%s) %s «%s»" % ("✗ ЛІЧИТЬСЯ" if хибне else "✓", чому, ф, ре))
        return рядки, хиба


def main(argv=None):
    ап = argparse.ArgumentParser(description="Прилад кореня Е3-місце-речі")
    ап.add_argument("--корінь", default=".")
    ап.add_argument("--тихо", action="store_true", help="без переліку місць")
    а = ап.parse_args(argv)
    п = Прилад(а.корінь)
    місця = п.лічити()
    if not а.тихо:
        for (ф, н), (пункт, чому, фн) in sorted(місця.items()):
            print("%s:%d · п.%d · %s · %s" % (ф, н, пункт, чому, фн))
    print("\nтаблиці місця (%d):" % len(п.таблиці))
    for к, т in sorted(п.таблиці.items(), key=lambda кт: (кт[1]["файл"], кт[1]["рядок"])):
        print("  %s:%d %s%s %s" % (т["файл"], т["рядок"], т["імя"], " (похідна)" if т["похідна"] else "",
                                   ",".join(т["слова"])))
    print("обгортки (%d): %s" % (len(п.обгортки), ", ".join("%s.%s" % к for к in sorted(п.обгортки))))
    print("не таблиці (причина поіменно, %d на дереві):" % len(п.не_таблиці))
    for (ф, ім), чому in sorted(НЕ_ТАБЛИЦІ.items()):
        print("  %s %s:%s — %s" % ("" if (ф, ім) in п.не_таблиці else "застаріле:", ф, ім, чому))
    за_пунктом = {}
    for пункт, _, _ in місця.values():
        за_пунктом[пункт] = за_пунктом.get(пункт, 0) + 1
    print("за пунктами: " + ", ".join("п.%d — %d" % (к, за_пунктом.get(к, 0)) for к in (1, 2, 3, 4)))
    print("модулів Python: %d" % len(п.модулі))
    рядки, хиба = п.самоперевірка()
    print("самоперевірка (вибірка паспорта):")
    print("\n".join(рядки))
    print("місць: %d" % len(місця))
    return 1 if хиба else 0


if __name__ == "__main__":
    sys.exit(main())
