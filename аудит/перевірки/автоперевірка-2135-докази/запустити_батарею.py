"""Повторює батарею і сусідні проби на точній голові PR, зберігаючи докази окремо."""
import gzip
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time

root = pathlib.Path(r'C:/Users/gemini/gemini-runs/w/review-2135')
src = root / 'джерела'
out = pathlib.Path(r'C:/Users/gemini/gemini-runs/w/codex-2/аудит/перевірки/автоперевірка-2135-докази')
out.mkdir(parents=True, exist_ok=True)
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_PATH=r'C:/Users/gemini/kod-shi-test-node/node_modules', CHROMIUM=r'C:/Program Files/Google/Chrome/Application/chrome.exe')
records = pathlib.Path(tempfile.mkdtemp(prefix='review-2135-records-'))
for p in (root / 'аудит/тести/сирі_2026-09-25/t7_remont_c59f301/stend_seed13').glob('seed13_*.txt.gz'):
    (records / p.stem).write_bytes(gzip.decompress(p.read_bytes()))
commands = [[sys.executable, *c.split()] for c in ['стенд_знімок.py --дим', 'тест_живого_шляху.py', 'тест_протоколу.py', 'прилади/розділи_гейтів.py', 'audit_contracts.py']]
commands += [['node', 'тест_показу.js']]
probes = sorted({p for pattern in ('відбір_*.py', 'семплер_*.py', 'cmp_*.py', 'ремонт_*.py', 'ремонт2_*.py', 'повнота_*.py', 'промпти3_ремонт*.py', 'поділ_composer_ast.py', 'поділ_pipeline_ast.py', 'поділ_bridge_ast.py') for p in (src / 'проби').glob(pattern) if not p.name.endswith('_живо.py')})
commands += [[sys.executable, str(p)] + ([str(records), '13'] if p.name in ('ремонт_опис_біля_номера.py', 'ремонт_слоти.py') else []) for p in probes]
results = []
for i, command in enumerate(commands):
    print(json.dumps({'почато': i, 'команда': command[1:]}, ensure_ascii=False), flush=True)
    start = time.monotonic()
    with (out / f'{i:02d}.log').open('w', encoding='utf-8') as log:
        result = subprocess.run(command, cwd=src, stdout=log, stderr=subprocess.STDOUT)
    item = {'команда': command, 'код': result.returncode, 'секунд': round(time.monotonic() - start, 2), 'журнал': f'{i:02d}.log'}
    results.append(item)
    (out / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(item, ensure_ascii=False), flush=True)
sys.exit(int(any(r['код'] for r in results)))
