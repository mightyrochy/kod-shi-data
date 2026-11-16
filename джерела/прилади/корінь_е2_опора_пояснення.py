# -*- coding: utf-8 -*-
"""Лічить місця кореня Е2-опора-пояснення: пояснення каже як факт те, чого продукт не знає (без запуску продукту).

Клас — `аудит/корені/Е2-опора-пояснення.md` («Клас місць»): точка коду продукту (`джерела/` на будь-якій глибині, Python,
JS і промпти в них; проби, прилади, тести й `джерела/аудит` — ні), де значення входить у текст, який читає жінка під
образом, без свого джерела й певності. Шість пунктів:
  1  поле запису речі (колір, крій, вид, тканина…) іде у вхід моделі опису чи перекладачки як факт — писач ключа на
     дріт (пара `("cut", …)`, ключ словника, цикл за перелічком ознак) чи рядок-ярлик промпта («colour code: …»)
     без умови певності в самому значенні (`кадр_колір`, `свідчення…`, `певн…`, `сирий` тощо);
  2  виведене чи взяте за замовчуванням значення сценарію й палітри (`metal`, `light`, `road_salt`, `season`…) іде у
     вхід без позначки джерела (`<ключ>_source`, `sources`, читання `…_джерело`/`походження…` у значенні);
  3  заява коду (визначення коду заяви — словник «код → англійське визначення») стверджує обставину (лід, дощ, сніг,
     вітер), а умова виходу заяви (`if` довкола `заява("код")`) читає не її слова про цю обставину, а смугу чи
     температуру;
  4  речення промпта вимагає сказати про властивість чи обставину (день, дорога, зручність, тепло, вибір) без умови
     «коли вона відома» (`when/if/only/known/support/omit…`);
  5  правило перекладу ставить значення коду (код кольору, виду) на місце того, що модель назвала з фото;
  6  виклик моделі з кадрами (JS) не читає, скільки кадрів дійшло (`x-images-dropped`, `дійшло(`), хоч далі йде як
     «із фото».
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
          5: "значення коду замість слова моделі з фото", 6: "виклик із кадрами не знає, скільки кадрів дійшло"}

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
    "сніг": (re.compile(_ЗАЧИН + _СИЛА + r"(snowy|snowing|snow\b|snowfall|salty slush|slush)", re.I),
             ("опади", "precipitation", "сніг", "snow", "реагент", "сльот", "сіль", "salt")),
    "вітер": (re.compile(_ЗАЧИН + _СИЛА + r"(windy|wind\b|gusts?)", re.I),
              ("вітер", "вітру", "wind")),
}
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
                читають = [і for мм, нн in виходи for і in умови_виходу(мм, нн)]
                збіг = next((і for і in читають if any(с in і.lower() for с in її)), None)
                if збіг:
                    не_місця.append((м.шлях, рядок, 3, f"заява «{код}»: умова виходу читає її слова (`{збіг}`)"))
                else:
                    місця.append((м.шлях, рядок, 3, f"заява «{код}» стверджує «{клас}» («{частина.strip()[:70]}»), "
                                                    f"умова виходу не читає її слів про це"))
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


БУДІВНИК_КАДРІВ = re.compile(r"кадр|Кадр|фото|Фото|блок|Блок|image|block", re.I)


def несуть_кадри(ток, області, к, мережеві):
    """Імена, що несуть кадри до виклику `ток[к]`: змінні й параметри з «фото»/«кадр» в імені та змінні, оголошені
    (`const`/`let`/`var`) раніше в тому самому тілі з виразу, де є такі імена чи вже відомі носії
    (`копії = … фото…`, `блоки = блокиЗадачі(промпт, копії)`) або рядок `image`/`photo`. Кадр у змінній без
    «фото»/«кадр» в імені — той самий виклик із кадрами (дошка 16059). Довжина (`фото.length`), виклик функції
    за іменем з «фото» і відповідь моделі (результат виклику, що ходить у мережу) кадрів не несуть, як і запис-обʼєкт (`{…}`) чи читання поля й елемента носія."""
    об = [о for о in області if о[1] < к < о[2]]
    if not об:
        return set()
    а = max(об, key=lambda о: о[2] - о[1])[1]
    носії = {ток[і][1] for і in range(а, к) if ток[і][0] == "id" and КАДРИ.search(ток[і][1])
             and ток[і + 1][1] != "(" and ток[і - 1][1] not in ("function", ".")}
    зміна = True
    while зміна:
        зміна = False
        for і in range(а + 1, к):
            if ток[і][0] == "id" and ток[і + 1][1] == "=" and ток[і - 1][1] in ("const", "let", "var") \
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
                        чужі.append(bool(назва) and not БУДІВНИК_КАДРІВ.search(назва)
                                    and назва not in ("map", "filter", "slice", "concat", "flat", "await", "async"))
                    elif вид == "p" and з in ")]}":
                        глиб -= 1
                        if чужі:
                            чужі.pop()
                        if глиб < 0:
                            break
                    elif вид == "p" and з == ";" and глиб == 0:
                        break
                    розгорнутий = e + 1 < к and ток[e + 1][1] == "("
                    читання = e + 2 < к and (ток[e + 1][1] == "[" or ток[e + 1][1] == "."
                                             and ток[e + 2][1] not in ("map", "filter", "slice", "concat", "flat"))
                    ключ_запису = e + 1 < к and ток[e + 1][1] == ":" and ток[e - 1][1] in ("{", ",")
                    if вид == "id" and (з in носії or КАДРИ.search(з) and not розгорнутий) and not читання \
                            and not ключ_запису and not any(чужі) \
                            and (e == і + 2 or ток[e - 1][1] != "."):
                        несе = True
                    elif вид == "str" and re.fullmatch(r"image|photo|фото", з):
                        несе = True
                    if вид == "id" and з in мережеві and розгорнутий:
                        відповідь = True
                    e += 1
                if несе and not відповідь:
                    носії.add(ток[і][1])
                    зміна = True
    return носії


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
    for шлях, ток, області in файли:
        for к, (в, з, р) in enumerate(ток):
            if в != "id" or з not in мережеві or к + 1 >= len(ток) or ток[к + 1][1] != "(" \
                    or (к and ток[к - 1][1] == "function"):
                continue
            глиб, e = 0, к + 1
            while e < len(ток):
                if ток[e][1] == "(":
                    глиб += 1
                elif ток[e][1] == ")":
                    глиб -= 1
                    if глиб == 0:
                        break
                e += 1
            носії = None
            if not any(t[0] in ("id", "str") and КАДРИ.search(t[1]) for t in ток[к + 2:e]):
                носії = несуть_кадри(ток, області, к, мережеві)
                if not any(t[0] == "id" and t[1] in носії for t in ток[к + 2:e]):
                    continue
            об = [о for о in області if о[1] < к < о[2]]
            if not об:
                continue
            тіло = min(об, key=lambda о: о[2] - о[1])
            if any(t[0] in ("id", "str") and ДІЙШЛО.search(t[1]) for t in ток[тіло[1]:тіло[2]]):
                не_місця.append((відн(шлях), р, 6, f"виклик {з}( з кадрами: у тілі читається лічба дійшлих"))
            else:
                місця.append((відн(шлях), р, 6, f"виклик {з}( з кадрами: не читає, скільки кадрів дійшло"))
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
