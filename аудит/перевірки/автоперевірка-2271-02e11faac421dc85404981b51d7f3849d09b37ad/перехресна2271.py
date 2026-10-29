import contextlib
import io
import json
from pathlib import Path
import runpy
import sys

root = Path(sys.argv[1]).resolve()
base = root.parent
sys.argv = [str(base / 'порівняння2245.py'), str(root / 'джерела')]
with contextlib.redirect_stdout(io.StringIO()):
    old = runpy.run_path(str(base / 'порівняння2245.py'))
old_rows = {s for rows in old['усі'].values() for s in rows}
data = json.loads((base / 'звірка2271.json').read_text(encoding='utf-8'))
new_rows = {f"{Path(e['file']).stem}:{e['line']}" for e in data['all'] if '1' in e['clauses']}
print('Прилад #2245: вузлів', sum(map(len, old['усі'].values())))
print('Прилад #2245: рядків', len(old_rows))
print('Збіг пункту 1:', len(old_rows & new_rows))
print('Пропущено:', sorted(old_rows - new_rows))
code = (base / 'тон_визначення_ps7.py').read_text(encoding='utf-8-sig')
with contextlib.redirect_stdout(io.StringIO()):
    g = {'__file__': str(root / 'джерела/проби/тон_визначення_ps7.py'), '__name__': '__main__'}
    exec(compile(code, g['__file__'], 'exec'), g)
print('Проба ПС-7: обходів', len(g['обходи']))
print('Відмінність рядків проби ПС-7 і приладу #2245:', len(set(g['обходи']) ^ old_rows))
print('Файл композитор_річ:173 — висота взуття:', (root / 'джерела/композитор_річ.py').read_text(encoding='utf-8').splitlines()[172].strip())
