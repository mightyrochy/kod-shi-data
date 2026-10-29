# -*- coding: utf-8 -*-
"""Е2-точка-виходу-всі-шляхи: лічба УСІХ записів у екран поза точкою виходу (`показ/мовний_шар.js`, блок «ОДНА ТОЧКА ВИХОДУ»).
Файли: `показ/*.js` і вбудовані скрипти `показ.html` (без `src`). Три класи записів:
  ТЕКСТ — `.textContent/.innerHTML/.placeholder/.title/.alt/.text/…=`, `createTextNode`, `insertAdjacent*`, `new Option`,
    `setAttribute('aria-label'|…)`, третій аргумент `ел(тег, клас, текст)`, `alert/confirm/prompt`, `SpeechSynthesisUtterance`,
    рядкові аргументи `append/prepend/replaceChildren/before/after/replaceWith`. Стале = рядок-літерал, число, `Number()`, `.length`,
    `Math.*`, `.toFixed/.toLocaleString`, умова між сталими, виклик самої точки; шаблон з `${}` і «виклик точки + сире» — НЕ стале.
    Решта — обхід (вимога: 0).
  ПОЛЕ — `.value =`: значення поля вводу. Кожне має стояти в `проби/текст_жінці_поля.txt` (файл ⇥ вираз ⇥ причина: її слова, ключ вибору,
    стан форми, вхід коду) — нове значення поза переліком є обходом, а не мовчить.
  ВУЗОЛ — аргумент `append(…)` без ознак рядка: ідентифікатор мусить бути присвоєний вузлом (`ел(…)`, `createElement`, `$()`, …) у тому ж файлі.
Запуск: python3 проби/текст_жінці_записи.py [тека-джерел] [--сталі]; ДО — на теці з `origin/main` (git worktree)."""
import os, re, sys
ТУТ = next((a for a in sys.argv[1:] if not a.startswith("--")), os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ТОЧКА = ("текстЖінціП", "збійЖінціП", "діагнозВласникаП", "елЖінціП", "елНазваП", "їїСловаЕлП", "розміткаЖінціП", "назваЖінціП", "їїСловаП")
ТОЧКА_АЛЬТ = "|".join(ТОЧКА)
ТЕКСТ = re.compile(r"\.(?:textContent|innerHTML|innerText|outerHTML|placeholder|title|alt|label|text|nodeValue)\s*\+?=(?!=)\s*()"
                   r"|(?<![\w.])(?:textContent|innerHTML|placeholder|title|alt)\s*:(?!:)\s*()|\bcreateTextNode\(()|\binsertAdjacent(?:HTML|Text)\(\s*[^,()]+,\s*()|\bnew Option\(()"
                   r"|\bsetAttribute\(\s*'(?:aria-label|title|placeholder|alt)'\s*,\s*()|(?<![\w.])ел\(\s*[^,()]+,\s*[^,()]+,\s*()"
                   r"|(?<![\w.])(?:alert|confirm|prompt)\(()|\bSpeechSynthesisUtterance\(()")
ПОЛЕ = re.compile(r"\.value\s*\+?=(?!=)\s*()")
ВУЗОЛ = re.compile(r"\.(?:append|prepend|replaceChildren|before|after|replaceWith)\(()")
ЛЕКС = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\$]|\\.|\$(?!\{))*`|\d[\d.]*|[^\W\d][\w]*|\|\||&&|\?\?|\S")
ВУЗЛОВІ_ПОЧАТКИ = re.compile(r"(?:ел|елЖінціП|елНазваП|їїСловаЕлП|\$|document\.createElement|document\.getElementById|[\w.$]+\.querySelector|[\w.$]+\.cloneNode|new\s+\w+|силуетКадру|рендерКартку|document\.createDocumentFragment)\(")
def кінець(к, і, кома):          # межа виразу: `;`/закривна дужка/(кома) на глибині 0 або перенос без продовження
    д = 0; q = None; j = і
    while j < len(к):
        c = к[j]
        if q:
            j += 2 if c == "\\" else 1
            if c == q: q = None
            continue
        if c in "'\"`": q = c
        elif c in "([{": д += 1
        elif c in ")]}":
            if д == 0: break
            д -= 1
        elif c == ";" and д == 0 or (c == "," and д == 0 and кома): break
        elif c == "\n" and д == 0 and not re.search(r"[+,?:&|(]\s*$", к[і:j]) and not re.match(r"\s*[+?:&|.]", к[j + 1:]): break
        j += 1
    return j
def тіло(к, і):                  # кінець тіла функції: парна `}`
    д = 0
    for j in range(і, len(к)):
        д += (к[j] == "{") - (к[j] == "}")
        if д == 0: return j
def цілий_виклик_точки(р):       # вираз ЦІЛКОМ є викликом точки: `текстЖінціП(…)`; `текстЖінціП(…) + сире` — ні
    м = re.match(r"(?:%s)\(" % ТОЧКА_АЛЬТ, р)
    if not м: return False
    д = 0; q = None
    for j in range(м.end() - 1, len(р)):
        c = р[j]
        if q:
            if c == "\\": continue
            if c == q: q = None
            continue
        if c in "'\"`": q = c
        elif c in "([{": д += 1
        elif c in ")]}":
            д -= 1
            if д == 0: return not р[j + 1:].strip()
    return False
def стале(в):
    т = ЛЕКС.findall(в); п = [0]
    def дивись(): return т[п[0]] if п[0] < len(т) else ""
    def бери(): п[0] += 1; return т[п[0] - 1]
    def вираз():
        c = двійк()
        if дивись() == "?":
            бери(); a = вираз(); бери(); b = вираз(); return a and b
        return c
    def двійк():
        c = первинне()
        while дивись() in ("+", "-", "*", "/", "%", "||", "&&", "??", "<", ">", "="): бери(); c = первинне() and c
        return c
    def первинне():
        x = бери() if п[0] < len(т) else ""
        if x in ("!", "-", "+"): return первинне()
        if x in ТОЧКА and дивись() == "(":
            бери(); д = 1
            while д and п[0] < len(т): z = бери(); д += (z in "([") - (z in ")]")
            return True
        if x == "`": return False    # шаблон з ${…} — не стале
        if x[:1] in "'\"`" or x[:1].isdigit(): return True
        ланц, ок = [x], x in ("Number", "Math")
        if x == "(": ок = вираз(); бери() if дивись() == ")" else 0
        if x == "[":
            д = 1
            while д and п[0] < len(т): z = бери(); д += (z == "[") - (z == "]")
        while дивись() in (".", "(", "["):
            o = бери()
            if o == ".": ланц.append(бери())
            else:
                д = 1
                while д and п[0] < len(т): z = бери(); д += (z in "([") - (z in ")]")
        return ок or ланц[-1] in ("length", "toFixed", "toLocaleString", "Number")
    return вираз() if т else True
def аргументи(р):                # верхній рівень, по комі
    вих, д, q, поч = [], 0, None, 0
    for j, c in enumerate(р):
        if q:
            if c == q and р[j - 1] != "\\": q = None
            continue
        if c in "'\"`": q = c
        elif c in "([{": д += 1
        elif c in ")]}": д -= 1
        elif c == "," and д == 0: вих.append(р[поч:j].strip()); поч = j + 1
    вих.append(р[поч:].strip())
    return [а for а in вих if а]
def вузол(арг, к, поз):               # аргумент append — вузол: має ознак рядка не мати й бути присвоєним вузлом
    а = арг.lstrip(".").strip()
    if ВУЗЛОВІ_ПОЧАТКИ.match(а): return True
    if re.search(r"""['"`]|\+|String\(|\.join\(|\.text\b""", а): return False
    if а.startswith("..."): а = а[3:]
    ід = re.match(r"[\w$]+", а)
    if not ід: return True
    if re.match(r"[\w$]+\(", а): return bool(ВУЗЛОВІ_ПОЧАТКИ.match(а)) or а.startswith(("силуетКадру", "створити", "малювати"))
    присвоєння = [х.strip() for х in re.findall(r"(?:(?:const|let|var)\s+|,\s*)%s\s*=\s*([^;\n]{0,80})" % re.escape(ід.group(0)), к[:поз])][-1:]
    вузловий = lambda х: bool(ВУЗЛОВІ_ПОЧАТКИ.match(х) or re.match(r"[\w.$]+\.(?:firstChild|lastChild|children|childNodes)", х))
    return bool(присвоєння) and all(вузловий(х) for х in присвоєння)
ПОЛЯ = {}
_шлях = os.path.join(os.path.dirname(os.path.abspath(__file__)), "текст_жінці_поля.txt")
if os.path.exists(_шлях):
    for рядок in open(_шлях, encoding="utf8"):
        if рядок.strip() and not рядок.startswith("#"):
            ч = рядок.rstrip("\n").split("\t")
            if len(ч) >= 3: ПОЛЯ[(ч[0], ч[1])] = ч[2]
джерела = []                      # (ім'я, код, зсув рядків)
for ф in sorted(os.listdir(os.path.join(ТУТ, "показ"))):
    if ф.endswith(".js"): джерела.append((ф, open(os.path.join(ТУТ, "показ", ф), encoding="utf8").read(), 0))
_html = os.path.join(ТУТ, "показ.html")
if os.path.exists(_html):
    сирий = open(_html, encoding="utf8").read()
    for м in re.finditer(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", сирий, re.S):
        джерела.append(("показ.html", м.group(1), сирий.count("\n", 0, м.start(1))))
обходи, сталі, поля_ок, поля_нові, вузли = [], [], [], [], 0
for ім, к, зсув in джерела:
    к = re.sub(r"/\*.*?\*/", lambda м: re.sub(r"[^\n]", " ", м.group(0)), к, flags=re.S)
    к = re.sub(r"(?m)(?<![:'\"`\\])//.*$", lambda м: " " * len(м.group(0)), к)
    точка = [(м.start(), тіло(к, к.index("{", м.end()))) for м in re.finditer(r"(?m)^function (?:%s)\(" % ТОЧКА_АЛЬТ, к)]
    рядок = lambda м: к.count("\n", 0, м.start()) + 1 + зсув
    в_точці = lambda м: any(а <= м.start() < б for а, б in точка)
    for м in ТЕКСТ.finditer(к):
        р = к[м.end():кінець(к, м.end(), м.group(1) is None)].strip()
        if в_точці(м) or цілий_виклик_точки(р): continue
        (сталі if стале(р) else обходи).append("%s:%d  %s" % (ім, рядок(м), " ".join(р.split())[:90]))
    for м in ПОЛЕ.finditer(к):
        р = " ".join(к[м.end():кінець(к, м.end(), False)].split())
        if в_точці(м) or стале(р) or цілий_виклик_точки(р): continue
        (поля_ок if (ім, р) in ПОЛЯ else поля_нові).append("%s:%d  %s" % (ім, рядок(м), р[:90]))
    for м in ВУЗОЛ.finditer(к):
        р = к[м.end():кінець(к, м.end(), False)].strip()
        if в_точці(м): continue
        for арг in аргументи(р):
            if вузол(арг, к, м.start()): вузли += 1; continue
            (сталі if стале(арг) else обходи).append("%s:%d  append: %s" % (ім, рядок(м), " ".join(арг.split())[:80]))
обходи += ["%s  (значення поля поза переліком проби/текст_жінці_поля.txt)" % п for п in поля_нові]
print("неконстантних записів в екран поза точкою виходу:", len(обходи), "· сталих (написи, числа):", len(сталі),
      "· полів `.value` у переліку:", len(поля_ок), "· вузлів у append:", вузли)
for о in обходи + (сталі if "--сталі" in sys.argv else []) + (["поле " + п for п in поля_ок] if "--поля" in sys.argv else []): print(" ", о)
