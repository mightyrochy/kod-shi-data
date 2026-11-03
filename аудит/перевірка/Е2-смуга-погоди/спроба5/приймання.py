"""Виконує батарею та погодні проби до кінця й зберігає коди завершення."""
import contextlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'джерела'
LOGS = Path(__file__).resolve().parent
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONWARNINGS'] = 'ignore'
sys.path.insert(0, str(SOURCE))
os.chdir(SOURCE)
results = []


def result(name, code, started):
    """Записує результат завершеної команди."""
    row = dict(перевірка=name, код=code, секунд=round(time.monotonic() - started, 1))
    results.append(row)
    print(json.dumps(row, ensure_ascii=False), flush=True)
    (LOGS / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def command(name, args):
    """Виконує наявну перевірку без зміни її входу чи таймаутів."""
    started = time.monotonic()
    with (LOGS / (name + '.txt')).open('w', encoding='utf-8') as output:
        code = subprocess.run(args, stdout=output, stderr=subprocess.STDOUT).returncode
    result(name, code, started)


def probe(name, args=()):
    """Повторює погодну пробу, розділяючи лише її журнал."""
    started = time.monotonic()
    code = 0
    sys.argv = [str(SOURCE / 'проби' / (name + '.py')), *map(str, args)]
    with (LOGS / (name + '.txt')).open('w', encoding='utf-8') as output:
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            try:
                runpy.run_path(sys.argv[0], run_name='__main__')
            except SystemExit as error:
                code = error.code or 0
            except Exception:
                traceback.print_exc()
                code = 1
    result(name, code, started)


if __name__ == '__main__':
    for name, args in (
        ('дим', [sys.executable, 'стенд_знімок.py', '--дим']),
        ('живий-шлях', [sys.executable, 'тест_живого_шляху.py']),
        ('протокол', [sys.executable, 'тест_протоколу.py']),
        ('гейти', [sys.executable, 'прилади/розділи_гейтів.py']),
        ('контракти', [sys.executable, 'audit_contracts.py']),
        ('показ', ['node', 'тест_показу.js']),
    ):
        command(name, args)
    for path in sorted((SOURCE / 'проби').glob('поділ_*_ast.py')):
        command(path.stem, [sys.executable, str(path)])
    for name in ('е2_смуга_погоди', 'е2_смуга_читачі'):
        probe(name)
    for path in sorted((SOURCE / 'проби').glob('wea_*.py')):
        if path.stem in ('wea_канон', 'wea_спека'):
            import bridge
            catalog = bridge.каталог_останнього_пакета()
            assert catalog, 'каталог останнього пакета порожній'
            catalog_path = ROOT.parent / 'tmp' / 'погодний-каталог.json'
            catalog_path.write_text(json.dumps(catalog, ensure_ascii=False, default=list), encoding='utf-8')
            probe(path.stem, (SOURCE, catalog_path))
        else:
            probe(path.stem)
    sys.exit(any(row['код'] for row in results))
