# -*- coding: utf-8 -*-
"""6150: `ярлик` кожного виклику `trace.запис`/`палітри._слід` — код із `ЯРЛИКИ_СЛІДУ`, без кирилиці й без висячих кодів."""
import ast, glob, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import внутрішня_мова as М
кир = re.compile(r"[а-яіїєґ]", re.I)
літерали, кирилиця, кількість = set(), [], 0
for ф in sorted(glob.glob("*.py")):
    джерело = open(ф, encoding="utf-8").read()
    for н in ast.walk(ast.parse(джерело)):
        if not (isinstance(н, ast.Call) and len(н.args) >= 2):
            continue
        trace_запис = isinstance(н.func, ast.Attribute) and н.func.attr == "запис" and getattr(н.func.value, "id", "") != "_ПЗ" and not ф.startswith("trace")
        if not (trace_запис or getattr(н.func, "id", None) == "_слід"):
            continue
        кількість += 1
        для = [н.args[1]] + ([н.args[1].body, н.args[1].orelse] if isinstance(н.args[1], ast.IfExp) else [])
        for а in для:
            if isinstance(а, ast.Constant) and isinstance(а.value, str):
                літерали.add(а.value)
                if кир.search(а.value): кирилиця.append("%s:%d" % (ф, н.lineno))
висячі = sorted(л for л in літерали if л not in М.ЯРЛИКИ_СЛІДУ and not л.startswith("_"))
assert not кирилиця, кирилиця
print("викликів=%d · літеральних_ярликів=%d · з_кирилицею=0 · поза_словником=%s · визначень=%d"
      % (кількість, len(літерали), висячі or 0, len(М.ЯРЛИКИ_СЛІДУ)))
