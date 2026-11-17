"""Послідовний дим і автономні проби на переданому дереві, зі збереженням повного виводу."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time

tree = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
env['NODE_PATH'] = str(tree/'джерела/node_modules')
commands = [
    [sys.executable, '-X', 'utf8', 'стенд_знімок.py', '--дим'],
    [sys.executable, '-X', 'utf8', 'тест_живого_шляху.py'],
    [sys.executable, '-X', 'utf8', 'тест_протоколу.py'],
    [sys.executable, '-X', 'utf8', 'прилади/розділи_гейтів.py'],
    [sys.executable, '-X', 'utf8', 'audit_contracts.py'],
    ['node', 'тест_показу.js'],
]
external = {'кадр_варіант_каталог.py','кадр_варіант_перезбір.py','кадр_варіант_факти.py','кадр_варіант_woo_факти.py'}
commands += [[sys.executable, '-X', 'utf8', 'проби/'+p.name]
             for p in sorted((tree/'джерела/проби').glob('кадр_варіант_*.py')) if p.name not in external]
results = []
for n, cmd in enumerate(commands, 1):
    start = time.monotonic()
    result = subprocess.run(cmd, cwd=tree/'джерела', env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    log = f'{n:02}.log.gz'
    (out/log).write_bytes(gzip.compress(result.stdout, mtime=0))
    row = dict(команда=cmd, код=result.returncode, секунд=round(time.monotonic()-start,1), журнал=log)
    results.append(row)
    (out/'результат.json').write_text(json.dumps(results, ensure_ascii=False, indent=1), encoding='utf-8')
    print(json.dumps(row, ensure_ascii=False), flush=True)
print('Кроків:',len(results),'негативних:',sum(r['код']!=0 for r in results),flush=True)
sys.exit(any(r['код']!=0 for r in results))
