"""Виконує повний перелік стендів обгортки й зберігає команди, коди та твердження."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def main():
    """Звіряє перелік CI зі стендами, запускає кожний до кінця й повертає сукупний код."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--дерево', type=Path, required=True)
    parser.add_argument('--журнали', type=Path, required=True)
    parser.add_argument('--нічний', type=Path)
    parser.add_argument('--лише', nargs='*')
    args = parser.parse_args()
    root = args.дерево.resolve()
    logs = args.журнали.resolve()
    logs.mkdir(parents=True, exist_ok=True)
    wrapper = root / 'аудит/адаптери/gemini'
    stands = wrapper / 'перевірка'
    shell = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe'
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PWSH='')
    env['TMPDIR'] = str(logs / 'tmp').replace('\\', '/')
    Path(env['TMPDIR']).mkdir(exist_ok=True)
    tasks = []
    for path in sorted(stands.glob('сценарії_*.sh')):
        tasks.append((path.name, [str(shell), (stands / 'запустити_стенд.sh').as_posix(), path.name]))
    # Парні .ps1 викликаються з .sh, решта — самостійні стенди.
    for path in sorted(stands.glob('сценарії_*.ps1')):
        if not path.with_suffix('.sh').exists():
            command = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(path)]
            if path.stem == 'сценарії_коду_збірки':
                command += ['-WrapperRoot', str(wrapper), '-Phase', 'ПІСЛЯ']
            else:
                command += ['-SourceDir', str(wrapper)]
            tasks.append((path.name, command))
    night = args.нічний or root / 'аудит/проби/перевірити_нічний_маркер.ps1'
    tasks.append(('перевірити_нічний_маркер.ps1', ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                  '-File', str(night.resolve()), '-WrapperRoot', str(wrapper)]))
    tasks.append(('перевірити_хеші.py', [sys.executable, '-X', 'utf8', str(stands / 'перевірити_хеші.py')]))
    workflow = (root / '.github/workflows/obhortka.yml').read_text(encoding='utf-8')
    for name in re.findall(r'запустити_стенд.sh (сценарії_\w+\.sh)', workflow):
        assert name in {name for name, _ in tasks}, name
    results = []
    for name, command in tasks:
        if args.лише and name not in args.лише:
            continue
        result = subprocess.run(command, cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        output = result.stdout.decode('utf-8', errors='replace')
        (logs / (name + '.log')).write_text(output, encoding='utf-8', newline='\n')
        good = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✓ |ok\s)', output, re.M))
        bad = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✗ |FAIL\s|ПОМИЛКА\s)', output, re.M))
        code = result.returncode or int(bool(bad) or good == 0)
        item = dict(стенд=name, команда=command, код_процесу=result.returncode, код=code, тверджень=good, провалів=bad)
        results.append(item)
        print(json.dumps(item, ensure_ascii=False), flush=True)
    (logs / 'результати.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(item['код'] for item in results))


if __name__ == '__main__':
    sys.exit(main())
