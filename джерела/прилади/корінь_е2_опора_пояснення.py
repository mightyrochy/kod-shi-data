# -*- coding: utf-8 -*-
"""Лічить місця кореня Е2-опора-пояснення: пояснення каже як факт те, чого продукт не знає (без запуску продукту).

Клас — `аудит/корені/Е2-опора-пояснення.md` («Клас місць»): точка коду продукту (`джерела/` на будь-якій глибині, Python,
JS і промпти в них; проби, прилади, тести й `джерела/аудит` — ні), де значення входить у текст, який читає жінка під
образом, без свого джерела й певності. Сім пунктів:
  1  поле запису речі (колір, крій, вид, тканина…) іде у вхід моделі опису чи перекладачки як факт — писач ключа на
     дріт (пара `("cut", …)`, ключ словника, цикл за перелічком ознак) чи рядок-ярлик промпта («colour code: …»)
     без умови певності в самому значенні (`кадр_колір`, `свідчення…`, `певн…`, `сирий` тощо);
  2  виведене чи взяте за замовчуванням значення сценарію й палітри (`metal`, `light`, `road_salt`, `season`…) іде у
     вхід без позначки джерела (`<ключ>_source`, `sources`, читання `…_джерело`/`походження…` у значенні);
  3  заява коду (визначення коду заяви — словник «код → англійське визначення») стверджує обставину (лід, дощ, сніг,
     вітер), а умова виходу заяви (`if` довкола `заява("код")`) читає не її слова про цю обставину, а смугу чи
     температуру: «читає її слова» — за джерелом значення (змінна з її слів чи полів запису), а не за збігом підрядка в
     імені; умова на змінній, присвоєній результатом виклику зі смугою чи температурою в аргументах (`сльота =
     сольова_сльота(реагенти, смуга_погоди, опади)`), читає виведене, не її слова;
  4  речення промпта вимагає сказати про властивість чи обставину (день, дорога, зручність, тепло, вибір) без умови
     «коли вона відома» (`when/if/only/known/support/omit…`);
  5  правило перекладу ставить значення коду (код кольору, виду) на місце того, що модель назвала з фото;
  6  виклик моделі з кадрами (JS) без лічби дійшлих, що вирішує шлях відповіді: лічба — в умові `if`/`while`/`?`, чия
     гілка міняє шлях (повтор, інший промпт, вихід), чи їде з відповіддю до викликача (`return`, вихідний параметр);
     згадка лічби лише в запису чи діагнозі — не рішення, відповідь далі йде як «із фото»;
  7  гілка за замовчуванням (нема запису, ключа, паспорта) вертає чи підставляє позначку довіри — «її слова»
     (`her_words`, `her`, `hand`) чи «перевірено» (`verified`), або ствердний прапор вердикту: невідоме дістає довіру.
     Ланцюг джерел розпізнається і зі сталими всередині виклику, включення — за умовою відсутності факту;
     дефолт прапора — лише без гарантованого запису на цьому шляху; значення параметра функції за замовчуванням
     (`перевірено=True`, `джерело="her"`) — теж гілка за замовчуванням (16365). П.3 читається ширше: обставину, яку код вивів з іншої обставини
     (ланцюг виведення), заява теж не стверджує жінці її словом.
Вхід пояснення в Python — функції, досяжні викликами від `дріт_моделі.опис`, `мовний_шар._абзац_речей` і `сценарій.день_кодами`; п.3–6 лічать
увесь обсяг (п.4 — і визначення заяв: вимога без умови в них — місце). Що прилад не бачить, друкує `--не-виміряно` (і в `гіпотези`): перелік імен у п.2,
виходи заяв без `if`, JS-тексти заяв, рядки коду, що не складаються з літералів.

Запуск (з кореня репозиторію): python3 джерела/прилади/корінь_е2_опора_пояснення.py [--деталі] [--json] [--корінь ТЕКА]
Вивід: `файл:рядок · пункт · що`, підсумок за пунктами, останній рядок `місць: <N>` (різних `файл:рядок · пункт`), код 0."""
import ast
import json
import os
import re
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import обсяг_приладу as ОБСЯГ  # Д10: непрочитане — код 1, не менше місць

warnings.simplefilter("ignore", SyntaxWarning)

НЕ_ТЕКИ = {"проби", "прилади", "аудит", "__pycache__", "node_modules", "тести", "tests", ".git"}
НЕ_ФАЙЛ = re.compile(r"^(тест|test_|gate_|audit_|build_|стенд|батарея_|measure_|pair_test|replay|проба|мутанти)")
ВХОДИ = (("дріт_моделі", "опис"), ("мовний_шар", "_абзац_речей"), ("сценарій", "день_кодами"))
ПУНКТИ = {1: "поле запису речі йде у вхід моделі як факт", 2: "виведене значення йде без позначки джерела",
          3: "заява коду стверджує обставину, якої нема в її словах", 4: "вимога твердження без умови «коли відома»",
          5: "значення коду замість слова моделі з фото", 6: "виклик із кадрами не знає, скільки кадрів дійшло",
          7: "значення без запису походження дістає позначку «її слова» чи «перевірено»"}

# ── п.1 ──
ВЛАСТИВОСТІ = {"kind", "type", "color", "colour", "hex", "cut", "fabric", "material", "length", "sleeve", "shaft",
               "heel", "pattern", "shine", "details", "set_half"}
ЯРЛИК = re.compile(r"^\s*(kind|type|colou?r|cut|fabric|material|length|sleeve|shaft|heel|pattern|shine|details)"
                   r"( code)?:\s*%?[sd{]?")
# Умова певності — про САМЕ значення поля: виміряне чи ні (`не_вимір`, `тип_кольору`), сире чи перевірене. Умова «кадр
# іншого кольору» (`інший_кадр`, `кадр_колір`) — про кадр, а не про значення: вона мовчить колір лише коли кадр
# суперечить, а колір зі слова крамниці без виміру їде далі як факт (дошка 16058), тож умовою певності не є.
ПЕВНІСТЬ = re.compile(r"свідчен|певн|перевірен|сирий|крамниц|uncertain|unverified|не_знаю|невідом|не_вимір|"
                      r"тип_кольору", re.I)
# Кадр іншого кольору (`інший_кадр`, `кадр_колір`) — умова певності лише для ВИМІРУ (`hex`, `lab`): чужий кадр його
# спростовує. Колір зі слова крамниці (`color`) вимірюваним не є: кадр мовчить його, лише коли суперечить, а без виміру
# слово їде далі як факт (дошка 16058) — для нього така умова не рахується.
ЧУЖИЙ_КАДР = re.compile(r"інший_кадр|кадр_колір|кадр_кольору|photo_other", re.I)
ВИМІРИ = {"hex", "lab"}
# ── п.2 ──
ВИВЕДЕНІ = {"metal", "light", "road_salt", "occasion_requirements", "season", "formality"}
ДЖЕРЕЛО_КЛЮЧА = re.compile(r"(^|_)(source|sources|from|basis|джерело|джерела|походження)$", re.I)
ДЖЕРЕЛО_ЗНАЧЕННЯ = re.compile(r"джерел|походження|source", re.I)
# ── п.3 ──
# Обставина стверджена як наявна: «today there is black ice», «the day is rainy», «today there is heavy snow», «salty slush:
# …», «it is raining». Після зачину — сила («heavy», «light», «a lot of») і назва обставини іменником чи прикметником.
_ЗАЧИН = r"(today (there (is|are)|is|brings)|there (is|are)|the day is|it is|it rains|it is raining|^)\s*"
_СИЛА = r"((a |the |some |a lot of |very |heavy |light |thick |fresh |wet |deep |hard |strong |steady |persistent )*)"
ОБСТАВИНИ = {
    "лід": (re.compile(_ЗАЧИН + _СИЛА + r"(black ice|icy|ice\b)", re.I), ("ожеледиц", "ожеледь", "ice", "icy")),
    "дощ": (re.compile(_ЗАЧИН + _СИЛА + r"(rainy|raining|rain\b|rainfall|wet\b)", re.I),
            ("опади", "precipitation", "дощ", "rain")),
    "сніг": (re.compile(_ЗАЧИН + _СИЛА + r"(snowy|snowing|snow\b|snowfall|salty slush|slush)|"
                        r"\b(salted|salty) (road|roads|pavement|street|streets)\b|\bunder salt\b|\bsalt on the (road|roads)\b",
                        re.I),
             ("опади", "precipitation", "сніг", "snow", "реагент", "сльот", "сіль", "salt")),
    "вітер": (re.compile(_ЗАЧИН + _СИЛА + r"(windy|wind\b|gusts?)", re.I),
              ("вітер", "вітру", "wind")),
    # що під ногами: мокра чи слизька дорога, калюжі, сніг під ногами — обставина дня, яку код виводить з опадів
    # (`сценарій.поверхня_під_ногами`), а не жінка називає (рішення менеджера 17.11, п.3 ширше)
    "дорога": (re.compile(_ЗАЧИН + _СИЛА + r"(wet|slippery|icy|snowy|slushy|muddy|salted) (road|roads|ground|pavement|street|streets|"
                          r"surface|path)\b|\bpuddles?\b|\b(snow|ice|slush) underfoot\b", re.I),
               ("поверх", "surface", "дорог", "road", "ground", "опади", "precipitation", "мокр", "сльот", "сніг", "snow",
                "дощ", "rain", "ожеледиц", "ice")),
}
# Значення в умові виходу виведене з погоди, а не взяте з її слів: присвоєно результатом виклику, чиї аргументи несуть смугу чи
# температуру (`сльота, звідки = сольова_сльота(реагенти, смуга_погоди, опади)`). Збіг імені з маркером обставини («сльота» ~
# «сльот») про це мовчить: маркер — за ДЖЕРЕЛОМ значення (поле її слів), а не за підрядком у назві.
ВХІД_ВИВОДУ = re.compile(r"смуг|band|температур|temperat|мороз|frost", re.I)
ЗАСТЕРЕЖЕННЯ = re.compile(r"\b(does not (say|know)|do(es)? not know|unknown|whether|may|might|when she|if she|"
                          r"in case|when it)\b", re.I)
# ── п.4, п.5 (речення промптів) ──
ВИМОГА = re.compile(r"(?:^|[,;:—(] |\bto |\bmust |\bshould |\bmay |\band )"
                    r"(say|tell|explain|describe|state|name|mention|write|note|speak of|speak about)\b", re.I)
ПРЕДМЕТ = re.compile(r"\b(how|what|why)\b[^.;]{0,90}\b(her day|the day|day|walk|walking|feet|comfort|comfortable|"
                     r"warm|warmth|wear|wears|lives?|chose|choose|means? for|feels?|stays?)\b|"
                     r"\b(comfort|comfortable|practical|practicality|convenien\w+|cosy|breathable|durable|"
                     r"warm enough)\b|\bwhy you (still )?chose\b", re.I)
УМОВА = re.compile(r"\b(known|knows?|supports?|supported|supporting|absent|unknown|omit(ted)?|leave (it )?out|"
                   r"carries|has no|visible|listed|stated|marked)\b", re.I)
ЗАПЕРЕЧЕННЯ = re.compile(r"\b(not|never|no|nor|without|n't)\b", re.I)
КОД_ЗНАЧЕННЯ = re.compile(r"\b(colou?r|kind|type)\s+code\b", re.I)
ЗАМІНА_СЛОВА = re.compile(r"(do not turn|do not take|stands? in (their|its|that|the) place|in place of the (english|model)|"
                          r"instead of the (english|model|word)|whatever (word|the english)|"
                          r"not by another|ignore the (english|model|word))", re.I)
# ── п.6 ──
ВИКЛИК_ЗБІР = re.compile(r"\bfetch\b")
ДІЙШЛО = re.compile(r"images-dropped|дійшло|випало|dropped", re.I)
КАДРИ = re.compile(r"кадр|Кадр|фото|Фото|image|блокиК", re.I)


def корінь_репозиторію():
    if "--корінь" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--корінь") + 1])
    return os.getcwd()


КОРІНЬ = корінь_репозиторію()


def відн(шлях):
    return os.path.relpath(шлях, КОРІНЬ).replace(os.sep, "/")


def файли_продукту(корінь, розширення):
    вих = []
    for д, теки, фф in os.walk(os.path.join(корінь, "джерела")):
        теки[:] = sorted(т for т in теки if т not in НЕ_ТЕКИ and not т.startswith("дані"))
        for ф in sorted(фф):
            if ф.endswith(розширення) and not НЕ_ФАЙЛ.match(ф):
                вих.append(os.path.join(д, ф))
    return вих


def прочитати(шлях):
    with open(шлях, encoding="utf-8", errors="replace") as ф:
        return ф.read()


# ───────────────────────────── Python: модулі, виклики, досяжність ─────────────────────────────
class Модуль:
    def __init__(self, шлях, текст, дерево):
        self.шлях, self.ім, self.дерево = шлях, os.path.basename(шлях)[:-3], дерево
        self.рядки = текст.splitlines()
        self.батько = {}
        for в in ast.walk(дерево):
            for д in ast.iter_child_nodes(в):
                self.батько[д] = в
        self.функції = {н.name: н for н in дерево.body if isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef))}
        self.псевдоніми = {}
        for н in ast.walk(дерево):
            if isinstance(н, ast.Import):
                for а in н.names:
                    self.псевдоніми[а.asname or а.name] = (а.name, None)
            elif isinstance(н, ast.ImportFrom) and н.module:
                for а in н.names:
                    self.псевдоніми[а.asname or а.name] = (н.module, а.name)
        self.docstr = set()
        for н in ast.walk(дерево):
            if isinstance(н, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and н.body \
                    and isinstance(н.body[0], ast.Expr) and isinstance(н.body[0].value, ast.Constant):
                self.docstr.add(н.body[0].value)

    def предки(self, в):
        while в in self.батько:
            в = self.батько[в]
            yield в

    def функція_вузла(self, в):
        for п in self.предки(в):
            if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return п
        return None


def модулі_продукту(корінь):
    вих = {}
    for шлях in файли_продукту(корінь, ".py"):
        дерево = ОБСЯГ.розібрати(прочитати(шлях), відн(шлях))
        if дерево is not None:
            м = Модуль(відн(шлях), прочитати(шлях), дерево)
            вих[м.ім] = м
    return вих


def виклики_функції(м, всі, вузол):
    """Функції продукту (модуль, імʼя), які кличе `вузол`: імʼя в модулі, `from m import f`, `Псевдонім.f`."""
    вих = set()
    for н in ast.walk(вузол):
        if not isinstance(н, ast.Call):
            continue
        ф = н.func
        if isinstance(ф, ast.Name):
            if ф.id in м.функції:
                вих.add((м.ім, ф.id))
            elif ф.id in м.псевдоніми:
                мод, імя = м.псевдоніми[ф.id]
                if імя and мод in всі and імя in всі[мод].функції:
                    вих.add((мод, імя))
        elif isinstance(ф, ast.Attribute) and isinstance(ф.value, ast.Name) and ф.value.id in м.псевдоніми:
            мод, імя = м.псевдоніми[ф.value.id]
            if імя is None and мод in всі and ф.attr in всі[мод].функції:
                вих.add((мод, ф.attr))
    return вих


def досяжні(всі):
    бачені, стек = set(), [в for в in ВХОДИ if в[0] in всі and в[1] in всі[в[0]].функції]
    while стек:
        х = стек.pop()
        if х in бачені:
            continue
        бачені.add(х)
        м = всі[х[0]]
        стек.extend(виклики_функції(м, всі, м.функції[х[1]]))
    return бачені


def імена_у_виразі(в):
    """Усі імена, атрибути й рядкові сталі виразу (для пошуку умов і джерел)."""
    вих = []
    for н in ast.walk(в):
        if isinstance(н, ast.Name):
            вих.append(н.id)
        elif isinstance(н, ast.Attribute):
            вих.append(н.attr)
        elif isinstance(н, ast.Constant) and isinstance(н.value, str):
            вих.append(н.value)
    return вих


def рядок_сталої(в):
    return в.value if isinstance(в, ast.Constant) and isinstance(в.value, str) else None


# ───────────────────────────── п.1 ─────────────────────────────
def писачі_ознак(м, функція):
    """(рядок, ключ, значення-вузол, форма) — місця, де властивість речі йде на дріт у `функції`."""
    вих = []
    for н in ast.walk(функція):
        if isinstance(н, (ast.Tuple, ast.List)):
            пари = [е for е in н.elts if isinstance(е, ast.Tuple) and len(е.elts) == 2
                    and рядок_сталої(е.elts[0]) in ВЛАСТИВОСТІ]
            if len(пари) >= 2:
                for е in пари:
                    вих.append((е.lineno, рядок_сталої(е.elts[0]), е.elts[1], "пара ключ-значення"))
        elif isinstance(н, ast.Dict):
            ключі = [(рядок_сталої(к), v) for к, v in zip(н.keys, н.values) if к is not None]
            власт = [(к, v) for к, v in ключі if к in ВЛАСТИВОСТІ]
            if len(власт) >= 3:
                for к, v in власт:
                    вих.append((v.lineno, к, v, "ключ словника"))
        elif isinstance(н, (ast.DictComp, ast.For)):
            ітер = н.iter if isinstance(н, ast.For) else н.generators[0].iter
            if isinstance(ітер, ast.Name):
                ключі = перелік_ознак(м, ітер.id)
                if len(ключі) >= 4:
                    вих.append((н.lineno, "+".join(ключі), н, "цикл за перелічком ознак"))
        elif isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Subscript) \
                and рядок_сталої(н.targets[0].slice) in ВЛАСТИВОСТІ:
            вих.append((н.lineno, рядок_сталої(н.targets[0].slice), н, "присвоєння ключа"))
        elif isinstance(н, (ast.BinOp, ast.JoinedStr, ast.Call)):
            текст = None
            if isinstance(н, ast.BinOp) and isinstance(н.op, ast.Mod):
                текст = рядок_сталої(н.left)
            elif isinstance(н, ast.JoinedStr) and н.values and isinstance(н.values[0], ast.Constant):
                текст = str(н.values[0].value)
            elif isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr == "format":
                текст = рядок_сталої(н.func.value)
            if текст and ЯРЛИК.match(текст):
                вих.append((н.lineno, ЯРЛИК.match(текст).group(1), н, "рядок-ярлик промпта"))
    return вих


def перелік_ознак(м, імя):
    for н in м.дерево.body:
        if isinstance(н, ast.Assign) and any(isinstance(т, ast.Name) and т.id == імя for т in н.targets) \
                and isinstance(н.value, (ast.Tuple, ast.List)):
            ключі = [рядок_сталої(е) for е in н.value.elts]
            if sum(1 for к in ключі if к in ВЛАСТИВОСТІ) >= 4:
                return [к for к in ключі if к]
    return []


def умови_присвоєння(м, н):
    """Імена в `if`-умовах довкола присвоєння (до функції) і в самому значенні."""
    імена = імена_у_виразі(н.value)
    for п in м.предки(н):
        if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef)):
            break
        if isinstance(п, ast.If):
            імена += імена_у_виразі(п.test)
    return імена


def п1(всі, шлях_входу):
    """Писачі властивостей речі у функціях входу пояснення. Функція, яку кличе функція з циклом за перелічком ознак,
    лише готує запис, з якого перелічок бере свої ключі: її писачі — не місця, місце — сам цикл."""
    місця, не_місця = [], []
    фільтри = {х for х in шлях_входу
               if any(ф == "цикл за перелічком ознак" for _, _, _, ф in писачі_ознак(всі[х[0]], всі[х[0]].функції[х[1]]))}
    відсіяні = {}
    for х in фільтри:
        for ц in виклики_функції(всі[х[0]], всі, всі[х[0]].функції[х[1]]):
            if ц not in фільтри:
                відсіяні.setdefault(ц, х[1])
    for (ім, імя) in sorted(шлях_входу):
        м = всі[ім]
        for рядок, ключ, в, форма in писачі_ознак(м, м.функції[імя]):
            if форма == "присвоєння ключа":
                імена = умови_присвоєння(м, в)
            elif not isinstance(в, (ast.For, ast.DictComp)):
                імена = імена_у_виразі(в)
            else:
                імена = []
            умова = [і for і in імена if ПЕВНІСТЬ.search(і) or ключ in ВИМІРИ and ЧУЖИЙ_КАДР.search(і)]
            if (ім, імя) in відсіяні:
                не_місця.append((м.шлях, рядок, 1, f"{форма} «{ключ}» (у {імя}): готує запис, ключі бере перелічок у `{відсіяні[(ім, імя)]}`"))
            elif умова:
                не_місця.append((м.шлях, рядок, 1, f"{форма} «{ключ}»: умова певності `{умова[0]}`"))
            else:
                місця.append((м.шлях, рядок, 1, f"{форма} «{ключ}» (у {імя}) іде без умови певності"))
    return місця, не_місця


# ───────────────────────────── п.2 ─────────────────────────────
ПАЛІТРА_ІМЯ = re.compile(r"пал|palette", re.I)


def ключі_палітри_опису(всі, шлях_входу):
    """Ключі палітри, які функція входу лишає у вході моделі: `{к: пал[к] for к in ("metal", "farthest", …)}`.
    Що палітра віддає опису, — не перелік у приладі, а те, що каже сам фільтр у коді."""
    вих = set()
    for (ім, імя) in шлях_входу:
        for н in ast.walk(всі[ім].функції[імя]):
            if isinstance(н, ast.DictComp) and isinstance(н.value, ast.Subscript) \
                    and isinstance(н.value.value, ast.Name) and ПАЛІТРА_ІМЯ.search(н.value.value.id):
                ітер = н.generators[0].iter
                if isinstance(ітер, (ast.Tuple, ast.List)):
                    вих.update(к for к in (рядок_сталої(е) for е in ітер.elts) if к)
    return вих


def ключі_з_таблиці(м, функція, н):
    """Присвоєння `д[ключ] = …` у циклі `for ключ, … in ТАБЛИЦЯ`, де ТАБЛИЦЯ — модульний перелік кортежів: ключі,
    яких назви писач не тримає в тілі, а бере з таблиці (динамічний ключ)."""
    if not (isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Subscript)
            and isinstance(н.targets[0].slice, ast.Name)):
        return []
    імя_ключа = н.targets[0].slice.id
    for ц in м.предки(н):
        if ц is функція:
            break
        if isinstance(ц, ast.For) and isinstance(ц.iter, ast.Name) and isinstance(ц.target, ast.Tuple):
            позиція = next((і for і, е in enumerate(ц.target.elts) if isinstance(е, ast.Name) and е.id == імя_ключа), None)
            if позиція is None:
                continue
            for в in м.дерево.body:
                if isinstance(в, ast.Assign) and any(isinstance(т, ast.Name) and т.id == ц.iter.id for т in в.targets) \
                        and isinstance(в.value, (ast.Tuple, ast.List)):
                    return [рядок_сталої(е.elts[позиція]) for е in в.value.elts
                            if isinstance(е, ast.Tuple) and len(е.elts) > позиція and рядок_сталої(е.elts[позиція])]
    return []


def п2(всі, шлях_входу):
    місця, не_місця = [], []
    з_коду = ключі_палітри_опису(всі, шлях_входу)
    for (ім, імя) in sorted(шлях_входу):
        м = всі[ім]
        функція = м.функції[імя]
        ключі_цілі = set()
        for н in ast.walk(функція):
            if isinstance(н, ast.Subscript) and isinstance(н.ctx, ast.Store) and рядок_сталої(н.slice):
                ключі_цілі.add(рядок_сталої(н.slice))
            elif isinstance(н, ast.Dict):
                ключі_цілі.update(к for к in (рядок_сталої(к) for к in н.keys if к is not None) if к)
        for н in ast.walk(функція):
            ключ = значення = None
            for кл in ключі_з_таблиці(м, функція, н):
                перевірити_виведене(м, імя, кл, н.value, ключі_цілі, місця, не_місця)
            if isinstance(н, ast.Assign) and len(н.targets) == 1 and isinstance(н.targets[0], ast.Subscript) \
                    and рядок_сталої(н.targets[0].slice):
                ключ, значення = рядок_сталої(н.targets[0].slice), н.value
            elif isinstance(н, ast.Dict):
                for к, v in zip(н.keys, н.values):
                    if к is not None and рядок_сталої(к) in ВИВЕДЕНІ | з_коду:
                        перевірити_виведене(м, імя, рядок_сталої(к), v, ключі_цілі, місця, не_місця)
                continue
            if ключ in ВИВЕДЕНІ | з_коду:
                перевірити_виведене(м, імя, ключ, значення, ключі_цілі, місця, не_місця)
    return місця, не_місця


# ───────────────────────────── п.7: позначка довіри за замовчуванням ─────────────────────────────
# Позначка довіри — значення, яким продукт каже «це її слово» чи «це перевірено»: `her_words`, `her`, `hand`, `verified`,
# `перевірено`. Ствердний прапор вердикту без записаного вердикту — така сама довіра без події.
ПОЗНАЧКИ_ДОВІРИ = {"her_words", "her", "hand", "verified", "перевірено"}
ПРАПОРИ_ВЕРДИКТУ = {"перевірено", "verified"}


def позначки_модулів(всі):
    """Рядкові модульні сталі й розпаковані пари: довірені та інші види джерела для розбору ланцюга."""
    вих = {}
    for м in всі.values():
        for н in м.дерево.body:
            if not isinstance(н, ast.Assign):
                continue
            for ц in н.targets:
                if isinstance(ц, ast.Name) and рядок_сталої(н.value) is not None:
                    вих[ц.id] = рядок_сталої(н.value)
                elif isinstance(ц, ast.Tuple) and isinstance(н.value, ast.Tuple) and len(ц.elts) == len(н.value.elts):
                    for а, б in zip(ц.elts, н.value.elts):
                        if isinstance(а, ast.Name) and рядок_сталої(б) is not None:
                            вих[а.id] = рядок_сталої(б)
    return вих


def рядкова_позначка(в, сталі):
    """Значення рядка чи модульної сталої, зокрема атрибута імпортованого модуля."""
    р = рядок_сталої(в)
    if р is not None:
        return р
    if isinstance(в, ast.Name):
        return сталі.get(в.id)
    if isinstance(в, ast.Attribute):
        return сталі.get(в.attr)
    return None


def позначка_довіри(в, сталі):
    """Позначка довіри у виразі; типове та невідоме джерела довіри не стверджують."""
    р = рядкова_позначка(в, сталі)
    return р if р in ПОЗНАЧКИ_ДОВІРИ else None


def перевірка_відсутності(т):
    """Умова гілки про ВІДСУТНІСТЬ запису: `not х`, `х is None`, `х not in …`, `не (… або …)`."""
    if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
        return True
    if isinstance(т, ast.Compare) and any(isinstance(о, (ast.Is, ast.NotIn)) for о in т.ops):
        return isinstance(т.ops[0], ast.Is) and isinstance(т.comparators[0], ast.Constant) and т.comparators[0].value is None \
            or isinstance(т.ops[0], ast.NotIn)
    return False


def є_відсутність(т):
    """Чи допускає фільтр відсутність запису, зокрема всередині сполучених умов включення."""
    if isinstance(т, ast.BoolOp):
        return any(є_відсутність(в) for в in т.values)
    return перевірка_відсутності(т)


def поле_вердикту(в):
    """Пара (носій, ключ) для читання прапора вердикту, незалежно від імені носія."""
    if isinstance(в, ast.Subscript) and рядок_сталої(в.slice) in ПРАПОРИ_ВЕРДИКТУ:
        return в.value, рядок_сталої(в.slice)
    if isinstance(в, ast.Attribute) and в.attr in ПРАПОРИ_ВЕРДИКТУ:
        return в.value, в.attr
    if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get" \
            and в.args and рядок_сталої(в.args[0]) in ПРАПОРИ_ВЕРДИКТУ:
        return в.func.value, рядок_сталої(в.args[0])
    return None


def те_саме_поле(а, б):
    """Порівнює носія й ключ без номерів рядків і контексту читання/запису AST."""
    return а is not None and б is not None and а[1] == б[1] \
        and ast.dump(а[0], include_attributes=False) == ast.dump(б[0], include_attributes=False)


def умова_наявності(т, поле):
    """Чи умова гарантує наявність саме цього ключа; None — невідома, False — гарантує відсутність."""
    if isinstance(т, ast.UnaryOp) and isinstance(т.op, ast.Not):
        є = умова_наявності(т.operand, поле)
        return None if є is None else not є
    if isinstance(т, ast.Compare) and len(т.ops) == 1 and рядок_сталої(т.left) == поле[1] \
            and ast.dump(т.comparators[0]) == ast.dump(поле[0]):
        if isinstance(т.ops[0], (ast.In, ast.NotIn)):
            return isinstance(т.ops[0], ast.In)
    if те_саме_поле(поле_вердикту(т), поле):
        return True
    if isinstance(т, ast.BoolOp) and isinstance(т.op, ast.And) \
            and any(умова_наявності(в, поле) is True for в in т.values):
        return True
    return None


def ключ_записаний(м, н, поле):
    """Чи ключ уже записано на цьому шляху: пряма попередня операція або захисна умова на ключ."""
    дитина = н
    for п in м.предки(н):
        if isinstance(п, ast.If):
            є = умова_наявності(п.test, поле)
            if (дитина in п.body and є is True) or (дитина in п.orelse and є is False):
                return True
        for список in (в for _, в in ast.iter_fields(п) if isinstance(в, list) and дитина in в):
            for попередній in reversed(список[:список.index(дитина)]):
                if isinstance(попередній, ast.Delete) \
                        and any(те_саме_поле(поле_вердикту(ц), поле) for ц in попередній.targets):
                    return False
                цілі = попередній.targets if isinstance(попередній, ast.Assign) else \
                    [попередній.target] if isinstance(попередній, ast.AnnAssign) else []
                if any(те_саме_поле(поле_вердикту(ц), поле) for ц in цілі):
                    return True
                if any(ast.dump(ц, include_attributes=False).replace("Store()", "Load()") == ast.dump(поле[0]) for ц in цілі):
                    return False
        if isinstance(п, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            break
        дитина = п
    return False


def дефолт_вердикту(м, н):
    """Ствердний дефолт прапора: метод словника, `or True`, умовний вираз або запис у гілці відсутності."""
    поле = None
    if isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr in ("get", "setdefault", "pop"):
        носій, арг = н.func.value, н.args
        if isinstance(носій, ast.Name) and носій.id == "dict" and арг:
            носій, арг = арг[0], арг[1:]
        if len(арг) == 2 and рядок_сталої(арг[0]) in ПРАПОРИ_ВЕРДИКТУ \
                and isinstance(арг[1], ast.Constant) and арг[1].value is True:
            поле = носій, рядок_сталої(арг[0])
    elif isinstance(н, ast.BoolOp) and isinstance(н.op, ast.Or) and len(н.values) == 2 \
            and isinstance(н.values[-1], ast.Constant) and н.values[-1].value is True:
        поле = поле_вердикту(н.values[0])
        # Навіть записаний False перетворюється на True: наявність ключа тут не захищає.
        return поле
    elif isinstance(н, ast.IfExp):
        for дефолт, читання, бік in ((н.orelse, н.body, True), (н.body, н.orelse, False)):
            кандидат = поле_вердикту(читання)
            if кандидат and isinstance(дефолт, ast.Constant) and дефолт.value is True \
                    and умова_наявності(н.test, кандидат) is бік:
                поле = кандидат
    elif isinstance(н, (ast.Assign, ast.AnnAssign)) and isinstance(н.value, ast.Constant) and н.value.value is True:
        for ц in н.targets if isinstance(н, ast.Assign) else [н.target]:
            кандидат = поле_вердикту(ц)
            if кандидат and any(isinstance(п, ast.If) and н in п.body
                                and умова_наявності(п.test, кандидат) is False for п in м.предки(н)):
                поле = кандидат
    return поле if поле and not ключ_записаний(м, н, поле) else None


def дефолти_параметрів(н):
    """Пари (параметр, значення за замовчуванням) функції чи лямбди: позиційні й лише-іменні; інший вузол — порожньо."""
    if not isinstance(н, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return []
    а = н.args
    позиційні = (а.posonlyargs + а.args)[len(а.posonlyargs + а.args) - len(а.defaults):]
    пари = list(zip((п.arg for п in позиційні), а.defaults))
    return пари + [(п.arg, д) for п, д in zip(а.kwonlyargs, а.kw_defaults) if д is not None]


def п7_python(всі):
    """Гілка за замовчуванням, що вертає позначку довіри: `if нема: return ПОЗНАЧКА`; кінцеве `return ПОЗНАЧКА` після гілок з
    іншими видами джерела; `.get(ключ, ПОЗНАЧКА)`, `.setdefault`, `х or ПОЗНАЧКА`; `… if … else ПОЗНАЧКА` останньою гілкою ланцюга,
    де попередні гілки — інші види джерела (`"code_rank" if … else "stylist" if … else "her"`);
    словникове включення без факту, ствердний дефолт прапора вердикту і значення за замовчуванням параметра функції
    (`def ф(…, перевірено=True)`, `def ф(…, джерело="her")`): викликач, що не передав значення, дістає довіру без події
    (рішення менеджера 17.11, дошка 16365)."""
    сталі = позначки_модулів(всі)
    місця = []
    for м in всі.values():
        for н in ast.walk(м.дерево):
            ф = м.функція_вузла(н)
            імя = ф.name if ф is not None else "модуль"
            власник = getattr(н, "name", f"лямбді в {імя}")
            for ім_п, дефолт in дефолти_параметрів(н):
                if ім_п in ПРАПОРИ_ВЕРДИКТУ and isinstance(дефолт, ast.Constant) and дефолт.value is True:
                    місця.append((м.шлях, дефолт.lineno, 7, f"у {власник}: параметр `{ім_п}=True` — вердикт за замовчуванням "
                                                             f"без події, коли викликач значення не передав"))
                elif позначка_довіри(дефолт, сталі):
                    місця.append((м.шлях, дефолт.lineno, 7, f"у {власник}: параметр `{ім_п}` за замовчуванням дає позначку "
                                                             f"«{позначка_довіри(дефолт, сталі)}» без запису"))
            вердикт = дефолт_вердикту(м, н)
            if вердикт:
                місця.append((м.шлях, н.lineno, 7, f"у {імя}: прапор `{вердикт[1]}` за замовчуванням True без запису вердикту"))
            if isinstance(н, ast.If) and перевірка_відсутності(н.test):
                for в in н.body:
                    if isinstance(в, ast.Return) and в.value is not None and позначка_довіри(в.value, сталі):
                        місця.append((м.шлях, в.lineno, 7, f"у {імя}: за відсутності запису (`{ast.unparse(н.test)[:60]}`) "
                                                              f"вертає позначку «{позначка_довіри(в.value, сталі)}»"))
            elif isinstance(н, ast.Call) and isinstance(н.func, ast.Attribute) and н.func.attr in ("get", "setdefault", "pop") \
                    and len(н.args) == 2 and позначка_довіри(н.args[1], сталі):
                місця.append((м.шлях, н.lineno, 7, f"у {імя}: `.{н.func.attr}(ключ, …)` без запису дає позначку "
                                                      f"«{позначка_довіри(н.args[1], сталі)}»"))
            elif isinstance(н, ast.BoolOp) and isinstance(н.op, ast.Or) and позначка_довіри(н.values[-1], сталі) \
                    and len(н.values) >= 2 and not isinstance(н.values[0], ast.Constant):
                місця.append((м.шлях, н.lineno, 7, f"у {імя}: `… or позначка` — відсутнє значення дістає «{позначка_довіри(н.values[-1], сталі)}»"))
            elif isinstance(н, ast.IfExp) and позначка_довіри(н.orelse, сталі) \
                    and ланцюг_джерел(н, сталі) and not перевірка_відсутності(н.test):
                місця.append((м.шлях, н.lineno, 7, f"у {імя}: ланцюг видів джерела кінчається «{позначка_довіри(н.orelse, сталі)}» "
                                                      f"за замовчуванням, без запису, що це її"))
            elif isinstance(н, ast.DictComp) and позначка_довіри(н.value, сталі) \
                    and any(є_відсутність(у) for г in н.generators for у in г.ifs):
                місця.append((м.шлях, н.lineno, 7, f"у {імя}: словникове включення за відсутності факту дає "
                                                      f"позначку «{позначка_довіри(н.value, сталі)}»"))
        # кінцеве `return ПОЗНАЧКА` у функції, де інші `return` — не позначки довіри
        for ф in м.функції.values():
            тіло = [х for х in ф.body if not (isinstance(х, ast.Expr) and isinstance(х.value, ast.Constant))]
            if len(тіло) >= 2 and isinstance(тіло[-1], ast.Return) and тіло[-1].value is not None \
                    and позначка_довіри(тіло[-1].value, сталі):
                інші = [в for в in ast.walk(ф) if isinstance(в, ast.Return) and в is not тіло[-1] and в.value is not None]
                if інші and not any(позначка_довіри(в.value, сталі) for в in інші):
                    місця.append((м.шлях, тіло[-1].lineno, 7, f"у {ф.name}: кінцеве `return` за замовчуванням дає позначку "
                                                              f"«{позначка_довіри(тіло[-1].value, сталі)}»"))
    return місця


def ланцюг_джерел(н, сталі):
    """`а if у1 else б if у2 else ПОЗНАЧКА`: хоч одна попередня гілка — рядок іншого виду джерела (не позначка довіри)."""
    гілки, в = [], н
    while isinstance(в, ast.IfExp):
        гілки.append(в.body)
        в = в.orelse
    return позначка_довіри(в, сталі) and any(рядкова_позначка(г, сталі) and not позначка_довіри(г, сталі) for г in гілки)


ПОЗНАЧКИ_JS = re.compile(r"^(her_words|her|hand|verified|перевірено)$")


def п7_js(корінь):
    """JS: `х || 'her_words'` і `х ?? 'hand'`: відсутнє значення дістає позначку довіри."""
    місця = []
    for шлях in файли_продукту(корінь, (".js", ".mjs", ".cjs")):
        ток = js_лекс(прочитати(шлях))
        for к in range(1, len(ток) - 2):
            якщо_або = ток[к][1] == "|" and ток[к + 1][1] == "|" and к + 2 < len(ток) and ток[к + 2][0] == "str"
            якщо_пара = ток[к][1] == "?" and ток[к + 1][1] == "?" and к + 2 < len(ток) and ток[к + 2][0] == "str"
            if (якщо_або or якщо_пара) and ПОЗНАЧКИ_JS.match(ток[к + 2][1]):
                місця.append((відн(шлях), ток[к][2], 7, f"`{'||' if якщо_або else '??'} '{ток[к + 2][1]}'`: відсутнє значення дістає "
                                                      f"позначку довіри"))
    return місця


def перевірити_виведене(м, імя, ключ, значення, ключі_цілі, місця, не_місця):
    рядок = значення.lineno
    сусід = next((к for к in ключі_цілі if к != ключ and ключ in к and ДЖЕРЕЛО_КЛЮЧА.search(к)), None) \
        or next((к for к in ключі_цілі if ДЖЕРЕЛО_КЛЮЧА.search(к) and к.startswith(ключ)), None)
    сусід = сусід or next((к for к in ключі_цілі if к in ("knowledge", "provenance", "status")), None)
    у_значенні = next((і for і in імена_у_виразі(значення) if ДЖЕРЕЛО_ЗНАЧЕННЯ.search(і)), None)
    if сусід or у_значенні:
        не_місця.append((м.шлях, рядок, 2, f"«{ключ}»: джерело `{сусід or у_значенні}`"))
    else:
        місця.append((м.шлях, рядок, 2, f"«{ключ}» (у {імя}) виведене чи типове, іде без позначки джерела"))


# ───────────────────────────── п.3 ─────────────────────────────
def словник_заяв(м):
    """Модульні словники «код → англійське визначення»: ≥20 записів snake_case → рядок."""
    вих = []
    for н in м.дерево.body:
        значення = н.value if isinstance(н, (ast.Assign, ast.AnnAssign)) else None
        if isinstance(значення, ast.Dict):
            пари = [(рядок_сталої(к), рядок_сталої(v)) for к, v in zip(значення.keys, значення.values)
                    if к is not None and v is not None]
            пари = [(к, v) for к, v in пари if к and v and re.fullmatch(r"[a-z][a-z0-9_]{4,}", к)
                    and len(v.split()) >= 4 and re.search(r"[A-Za-z]{3}", v)]
            if len(пари) >= 20:
                for к, vv in zip(значення.keys, значення.values):
                    if к is not None and рядок_сталої(к) in dict(пари) and рядок_сталої(vv) == dict(пари)[рядок_сталої(к)]:
                        вих.append((к.lineno, рядок_сталої(к), dict(пари)[рядок_сталої(к)]))
    return вих


def діапазони_визначень(корінь):
    """{файл: [(від, до)]} — рядки записів словників заяв: визначення коду лежить у вході моделі, але належить п.3."""
    вих = {}
    for м in модулі_кеш(корінь).values():
        for н in м.дерево.body:
            значення = н.value if isinstance(н, (ast.Assign, ast.AnnAssign)) else None
            if isinstance(значення, ast.Dict) and словник_заяв_у(м, значення):
                вих.setdefault(м.шлях, []).extend((к.lineno, v.end_lineno) for к, v in zip(значення.keys, значення.values)
                                                    if к is not None)
    return вих


def словник_заяв_у(м, значення):
    пари = [(рядок_сталої(к), рядок_сталої(v)) for к, v in zip(значення.keys, значення.values)
            if к is not None and v is not None]
    пари = [(к, v) for к, v in пари if к and v and re.fullmatch(r"[a-z][a-z0-9_]{4,}", к)
            and len(v.split()) >= 4 and re.search(r"[A-Za-z]{3}", v)]
    return len(пари) >= 20


def коди_аргумента(а):
    """Коди заяви, які може нести перший аргумент виклику: літерал чи `a if умова else b`."""
    if isinstance(а, ast.IfExp):
        return коди_аргумента(а.body) | коди_аргумента(а.orelse)
    к = рядок_сталої(а)
    return {к} if к else set()


def виходи_заяви(всі, код):
    вих = []
    for м in всі.values():
        for н in ast.walk(м.дерево):
            if isinstance(н, ast.Call) and н.args and код in коди_аргумента(н.args[0]) \
                    and (isinstance(н.func, ast.Name) and н.func.id == "заява"
                         or isinstance(н.func, ast.Attribute) and н.func.attr == "заява"):
                вих.append((м, н))
    return вих


def умови_виходу(м, н):
    """Імена в умовах, що пускають до виклику: `if`-предки й ранні виходи (`if …: return/continue/raise`) перед ним."""
    імена = []
    if н.args and isinstance(н.args[0], ast.IfExp):
        імена += імена_у_виразі(н.args[0].test)
    дитина = н
    for п in м.предки(н):
        if isinstance(п, (ast.If, ast.IfExp)):
            імена += імена_у_виразі(п.test)
        for поле in ("body", "orelse", "finalbody"):
            тіло = getattr(п, поле, None)
            if isinstance(тіло, list) and дитина in тіло:
                for попередній in тіло[:тіло.index(дитина)]:
                    if isinstance(попередній, ast.If) and any(
                            isinstance(х, (ast.Return, ast.Raise, ast.Continue, ast.Break)) for х in попередній.body):
                        імена += імена_у_виразі(попередній.test)
        дитина = п
    return імена


def імена_цілі(ціль):
    return {н.id for н in ast.walk(ціль) if isinstance(н, ast.Name)}


def виклик_виводить(в, похідні):
    """Виклик, чий результат виведено з погоди: у аргументах імена смуги чи температури (`ВХІД_ВИВОДУ`) або вже виведене значення."""
    арги = list(в.args) + [k.value for k in в.keywords]
    return any(ВХІД_ВИВОДУ.search(і) or і in похідні for a in арги for і in імена_у_виразі(a))


ЛЕГКІ_ВИКЛИКИ = {"bool", "any", "all", "len", "str", "int", "float", "min", "max", "abs", "round", "get"}


def легке_виведення(в, похідні):
    """Вираз зберігає виведене значення: булева/порівняльна/умовна комбінація, читання поля чи елемента, `.get`, чисті вбудовані — без
    запису (`{…}`), переліку, замикання й виклику довільної функції: `пак = f(…, виведене)` складає інше, а не лишає обставину."""
    if any(isinstance(х, (ast.Dict, ast.List, ast.Set, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.Lambda,
                          ast.JoinedStr)) for х in ast.walk(в)):
        return False
    for х in ast.walk(в):
        if isinstance(х, ast.Call):
            імя = х.func.id if isinstance(х.func, ast.Name) else х.func.attr if isinstance(х.func, ast.Attribute) else None
            if імя not in ЛЕГКІ_ВИКЛИКИ:
                return False
    return any(isinstance(х, ast.Name) and х.id in похідні for х in ast.walk(в))


def виведене_з_погоди(функція, ім, параметри_виведені=frozenset()):
    """У тілі `функція` імʼя `ім` виведено з погоди — прямо (присвоєно результатом виклику, чиї аргументи несуть смугу чи
    температуру) чи ланцюгом: з іншого виведеного значення (`сіль = сольова_сльота(…)`, `слизько = сіль and мороз`), а також
    параметром, який усі викликачі дають виведеним (`параметри_виведені`). Обставина, яку код вивів з іншої обставини, — не її
    слово (рішення менеджера 17.11, п.3 ширше)."""
    if функція is None:
        return False
    похідні = set(параметри_виведені)
    зміна = True
    while зміна:
        зміна = False
        for н in ast.walk(функція):
            if isinstance(н, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
                цілі = н.targets if isinstance(н, ast.Assign) else [н.target]
                значення = н.value
            elif isinstance(н, ast.NamedExpr):
                цілі, значення = [н.target], н.value
            else:
                continue
            якщо_нові = set().union(*(імена_цілі(ц) for ц in цілі)) - похідні if значення is not None else set()
            if not якщо_нові:
                continue
            виведене = any(isinstance(в, ast.Call) and виклик_виводить(в, set()) for в in ast.walk(значення)) \
                or легке_виведення(значення, похідні)
            if виведене:
                похідні |= якщо_нові
                зміна = True
    return ім in похідні


_ІНДЕКС_ВИКЛИКІВ = {}
_КЕШ_ПАРАМЕТРІВ = {}


def виклики_за_іменем(всі):
    """{імʼя функції: [(модуль, виклик)]} — усі виклики в продукті за імʼям (`f(…)` і `мод.f(…)`), один обхід на запуск."""
    ключ = id(всі)
    if ключ not in _ІНДЕКС_ВИКЛИКІВ:
        інд = {}
        for м in всі.values():
            for н in ast.walk(м.дерево):
                if isinstance(н, ast.Call):
                    імя = н.func.id if isinstance(н.func, ast.Name) else н.func.attr if isinstance(н.func, ast.Attribute) else None
                    if імя:
                        інд.setdefault(імя, []).append((м, н))
        _ІНДЕКС_ВИКЛИКІВ[ключ] = інд
    return _ІНДЕКС_ВИКЛИКІВ[ключ]


def параметри_виведені(всі, мод, функція, глибина=0):
    """Параметри `функція`, які кожен її викликач у продукті дає виведеним значенням (ланцюг через виклик)."""
    ключ = (id(всі), id(функція))
    if ключ in _КЕШ_ПАРАМЕТРІВ:
        return _КЕШ_ПАРАМЕТРІВ[ключ]
    _КЕШ_ПАРАМЕТРІВ[ключ] = frozenset()  # захист від рекурсії
    імена = [а.arg for а in функція.args.args + функція.args.kwonlyargs]
    вих = set()
    інд = виклики_за_іменем(всі).get(функція.name, [])
    for п, імя_параметра in enumerate(імена):
        виклики = []
        for м, н in інд:
            арг = н.args[п] if п < len(н.args) else next((k.value for k in н.keywords if k.arg == імя_параметра), None)
            if арг is not None:
                виклики.append((м, н, арг))
        if виклики and all(аргумент_виведений(всі, м, н, арг) for м, н, арг in виклики):
            вих.add(імя_параметра)
    _КЕШ_ПАРАМЕТРІВ[ключ] = frozenset(вих)
    return _КЕШ_ПАРАМЕТРІВ[ключ]


def аргумент_виведений(всі, м, н, арг):
    """Аргумент виклику виведений: його імена — виведені у викликача (і самі виведені параметром), чи сам вираз — виклик, чиї
    аргументи несуть смугу."""
    ф = м.функція_вузла(н)
    пв = параметри_виведені(всі, м, ф) if ф is not None else frozenset()
    for в in ast.walk(арг):
        if isinstance(в, ast.Call) and виклик_виводить(в, set()):
            return True
        if isinstance(в, ast.Name) and виведене_з_погоди(ф, в.id, пв):
            return True
    return False


def п3(всі):
    місця, не_місця, без_виходу = [], [], []
    for м in всі.values():
        for рядок, код, визначення in словник_заяв(м):
            for частина in re.split(r",\s+and\s+|;|,\s+so\s+|\.\s+", визначення):
                клас = next((к for к, (р, _) in ОБСТАВИНИ.items() if р.search(частина)), None)
                if not клас or ЗАСТЕРЕЖЕННЯ.search(частина):
                    continue
                виходи = виходи_заяви(всі, код)
                if not виходи:
                    без_виходу.append((м.шлях, рядок, 3, f"заява «{код}»: стверджує «{клас}», виходу в коді не знайдено"))
                    break
                її = ОБСТАВИНИ[клас][1]
                # заява має кілька виходів: кожен — окремий шлях до жінки, і хоч один, що не читає її слів, — місце
                збіги, без_слів = [], []
                for мм, нн in виходи:
                    фн = мм.функція_вузла(нн)
                    пв = параметри_виведені(всі, мм, фн) if фн is not None else frozenset()
                    читають = [і for і in умови_виходу(мм, нн) if not виведене_з_погоди(фн, і, пв)]
                    зб = next((і for і in читають if any(с in і.lower() for с in її)), None)
                    (збіги if зб else без_слів).append((мм, нн, зб))
                if без_слів:
                    мм, нн, _ = без_слів[0]
                    місця.append((м.шлях, рядок, 3, f"заява «{код}» стверджує «{клас}» («{частина.strip()[:70]}»), "
                                                    f"умова виходу ({мм.шлях}:{нн.lineno}) не читає її слів про це"))
                else:
                    не_місця.append((м.шлях, рядок, 3, f"заява «{код}»: умова виходу читає її слова (`{збіги[0][2]}`)"))
                break
    return місця, не_місця, без_виходу


# ───────────────────────────── п.4, п.5: речення промптів ─────────────────────────────
def рядки_python(м):
    """(рядок, текст) англійських текстових літералів не-докстрінгів, не коментарів."""
    for н in ast.walk(м.дерево):
        if isinstance(н, ast.Constant) and isinstance(н.value, str) and н not in м.docstr:
            if len(н.value.split()) >= 6 and len(re.findall(r"[A-Za-z]", н.value)) > 0.6 * len(re.findall(r"\w", н.value)):
                yield н.lineno, getattr(н, "end_lineno", н.lineno), н.value


def рядок_фрагмента(рядки, від, до, фрагмент):
    слова = re.findall(r"[A-Za-z«»]{3,}", фрагмент)[:2]
    for р in range(від, до + 1):
        лінія = рядки[р - 1] if р - 1 < len(рядки) else ""
        if слова and all(с in лінія for с in слова):
            return р
    return від


def речення(текст):
    return [х.strip() for х in re.split(r"(?<=[.;!?])\s+", текст) if х.strip()]


def текстові_літерали(корінь):
    """(файл, від, до, текст, рядки файла) для Python і JS."""
    for м in модулі_кеш(корінь).values():
        for від, до, текст in рядки_python(м):
            yield м.шлях, від, до, текст, м.рядки
    for шлях in файли_продукту(корінь, (".js", ".mjs", ".cjs")):
        вміст = прочитати(шлях)
        рядки = вміст.splitlines()
        for від, до, текст in js_рядки(вміст):
            if len(текст.split()) >= 6 and len(re.findall(r"[A-Za-z]", текст)) > 0.6 * len(re.findall(r"\w", текст)):
                yield відн(шлях), від, до, текст, рядки


_КЕШ = {}


def модулі_кеш(корінь):
    if корінь not in _КЕШ:
        _КЕШ[корінь] = модулі_продукту(корінь)
    return _КЕШ[корінь]


def п4_п5(корінь):
    п4, п5, не_п4 = [], [], []
    визначення = діапазони_визначень(корінь)
    for файл, від, до, текст, рядки in текстові_літерали(корінь):
        ре = речення(текст)
        у_визначенні = any(а <= від <= б for а, б in визначення.get(файл, ()))
        for і, р in enumerate(ре):
            рядок = рядок_фрагмента(рядки, від, до, р)
            # п.4: вимога сказати про властивість чи обставину без умови
            в = ВИМОГА.search(р)
            if в and ПРЕДМЕТ.search(р) and not ЗАПЕРЕЧЕННЯ.search(р[:в.start()] + " " + р[в.start():в.end() + 3]):
                if УМОВА.search(р):
                    не_п4.append((файл, рядок, 4, f"умова в реченні: «{р[:90]}»"))
                else:
                    п4.append((файл, рядок, 4, f"вимога без умови «коли відома»: «{р[:110]}»"))
            # п.5: значення коду замість слова моделі (вікно — це речення й наступні два)
            if КОД_ЗНАЧЕННЯ.search(р):
                вікно = " ".join(ре[і:і + 3])
                if ЗАМІНА_СЛОВА.search(вікно):
                    п5.append((файл, рядок, 5, f"код на місці слова моделі: «{р[:110]}»"))
    return п4, п5, не_п4


# ───────────────────────────── JS: літерали й області ─────────────────────────────
ПІСЛЯ_ЯКИХ_РЕГЕКС = {"(", ",", "=", ":", "[", "!", "&", "|", "?", "{", "}", ";", "+", "-", "*", "%", "<", ">", "~",
                     "^", "return", "typeof", "=>", "&&", "||", "??", "==", "===", "!=", "!==", "await"}


def js_лекс(текст):
    """Токени JS: (вид, значення, рядок); вид — 'id' | 'str' | 'p'. Коментарі пропущено, шаблон — один 'str'."""
    ток, і, н, р = [], 0, len(текст), 1
    ід = re.compile(r"[\w$ʼ’]+")
    while і < н:
        с = текст[і]
        if с == "\n":
            р += 1
            і += 1
        elif с.isspace():
            і += 1
        elif текст.startswith("//", і):
            і = текст.find("\n", і)
            і = н if і < 0 else і
        elif текст.startswith("/*", і):
            к = текст.find("*/", і + 2)
            к = н if к < 0 else к + 2
            р += текст.count("\n", і, к)
            і = к
        elif с in "'\"`":
            к, глиб = і + 1, 0
            while к < н:
                if текст[к] == "\\":
                    к += 2
                    continue
                if с == "`" and текст.startswith("${", к):
                    глиб += 1
                    к += 2
                    continue
                if с == "`" and глиб and текст[к] == "}":
                    глиб -= 1
                elif текст[к] == с and not глиб:
                    break
                к += 1
            ток.append(("str", текст[і + 1:к], р))
            р += текст.count("\n", і, к)
            і = к + 1
        elif с == "/" and (not ток or ток[-1][1] in ПІСЛЯ_ЯКИХ_РЕГЕКС or ток[-1][0] == "p" and ток[-1][1] in "([,=:!&|?{;"):
            к, клас = і + 1, False
            while к < н and текст[к] != "\n":
                if текст[к] == "\\":
                    к += 2
                    continue
                if текст[к] == "[":
                    клас = True
                elif текст[к] == "]":
                    клас = False
                elif текст[к] == "/" and not клас:
                    break
                к += 1
            ток.append(("str", "", р))
            і = к + 1
        else:
            м = ід.match(текст, і)
            if м:
                ток.append(("id", м.group(), р))
                і = м.end()
            elif текст.startswith("=>", і):
                ток.append(("p", "=>", р))
                і += 2
            else:
                ток.append(("p", с, р))
                і += 1
    return ток


def js_рядки(текст):
    """(від, до, текст) літералів, зшитих `+`."""
    ток = js_лекс(текст)
    вих, і = [], 0
    while і < len(ток):
        if ток[і][0] == "str":
            від, частини, к = ток[і][2], [ток[і][1]], і
            while к + 2 < len(ток) and ток[к + 1][1] == "+" and ток[к + 2][0] == "str":
                частини.append(ток[к + 2][1])
                к += 2
            вих.append((від, ток[к][2] + ток[к][1].count("\n"), "".join(частини)))
            і = к + 1
        else:
            і += 1
    return вих


def js_області(ток):
    """[(імʼя | None, від_токена, до_токена)] тіл функцій: `=> {`, `) {` не після if/for/while/switch/catch/with."""
    стек, вих = [], []
    for і, (в, з, _) in enumerate(ток):
        if з == "{" and в == "p":
            ф, імя, j = False, None, і - 1
            if j >= 0 and ток[j][1] == "=>":
                ф = True
                if j >= 1 and ток[j - 1][1] == ")":
                    дужка = j - 1
                else:
                    дужка = None
                    імя_параметра = j - 1
                к = дужка
                if к is not None:
                    глиб = 0
                    while к >= 0:
                        if ток[к][1] == ")":
                            глиб += 1
                        elif ток[к][1] == "(":
                            глиб -= 1
                            if глиб == 0:
                                break
                        к -= 1
                    перед = к - 1
                else:
                    перед = j - 2
                if перед >= 0 and ток[перед][1] == "async":
                    перед -= 1
                if перед >= 1 and ток[перед][1] == "=" and ток[перед - 1][0] == "id":
                    імя = ток[перед - 1][1]
            elif j >= 0 and ток[j][1] == ")":
                глиб, к = 0, j
                while к >= 0:
                    if ток[к][1] == ")":
                        глиб += 1
                    elif ток[к][1] == "(":
                        глиб -= 1
                        if глиб == 0:
                            break
                    к -= 1
                if к >= 1 and ток[к - 1][1] not in {"if", "for", "while", "switch", "catch", "with"}:
                    ф = True
                    імя = ток[к - 1][1] if ток[к - 1][0] == "id" and ток[к - 1][1] != "function" else None
                    if ток[к - 1][1] == "function" and к >= 3 and ток[к - 2][1] == "=":
                        імя = ток[к - 3][1]
            стек.append((ф, імя, і))
        elif з == "}" and в == "p" and стек:
            ф, імя, поч = стек.pop()
            if ф:
                вих.append((імя, поч, і))
    return вих


def js_файли(корінь):
    """[(шлях, токени, області)] JS продукту; файл, що сам ставить `x-images-dropped` (воркер), — виробник лічби,
    а не сторінка: його виклики не лічаться."""
    вих = []
    for шлях in файли_продукту(корінь, (".js", ".mjs", ".cjs")):
        ток = js_лекс(прочитати(шлях))
        виробник = any(ток[к][0] == "str" and "images-dropped" in ток[к][1] and ток[к - 1][1] == "(" and ток[к - 2][1] == "set"
                       for к in range(2, len(ток)))
        if not виробник:
            вих.append((шлях, ток, js_області(ток)))
    return вих


def виклик_моста(ток, а, б):
    """У `ток[а:б]` є `fetch(` на міст до моделі: в аргументах `/v1/messages`, `anthropic.com` чи імʼя з «міст»."""
    for к in range(а, б - 1):
        if ток[к][1] == "fetch" and ток[к + 1][1] == "(":
            for t in ток[к + 2:к + 12]:
                if t[0] in ("id", "str") and re.search(r"v1/messages|anthropic\.com|міст", t[1], re.I):
                    return True
    return False


# Ім'я, що каже ПРО кадр (підпис, опис, назва, кількість, причина), а не несе його: `підписКадру`, `описФото`, `чому_без_фото`.
ТЕКСТ_ПРО_КАДР = re.compile(r"^(підпис|опис|назв|питання|лічб|кільк|довж|чому|причин|рядок|текст|код|стан|без_|нема_|вердикт)|"
                            r"(Підпис|Опис|Назв|Питання|Лічб|Кільк|Довж|Причин|Рядок)|(ПИТАННЯ|ПІДПИС|ОПИС)_", re.U | re.I)
# Рядок-маркер кадру в аргументах: тип блока чи ключ, а не код-ярлик (`'нема_фото'`, `'за_фото'`).
МАРКЕР_КАДРУ = re.compile(r"image|photo|фото|image_url", re.I)


def несе_кадр_токен(т):
    """Токен аргумента виклику моделі, що несе кадр: ім'я з «кадр/фото/…» (не текст про кадр) чи рядок-маркер типу."""
    if т[0] == "id":
        return bool(КАДРИ.search(т[1])) and not ТЕКСТ_ПРО_КАДР.search(т[1])
    return т[0] == "str" and bool(re.fullmatch(МАРКЕР_КАДРУ, т[1]))


БУДІВНИК_КАДРІВ = re.compile(r"кадр|Кадр|фото|Фото|блок|Блок|image|block", re.I)


# Виробник кадру — за будовою тіла, не за іменем (дошка 16250): функція, що сама кодує зображення (`toDataURL`,
# `readAsDataURL`, `createImageBitmap`, рядок `image/…` чи `data:image`), чи повертає результат такого виробника. Змінна, яку
# присвоєно його результатом, несе кадр, хоч в імені нема «фото»/«кадр» (`її = await блобВБазу(блоб)`).
ЗНАК_КОДУВАННЯ = re.compile(r"toDataURL|readAsDataURL|createImageBitmap|^image/|data:image", re.I)


def виробники_кадрів(файли):
    """Імена функцій, що створюють кадр для моделі (структурно), і ті, що повертають результат такої функції."""
    тіла = {}
    for _, ток, області in файли:
        for імя, а, б in області:
            if імя:
                тіла.setdefault(імя, []).append((ток, а, б))
    виробники = {імя for імя, ввв in тіла.items()
                 if any(ЗНАК_КОДУВАННЯ.search(т[1]) for ток, а, б in ввв for т in ток[а:б] if т[0] in ("id", "str"))}
    зміна = True
    while зміна:
        зміна = False
        for імя, ввв in тіла.items():
            if імя in виробники:
                continue
            for ток, а, б in ввв:
                if повертає_виклик_із(ток, а, б, виробники):
                    виробники.add(імя)
                    зміна = True
                    break
    return виробники


def повертає_виклик_із(ток, а, б, імена):
    """У тілі `[а, б]` є `return …` (чи стрілочне тіло), у виразі якого клична функція з `імена`."""
    for к in range(а + 1, б):
        if ток[к][1] == "return" and ток[к][0] == "id":
            глиб, і = 0, к + 1
            while і < б:
                if ток[і][0] == "p" and ток[і][1] in "([{":
                    глиб += 1
                elif ток[і][0] == "p" and ток[і][1] in ")]}":
                    глиб -= 1
                    if глиб < 0:
                        break
                elif ток[і][1] == ";" and глиб == 0:
                    break
                if ток[і][0] == "id" and ток[і][1] in імена and ток[і + 1][1] == "(" and ток[і - 1][1] != ".":
                    return True
                і += 1
    return False


def змінні_з_фільтра(ток, а, к, відфільтровані):
    """Змінні, оголошені раніше в тілі `[а, к)` з результату функції-фільтра лічби (`фото = фотоДійшло…()`)."""
    return {ток[і][1] for і in range(а + 1, к) if ток[і][0] == "id" and ток[і + 1][1] == "="
            and ток[і + 2][1] in відфільтровані and ток[і + 3][1] == "("}


def присвоєння_змінної(ток, і):
    """`ім = …` як окремий оператор (не `const`, не поле, не порівняння): змінну оголошено раніше (`let зміст;`), кадр кладуть у гілці."""
    return ток[і - 1][1] in (";", "{", "}", ")") or (ток[і - 1][2] < ток[і][2] and ток[і - 1][1] not in (".", ",", "=", "(", "[", "?", ":", "+", "&", "|"))


def несуть_кадри(ток, області, к, мережеві, відфільтровані=frozenset(), виробники=frozenset()):
    """Імена, що несуть кадри до виклику `ток[к]`: змінні й параметри з «фото»/«кадр» в імені та змінні, оголошені
    (`const`/`let`/`var`) раніше в тому самому тілі з виразу, де є такі імена чи вже відомі носії
    (`копії = … фото…`, `блоки = блокиЗадачі(промпт, копії)`) або рядок `image`/`photo`. Кадр у змінній без
    «фото»/«кадр» в імені — той самий виклик із кадрами (дошка 16059). Довжина (`фото.length`), виклик функції
    за іменем з «фото» і відповідь моделі (результат виклику, що ходить у мережу) кадрів не несуть, як і запис-обʼєкт (`{…}`) чи читання поля й елемента носія."""
    об = [о for о in області if о[1] < к < о[2]]
    if not об:
        return set()
    а = max(об, key=lambda о: о[2] - о[1])[1]
    носії = {ток[і][1] for і in range(а, к) if ток[і][0] == "id" and несе_кадр_токен(ток[і])
             and ток[і + 1][1] != "(" and ток[і - 1][1] not in ("function", ".")}
    # змінна з результату функції-фільтра лічби (`фото = фотоДійшло…()`) кадрів не несе, хоч ім'я каже «фото»
    відфільтрована = змінні_з_фільтра(ток, а, к, відфільтровані)
    носії -= відфільтрована
    зміна = True
    while зміна:
        зміна = False
        for і in range(а + 1, к):
            if ток[і][0] == "id" and ток[і + 1][1] == "=" and ток[і + 2][1] != "=" and ток[і][1] not in відфільтрована \
                    and (ток[і - 1][1] in ("const", "let", "var") or присвоєння_змінної(ток, і)) \
                    and ток[і][1] not in носії:
                глиб, несе, відповідь = 0, False, ток[і + 2][1] == "{"
                # умова трійки `умова ? значення : …` — не значення: `фото ? await виміряти(фото) : null` кадрів не несе
                г2, початок = 0, і + 2
                for y in range(і + 2, к):
                    if ток[y][0] == "p" and ток[y][1] in "([{":
                        г2 += 1
                    elif ток[y][0] == "p" and ток[y][1] in ")]}":
                        г2 -= 1
                    elif ток[y][1] == ";" and г2 == 0:
                        break
                    elif ток[y][1] == "?" and г2 == 0 and ток[y + 1][1] not in (".", "?") and ток[y - 1][1] != "?":
                        початок = y + 1
                        break
                e = початок
                чужі = []  # стек викликів: виклик чужої функції (`виміряти(фото)`) дає не кадри, а свій результат
                while e < к:
                    з, вид = ток[e][1], ток[e][0]
                    if вид == "p" and з in "([{":
                        глиб += 1
                        назва = ток[e - 1][1] if з == "(" and ток[e - 1][0] == "id" else None
                        чужі.append(bool(назва) and not БУДІВНИК_КАДРІВ.search(назва) and назва not in виробники
                                    and назва not in ("map", "filter", "slice", "concat", "flat", "await", "async"))
                    elif вид == "p" and з in ")]}":
                        глиб -= 1
                        if чужі:
                            чужі.pop()
                        if глиб < 0:
                            break
                    elif вид == "p" and з in (";", ",") and глиб == 0:
                        break
                    розгорнутий = e + 1 < к and ток[e + 1][1] == "("
                    читання = e + 2 < к and (ток[e + 1][1] == "[" or ток[e + 1][1] == "."
                                             and ток[e + 2][1] not in ("map", "filter", "slice", "concat", "flat"))
                    ключ_запису = e + 1 < к and ток[e + 1][1] == ":" and ток[e - 1][1] in ("{", ",")
                    if вид == "id" and (з in носії or КАДРИ.search(з) and not ТЕКСТ_ПРО_КАДР.search(з) and not розгорнутий) and not читання \
                            and not ключ_запису and not any(чужі) \
                            and (e == і + 2 or ток[e - 1][1] != "."):
                        несе = True
                    elif вид == "str" and re.fullmatch(r"image|photo|фото", з):
                        несе = True
                    elif вид == "id" and з in виробники and розгорнутий and not any(чужі[:-1]) and ток[e - 1][1] != ".":
                        несе = True  # результат виробника кадру (`блобВБазу(блоб)`): кадр, хоч імʼя змінної цього не каже
                    if вид == "id" and з in мережеві and розгорнутий:
                        відповідь = True
                    e += 1
                if несе and not відповідь:
                    носії.add(ток[і][1])
                    зміна = True
    return носії


# Лічба дійшлих кадрів у потоці значення. Згадки слова мало: функція, що лише пише лічбу в діагноз чи кладе її в запис, а
# відповідь не зважає, — місце (дошка 16205). Рішення — лічба в умові, чия гілка міняє шлях відповіді (`if (кд.жодного)`,
# трійка, `кадрівНеДійшлоП(` кидає виняток), або лічба, що йде з відповіддю `return` до викликача (він теж виклик із кадрами,
# і його лічить той самий розбір).
ЧИТАННЯ_ЛІЧБИ = {"дійшлоКадрівП", "дійшлоКадрівЗаП", "записатиКадриП"}
КИДАЄ_ЛІЧБА = {"кадрівНеДійшлоП"}
ВЛАСТИВІСТЬ_ЛІЧБИ = {"жодного", "дійшло", "надіслано"}
ГІЛКА_ШЛЯХУ = {"return", "throw", "continue", "break", "await", "yield"}


def парна_дужка(ток, і):
    """Індекс токена, що закриває дужку `ток[і]`."""
    закрива = {"(": ")", "[": "]", "{": "}"}[ток[і][1]]
    глиб = 0
    for к in range(і, len(ток)):
        if ток[к][0] == "p" and ток[к][1] == ток[і][1]:
            глиб += 1
        elif ток[к][0] == "p" and ток[к][1] == закрива:
            глиб -= 1
            if глиб == 0:
                return к
    return len(ток) - 1


def кінець_оператора(ток, і, межа):
    """Перший токен після оператора, що починається в `ток[і]`: блок `{…}` чи до `;` на рівні 0 (і далі `else`)."""
    if ток[і][1] == "{":
        к = парна_дужка(ток, і) + 1
    else:
        к, глиб = і, 0
        while к < межа:
            if ток[к][0] == "p" and ток[к][1] in "([{":
                глиб += 1
            elif ток[к][0] == "p" and ток[к][1] in ")]}":
                глиб -= 1
                if глиб < 0:
                    break
            elif ток[к][1] == ";" and глиб == 0:
                к += 1
                break
            к += 1
    if к < межа and ток[к][1] == "else":
        return кінець_оператора(ток, к + 1, межа)
    return к


def гілка_міняє_шлях(ток, від, до, мережеві):
    """Гілка умови міняє шлях відповіді: вихід, кидок, присвоєння, `await` чи виклик моделі; лише діагноз (`.push(`, виклик
    допоміжного запису) шлях не міняє."""
    for к in range(від, до):
        в, з = ток[к][0], ток[к][1]
        if в == "id" and (з in ГІЛКА_ШЛЯХУ or з in мережеві and к + 1 < до and ток[к + 1][1] == "("):
            return True
        if в == "p" and з == "=" and ток[к + 1][1] not in ("=", ">") and ток[к - 1][1] not in ("=", "!", "<", ">"):
            return True
    return False


def розв_умов(ток, а, б, мережеві):
    """Токени тіла `[а, б)`, що стоять в умові, яка міняє шлях: у дужках `if (…)`/`while (…)`, лівіше від `?` трійки."""
    в_умові = set()
    for к in range(а, б):
        if ток[к][1] in ("if", "while") and ток[к][0] == "id" and к + 1 < б and ток[к + 1][1] == "(":
            кінець = парна_дужка(ток, к + 1)
            після = кінець + 1
            до = кінець_оператора(ток, після, б)
            if гілка_міняє_шлях(ток, після, до, мережеві):
                в_умові.update(range(к + 2, кінець))
        elif ток[к][1] == "?" and ток[к][0] == "p" and ток[к + 1][1] not in (".", "?") and ток[к - 1][1] != "?":
            глиб, і = 0, к - 1
            while і >= а:
                if ток[і][0] == "p" and ток[і][1] in ")]}":
                    глиб += 1
                elif ток[і][0] == "p" and ток[і][1] in "([{":
                    глиб -= 1
                    if глиб < 0:
                        break
                elif глиб == 0 and (ток[і][1] in (";", ",") or ток[і][1] == "=" and ток[і + 1][1] != "="
                                    and ток[і - 1][1] not in ("=", "!", "<", ">")):
                    break
                і -= 1
            в_умові.update(range(і + 1, к))
    return в_умові


def носії_лічби(ток, а, б):
    """Імена змінних, що несуть лічбу: `const x = … читання лічби … ;`, і далі ланцюгом."""
    носії = set()
    зміна = True
    while зміна:
        зміна = False
        for і in range(а + 1, б):
            if ток[і][0] == "id" and ток[і + 1][1] == "=" and ток[і + 2][1] != "=" and ток[і - 1][1] == "." and ток[і][1] not in носії:
                # `к.примірка.речей = … лічба …;`: поле обʼєкта несе лічбу, і умова далі читає це поле
                к, глиб = і + 2, 0
                while к < б:
                    if ток[к][0] == "p" and ток[к][1] in "([{":
                        глиб += 1
                    elif ток[к][0] == "p" and ток[к][1] in ")]}":
                        глиб -= 1
                        if глиб < 0:
                            break
                    elif ток[к][1] == ";" and глиб == 0:
                        break
                    if читання_лічби(ток, к) or ток[к][0] == "id" and ток[к][1] in носії:
                        носії.add(ток[і][1])
                        зміна = True
                        break
                    к += 1
            if ток[і][0] == "id" and ток[і + 1][1] == "=" and ток[і - 1][1] in ("const", "let", "var") and ток[і][1] not in носії:
                к, глиб = і + 2, 0
                while к < б:
                    if ток[к][0] == "p" and ток[к][1] in "([{":
                        глиб += 1
                    elif ток[к][0] == "p" and ток[к][1] in ")]}":
                        глиб -= 1
                        if глиб < 0:
                            break
                    elif ток[к][1] == ";" and глиб == 0:
                        break
                    if читання_лічби(ток, к) or ток[к][0] == "id" and ток[к][1] in носії:
                        носії.add(ток[і][1])
                        зміна = True
                        break
                    к += 1
    return носії


# Локальні читачі лічби: стрілка-вираз `const дійшло = зг => … .дійшло …;` (дошка 16250: рішення в приміряння.js читає лічбу
# через неї). Заповнює `п6`; виклик такого читача — те саме читання лічби, що й `дійшлоКадрівП(…)`.
ЧИТАЧІ_ЛІЧБИ = set()


def читачі_лічби(файли):
    вих = set()
    for _, ток, _ in файли:
        for і in range(1, len(ток) - 4):
            if ток[і][0] == "id" and ток[і + 1][1] == "=" and ток[і - 1][1] in ("const", "let", "var"):
                к = і + 2
                if ток[к][1] == "async":
                    к += 1
                if ток[к][1] == "(":
                    к = парна_дужка(ток, к) + 1
                else:
                    к += 1
                if ток[к][1] != "=>" or ток[к + 1][1] == "{":
                    continue
                глиб, y = 0, к + 1
                while y < len(ток):
                    if ток[y][0] == "p" and ток[y][1] in "([{":
                        глиб += 1
                    elif ток[y][0] == "p" and ток[y][1] in ")]}":
                        глиб -= 1
                        if глиб < 0:
                            break
                    elif ток[y][1] == ";" and глиб == 0:
                        break
                    if ток[y][0] == "id" and ток[y][1] in ВЛАСТИВІСТЬ_ЛІЧБИ and ток[y - 1][1] == ".":
                        вих.add(ток[і][1])
                        break
                    y += 1
    return вих


def читання_лічби(ток, к):
    в, з = ток[к][0], ток[к][1]
    if в == "id" and (з in ЧИТАННЯ_ЛІЧБИ or з in КИДАЄ_ЛІЧБА):
        return True
    if в == "id" and з in ЧИТАЧІ_ЛІЧБИ and ток[к + 1][1] == "(":
        return True
    if в == "str" and "images-dropped" in з:
        return True
    return в == "id" and з in ВЛАСТИВІСТЬ_ЛІЧБИ and ток[к - 1][1] == "."


def лічба_вирішує(ток, а, б, мережеві, до_виклику, після_виклику, області=()):
    """Виклик у `ток[до_виклику]`: у вікні `[до_виклику, після_виклику)` (і в замиканнях, які вікно кличе) лічба йде в умову,
    що міняє шлях (`рішення`), чи їде з відповіддю `return` до викликача чи в поле параметра (`передано`), чи ніде."""
    вікна = [(до_виклику, після_виклику)]
    for к in range(до_виклику, після_виклику):
        if ток[к][0] == "id" and к + 1 < б and ток[к + 1][1] == "(":
            вікна += [(а2 + 1, б2) for імя, а2, б2 in області if імя == ток[к][1] and а <= а2 and б2 <= б
                      and not (а2 <= до_виклику <= б2)]
    у_вікні = lambda т: any(від <= т < до for від, до in вікна)
    носії = носії_лічби(ток, а, б)
    в_умові = розв_умов(ток, а, б, мережеві)
    # `кадрівНеДійшлоП(` кидає виняток: шлях відповіді вирішено будовою, умови не треба
    for к in range(а, б):
        if у_вікні(к) and ток[к][0] == "id" and ток[к][1] in КИДАЄ_ЛІЧБА and ток[к + 1][1] == "(":
            return "рішення"
    for к in range(а, б):
        if у_вікні(к) and (читання_лічби(ток, к) or ток[к][0] == "id" and ток[к][1] in носії) and к in в_умові:
            return "рішення"
    локальні = оголошені_імена(ток, а, б)
    передано = False
    for к in range(а, б):
        if not у_вікні(к):
            continue
        # `return … лічба …;`: лічба їде з відповіддю до викликача
        if ток[к][1] == "return" and ток[к][0] == "id":
            і, глиб = к + 1, 0
            while і < б:
                if ток[і][0] == "p" and ток[і][1] in "([{":
                    глиб += 1
                elif ток[і][0] == "p" and ток[і][1] in ")]}":
                    глиб -= 1
                    if глиб < 0:
                        break
                elif ток[і][1] == ";" and глиб == 0:
                    break
                if читання_лічби(ток, і) or ток[і][0] == "id" and ток[і][1] in носії:
                    передано = True
                і += 1
        # `параметр.поле = … лічба …;`: лічба лягає в обʼєкт викликача (вихідний параметр), не в локальний запис
        if ток[к][1] == "=" and ток[к][0] == "p" and ток[к + 1][1] not in ("=", ">") and ток[к - 1][1] not in ("=", "!", "<", ">") \
                and ток[к - 1][0] == "id" and к >= 3 and ток[к - 2][1] == "." and ток[к - 3][0] == "id" \
                and ток[к - 3][1] not in локальні and ток[к - 4][1] != ".":
            і, глиб = к + 1, 0
            while і < б:
                if ток[і][0] == "p" and ток[і][1] in "([{":
                    глиб += 1
                elif ток[і][0] == "p" and ток[і][1] in ")]}":
                    глиб -= 1
                    if глиб < 0:
                        break
                elif ток[і][1] == ";" and глиб == 0:
                    break
                if читання_лічби(ток, і) or ток[і][0] == "id" and ток[і][1] in носії:
                    передано = True
                і += 1
    return "передано" if передано else "нічого"


def оголошені_імена(ток, а, б):
    """Усі імена, оголошені в тілі `[а, б)` через `const`/`let`/`var`: і після коми (`const а = {}, б = {}`), і в деструктуруванні
    (`const {х, у} = …`, `const [х, у] = …`) — дошка 16249: друга змінна оголошення теж локальна."""
    вих = set()
    for і in range(а, б):
        if ток[і][0] != "id" or ток[і][1] not in ("const", "let", "var") or ток[і - 1][1] == ".":
            continue
        к, глиб = і + 1, 0
        чекаємо_імя = True
        while к < б:
            в, з = ток[к][0], ток[к][1]
            if в == "p" and з in "([{":
                if чекаємо_імя and з in "[{":
                    кінець = парна_дужка(ток, к)
                    вих.update(т[1] for т in ток[к + 1:кінець] if т[0] == "id")
                    к = кінець + 1
                    чекаємо_імя = False
                    continue
                глиб += 1
            elif в == "p" and з in ")]}":
                глиб -= 1
                if глиб < 0:
                    break
            elif в == "p" and з == ";" and глиб == 0:
                break
            elif в == "p" and з == "," and глиб == 0:
                чекаємо_імя = True
            elif в == "id" and чекаємо_імя and глиб == 0:
                вих.add(з)
                чекаємо_імя = False
            к += 1
    return вих


ЛІТЕРАЛИ_БЕЗ_ОБ_ЄКТА = {"undefined", "null", "true", "false", "NaN", "Infinity", "this"}


def імена_обєктів(ток):
    """Імена, яким у файлі присвоєно обʼєкт, масив чи `new …` (`const вміщ = {}`): вихідний параметр лічби — лише такий."""
    return {ток[і][1] for і in range(1, len(ток) - 2) if ток[і][0] == "id" and ток[і + 1][1] == "="
            and ток[і + 2][1] in ("{", "[", "new", "Object")}


def вихідні_параметри(ток, а, б):
    """Номери параметрів функції (тіло `[а, б]`), у які вона кладе лічбу дійшлих кадрів для викликача:
    `Object.assign(П, …, {кадри})` чи `П.поле = …`, де праворуч читання лічби чи змінна з неї."""
    імена = параметри_функції(ток, а)
    носії = носії_лічби(ток, а, б)
    вих = set()
    for к in range(а + 1, б):
        if ток[к][0] == "id" and ток[к][1] == "assign" and ток[к - 1][1] == "." and ток[к - 2][1] == "Object" \
                and ток[к + 1][1] == "(" and ток[к + 2][1] in імена:
            кінець = парна_дужка(ток, к + 1)
            if any(читання_лічби(ток, і) or ток[і][0] == "id" and ток[і][1] in носії for і in range(к + 3, кінець)):
                вих.add(імена.index(ток[к + 2][1]))
        if ток[к][1] == "=" and ток[к][0] == "p" and ток[к + 1][1] not in ("=", ">") and ток[к - 1][1] not in ("=", "!", "<", ">") \
                and к >= 3 and ток[к - 2][1] == "." and ток[к - 3][1] in імена:
            і, глиб = к + 1, 0
            while і < б:
                if ток[і][0] == "p" and ток[і][1] in "([{":
                    глиб += 1
                elif ток[і][0] == "p" and ток[і][1] in ")]}":
                    глиб -= 1
                    if глиб < 0:
                        break
                elif ток[і][1] == ";" and глиб == 0:
                    break
                if читання_лічби(ток, і) or ток[і][0] == "id" and ток[і][1] in носії:
                    вих.add(імена.index(ток[к - 3][1]))
                і += 1
    return вих


def аргументи_виклику(ток, відкрита, закрита):
    """[(від, до)] токенів кожного аргумента виклику `ток[відкрита] = "("`…`ток[закрита] = ")"` (коми на рівні 0)."""
    вих, глиб, від = [], 0, відкрита + 1
    for к in range(відкрита + 1, закрита):
        if ток[к][0] == "p" and ток[к][1] in "([{":
            глиб += 1
        elif ток[к][0] == "p" and ток[к][1] in ")]}":
            глиб -= 1
        elif ток[к][1] == "," and глиб == 0:
            вих.append((від, к))
            від = к + 1
    if від < закрита:
        вих.append((від, закрита))
    return вих


def параметри_функції(ток, а):
    """Імена параметрів функції з тілом, що починається в `ток[а] = "{"`: `(x, y) {`, `(x, y) => {`, `x => {`."""
    і = а - 1
    if ток[і][1] == "=>":
        і -= 1
    if ток[і][1] != ")":
        return [ток[і][1]] if ток[і][0] == "id" else []
    початок = і
    глиб = 0
    while початок >= 0:
        if ток[початок][1] == ")":
            глиб += 1
        elif ток[початок][1] == "(":
            глиб -= 1
            if глиб == 0:
                break
        початок -= 1
    вих = []
    for від, до in аргументи_виклику(ток, початок, і):
        вих.append(ток[від][1] if ток[від][0] == "id" else "")
    return вих


def проєкція_мапи(ток, к):
    """`ток[к]` — `map` у `X.map(ф => ({ключ: ф.поле, …}))`: кожен елемент замінено записом полів без самого елемента
    (`ф` лише з `.поле`, поле — не дані кадру), тож кадр ним не йде."""
    if ток[к + 1][1] != "(":
        return False
    кінець = парна_дужка(ток, к + 1)
    тіло = ток[к + 2:кінець]
    if len(тіло) < 6 or тіло[1][1] != "=>" or тіло[0][0] != "id" or тіло[2][1] != "(" or тіло[3][1] != "{":
        return False
    параметр = тіло[0][1]
    for т, t in enumerate(тіло[4:], 4):
        if t[0] == "str" and МАРКЕР_КАДРУ.fullmatch(t[1]):
            return False
        if t[0] == "id" and t[1] == параметр:
            if тіло[т + 1][1] != "." or тіло[т + 2][1] in {"дані", "data", "base64", "source", "url", "blob", "bytes", "тип"}:
                return False
    return True


def виклик_аргумента(ток, т):
    """Якщо `ток[т]` — окремий аргумент виклику `ім(…, х, …)` (не метод): (імʼя функції, номер аргумента), інакше None."""
    if ток[т - 1][1] not in ("(", ",") or ток[т + 1][1] not in (",", ")"):
        return None
    глиб, номер, і = 0, 0, т - 1
    while і >= 0:
        в, з = ток[і][0], ток[і][1]
        if в == "p" and з in ")]}":
            глиб += 1
        elif в == "p" and з in "([{":
            if глиб == 0:
                if з == "(" and ток[і - 1][0] == "id" and ток[і - 2][1] != ".":
                    return ток[і - 1][1], номер
                return None
            глиб -= 1
        elif в == "p" and з == "," and глиб == 0:
            номер += 1
        і -= 1
    return None


def використання_без_пересилання(ток, т, мережеві, визначення, бачені):
    """Використання параметра `ток[т]` не веде кадр до моделі: умова (`!х`, `х ?`) чи аргумент визначеної функції, яка кадр до
    моделі не веде (`вимірПортретаП(фото, зони)` — міряє, не питає; `виправитиПерелікП(…, пікселі)` — далі лише вимір). Усе, що
    йде в запис, масив, повернення, функцію зі збирача блоків чи моделі, — пересилання (дошка 16250: кадр у змінній)."""
    if ток[т - 1][1] == "!" or ток[т + 1][1] == "?":
        return True
    # читання елемента `х[ід]` й `(х || {})[ід]`: з обʼєкта дістають один запис, а не передають його весь
    if ток[т + 1][1] == "[" or (ток[т - 1][1] == "(" and ток[т + 1][1] == "|" and ток[т + 2][1] == "|"
                               and ток[т + 3][1] in ("{", "[") and ток[т + 4][1] in ("}", "]")
                               and ток[т + 5][1] == ")" and ток[т + 6][1] == "["):
        return True
    ви = виклик_аргумента(ток, т)
    if not ви:
        return False
    імя, номер = ви
    if імя not in визначення or БУДІВНИК_КАДРІВ.search(імя):
        return False
    if імя not in мережеві:
        return True
    return all(not параметр_пересилає(т2, а2, б2, номер, мережеві, визначення, бачені)
               for т2, а2, б2 in визначення[імя])


def параметр_пересилає(ток, а, б, номер, мережеві=None, визначення=None, бачені=None):
    """Параметр функції №`номер` (тіло `[а, б]`) іде далі, крім: довжини, запису-ключа й проєкції `.map` у поля без даних; зі
    знанням мережевих функцій — ще й використання, що кадр до моделі не веде (`використання_без_пересилання`)."""
    ключ_візиту = (id(ток), а, номер)
    if бачені is not None:
        if ключ_візиту in бачені:
            return False
        бачені = бачені | {ключ_візиту}
    імена = параметри_функції(ток, а)
    if номер >= len(імена) or not імена[номер]:
        return True
    ім = імена[номер]
    for т in range(а + 1, б):
        if ток[т][0] != "id" or ток[т][1] != ім or ток[т - 1][1] == ".":
            continue
        if ток[т + 1][1] == "." and ток[т + 2][1] == "length":
            continue
        if ток[т + 1][1] == ":" and ток[т - 1][1] in ("{", ","):
            continue
        if ток[т + 1][1] == "." and ток[т + 2][1] == "map" and проєкція_мапи(ток, т + 2):
            continue
        if ток[т - 1][1] == "(" and ток[т + 1][1] == "|" and ток[т + 2][1] == "|" and ток[т + 3][1] == "[" \
                and ток[т + 4][1] == "]" and ток[т + 5][1] == ")" and ток[т + 6][1] == "." and ток[т + 7][1] == "length":
            continue
        if мережеві is not None and використання_без_пересилання(ток, т, мережеві, визначення, бачені or frozenset()):
            continue
        return True
    return False


def шлях_області(файли, ток):
    return next(ш for ш, т, _ in файли if т is ток)


def наступний_виклик(ток, від, межа, мережеві):
    """Токен наступного виклику моделі, що йде ПІСЛЯ виклику, який закінчився в `ток[від]`; виклик в іншій гілці того
    самого `if … else` (альтернативний шлях) — не наступний: лічба після обох гілок стосується обох."""
    глиб, т = 0, від + 1
    while т < межа:
        в, з = ток[т][0], ток[т][1]
        if в == "p" and з in "([{":
            глиб += 1
        elif в == "p" and з in ")]}":
            глиб -= 1
        elif в == "id" and з == "else" and глиб <= 0:
            т = кінець_оператора(ток, т + 1, межа)
            continue
        elif в == "id" and з in мережеві and ток[т + 1][1] == "(" and ток[т - 1][1] != "function":
            return т
        т += 1
    return межа


def виклик_повертається_як_є(ток, к, закриття, а):
    """`return [await] f(…);` чи `=> f(…)`: відповідь іде викликачеві без змін — рішення за ним, а він теж виклик із кадрами."""
    після = ток[закриття + 1][1] if закриття + 1 < len(ток) else ";"
    if після not in (";", "}", ")", ","):
        return False
    і = к - 1
    while і > а and ток[і][1] == ".":
        і -= 2
    if ток[і][1] == "await":
        і -= 1
    return ток[і][1] in ("return", "=>")


def п6(корінь):
    місця, не_місця = [], []
    файли = js_файли(корінь)
    # функції, що ходять до моделі, і ті, що їх кличуть, — по всіх файлах за імʼям
    мережеві = set()
    for _, ток, області in файли:
        мережеві |= {імя for імя, а, б in області if імя and виклик_моста(ток, а, б)}
    зміна = True
    while зміна:
        зміна = False
        for _, ток, області in файли:
            for імя, а, б in області:
                if імя and імя not in мережеві and any(ток[к][0] == "id" and ток[к][1] in мережеві
                                                       and к + 1 < len(ток) and ток[к + 1][1] == "(" for к in range(а, б)):
                    мережеві.add(імя)
                    зміна = True
    області_файлів = {id(ток): області for _, ток, області in файли}
    виробники = виробники_кадрів(файли)
    ЧИТАЧІ_ЛІЧБИ.clear()
    ЧИТАЧІ_ЛІЧБИ.update(читачі_лічби(файли))
    # Функція, чий результат відібрано за лічбою дійшлих (`фотоДійшлоВідповіді…`: кадр лишається, лише коли жодного не втрачено),
    # кадрів не несе: те, що вона віддає, уже пройшло рішення.
    відфільтровані = set()
    for _, ток, області in файли:
        for імя, а, б in області:
            if імя:
                умови = розв_умов(ток, а, б, мережеві)
                if any(к in умови and (читання_лічби(ток, к) or ток[к][0] == "id" and ток[к][1] in носії_лічби(ток, а, б))
                       for к in range(а, б)):
                    відфільтровані.add(імя)
    визначення = {}  # імʼя → [(токени, від, до)]: хто пересилає параметр кадрів далі (див. `параметр_пересилає`)
    for _, ток, області in файли:
        for імя, а, б in області:
            if імя:
                визначення.setdefault(імя, []).append((ток, а, б))

    def виклики_з_кадрами():
        """Виклики функцій, що ходять до моделі, з кадром в аргументі: (файл, токени, k, імʼя, рядок, закриття,
        імʼя_тіла, від, до). Аргумент, який викликана функція далі не пересилає (лише ід чи довжина), кадрів не несе."""
        вих = []
        for шлях, ток, області in файли:
            for к, (в, з, р) in enumerate(ток):
                if в != "id" or з not in мережеві or к + 1 >= len(ток) or ток[к + 1][1] != "(" \
                        or (к and ток[к - 1][1] == "function"):
                    continue
                e = парна_дужка(ток, к + 1)
                носії = None
                несе = False
                for п, (від, до) in enumerate(аргументи_виклику(ток, к + 1, e)):
                    об0 = [о for о in області if о[1] < к < о[2]]
                    з_фільтра = змінні_з_фільтра(ток, min(об0, key=lambda о: о[2] - о[1])[1], к, відфільтровані) if об0 else set()
                    сегмент = [t for t in ток[від:до] if t[1] not in з_фільтра]
                    inline_виробник = any(ток[ї][0] == "id" and ток[ї][1] in виробники and ток[ї + 1][1] == "("
                                          for ї in range(від, до))
                    if not inline_виробник and not any(несе_кадр_токен(t) for t in сегмент):
                        if носії is None:
                            носії = несуть_кадри(ток, області, к, мережеві, відфільтровані, виробники)
                        if not any(t[0] == "id" and t[1] in носії for t in сегмент):
                            continue
                    if all(not параметр_пересилає(т2, а2, б2, п, мережеві, визначення, frozenset()) for т2, а2, б2 in визначення.get(з, [])) \
                            and визначення.get(з):
                        continue
                    несе = True
                if not несе:
                    continue
                об = [о for о in області if о[1] < к < о[2]]
                if not об:
                    continue
                імя_тіла, а, б = min(об, key=lambda о: о[2] - о[1])
                вих.append((шлях, ток, к, з, р, e, імя_тіла, а, б))
        return вих

    виклики = виклики_з_кадрами()

    вихідні = {}
    for _, ток, області in файли:
        for імя, а, б in області:
            if імя:
                вихідні.setdefault(імя, set()).update(вихідні_параметри(ток, а, б))

    def оцінити(судді):
        вих = []
        for шлях, ток, к, з, р, e, імя_тіла, а, б in виклики:
            локальні = оголошені_імена(ток, а, б)
            власні_параметри = set(параметри_функції(ток, а))
            обєкти = імена_обєктів(ток)
            аргументи = аргументи_виклику(ток, к + 1, e)
            if з in судді:
                вид = "суддя"
            elif з == імя_тіла:
                вид = "самовиклик"
            elif any(п in вихідні.get(з, ()) and п < len(аргументи) and аргументи[п][1] - аргументи[п][0] == 1
                     and ток[аргументи[п][0]][0] == "id" and ток[аргументи[п][0]][1] not in локальні
                     and ток[аргументи[п][0]][1] not in ЛІТЕРАЛИ_БЕЗ_ОБ_ЄКТА
                     and (ток[аргументи[п][0]][1] in власні_параметри or ток[аргументи[п][0]][1] in обєкти)
                     for п in range(len(аргументи))):
                # викликана функція кладе лічбу в параметр, який викликач дістав від свого викликача: рішення за ним
                вид = "передано"
            else:
                наступний = наступний_виклик(ток, e, б, мережеві)
                вид = лічба_вирішує(ток, а, б, мережеві, к, наступний, області_файлів[id(ток)])
                if вид == "нічого" and any(t[0] in ("id", "str") and ДІЙШЛО.search(t[1]) for t in ток[а:б]):
                    вид = "лише згадка"
            вих.append(вид)
        return вих

    # Функція, що сама вирішує за лічбою кожен свій виклик із кадрами, — суддя: її викликачі рішення не дублюють.
    судді = set()
    while True:
        види = оцінити(судді)
        нові = set()
        за_тілом = {}
        for (шлях, ток, к, з, р, e, імя_тіла, а, б), вид in zip(виклики, види):
            if імя_тіла and вид != "самовиклик":
                за_тілом.setdefault((імя_тіла, шлях, а), []).append(вид)
        for (імя_тіла, _, _), вв in за_тілом.items():
            if ("рішення" in вв or "суддя" in вв) and all(в in ("рішення", "суддя", "як є", "передано") for в in вв):
                нові.add(імя_тіла)
        # Функція з параметром-кадром, що віддає його (через стан модуля: `ОЦ.фото = фото…`) тому, хто вирішує, суддя, коли
        # кличе суддю й сама має лише покриті виклики з кадрами (гіпотеза: що саме кадр іде до того судді, не виміряно).
        for _, ток, області in файли:
            for імя, а, б in області:
                if імя and імя not in судді and any(несе_кадр_токен(("id", п, 0)) for п in параметри_функції(ток, а)) \
                        and all(в in ("рішення", "суддя", "як є", "передано") for в in за_тілом.get((імя, шлях_області(файли, ток), а), [])) \
                        and any(ток[к][0] == "id" and ток[к][1] in судді and ток[к + 1][1] == "(" for к in range(а, б)):
                    нові.add(імя)
        if нові <= судді:
            break
        судді |= нові
    ОПИС = {"суддя": "лічбу дійшлих вирішує сама викликана функція", "як є": "відповідь іде викликачеві як є, рішення за ним",
            "рішення": "лічба дійшлих вирішує шлях відповіді", "передано": "лічба дійшлих їде з відповіддю до викликача"}
    for (шлях, ток, к, з, р, e, імя_тіла, а, б), вид in zip(виклики, види):
        if вид == "самовиклик" and імя_тіла in судді:
            вид = "суддя"
        elif вид == "самовиклик":
            вид = "лише згадка"
        if вид in ОПИС:
            не_місця.append((відн(шлях), р, 6, f"виклик {з}( з кадрами: {ОПИС[вид]}"))
        else:
            місця.append((відн(шлях), р, 6, f"виклик {з}( з кадрами: відповідь не зважає на лічбу дійшлих"
                                             + (" (лічба лише згадана: діагноз чи запис, не умова)" if вид == "лише згадка" else "")))
    return місця, не_місця


# ───────────────────────────── вимір ─────────────────────────────
ГІПОТЕЗИ = (
    "п.2: клас виведених значень — перелік ключів ВИВЕДЕНІ (`metal`, `light`, `road_salt`, `season`, `formality`, "
    "`occasion_requirements`) плюс ключі, які фільтр палітри в коді лишає у вході (`farthest`, `combinations`), і ключі "
    "з таблиці кодів у циклі (`для ключ, … in ТАБЛИЦЯ: д[ключ] = …`); виведене значення з ключем поза цим (`part_of_day` — "
    "його дає слово жінки через модель, а не вивід коду), динамічний ключ не з модульної таблиці й промпти пакета "
    "образів, що не йдуть від трьох входів, прилад не бачить",
    "п.3: лише визначення заяв «код → англійське», що стверджують лід, дощ, сніг, вітер (силу «heavy/light/a lot of» "
    "перед назвою зчитує вираз; словник реєстру ≥ 20 кодів); обставини «місце», «дорога», «вибір», тексти заяв у JS і "
    "українські фрази коду не виміряно; чи є слово про обставину в її словах — лише за назвами в умові `if` довкола виходу",
    "п.1: прилад лічить писачів ознак (пара, ключ словника, присвоєння `д[\"color\"] = …`, цикл за перелічком, ярлик) без "
    "умови певності, але не знає, яка ознака речі невпевнена (вид, тип, кількість не мають в записі позначки «не певний», "
    "«кількість» не в переліку ознак); кадр іншого кольору захищає лише вимір (`hex`), але не колір зі слова крамниці; "
    "поле запису, яке йде динамічним ключем не з перелічка, не виміряно; вхід — досяжне від `дріт_моделі.опис` і "
    "`мовний_шар._абзац_речей`, інші входи пояснення не виміряно",
    "п.4: лише англійські речення літералів Python і JS (разом із визначеннями заяв); промпти зі складених рядків "
    "(`%`, `.join`, f-рядки з вставленим реченням) бачаться частинами, а вимога в JSON-схемі й в .md-базах не виміряна; "
    "предмет вимоги — перелік слів у ПРЕДМЕТ",
    "п.6 (зміст): суддя — функція, чия умова чи вихід читає лічбу дійшлих; лічба, що йде в стан модуля (`ОЦ.фото = …`) і "
    "читається в іншій функції, — «гіпотеза»: суддею лічиться функція з параметром-кадром, що кличе суддю; носій лічби і "
    "кадрів — за іменем та ланцюгом присвоєнь, текст про кадр (підпис, опис, назва, питання, коди-ярлики) — за іменем "
    "(ТЕКСТ_ПРО_КАДР); чи умова справді міняє шлях — за формою гілки (`return`, виклик, присвоєння), не за наслідком",
    "п.3 (зміст): «виведене» — присвоєння результатом виклику, в аргументах якого імена смуги чи температури "
    "(ВХІД_ВИВОДУ); виведення через поле об'єкта чи стан модуля не виміряно; обставину «сіль на дорозі» зчитує вираз "
    "(`salted road`, `under salt`)",
    "п.7: лише гілка за замовчуванням, що вертає чи підставляє позначку довіри `her_words`/`her`/`hand`/`verified`/"
    "`перевірено` (`return`, `.get(ключ, …)`, `х or …`, ланцюг `… else …` з рядковими сталими на будь-якій глибині, "
    "словникове включення з умовою відсутності, JS `|| …`/`?? …`); ствердний дефолт прапора `перевірено`/`verified` "
    "лічиться в методах словника, `or True`, умовному виразі й записі у гілці відсутності; подія — наявність того самого "
    "ключа в захисній умові чи прямий попередній запис. Міжпроцедурне походження вердикту, прапори `measured`/`виміряно`, "
    "позначка, що йде через "
    "змінну, поле чи таблицю кодів, не виміряно; дефолт параметра функції лічиться (`перевірено=True`, `джерело=\"her\"` "
    "рядком чи модульною сталою), а значення, яке викликач передає явно, не читається — місце сам дефолт",
    "п.3 (ланцюг, 17.11): обставина «дорога» (мокра чи слизька дорога, калюжі) і ланцюг виведення «виведене з виведеного» "
    "лише через виклик із погодою в аргументах і параметр, у який викликач віддає такий виклик; виведення із «типового» "
    "(сезон за замовчуванням), через стан модуля чи поле об'єкта — гіпотеза, не виміряно",
    "п.6: лише JS-виклики моделі, що ходять у мережу (`fetch` у тілі чи в замикання) з кадром в аргументах — прямо чи "
    "через змінну в тому самому тілі (`копії = … фото…`, `блоки = блокиЗапиту(…, копії)`); кадри, що йдуть параметром із "
    "іншої функції під іншим іменем, виклики Python-моста й повтори поза тілом викликача не виміряно",
)


def вимір(корінь=None):
    корінь = корінь or КОРІНЬ
    всі = модулі_кеш(корінь)
    вхід = досяжні(всі)
    місця, не_місця = [], []
    а, б = п1(всі, вхід)
    місця += а
    не_місця += б
    а, б = п2(всі, вхід)
    місця += а
    не_місця += б
    а, б, без_виходу = п3(всі)
    місця += а
    не_місця += б
    п4, п5, не_п4 = п4_п5(корінь)
    місця += п4 + п5
    не_місця += не_п4
    а, б = п6(корінь)
    місця += а
    не_місця += б
    місця += п7_python(всі) + п7_js(корінь)
    унікальні = {}
    for ф, р, п, що in місця:
        унікальні.setdefault((ф, р, п), що)
    місця = [(ф, р, п, що) for (ф, р, п), що in sorted(унікальні.items(), key=lambda х: (х[0][2], х[0][0], х[0][1]))]
    за = {п: sum(1 for _, _, пп, _ in місця if пп == п) for п in ПУНКТИ}
    return dict(місця=місця, не_місця=не_місця, без_виходу=без_виходу, за_пунктами=за, у_вході=len(вхід),
                гіпотези=list(ГІПОТЕЗИ))


def main():
    д = вимір()
    if "--json" in sys.argv:
        print(json.dumps({"місць": len(д["місця"]), "за_пунктами": д["за_пунктами"],
                          "місця": [dict(файл=ф, рядок=р, пункт=п, що=що) for ф, р, п, що in д["місця"]],
                          "гіпотези": д["гіпотези"]}, ensure_ascii=False, indent=2))
        return 0
    for ф, р, п, що in д["місця"]:
        print(f"{ф}:{р} · п.{п} · {що}")
    if "--деталі" in sys.argv:
        for ф, р, п, що in sorted(д["не_місця"]):
            print(f"не місце: {ф}:{р} · п.{п} · {що}")
        for ф, р, п, що in sorted(д["без_виходу"]):
            print(f"без виходу: {ф}:{р} · п.{п} · {що}")
    if "--не-виміряно" in sys.argv:
        for г in д["гіпотези"]:
            print("гіпотеза: " + г)
    print("за пунктами: " + ", ".join(f"п.{п} {к}" for п, к in д["за_пунктами"].items())
          + f"; функцій у вході пояснення: {д['у_вході']}")
    print(f"місць: {len(д['місця'])}")
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
