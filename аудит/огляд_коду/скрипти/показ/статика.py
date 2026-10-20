"""Статичний розбір `джерела/показ.html` (наряд ОЦІНКА-ПОКАЗУ): токенізатор JS без залежностей,
межі верхніх функцій, досяжність від коду, що біжить при завантаженні, глобальний стан (хто пише й читає),
таймери, слухачі, сховища, виклики `містП` і моделі, коментарі-історії, повтори функцій.
Запуск: python3 статика.py [джерела/показ.html] > статика.json; друкує зведення в stderr."""
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict

ШЛЯХ = sys.argv[1] if len(sys.argv) > 1 else "джерела/показ.html"
ТЕКСТ = open(ШЛЯХ, encoding="utf-8").read()
ІД = re.compile(r"[A-Za-z_$Ѐ-ӿ’ʼ][A-Za-z0-9_$Ѐ-ӿ’ʼ]*")
ПЕРЕД_РЕГЕКСОМ = set("(,=:[!&|?{};+-*%<>~^") | {""}
СЛОВА_ПЕРЕД_РЕГЕКСОМ = {"return", "typeof", "case", "do", "else", "in", "of", "new", "delete", "void", "throw", "yield", "await"}


def токени(js, база=0):
    """[(вид, текст, позиція)]: вид — id, str, tpl, num, re, p (пунктуація); коментарі — окремо в `коментарі`."""
    out, ком, i, n = [], [], 0, len(js)
    стек_шаблонів = []  # глибина фігурних дужок усередині ${…}
    def попередній():
        for в, т, _ in reversed(out):
            return (в, т)
        return ("p", "")
    while i < n:
        c = js[i]
        if c in " \t\r\n":
            i += 1
            continue
        if js.startswith("//", i):
            j = js.find("\n", i)
            j = n if j < 0 else j
            ком.append((база + i, js[i:j]))
            i = j
            continue
        if js.startswith("/*", i):
            j = js.find("*/", i + 2)
            j = n if j < 0 else j + 2
            ком.append((база + i, js[i:j]))
            i = j
            continue
        if c in "'\"":
            j = i + 1
            while j < n and js[j] != c:
                j += 2 if js[j] == "\\" else 1
            out.append(("str", js[i + 1:j], база + i))
            i = j + 1
            continue
        if c == "`" or (c == "}" and стек_шаблонів and стек_шаблонів[-1] == 0):
            if c == "}":
                стек_шаблонів.pop()
            j = i + 1
            while j < n and js[j] != "`":
                if js[j] == "\\":
                    j += 2
                    continue
                if js.startswith("${", j):
                    break
                j += 1
            out.append(("tpl", js[i + 1:j], база + i))
            if j < n and js[j] == "$":
                стек_шаблонів.append(0)
                i = j + 2
            else:
                i = j + 1
            continue
        if c == "/":
            в, т = попередній()
            if (в == "p" and т in ПЕРЕД_РЕГЕКСОМ) or (в == "id" and т in СЛОВА_ПЕРЕД_РЕГЕКСОМ) or (в == "p" and т == ")" and False):
                j, клас = i + 1, False
                while j < n:
                    if js[j] == "\\":
                        j += 2
                        continue
                    if js[j] == "[":
                        клас = True
                    elif js[j] == "]":
                        клас = False
                    elif js[j] == "/" and not клас:
                        break
                    elif js[j] == "\n":
                        break
                    j += 1
                j += 1
                while j < n and js[j].isalpha():
                    j += 1
                out.append(("re", js[i:j], база + i))
                i = j
                continue
        m = ІД.match(js, i)
        if m:
            out.append(("id", m.group(0), база + i))
            i = m.end()
            continue
        if c.isdigit():
            m = re.compile(r"[0-9][0-9a-fA-FxXoObBn_.eE]*").match(js, i)
            out.append(("num", m.group(0), база + i))
            i = m.end()
            continue
        if стек_шаблонів and c in "{}":
            стек_шаблонів[-1] += 1 if c == "{" else -1
        out.append(("p", c, база + i))
        i += 1
    return out, ком


def рядок(поз):
    return ТЕКСТ.count("\n", 0, поз) + 1


# ── скрипти й обробники в атрибутах
скрипти = [(m.start(1), m.group(1)) for m in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", ТЕКСТ, re.S)]
головний = max(скрипти, key=lambda с: len(с[1]))
атрибути = [(m.start(1), m.group(1)) for m in re.finditer(r"\son[a-z]+=\"([^\"]*)\"", ТЕКСТ[:головний[0]])]
стилі = [(m.start(1), m.group(1)) for m in re.finditer(r"<style[^>]*>(.*?)</style>", ТЕКСТ, re.S)]
розмітка = re.sub(r"<script.*?</script>|<style.*?</style>", "", ТЕКСТ, flags=re.S)

ТОК, КОМ = токени(головний[1], головний[0])

# ── верхні оголошення: function, async function, const/let/var на глибині 0
верхні = []  # (ім, вид, поч_токен, кін_токен)
глибина, і = 0, 0
while і < len(ТОК):
    в, т, п = ТОК[і]
    if в == "p" and т in "{([":
        глибина += 1
    elif в == "p" and т in "})]":
        глибина -= 1
    elif глибина == 0 and в == "id" and т == "function":
        ім = ТОК[і + 1][1] if ТОК[і + 1][0] == "id" else (ТОК[і + 2][1] if ТОК[і + 1][1] == "*" else "?")
        поч = і - 1 if і and ТОК[і - 1][1] == "async" else і
        # тіло — перша «{» після параметрів
        j, г = і, 0
        while not (ТОК[j][1] == "{" and г == 0 and ТОК[j - 1][1] == ")"):
            if ТОК[j][1] in "([":
                г += 1
            elif ТОК[j][1] in ")]":
                г -= 1
            j += 1
        г = 0
        while True:
            if ТОК[j][0] == "p" and ТОК[j][1] in "{([":
                г += 1
            elif ТОК[j][0] == "p" and ТОК[j][1] in "})]":
                г -= 1
                if г == 0:
                    break
            j += 1
        верхні.append((ім, "function", поч, j))
        і = j + 1
        continue
    elif глибина == 0 and в == "id" and т in ("const", "let", "var"):
        # const А = …, Б = …; — до «;» або до нового рядка на глибині 0, де наступний токен не продовжує вираз
        j, г, імена = і + 1, 0, []
        очікую_ім = True
        while j < len(ТОК):
            вj, тj, пj = ТОК[j]
            if вj == "p" and тj in "{([":
                if г == 0 and очікую_ім:  # деструктуризація
                    к, гг = j, 0
                    while True:
                        if ТОК[к][1] in "{([" and ТОК[к][0] == "p":
                            гг += 1
                        elif ТОК[к][1] in "})]" and ТОК[к][0] == "p":
                            гг -= 1
                            if гг == 0:
                                break
                        elif ТОК[к][0] == "id" and ТОК[к + 1][1] in ",}]=" and ТОК[к - 1][1] != ".":
                            імена.append(ТОК[к][1])
                        к += 1
                    j = к + 1
                    очікую_ім = False
                    continue
                г += 1
            elif вj == "p" and тj in "})]":
                г -= 1
            elif г == 0 and вj == "id" and очікую_ім:
                імена.append(тj)
                очікую_ім = False
            elif г == 0 and вj == "p" and тj == ",":
                очікую_ім = True
            elif г == 0 and вj == "p" and тj == ";":
                break
            if г == 0 and j + 1 < len(ТОК):
                наст = ТОК[j + 1]
                if ТЕКСТ.count("\n", пj, наст[2]) and not (наст[0] == "p" and наст[1] in ".?:+-*/%&|,=<>)]}") \
                        and not (вj == "p" and тj in "=(,[{?:+-*/%&|<>!") and not (вj == "id" and тj in ("new", "await", "typeof", "return")) \
                        and not (наст[0] == "id" and наст[1] in ("in", "of", "instanceof")):
                    break
            j += 1
        вид = т
        тіло = ТОК[і + 3] if і + 3 < len(ТОК) else ("", "", 0)
        def стр(к):
            return ТОК[к][1] == "=" and ТОК[к + 1][1] == ">" and ТОК[к + 1][2] == ТОК[к][2] + 1
        # const ім = (…) => …, const ім = х => …, const ім = async (…) => …
        к0 = і + 3 + (ТОК[і + 3][1] == "async")
        if ТОК[к0][1] == "(":
            г, к = 0, к0
            while True:
                if ТОК[к][1] in "([{" and ТОК[к][0] == "p":
                    г += 1
                elif ТОК[к][1] in ")]}" and ТОК[к][0] == "p":
                    г -= 1
                    if г == 0:
                        break
                к += 1
            стрілка = стр(к + 1)
        else:
            стрілка = ТОК[к0][0] == "id" and стр(к0 + 1)
        for ім in імена:
            верхні.append((ім, "arrow" if (стрілка and len(імена) == 1) else вид, і, j))
        і = j + 1
        continue
    і += 1

ім_верхні = Counter(в[0] for в in верхні)
функції = [в for в in верхні if в[1] in ("function", "arrow")]
змінні = [в for в in верхні if в[1] in ("const", "let", "var")]


def ідентифікатори(від, до):
    """Посилання (не властивості) і слова з рядків/шаблонів — обробники в шаблонах розмітки."""
    сл = Counter()
    for к in range(від, до + 1):
        в, т, _ = ТОК[к]
        if в == "id" and not (к and ТОК[к - 1][1] == "." and ТОК[к - 1][0] == "p"):
            сл[т] += 1
        elif в in ("str", "tpl"):
            for м in ІД.finditer(т):
                сл["\x00" + м.group(0)] += 1
    return сл


покрито = [False] * len(ТОК)
for _, _, а, б in верхні:
    if б >= а:
        for к in range(а, б + 1):
            покрито[к] = True
# код верхнього рівня, що біжить при завантаженні (поза тілами функцій; ініціалізатори const/let теж біжать)
верх_код = Counter()
for _, вид, а, б in верхні:
    if вид in ("const", "let", "var"):
        верх_код.update(ідентифікатори(а, б))
for к, (в, т, _) in enumerate(ТОК):
    if not покрито[к]:
        if в == "id" and not (к and ТОК[к - 1][1] == "."):
            верх_код[т] += 1
        elif в in ("str", "tpl"):
            for м in ІД.finditer(т):
                верх_код["\x00" + м.group(0)] += 1
зовні = Counter()
for _, к in [с for с in скрипти if с is not головний] + атрибути:
    for м in ІД.finditer(к):
        зовні[м.group(0)] += 1
for м in ІД.finditer(розмітка):
    зовні[м.group(0)] += 1

посилання = {}
for ім, вид, а, б in функції:
    посилання.setdefault(ім, Counter()).update(ідентифікатори(а, б))
імена_ф = set(посилання)

# Хто згадує функцію: тільки ім'я-ідентифікатор поза власним тілом
згадки = defaultdict(set)
for ім, сл in посилання.items():
    for ід in сл:
        чисте = ід.lstrip("\x00")
        if чисте in імена_ф and чисте != ім:
            згадки[чисте].add(ім)
корені = {ід.lstrip("\x00") for ід in верх_код} | set(зовні)
досяжні, черга = set(), [ф for ф in імена_ф if ф in корені]
while черга:
    ф = черга.pop()
    if ф in досяжні:
        continue
    досяжні.add(ф)
    for ід in посилання.get(ф, ()):
        чисте = ід.lstrip("\x00")
        if чисте in імена_ф and чисте not in досяжні:
            черга.append(чисте)

СТЕНД = open("аудит/проби/рв6_стенд.js", encoding="utf-8").read()
ТЕСТ = open("джерела/тест_показу.js", encoding="utf-8").read()
слова_стенда = set(ІД.findall(СТЕНД))
слова_тесту = set(ІД.findall(ТЕСТ))


def межі(а, б):
    return рядок(ТОК[а][2]), рядок(ТОК[б][2])


реєстр = []
for ім, вид, а, б in функції:
    п, к = межі(а, б)
    реєстр.append({"ім": ім, "вид": вид, "з": п, "по": к, "рядків": к - п + 1,
                   "згадок": len(згадки.get(ім, ())) + (1 if ім in корені else 0),
                   "досяжна": ім in досяжні, "стенд": ім in слова_стенда, "тест": ім in слова_тесту,
                   "дублів_імені": ім_верхні[ім]})

# ── глобальний стан: верхні let/var (і const-об'єкти, які мутують) — хто пише, хто читає
ПРИСВОЄННЯ = {"=", "+=", "-=", "*=", "||=", "&&=", "??=", "++", "--"}
def присвоєння_після(к):
    т = "".join(ТОК[м][1] for м in range(к + 1, min(к + 4, len(ТОК))) if ТОК[м][0] == "p")
    for оп in ("===", "=="):
        if т.startswith(оп):
            return False
    return any(т.startswith(оп) for оп in ПРИСВОЄННЯ) or (к and ТОК[к - 1][1] in ("++", "--"))


функція_токена = [None] * len(ТОК)
for ім, вид, а, б in функції:
    for к in range(а, б + 1):
        функція_токена[к] = ім
глобалі = {}
for ім, вид, а, б in змінні:
    глобалі[ім] = {"вид": вид, "рядок": рядок(ТОК[а][2]), "пишуть": set(), "читають": set(), "мутують": set()}
for к, (в, т, _) in enumerate(ТОК):
    if в != "id" or т not in глобалі or (к and ТОК[к - 1][1] == "."):
        continue
    if к + 1 < len(ТОК) and ТОК[к + 1][1] == ":" and ТОК[к - 1][1] in ("{", ","):
        continue  # ключ об'єкта
    хто = функція_токена[к] or "<верх>"
    if присвоєння_після(к) and not (ТОК[к - 1][1] in ("let", "const", "var")):
        глобалі[т]["пишуть"].add(хто)
    elif ТОК[к + 1][1] in (".", "[") and any(ТОК[м][1] in ("push", "splice", "set", "delete", "add", "clear", "pop", "shift", "unshift") for м in range(к + 1, min(к + 4, len(ТОК)))):
        глобалі[т]["мутують"].add(хто)
    elif ТОК[к - 1][1] == "delete":
        глобалі[т]["мутують"].add(хто)
    else:
        # запис у властивість: А.б = …, А[б] = …
        м = к + 1
        if ТОК[м][1] == ".":
            м += 2
            if присвоєння_після(м - 1):
                глобалі[т]["мутують"].add(хто)
                continue
        глобалі[т]["читають"].add(хто)

# ── таймери, слухачі, сховища, містП, модель
def де(шаблон):
    return [(рядок(ТОК[к][2]), функція_токена[к] or "<верх>") for к, (в, т, _) in enumerate(ТОК) if в == "id" and т == шаблон and not (к and ТОК[к - 1][1] == "." and шаблон not in ("addEventListener", "removeEventListener", "setItem", "getItem", "removeItem"))]

лічба = {к: де(к) for к in ("setTimeout", "setInterval", "clearTimeout", "clearInterval", "requestAnimationFrame",
                              "addEventListener", "removeEventListener", "setItem", "getItem", "removeItem", "indexedDB",
                              "MutationObserver", "ResizeObserver", "IntersectionObserver", "fetch", "atob", "innerHTML", "outerHTML",
                              "insertAdjacentHTML", "replaceChildren", "JSON")}
лічба["innerHTML"] = [(рядок(ТОК[к][2]), функція_токена[к] or "<верх>") for к, (в, т, _) in enumerate(ТОК) if в == "id" and т == "innerHTML"]
лічба["JSON.parse"] = [(рядок(ТОК[к][2]), функція_токена[к] or "<верх>") for к, (в, т, _) in enumerate(ТОК) if в == "id" and т == "parse" and ТОК[к - 2][1] == "JSON"]
лічба["onclick="] = [(рядок(ТОК[к][2]), функція_токена[к] or "<верх>") for к, (в, т, _) in enumerate(ТОК) if в == "id" and re.fullmatch(r"on[a-z]+", т) and ТОК[к - 1][1] == "." and ТОК[к + 1][1] == "="]
лічба["onX у шаблонах"] = [(рядок(ТОК[к][2]), функція_токена[к] or "<верх>") for к, (в, т, _) in enumerate(ТОК) if в in ("str", "tpl") and re.search(r"\son[a-z]+=", т)]
ключі_сховища = Counter()
for к, (в, т, _) in enumerate(ТОК):
    if в == "id" and т in ("setItem", "getItem", "removeItem") and ТОК[к + 1][1] == "(":
        аргум = ТОК[к + 2]
        ключі_сховища[(т, аргум[1] if аргум[0] in ("str", "tpl") else "<" + аргум[1] + ">")] += 1
містп = Counter()
містп_хто = defaultdict(set)
for к, (в, т, _) in enumerate(ТОК):
    if в == "id" and т == "містП" and ТОК[к + 1][1] == "(" and ТОК[к + 2][0] == "str":
        містп[ТОК[к + 2][1]] += 1
        містп_хто[ТОК[к + 2][1]].add(функція_токена[к] or "<верх>")
модель = [(рядок(ТОК[к][2]), функція_токена[к]) for к, (в, т, _) in enumerate(ТОК) if в == "id" and т == "_дзвінокП" and ТОК[к + 1][1] == "(" and ТОК[к - 1][1] != "function"]

# ── коментарі: рядки й «історії»
ІСТОРІЯ = re.compile(r"рядок\s*\d|рядк[иів]\s*\d|#\d{2,}|\b\d{1,2}\.(0?[1-9]|1[0-2])(\.\d{4})?\b|\bдоти\b|\bраніше\b|\bбуло\b|\bv\d(\.\d)?\b|ЖИВІ-|ПАЧКА|пачк[аи]\s*\d|\bнаряд", re.I)
рядки_ком = set()
рядки_істор = set()
for п, т in КОМ:
    р0 = рядок(п)
    for зсув, ряд in enumerate(т.split("\n")):
        рядки_ком.add(р0 + зсув)
        if ІСТОРІЯ.search(ряд):
            рядки_істор.add(р0 + зсув)
for _, ст in стилі:
    for м in re.finditer(r"/\*.*?\*/", ст, re.S):
        pass
рядки_всього = ТЕКСТ.count("\n") + 1
рядки_ком_css = sum(м.group(0).count("\n") + 1 for _, ст in стилі for м in re.finditer(r"/\*.*?\*/", ст, re.S))
рядки_ком_html = sum(м.group(0).count("\n") + 1 for м in re.finditer(r"<!--.*?-->", розмітка, re.S))
# частка коментарів, що містять маркер історії (на коментар)
ком_з_іст = sum(1 for _, т in КОМ if ІСТОРІЯ.search(т))

# ── повтори функцій: однакове тіло без імені й пробілів; близькі — Жаккар 5-грам токенів ≥ 0,8
def нормоване(а, б, з_іменами=True):
    return [т if (в != "id" or з_іменами) else "I" for в, т, _ in ТОК[а:б + 1]]

точні, групи = defaultdict(list), []
шингли = {}
for ім, вид, а, б in функції:
    if б - а < 30:
        continue
    тіло = нормоване(а, б)
    # без власного імені
    ключ = hashlib.md5(" ".join(т for т in тіло if т != ім).encode()).hexdigest()
    точні[ключ].append(ім)
    сп = нормоване(а, б, False)
    шингли[ім] = {" ".join(сп[к:к + 5]) for к in range(len(сп) - 4)}
близькі = []
імена_ш = sorted(шингли, key=lambda и: len(шингли[и]))
for x, а in enumerate(імена_ш):
    for б in імена_ш[x + 1:]:
        ла, лб = len(шингли[а]), len(шингли[б])
        if лб > ла / 0.8:
            break
        перетин = len(шингли[а] & шингли[б])
        ж = перетин / (ла + лб - перетин)
        if ж >= 0.8:
            близькі.append((а, б, round(ж, 2)))

рез = {
    "рядків": рядки_всього, "байтів": len(ТЕКСТ.encode()),
    "скриптів": len(скрипти), "головний_з_рядка": рядок(головний[0]), "токенів": len(ТОК),
    "функцій_верхніх": len(функції), "з_них_function": sum(1 for ф in функції if ф[1] == "function"),
    "стрілкових_верхніх": sum(1 for ф in функції if ф[1] == "arrow"),
    "змінних_верхніх": Counter(в[1] for в in змінні), "імен_двічі": {ім: к for ім, к in ім_верхні.items() if к > 1},
    "недосяжні": sorted([р for р in реєстр if not р["досяжна"]], key=lambda р: -р["рядків"]),
    "без_згадок": [р["ім"] for р in реєстр if р["згадок"] == 0],
    "коментарів": len(КОМ), "рядків_коментаря_js": len(рядки_ком), "рядків_історії": len(рядки_істор),
    "коментарів_з_історією": ком_з_іст, "рядків_коментаря_css": рядки_ком_css, "рядків_коментаря_html": рядки_ком_html,
    "глобалі": {ім: {"вид": г["вид"], "рядок": г["рядок"], "пишуть": sorted(г["пишуть"]), "мутують": sorted(г["мутують"]),
                     "читають": len(г["читають"])} for ім, г in глобалі.items()},
    "лічба": {к: len(в) for к, в in лічба.items()}, "місця": {к: в for к, в in лічба.items() if к in ("setInterval", "addEventListener", "removeEventListener", "requestAnimationFrame", "MutationObserver", "ResizeObserver", "JSON.parse", "atob", "indexedDB")},
    "ключі_сховища": sorted([[к[0], к[1], в] for к, в in ключі_сховища.items()]),
    "містП": dict(містп.most_common()), "містП_хто": {к: sorted(в) for к, в in містп_хто.items()},
    "дзвінокП": модель,
    "точні_повтори": [в for в in точні.values() if len(в) > 1], "близькі_повтори": близькі,
    "реєстр": реєстр,
    # граф: функція → верхні імена (функції й глобалі), які вона згадує як ідентифікатор
    "граф": {ім: sorted(к for к in сл if not к.startswith("\x00") and (к in імена_ф or к in глобалі) and к != ім)
             for ім, сл in посилання.items()},
}
json.dump(рез, sys.stdout, ensure_ascii=False, indent=0, default=sorted)
пиши = lambda *а: print(*а, file=sys.stderr)
пиши("рядків %d · токенів %d · верхніх функцій %d (function %d, стрілкових %d) · змінних %s" % (
    рядки_всього, len(ТОК), len(функції), рез["з_них_function"], рез["стрілкових_верхніх"], dict(рез["змінних_верхніх"])))
пиши("недосяжних статично: %d функцій, %d рядків; без жодної згадки: %d" % (
    len(рез["недосяжні"]), sum(р["рядків"] for р in рез["недосяжні"]), len(рез["без_згадок"])))
пиши("коментарі: JS %d рядків (історій %d), CSS %d, HTML %d з %d" % (len(рядки_ком), len(рядки_істор), рядки_ком_css, рядки_ком_html, рядки_всього))
пиши("повтори: точних груп %d, близьких пар %d" % (len(рез["точні_повтори"]), len(близькі)))
пиши("лічба:", рез["лічба"])
пиши("містП: %d ендпойнтів, %d викликів; _дзвінокП: %d" % (len(містп), sum(містп.values()), len(модель)))
