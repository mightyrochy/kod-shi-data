# -*- coding: utf-8 -*-
"""Е2-точка-виходу-всі-шляхи: лічба УСІХ неконстантних записів у екран поза точкою виходу (`показ/мовний_шар.js`, блок «ОДНА
ТОЧКА ВИХОДУ»). Екран = `.textContent/.innerHTML/.placeholder/.title/.alt/…=`, `createTextNode`, `insertAdjacent*`, `new Option`,
`setAttribute('aria-label'|…)`, третій аргумент `ел(тег, клас, текст)`. Стале = рядок-літерал, число, `Number()`, `.length`, `Math.*`,
`.toFixed/.toLocaleString`, умова між сталими (умову не міряємо); решта — обхід. Друкує факт: обходи, а з --сталі — ще й перелік сталих.
Запуск: python3 проби/текст_жінці_записи.py [тека-джерел] [--сталі]; ДО — на теці з `origin/main` (git worktree)."""
import os, re, sys
ТУТ = next((a for a in sys.argv[1:] if not a.startswith("--")), os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ТОЧКА = ("текстЖінціП", "збійЖінціП", "діагнозВласникаП", "елЖінціП", "елНазваП", "їїСловаЕлП", "розміткаЖінціП", "назваЖінціП", "їїСловаП")
ВИХІД = re.compile(r"\.(?:textContent|innerHTML|innerText|outerHTML|placeholder|title|alt|label|nodeValue)\s*\+?=(?!=)\s*()"
                   r"|(?<![\w.])(?:textContent|innerHTML|placeholder|title|alt)\s*:(?!:)\s*()|\bcreateTextNode\(()|\binsertAdjacent(?:HTML|Text)\(\s*[^,()]+,\s*()|\bnew Option\(()"
                   r"|\bsetAttribute\(\s*'(?:aria-label|title|placeholder|alt)'\s*,\s*()|(?<![\w.])ел\(\s*[^,()]+,\s*[^,()]+,\s*()")
ЛЕКС = re.compile(r"'(?:[^'\\\n]|\\.)*'|\"(?:[^\"\\\n]|\\.)*\"|`(?:[^`\\$]|\\.|\$(?!\{))*`|\d[\d.]*|[^\W\d][\w]*|\|\||&&|\?\?|\S")
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
обходи, сталі = [], []
for ф in sorted(os.listdir(os.path.join(ТУТ, "показ"))):
    if not ф.endswith(".js"): continue
    к = open(os.path.join(ТУТ, "показ", ф), encoding="utf8").read()
    к = re.sub(r"/\*.*?\*/", lambda м: re.sub(r"[^\n]", " ", м.group(0)), к, flags=re.S)
    к = re.sub(r"(?m)(?<![:'\"`\\])//.*$", lambda м: " " * len(м.group(0)), к)
    точка = [(м.start(), тіло(к, к.index("{", м.end()))) for м in re.finditer(r"(?m)^function (?:%s)\(" % "|".join(ТОЧКА), к)]
    for м in ВИХІД.finditer(к):
        р = к[м.end():кінець(к, м.end(), м.group(1) is None)].strip()
        if any(а <= м.start() < б for а, б in точка) or re.match(r"(?:%s)\(" % "|".join(ТОЧКА), р): continue
        (сталі if стале(р) else обходи).append("%s:%d  %s" % (ф, к.count("\n", 0, м.start()) + 1, " ".join(р.split())[:90]))
print("неконстантних записів в екран поза точкою виходу:", len(обходи), "· сталих (написи, числа):", len(сталі))
for о in обходи + (сталі if "--сталі" in sys.argv else []): print(" ", о)
