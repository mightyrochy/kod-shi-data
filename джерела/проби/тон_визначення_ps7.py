"""ПС-7: скільки визначень сім'ї й меж тону, скільки обходів поза `колір_тон` (друкує факт; ПІСЛЯ: 1 · 1 · 0)."""
import ast, glob, os
К = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВЛАСНИК = "колір_тон"
МЕЖІ = {"СІГМА_МЕЖІ", "ДУГА_ВІДЛУННЯ", "СЕКТОР_КОЛА", "МЕЖА_БЛИЗЬКИХ", "ТЕПЛИЙ_ПОЛЮС", "СІГМА_ΔH", "_КОЛО", "RELATIONS",
        "ВІКНА_ТОНУ", "ВІКНА_ΔH", "СІМ_Ї_КОЛО", "FAMILIES"}
число = lambda n: isinstance(n, ast.Constant) and isinstance(n.value, (int, float))
дуга = lambda n: isinstance(n, ast.Tuple) and len(n.elts) == 2 and all(число(e) and -1 <= e.value <= 360 for e in n.elts)
ім = lambda n: n.id if isinstance(n, ast.Name) else None
def таблиця_сімей(v):
    """Таблиця «тон → сім'я»: трійки (від, до, ім'я), версії тепла/холодна з дугами або дуги під ключем families."""
    трійки = [x for x in ast.walk(v) if isinstance(x, ast.Tuple) and len(x.elts) == 3 and число(x.elts[0])
              and число(x.elts[1]) and isinstance(x.elts[2], ast.Constant) and isinstance(x.elts[2].value, str)]
    ключі = {k.value for x in ast.walk(v) if isinstance(x, ast.Dict) for k in x.keys if isinstance(k, ast.Constant)}
    ключі |= {k.arg for x in ast.walk(v) if isinstance(x, ast.Call) for k in x.keywords}
    дуг = sum(дуга(x) for x in ast.walk(v))
    return len(трійки) >= 3 or {"тепла", "холодна"} <= ключі and дуг >= 6 or "families" in ключі and дуг >= 6
def обхід_дуги(n):
    """Своя лічба дуги: належність з переходом через 0° (h >= a or h <= b), середина (… % 360) / 2, ширина (д[1] - д[0]) % 360."""
    мод = lambda x: isinstance(x, ast.BinOp) and isinstance(x.op, ast.Mod) and число(x.right) and x.right.value == 360
    if isinstance(n, ast.BinOp) and мод(n) and isinstance(n.left, ast.BinOp) and isinstance(n.left.op, ast.Sub):
        a, b = n.left.left, n.left.right
        return all(isinstance(x, ast.Subscript) for x in (a, b)) and ast.dump(a.value) == ast.dump(b.value)
    if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or) and len(n.values) == 2 \
            and all(isinstance(c, ast.Compare) and len(c.ops) == 1 for c in n.values):
        a, b = n.values
        if not all(isinstance(c.comparators[0], (ast.Name, ast.Subscript, ast.Attribute)) for c in n.values): return False
        return ast.dump(a.left) == ast.dump(b.left) and type(a.ops[0]) in (ast.GtE, ast.Gt) and type(b.ops[0]) in (ast.LtE, ast.Lt)
    return isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and число(n.right) and n.right.value == 2 and any(мод(x) for x in ast.walk(n.left))
таблиці, межі, обходи = [], {}, []
for шлях in sorted(glob.glob(os.path.join(К, "*.py"))):
    м = os.path.basename(шлях)[:-3]
    дерево = ast.parse(open(шлях, encoding="utf-8").read())
    for n in дерево.body:
        if isinstance(n, ast.Assign) and ім(n.targets[0]) != "ITA_BANDS" and таблиця_сімей(n.value): таблиці.append("%s.%s" % (м, ім(n.targets[0])))
        if isinstance(n, ast.Assign) and ім(n.targets[0]) in МЕЖІ: межі.setdefault(ім(n.targets[0]), []).append(м)
    if м != ВЛАСНИК: обходи += ["%s:%d" % (м, x.lineno) for x in ast.walk(дерево) if обхід_дуги(x)]
print("визначень сім'ї (таблиць тон→сім'я):", len(таблиці), таблиці)
print("модулів, що задають межі тону:", len({м for v in межі.values() for м in v}), {k: v for k, v in sorted(межі.items())})
print("обходів (своя належність, середина чи ширина дуги поза %s):" % ВЛАСНИК, len(обходи), обходи)
