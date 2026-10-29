"""Перевірка ПС-7 (#2245): власна арифметика кута тону поза `колір_тон` у модулях продукту (джерела/*.py, без проб і
приладів) — ширше за `проби/тон_визначення_ps7.py`: будь-які операнди (виклики float(), імена, підписки).
Види: ширина/зсув — (x − y) % 360; кут — 360 − |x − y| чи min(d, 360 − d); середина — (… ) / 2 з % 360 поруч;
знакова різниця — (x − y + 180) % 360 − 180; належність — x >= a or x <= b."""
import ast, glob, os, sys
К = sys.argv[1]
число = lambda n, v=None: isinstance(n, ast.Constant) and isinstance(n.value, (int, float)) and (v is None or n.value == v)
мод360 = lambda n: isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and число(n.right, 360)
def вид(n):
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub) and мод360(n.left) and число(n.right, 180): return "знакова"
    if мод360(n) and isinstance(n.left, ast.BinOp) and isinstance(n.left.op, ast.Add) and число(n.left.right, 180) \
            and isinstance(n.left.left, ast.BinOp) and isinstance(n.left.left.op, ast.Sub): return None   # частина знакової
    if мод360(n) and isinstance(n.left, ast.BinOp) and isinstance(n.left.op, ast.Sub) and not число(n.left.right): return "ширина/зсув"
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Sub) and число(n.left, 360) and not число(n.right): return "кут"
    if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Div) and число(n.right, 2) and any(мод360(x) for x in ast.walk(n.left)): return "середина"
    if мод360(n) and isinstance(n.left, ast.BinOp) and isinstance(n.left.op, ast.Div) and число(n.left.right, 2): return "середина"
    if isinstance(n, ast.BoolOp) and isinstance(n.op, ast.Or) and len(n.values) == 2 and all(isinstance(c, ast.Compare) and len(c.ops) == 1 for c in n.values):
        a, b = n.values
        if ast.dump(a.left) == ast.dump(b.left) and type(a.ops[0]) in (ast.GtE, ast.Gt) and type(b.ops[0]) in (ast.LtE, ast.Lt) \
                and not число(a.comparators[0]) and not число(b.comparators[0]): return "належність"
    return None
усі = {}
for шлях in sorted(glob.glob(os.path.join(К, "*.py"))):
    м = os.path.basename(шлях)[:-3]
    if м == "колір_тон": continue
    for x in ast.walk(ast.parse(open(шлях, encoding="utf-8").read())):
        в = вид(x)
        if в: усі.setdefault(в, []).append("%s:%d" % (м, x.lineno))
print("усього:", sum(map(len, усі.values())), {в: len(v) for в, v in sorted(усі.items())})
for в, v in sorted(усі.items()): print(в, len(set(v)), sorted(set(v)))
