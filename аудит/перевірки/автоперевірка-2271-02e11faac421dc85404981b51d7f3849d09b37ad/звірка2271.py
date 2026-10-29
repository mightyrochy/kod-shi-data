import importlib.util
import json
from pathlib import Path
import random
import sys

root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('prylad', root / 'джерела/прилади/корінь_річ_колір_межі.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
items = list(m.файли(str(root)))
names = m.імена_визначень(str(root))
found = m.Збір()
for path, rel, kind in items:
    if kind == 'py':
        m.обхід_python(path, rel, found, names)
    else:
        m.обхід_js(path, rel, found)
rows = sorted(found.м)
selected = random.Random(2271).sample(rows, 20)
absent = [r for p, r, k in items if r not in {f for f, l in rows}]
negative = random.Random(2271).sample(sorted(absent), 20)
data = {'total': len(rows), 'sample': [], 'negative': negative, 'all': []}
for f, l in selected:
    lines = (root / f).read_text(encoding='utf-8').splitlines()
    entry = {'file': f, 'line': l, 'clauses': found.м[(f, l)]['пункти'], 'source': '\n'.join(f'{i+1}: {lines[i]}' for i in range(max(0,l-3), min(len(lines), l+2)))}
    data['sample'].append(entry)
for f, l in rows:
    data['all'].append({'file': f, 'line': l, 'clauses': found.м[(f, l)]['пункти']})
output = root.parent / 'звірка2271.json'
output.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in data.items() if k != 'all'}, ensure_ascii=False, indent=2))
