import contextlib
import importlib.util
import io
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location('prylad', root / 'джерела/прилади/корінь_річ_колір_межі.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
fixture = root.parent / 'контроль2271'
src = fixture / 'джерела'
src.mkdir(parents=True, exist_ok=True)
source = '''def сім_я_тону(h):
    return int(h / 30)

def той_самий(h1, h2):
    return abs(h1 - h2) < 12

ВІКНА = {
    "червоний": (10, 90, 15, 80, (0, 40)),
    "зелений": (10, 90, 15, 80, (90, 160)),
    "синій": (10, 90, 15, 80, (220, 280)),
}
'''
for name in ('колір_тон.py', 'колір_відношення.py'):
    (src / name).write_text(source, encoding='utf-8')
js = src / 'показ' / 'колір.js'
js.parent.mkdir(exist_ok=True)
js.write_text('''const ВІКНА = {
  червоний: [10, 90, 15, 80, [0, 40]],
  зелений: [10, 90, 15, 80, [90, 160]],
  синій: [10, 90, 15, 80, [220, 280]]
};
function уДузі(h, lo, hi) {
  return lo <= hi ? lo <= h && h <= hi : h >= lo || h <= hi;
}
''', encoding='utf-8')
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    code = m.головна([str(fixture), '--шляхи'])
print('Контрольне дерево: два однакові Python-файли та JS з ручними вікнами й власною дугою.')
print(buf.getvalue(), end='')
print('код:', code)
for name in ('колір_тон.py', 'колір_відношення.py'):
    lines = [s for s in buf.getvalue().splitlines() if name + ':' in s]
    print(name + ': рядків виводу ' + str(len(lines)))
print('показ/колір.js: рядків виводу', sum('колір.js:' in s for s in buf.getvalue().splitlines()))
for name in ('numpy', 'PIL', 'playwright'):
    print('залежність', name, importlib.util.find_spec(name) is not None)
