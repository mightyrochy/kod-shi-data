"""Відтворення Д11 на точній голові PR; допоміжні проби прибираються після виміру."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

корінь = Path(sys.argv[1]).resolve()
вихід = Path(sys.argv[2]).resolve()
вихід.mkdir(parents=True, exist_ok=True)
модуль = корінь / 'джерела/прилади/лічба_проб.py'
env = dict(os.environ, NYTOK='2', STELYA='15', PYTHONIOENCODING='utf-8')
перший = корінь / 'джерела/проби/review2707_once.py'
другий = корінь / 'джерела/проби/review2707_neighbor.py'
проби = ['джерела/проби/' + п.name for п in (перший, другий)]
маркер = вихід / 'вже_писала'
початкові = {ім: (корінь / ім).read_bytes() for ім in ('README.md', 'AGENTS.md')}

def git(*арг):
    return subprocess.run(['git', *арг], cwd=корінь, capture_output=True, check=True).stdout

if git('rev-parse', 'HEAD').decode().strip() != 'ac717e38f62c33669f9c1093dfe68365e834357b':
    raise SystemExit('Потрібне тимчасове дерево точної голови PR #2707')
if git('status', '--porcelain').strip() or перший.exists() or другий.exists():
    raise SystemExit('Потрібне чисте тимчасове дерево без допоміжних проб')

def прогін(назва, once=True, partial=False):
    if маркер.exists():
        маркер.unlink()
    перший.write_text(
        'from pathlib import Path\nimport time\ntime.sleep(0.4)\n'
        f'm = Path({str(маркер)!r})\n'
        + ('if not m.exists():\n' if once else 'if True:\n')
        + '    m.write_text("1")\n'
        + f'    p = Path({str(корінь / "README.md")!r})\n'
        + '    p.write_bytes(p.read_bytes() + b"\\nreview2707\\n")\n'
        + (f'    p = Path({str(корінь / "AGENTS.md")!r})\n'
           '    p.write_bytes(p.read_bytes() + b"\\nreview2707\\n")\n' if partial else ''),
        encoding='utf-8')
    другий.write_text(
        'from pathlib import Path\nimport time\ntime.sleep(1.4)\n'
        + (f'p = Path({str(корінь / "README.md")!r})\n'
           'p.write_bytes(p.read_bytes() + b"\\nneighbor2707\\n")\n' if partial else ''),
        encoding='utf-8')
    журнал = вихід / (назва + '.jsonl')
    команда = [sys.executable, '-X', 'utf8', str(модуль), '--гейт', '--лише', *проби]
    р = subprocess.run(команда, cwd=корінь / 'джерела', env=dict(env, ZVIT=str(журнал)),
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=90)
    (вихід / (назва + '.txt')).write_text(р.stdout + '\nSTDERR:\n' + р.stderr, encoding='utf-8')
    останні = {}
    if журнал.exists():
        for рядок in журнал.read_text(encoding='utf-8').splitlines():
            z = json.loads(рядок)
            останні[z['проба']] = z
    print(назва, 'rc', р.returncode, json.dumps(останні, ensure_ascii=False))
    for рядок in р.stdout.splitlines():
        if рядок.startswith(('проб ', 'дерево після', '  ✗ ПООДИНЦІ')):
            print(рядок)
    print('байти_повернуто', all((корінь / ім).read_bytes() == в for ім, в in початкові.items()))

try:
    if '--лише-індекс' not in sys.argv:
        прогін('одноразовий')
        прогін('постійний', once=False)
        прогін('частковий_збіг', partial=True)
finally:
    for п in (перший, другий):
        п.unlink(missing_ok=True)
    for ім, в in початкові.items():
        if (корінь / ім).read_bytes() != в:
            (корінь / ім).write_bytes(в)

# Окремо перевіряється обіцяне збереження вже брудного дерева та індексу.
спец = importlib.util.spec_from_file_location('лічба2707', модуль)
лічба = importlib.util.module_from_spec(спец)
спец.loader.exec_module(лічба)
файл = корінь / 'README.md'
try:
    файл.write_bytes(початкові['README.md'] + b'\nuser staged edit\n')
    робочий_до = файл.read_bytes()
    git('add', '--', 'README.md')
    індекс_до = git('show', ':README.md')
    дерево = лічба.Дерево()
    файл.write_bytes(початкові['README.md'] + b'\nprobe staged edit\n')
    git('add', '--', 'README.md')
    зміни = дерево.зміни()
    дерево.повернути(зміни)
    результат = dict(зміни=зміни, робочий_файл_повернуто=файл.read_bytes() == робочий_до,
                     індекс_повернуто=git('show', ':README.md') == індекс_до,
                     залишок=дерево.зміни())
    дерево.прибрати()
    print('індекс', json.dumps(результат, ensure_ascii=False))
    (вихід / 'індекс.json').write_text(json.dumps(результат, ensure_ascii=False, indent=2), encoding='utf-8')
finally:
    git('restore', '--source=HEAD', '--staged', '--worktree', '--', 'README.md')
print('фінальний_git_status', git('status', '--porcelain').decode('utf-8'))
