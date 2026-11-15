"""Рядки «неперевіреного» руки 1, які бачить жінка (рядки «→» після `hand_1.code_unknowns · питання.N`), за класом заяви:
службовий — код поза `внутрішня_мова.ЇЙ_У_НЕПЕРЕВІРЕНОМУ` (гілка), її — у ньому. Аргументи: <джерела гілки> <лог.txt>…"""
import re, sys
sys.path.insert(0, sys.argv[1]); import внутрішня_мова as В
for ф in sys.argv[2:]:
    рядки, код = [], None
    for р in open(ф, encoding="utf-8", errors="replace"):
        м = re.match(r"\s+· hand_1\.code_unknowns · питання[^:]*: (\{.*)", р)
        if м:
            код = ",".join(dict.fromkeys(re.findall(r'"code":"([a-z_]+)"', м.group(1)))); continue
        м = re.match(r"\s+→ (.*)", р)
        if м and код is not None:
            рядки.append((код, м.group(1))); код = None
    служб = [(к, т) for к, т in рядки if any(c not in В.ЇЙ_У_НЕПЕРЕВІРЕНОМУ for c in к.split(","))]
    print("%s: рядків %d, службових %d" % (ф, len(рядки), len(служб)))
    for к, т in рядки: print("   %s %s — %s" % ("✗" if (к, т) in служб else "·", к, т[:150]))
