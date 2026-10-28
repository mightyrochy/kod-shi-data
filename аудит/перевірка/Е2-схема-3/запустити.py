"""Незалежний запуск команд перевірки; повні журнали поза репозиторієм."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
TEMP = Path('C:/Users/gemini/gemini-runs/20261028-171005-42cc673ca36e/e2-check')
OUT = Path(__file__).resolve().parent


def run(name, args, cwd):
    start = time.perf_counter()
    result = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf8', errors='replace')
    (TEMP / (name + '.txt')).write_text(result.stdout, encoding='utf8')
    record = dict(команда=subprocess.list2cmdline(args), тека=str(cwd), код=result.returncode,
                  секунд=round(time.perf_counter() - start, 2), вивід=result.stdout[-2400:])
    print(name, result.returncode, record['секунд'], flush=True)
    return record


if __name__ == '__main__':
    TEMP.mkdir(exist_ok=True)
    os.environ['PYTHONUTF8'] = '1'
    os.environ['NODE_PATH'] = str(ROOT / 'джерела/node_modules')
    mode = sys.argv[1]
    if mode == 'підготовка':
        before = TEMP / 'before'
        before.mkdir(exist_ok=True)
        data = subprocess.check_output(['git', 'archive', 'bd628bb29a90637ae18833c92eceb8230bd9b995', 'джерела'], cwd=ROOT)
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(before, filter='data')
        print('Архів ДО підготовлено')
    elif mode == 'батарея':
        commands = [[sys.executable, '-X', 'utf8', p, *extra] for p, extra in [
            ('стенд_знімок.py', ['--дим']), ('тест_живого_шляху.py', []),
            ('тест_протоколу.py', []), ('прилади/розділи_гейтів.py', []),
            ('audit_contracts.py', [])]] + [['node', 'тест_показу.js']]
        results = [run('батарея-' + str(i), command, ROOT / 'джерела')
                   for i, command in enumerate(commands, 1)]
        results += [run('досяжність', [sys.executable, '-X', 'utf8', 'досяжність.py'], ROOT / 'джерела')]
        (OUT / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
