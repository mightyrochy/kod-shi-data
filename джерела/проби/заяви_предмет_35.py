"""3.5: AST-лічба предметів заяви; аргумент — SHA для ДО, без нього — робоче дерево."""
import ast, pathlib, subprocess, sys
root = pathlib.Path(__file__).resolve().parents[1]
ref = sys.argv[1] if len(sys.argv) > 1 else None
paths = subprocess.check_output(['git', '-c', 'core.quotepath=off', 'ls-tree', '-r', '--name-only', ref, 'джерела'], text=True).splitlines() if ref else []
files = [p for p in paths if p.endswith('.py') and p.count('/') == 1] if ref else [str(p) for p in root.glob('*.py')]
count_codes = {'edge_branch_absent_in_catalogue', 'scheme_colour_lies_in_kinds', 'costume_one_genre_everywhere',
               'named_metal_is_detail_not_surface', 'named_metal_reads_other_tone_on_frame', 'no_third_piece_dressed_not_styled'}
all_calls, subjects, counts, missing, modules = 0, 0, 0, [], set()
for path in files:
    src = subprocess.check_output(['git', 'show', ref + ':' + path], text=True) if ref else pathlib.Path(path).read_text()
    for n in ast.walk(ast.parse(src)):
        if not isinstance(n, ast.Call) or not ((isinstance(n.func, ast.Attribute) and n.func.attr == 'заява') or (isinstance(n.func, ast.Name) and n.func.id == 'заява')): continue
        all_calls += 1; modules.add(path)
        kw = {k.arg: k.value for k in n.keywords}
        if not {'item', 'items'} & kw.keys(): continue
        subjects += 1
        code = n.args[0].value if n.args and isinstance(n.args[0], ast.Constant) else None
        if code in count_codes: counts += 1; continue
        if {'item_id', 'item_ids'} & kw.keys(): continue
        val = kw.get('item', kw.get('items'))
        nested = any(isinstance(x, ast.keyword) and x.arg == 'item_id' for x in ast.walk(val))
        helper = any(isinstance(x, ast.Call) and isinstance(x.func, ast.Name) and x.func.id in ('_річ_заяви', '_речі_кодом') for x in ast.walk(val))
        if not nested and not helper: missing.append((path, n.lineno, code))
print('виклики', all_calls, 'модулі', len(modules), 'item/items', subjects, 'з них лічби', counts,
      'предмети без ід', len(missing))
for path, line, code in missing: print(path, line, code)
