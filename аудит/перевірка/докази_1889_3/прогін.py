"""Послідовний прогін наряду 1889-3; зовнішні команди виконуються до кінця."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

p = argparse.ArgumentParser()
p.add_argument('group', choices=['межі', 'стенди', 'дим'])
p.add_argument('--run', required=True, type=Path)
args = p.parse_args()
repo = Path(__file__).resolve().parents[3]
out = Path(__file__).resolve().parent
old = out.parent / 'докази_1889_2'
args.run = args.run.resolve()
env = os.environ.copy()
env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
results = []


def run(name, cmd, cwd=repo, extra=None):
    print('ПОЧАТО ' + name, flush=True)
    started = time.monotonic()
    result = subprocess.run([str(x) for x in cmd], cwd=cwd,
                            env=env | (extra or {}), stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT)
    output = result.stdout.decode('utf-8-sig', errors='replace')
    # Лише формат текстового артефакту: CRLF -> LF, кінцеві пробіли прибрано.
    output = '\n'.join(line.rstrip() for line in output.splitlines()) + '\n'
    dest = out / (name + '.txt')
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(output, encoding='utf-8')
    checks = re.findall(r'^\s*(✓|✗|ok\b|FAIL\b|ПОМИЛКА\b)', output, re.M)
    record = dict(name=name, command=[str(x) for x in cmd], cwd=str(cwd),
                  exit=result.returncode, seconds=round(time.monotonic()-started, 1),
                  passed=sum(x in ('✓', 'ok') for x in checks),
                  failed=sum(x not in ('✓', 'ok') for x in checks))
    results.append(record)
    (out / (args.group + '.json')).write_text(
        json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(record, ensure_ascii=False), flush=True)
    if args.group == 'межі':
        print(output, end='', flush=True)
    else:
        print('\n'.join(output.splitlines()[-5:]), flush=True)


ps = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File']
if args.group == 'межі':
    for rev in ('before', 'after'):
        root = args.run / rev
        for engine in ('gemini', 'claude'):
            for case in ('directory', 'quota', 'worker', 'spawn', 'orphan'):
                label = f'{rev}-{engine}-{case}'
                run(label, ps + [old/'межі.ps1', '-Root', root, '-Temp',
                                 args.run/label, '-Engine', engine, '-Case', case])
            label = f'{rev}-{engine}-live'
            run(label, ps + [out/'живий_claim.ps1', '-Root', root, '-Temp',
                             args.run/label, '-Engine', engine])
        for limit in (0, 2):
            label = f'{rev}-cap-{limit}'
            run(label, ps + [old/'стелі.ps1', '-Root', root, '-Temp',
                             args.run/label, '-CodexLimit', str(limit)])
    run('хеші', [sys.executable, old/'хеші.py',
                 'a08790db3aaedc122896cef8bdd4ee59bbc3435b'])
elif args.group == 'стенди':
    for suite_id, suite in enumerate(('смуг', 'claude', 'рушіїв', 'доставки', 'черги', 'm9v')):
        for rev in ('before', 'after'):
            root = args.run / rev
            # .cmd заглушок на Windows вимагає лише ASCII в TMPDIR.
            tmp = args.run / f'suites-{rev}-{suite_id}'
            tmp.mkdir(exist_ok=True)
            script = root / f'аудит/адаптери/gemini/перевірка/сценарії_{suite}.sh'
            run(f'стенди/{rev}-{suite}',
                ['C:/Program Files/Git/usr/bin/bash.exe', '--noprofile', '--norc',
                 '-c', 'export PATH="/usr/bin:/bin:$PATH"; unset PWSH; '
                 'export TMPDIR="$(cygpath -u "$REVIEW_TMP")"; exec bash "$1"',
                 '--', script.as_posix()], extra={'REVIEW_TMP': tmp.as_posix()})
elif args.group == 'дим':
    root = args.run / 'after' / 'джерела'
    for name, cmd in (
        ('знімок', [sys.executable, 'стенд_знімок.py', '--дим']),
        ('живий_шлях', [sys.executable, 'тест_живого_шляху.py']),
        ('протокол', [sys.executable, 'тест_протоколу.py']),
        ('розділи', [sys.executable, 'прилади/розділи_гейтів.py']),
        ('контракти', [sys.executable, 'audit_contracts.py']),
        ('показ', ['node', 'тест_показу.js']),
    ):
        run('дим/' + name, cmd, root,
            {'NODE_PATH': str(repo/'джерела/node_modules')})
sys.exit(any(r['exit'] != 0 for r in results))
