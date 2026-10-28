"""Виконує повний перелік стендів обгортки й зберігає команди, коди та твердження."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys


def виконати():
    """Звіряє перелік CI зі стендами, запускає кожний до кінця й повертає сукупний код."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--дерево', type=Path, required=True)
    парсер.add_argument('--журнали', type=Path, required=True)
    парсер.add_argument('--нічний', type=Path)
    парсер.add_argument('--план', type=Path)
    парсер.add_argument('--лише', nargs='*')
    аргументи = парсер.parse_args()
    дерево = аргументи.дерево.resolve()
    журнали = аргументи.журнали.resolve()
    журнали.mkdir(parents=True, exist_ok=True)
    обгортка = дерево / 'аудит/адаптери/gemini'
    стенди = обгортка / 'перевірка'
    оболонка = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe'
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PWSH='')
    середовище['TMPDIR'] = str(журнали / 'tmp').replace('\\', '/')
    Path(середовище['TMPDIR']).mkdir(exist_ok=True)
    запуски = []
    for файл in sorted(стенди.glob('сценарії_*.sh')):
        запуски.append((файл.name, [str(оболонка), (стенди / 'запустити_стенд.sh').as_posix(), файл.name]))
    # Парні .ps1 викликаються з .sh, решта — самостійні стенди.
    for файл in sorted(стенди.glob('сценарії_*.ps1')):
        if not файл.with_suffix('.sh').exists():
            if файл.stem == 'сценарії_менше_прогонів' and аргументи.план:
                файл = аргументи.план.resolve()
            команда = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(файл)]
            if файл.stem == 'сценарії_коду_збірки':
                команда += ['-WrapperRoot', str(обгортка), '-Phase', 'ПІСЛЯ']
            else:
                команда += ['-SourceDir', str(обгортка)]
            запуски.append((файл.name, команда))
    нічний = аргументи.нічний or дерево / 'аудит/проби/перевірити_нічний_маркер.ps1'
    запуски.append(('перевірити_нічний_маркер.ps1', ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                  '-File', str(нічний.resolve()), '-WrapperRoot', str(обгортка)]))
    запуски.append(('перевірити_хеші.py', [sys.executable, '-X', 'utf8', str(стенди / 'перевірити_хеші.py')]))
    воркфлоу = (дерево / '.github/workflows/obhortka.yml').read_text(encoding='utf-8')
    for назва in re.findall(r'запустити_стенд.sh (сценарії_\w+\.sh)', воркфлоу):
        assert назва in {назва for назва, _ in запуски}, назва
    результати = []
    for назва, команда in запуски:
        if аргументи.лише and назва not in аргументи.лише:
            continue
        print('ВИКОНУЄТЬСЯ ' + назва, flush=True)
        результат = subprocess.run(команда, cwd=дерево, env=середовище, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        вивід = результат.stdout.decode('utf-8', errors='replace')
        (журнали / (назва + '.log')).write_text(вивід, encoding='utf-8', newline='\n')
        тверджень = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✓ |ok\s)', вивід, re.M))
        провалів = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✗ |FAIL\s|ПОМИЛКА\s)', вивід, re.M))
        код = результат.returncode or int(bool(провалів) or тверджень == 0)
        запис = dict(стенд=назва, команда=команда, код_процесу=результат.returncode, код=код, тверджень=тверджень, провалів=провалів)
        результати.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
    (журнали / 'результати.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(запис['код'] for запис in результати))


if __name__ == '__main__':
    sys.exit(виконати())
