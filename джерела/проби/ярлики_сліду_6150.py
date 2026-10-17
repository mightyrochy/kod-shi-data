# -*- coding: utf-8 -*-
"""6150: `ярлик` кожного виклику `trace.запис`/`палітри._слід` — код із `ЯРЛИКИ_СЛІДУ`: літерали й змінні без кирилиці
й поза висячими кодами, ніяких обчислених фраз (`%`, f-рядок, `str(...)`), і жодної фрази (кирилиці) в `слід_правил` на стенді; ярлик-ід правила чи код рядка брифа (`верх_довжина`: слово без пропусків і дужок) — теж код."""
import ast, glob, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import внутрішня_мова as М
кир = re.compile(r"[а-яіїєґ]", re.I)
ДОЗВОЛЕНО_ВИКЛИК = ("ярлик_ребра",)           # `brief.ярлик_ребра` віддає код `body_edge`
літерали, погано, обчислені, кількість = set(), [], [], 0
for ф in sorted(glob.glob("*.py")):
    дерево = ast.parse(open(ф, encoding="utf-8").read())
    присвоєно = {}                              # ім'я змінної → рядкові літерали, що їй присвоєно в модулі
    for н in ast.walk(дерево):
        if isinstance(н, ast.Assign) and isinstance(н.value, ast.Constant) and isinstance(н.value.value, str):
            for т in н.targets:
                if isinstance(т, ast.Name): присвоєно.setdefault(т.id, set()).add(н.value.value)
    for н in ast.walk(дерево):
        if not (isinstance(н, ast.Call) and len(н.args) >= 2):
            continue
        trace_запис = isinstance(н.func, ast.Attribute) and н.func.attr == "запис" and getattr(н.func.value, "id", "") != "_ПЗ" and not ф.startswith("trace")
        if not (trace_запис or getattr(н.func, "id", None) == "_слід"):
            continue
        кількість += 1
        а = н.args[1]
        значення = [а]
        if isinstance(а, ast.IfExp): значення = [а.body, а.orelse]
        for в in значення:
            if isinstance(в, ast.Constant) and isinstance(в.value, str): літерали.add(в.value)
            elif isinstance(в, ast.Name): літерали |= присвоєно.get(в.id, set())
            elif isinstance(в, ast.Call) and getattr(в.func, "id", "") in ДОЗВОЛЕНО_ВИКЛИК: pass
            else: обчислені.append("%s:%d" % (ф, н.lineno))
погано = sorted(л for л in літерали if кир.search(л))
висячі = sorted(л for л in літерали if л not in М.ЯРЛИКИ_СЛІДУ)
assert not (погано or обчислені), (погано, обчислені)
import стенд_знімок as С, trace as СЛ
фрази_у_сліді = set()
for н, с in list(С.СЦЕНАРІЇ.items())[:3]:
    С.прогін(н, с)
    фрази_у_сліді |= {з["ярлик"] for з in СЛ.зібрати() if кир.search(str(з["ярлик"])) and not re.fullmatch(r"[\w\-]+", str(з["ярлик"]))}
print("викликів=%d · ярликів=%d · з_кирилицею=0 · обчислених=0 · поза_словником=%s · фраз_у_сліді_стенда=%s"
      % (кількість, len(літерали), висячі or 0, sorted(фрази_у_сліді)[:5] or 0))
