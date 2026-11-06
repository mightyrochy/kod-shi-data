"""Е3-сила-правила, п.1а, частина 2 (`суд_від_моделі.py`): батарея й проби сімей місць одним запуском, до кінця.

python3 аудит/проби/е3_сила_правила/суд_перевірки.py [<дерево>] [--лише <проба> …]
<дерево> — корінь робочого дерева (типово — це). Сім'ї — `pal_*`, `col_*`, `cra_*`, `сила_*` і три проби місць
K-PAL-03 (`н1_схема_не_її`, `схема_нейтральна_роль`, `дріт_сирота_2882`); кроки йдуть по чотири паралельно.
`--лише` — лише названі проби (повтор упалих на іншому дереві). Коди й хвости — у суд_перевірки.json поруч
(для іншого дерева — у /tmp/суд_перевірки_база.json). Повні журнали — у /tmp/суд_перевірки_<дерево>_NN.log.
"""
import json, os, pathlib, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

тут = pathlib.Path(__file__).resolve()
арг = sys.argv[1:]
лише = арг[арг.index('--лише') + 1:] if '--лише' in арг else None
арг = арг[:арг.index('--лише')] if '--лише' in арг else арг
root = pathlib.Path(арг[0]).resolve() if арг else тут.parents[3]
src = root / 'джерела'
своє = root == тут.parents[3]
out = тут.parent / 'суд_перевірки.json' if своє else pathlib.Path('/tmp/суд_перевірки_база.json')
мітка = 'голова' if своє else 'база'
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', NODE_PATH=str(src / 'node_modules'))
steps = [
    [sys.executable, 'стенд_знімок.py', '--дим'],
    [sys.executable, 'тест_живого_шляху.py'],
    [sys.executable, 'тест_протоколу.py'],
    [sys.executable, 'прилади/розділи_гейтів.py'],
    [sys.executable, 'audit_contracts.py'],
    ['node', 'тест_показу.js'],
]
family = sorted(p.name for ш in ('pal_*.py', 'col_*.py', 'cra_*.py', 'сила_*.py') for p in (src / 'проби').glob(ш)
                if p.name not in ('pal_вердикт.py', 'pal_вимір.py'))
family += ['н1_схема_не_її.py', 'схема_нейтральна_роль.py', 'дріт_сирота_2882.py']
steps += [[sys.executable, 'проби/' + p] for p in family]
if лише:
    steps = [s for s in steps if s[-1].split('/')[-1] in лише or s[-1] in лише]


def крок(i):
    command = steps[i]
    begin = time.monotonic()
    p = subprocess.run(command, cwd=src, env=env, capture_output=True)
    log = (p.stdout + p.stderr).decode('utf-8', errors='replace')
    pathlib.Path('/tmp/суд_перевірки_%s_%02d.log' % (мітка, i)).write_text(log, encoding='utf-8')
    print(i, command[-1][:60], 'код', p.returncode, flush=True)
    return dict(команда=command[1:] if command[0] == sys.executable else command, код=p.returncode,
                секунд=round(time.monotonic() - begin, 2), хвіст=log.splitlines()[-6:])


with ThreadPoolExecutor(4) as пул:
    results = list(пул.map(крок, range(len(steps))))
out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ФАКТ · кроків', len(results), 'код 0:', sum(x['код'] == 0 for x in results),
      'без входу (77):', sum(x['код'] == 77 for x in results))
