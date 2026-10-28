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
    if name.startswith('стенд-'):
        record['звірки'] = [line for line in result.stdout.splitlines()
                             if line.lstrip().startswith(('✔ ', '✗ '))]
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
        data = subprocess.check_output(['git', 'archive', 'bd628bb29a90637ae18833c92eceb8230bd9b995',
                                        'джерела', 'каталог_повний.xml.gz'], cwd=ROOT)
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
    elif mode == 'збірки':
        os.environ['LYUSTERKO_PYC_PYTHON'] = 'C:/Users/gemini/tools/python-3.12.1/python.exe'
        results = []
        for name, source in [('до', TEMP / 'before/джерела'), ('після', ROOT / 'джерела')]:
            target = TEMP / ('build-' + name)
            target.mkdir(exist_ok=True)
            results.append(run('збірка-' + name, [sys.executable, '-X', 'utf8', 'build_артефакт.py', '.',
                               str(target / 'index.html'), 'показ-повний'], source))
        (OUT / 'збірки.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif mode == 'стенди':
        os.environ['CHROMIUM'] = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
        for key in ('MODEL', 'MODEL_MOVA', 'ZHYVA', 'REPLAY_EXCHANGE', 'REPLAY_RECORDINGS'):
            os.environ.pop(key, None)
        results = []
        for name in ['до', 'після']:
            shots = TEMP / ('shots-' + name)
            shots.mkdir(exist_ok=True)
            os.environ['ZNIMKY'] = str(shots)
            results.append(run('стенд-' + name, ['node', 'аудит/проби/рв6_стенд.js',
                               'http://127.0.0.1:8765', str(TEMP / ('build-' + name)),
                               'C:/Users/gemini/pyodide', '3'], ROOT))
        (OUT / 'стенди.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif mode == 'родини':
        probes = ['ремонт_понад_просили', 'ремонт_порядок_5511', 'повнота_до_вибору_ходи',
                  'повнота_після_вибору_ходи', 'повнота_вибір_прийняття']
        results = [run(p, [sys.executable, '-X', 'utf8', 'проби/' + p + '.py'], ROOT / 'джерела') for p in probes]
        (OUT / 'родини.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif mode == 'показ-збірки':
        result = run('показ-збірки', ['node', 'тест_показу.js', str(TEMP / 'build-після/index.html')], ROOT / 'джерела')
        lines = (TEMP / 'показ-збірки.txt').read_text(encoding='utf8').splitlines()
        result['вивід'] = '\n'.join(line for line in lines if line.lstrip().startswith(('✗ ', 'ВИКОНАНО ЗВІРОК:', 'ВПАЛО ')))
        result['помилки'] = sorted({line[:500] for line in lines if line.lstrip().startswith('✗ ')})
        (OUT / 'показ-збірки.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif mode == 'стенд-до-повтор':
        os.environ['CHROMIUM'] = 'C:/Program Files/Google/Chrome/Application/chrome.exe'
        for key in ('MODEL', 'MODEL_MOVA', 'ZHYVA', 'REPLAY_EXCHANGE', 'REPLAY_RECORDINGS'):
            os.environ.pop(key, None)
        first = OUT / 'стенди.json'
        old = json.loads(first.read_text(encoding='utf8'))
        (OUT / 'стенди-перша-спроба.json').write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        shots = TEMP / 'shots-до-повтор'
        shots.mkdir(exist_ok=True)
        os.environ['ZNIMKY'] = str(shots)
        old[0] = run('стенд-до-повтор', ['node', 'аудит/проби/рв6_стенд.js',
                      'http://127.0.0.1:8765', str(TEMP / 'build-до'), 'C:/Users/gemini/pyodide', '3'], ROOT)
        first.write_text(json.dumps(old, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    elif mode == 'стиснути-доказ-показу':
        file = OUT / 'показ-збірки.json'
        result = json.loads(file.read_text(encoding='utf8'))
        lines = (TEMP / 'показ-збірки.txt').read_text(encoding='utf8').splitlines()
        result['вивід'] = '\n'.join(line for line in lines if line.lstrip().startswith(('✗ ', 'ВИКОНАНО ЗВІРОК:', 'ВПАЛО ')))
        result['помилки'] = sorted({line for line in lines if line.lstrip().startswith('✗ ')})
        file.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
        print(result['вивід'])
