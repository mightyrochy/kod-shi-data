"""Повторює неповні перевірки смуг, зберігаючи окремі журнали."""
import contextlib
import hashlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback

root = Path.cwd()
source = root / 'джерела'
logs = root / 'аудит/перевірка/Е2-смуга-погоди/спроба4'
os.environ['NODE_PATH'] = str(source / 'node_modules')
os.environ['PYTHONUTF8'] = '1'
for key in ('MODEL_URL', 'MODEL_MOVA'):
    os.environ.pop(key, None)
sys.path.insert(0, str(source))
os.chdir(source)
summary = []
codes = []

def save_result(name, code, start):
    """Записує завершення одного повтору."""
    line = f'{name}: код {code}; {time.monotonic() - start:.1f} с'
    summary.append(line)
    codes.append(code)
    print(line, flush=True)
    (logs / 'підсумок-повторів.txt').write_text('\n'.join(summary) + '\n', encoding='utf-8')

start = time.monotonic()
with (logs / 'показ-повтор.txt').open('w', encoding='utf-8') as out:
    code = subprocess.run(['node', 'тест_показу.js'], stdout=out, stderr=subprocess.STDOUT).returncode
save_result('показ-повтор', code, start)

def probe(name, args=()):
    """Виконує пробу в одному процесі, як попередня погодна сім'я."""
    start = time.monotonic()
    code = 0
    sys.argv = [str(source / 'проби' / (name + '.py')), *map(str, args)]
    with (logs / (name + '-повтор.txt')).open('w', encoding='utf-8') as out:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            try:
                runpy.run_path(sys.argv[0], run_name='__main__')
            except SystemExit as error:
                code = error.code or 0
            except Exception:
                traceback.print_exc()
                code = 1
    save_result(name + '-повтор', code, start)

probe('wea_K-WEA-06')
probe('wea_K-WEA-08')
import bridge
catalog = bridge.каталог_останнього_пакета()
assert catalog, 'каталог останнього пакета порожній'
catalog_file = root.parent / 'tmp/погодний-каталог.json'
catalog_file.write_text(json.dumps(catalog, ensure_ascii=False, default=list), encoding='utf-8')
metadata = {'каталог': len(catalog), 'sha256': hashlib.sha256(catalog_file.read_bytes()).hexdigest(),
            'джерело': 'bridge.каталог_останнього_пакета після проб на каталог_повний.xml'}
(logs / 'каталог-повторів.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
probe('wea_канон', (source, catalog_file))
probe('wea_спека', (source, catalog_file))
sys.exit(any(codes))
