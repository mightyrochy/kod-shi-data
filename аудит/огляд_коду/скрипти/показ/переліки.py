"""Переліки показу, що мають копію в Python (за `скрипти/карта/дублі.py`: ≥ 3 рядкові елементи, ≥ 75 % елементів JS
є в Python-переліку, Жаккар ≥ 0,6), і чи копії РІВНІ. Python — усі модулі `джерела/*.py` крім тестів, батарей і приладів.
Запуск з кореня: python3 аудит/огляд_коду/скрипти/показ/переліки.py > переліки.tsv; зведення — у stderr."""
import ast, glob, os, re, sys, warnings
from pathlib import Path
warnings.simplefilter("ignore")
пи = []
for ф in sorted(glob.glob("джерела/*.py")):
    ім = os.path.basename(ф)[:-3]
    if re.match(r"(тест|батарея|test|audit|gate_|measure|проба|стенд)", ім):
        continue
    try:
        t = ast.parse(open(ф, encoding="utf-8").read())
    except SyntaxError:
        continue
    for n in ast.walk(t):
        if isinstance(n, (ast.Tuple, ast.List, ast.Set)):
            s = [e.value for e in n.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]
            if len(s) >= 3 and len(s) == len(n.elts):
                пи.append((ім, n.lineno, frozenset(s)))
        elif isinstance(n, ast.Dict):
            s = [k.value for k in n.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)]
            if len(s) >= 3:
                пи.append((ім, n.lineno, frozenset(s)))
файли = sorted(Path("джерела/показ").glob("*.js"))
текст = "\n".join(ф.read_text(encoding="utf-8") for ф in файли)
адреси = []
for ф in файли:
    адреси.extend((str(ф).replace('\\', '/'), н) for н, _ in enumerate(ф.read_text(encoding="utf-8").split('\n'), 1))
чист = re.sub(r"/\*.*?\*/", lambda m: "\n" * m.group(0).count("\n"), текст, flags=re.S)
чист = re.sub(r"(?m)^\s*//.*$", "", чист)
дж = []
def літерал(т):
    """Відділяє статичний перелік від об'єкта з поточними даними."""
    т = re.sub(r"\b(null|true|false)\b", lambda м: {'null': 'None', 'true': 'True', 'false': 'False'}[м[0]], т)
    т = re.sub(r"([,{]\s*)([\wЀ-ӿ]+)\s*:", r"\1'\2':", т)
    try:
        return ast.literal_eval(т)
    except (SyntaxError, ValueError):
        return None
for m in re.finditer(r"\[([^\[\]]{5,800})\]", чист):
    в = m.group(1)
    s = re.findall(r"['\"]([^'\"\n]{1,40})['\"]", в)
    if len(s) >= 3 and not re.sub(r"['\"][^'\"\n]{1,40}['\"]|[\s,]", "", в):
        дж.append((чист.count("\n", 0, m.start()) + 1, frozenset(s)))
for m in re.finditer(r"\{([^{}]{10,800})\}", чист):
    if літерал(m[0]) is None:
        continue
    s = re.findall(r"(?:^|[,{])\s*['\"]?([\wЀ-ӿ]+)['\"]?\s*:(?!:)", m.group(1))
    if len(s) >= 3 and any(re.search("[Ѐ-ӿ]", x) for x in s):
        дж.append((чист.count("\n", 0, m.start()) + 1, frozenset(s)))
пари = []
for л, js in дж:
    if not any(re.search("[Ѐ-ӿ]", x) for x in js):
        continue
    кращі = []
    for м, пл, ps in пи:
        i = len(js & ps)
        if i >= 3 and i / len(js) >= 0.75:
            кращі.append((i / len(js | ps), м, пл, ps))
    if кращі and max(кращі)[0] >= 0.6:  # поріг Жаккара карти (`дублі.py`): нижче — форма запиту, не перелік
        ж, м, пл, ps = max(кращі)
        пари.append((л, js, ж, м, пл, ps, len({(к[1], к[2]) for к in кращі})))
print("рядок_показу\tел_JS\tpython\tел_Py\tЖаккар\tрівні\tлише_JS\tлише_Py\tкопій_Py")
рівних = 0
for л, js, ж, м, пл, ps, к in sorted(пари):
    рівних += js == ps
    print("%s:%d\t%d\t%s.py:%d\t%d\t%.2f\t%s\t%s\t%s\t%d" % (*адреси[л - 1], len(js), м, пл, len(ps), ж, "так" if js == ps else "ні",
          ",".join(sorted(js - ps))[:80], ",".join(sorted(ps - js))[:80], к))
print("JS-переліків з копією в Python: %d (різних Python-переліків %d); рівних множин %d, різних %d" % (
    len(пари), len({(п[3], п[4]) for п in пари}), рівних, len(пари) - рівних), file=sys.stderr)
