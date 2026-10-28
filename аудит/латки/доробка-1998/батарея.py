"""Послідовно запускає всі сценарії обгортки й зберігає повні журнали."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    """Повертає ненульовий код при провалі будь-якого сценарію."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--logs', type=Path, required=True)
    parser.add_argument('--first', action='append', default=[])
    args = parser.parse_args()
    source = args.source.resolve()
    logs = args.logs.resolve()
    logs.mkdir(parents=True, exist_ok=True)
    harness = source / 'аудит/адаптери/gemini/перевірка'
    cases = sorted(harness.glob('сценарії_*.sh'))
    cases.sort(key=lambda p: (p.name not in args.first, args.first.index(p.name) if p.name in args.first else p.name))
    if len(cases) != 12:
        raise RuntimeError(f'Очікується 12 сценаріїв, є {len(cases)}')
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
    bash = r'C:\Program Files\Git\bin\bash.exe'
    summary = []
    bad = 0
    for case in cases:
        command = [bash, str(harness / 'запустити_стенд.sh'), case.name]
        print(f'Запуск: {case.name}', flush=True)
        with (logs / (case.stem + '.txt')).open('wb') as output:
            result = subprocess.run(command, cwd=source, env=env, stdout=output, stderr=subprocess.STDOUT)
        text = (logs / (case.stem + '.txt')).read_text(encoding='utf-8', errors='replace')
        totals = re.findall(r'^ПІДСУМОК .*$', text, re.M)
        line = f'{case.name}: код {result.returncode}; ' + (totals[-1] if totals else 'немає підсумку')
        summary.append(line)
        print(line, flush=True)
        bad += result.returncode != 0
    summary.append(f'Сценарії: {len(cases) - bad}/12 успішних')
    (logs / 'підсумок.txt').write_text('\n'.join(summary) + '\n', encoding='utf-8', newline='\n')
    print(summary[-1], flush=True)
    return int(bool(bad))


if __name__ == '__main__':
    sys.exit(main())
