"""Виконує повний перелік стендів обгортки й зберігає команди, коди та твердження."""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def перелік_запусків(дерево, нічний=None, план=None):
    """Знаходить усі самостійні стенди, нічну перевірку та хеші з їхніми командами."""
    обгортка = дерево / 'аудит/адаптери/gemini'
    стенди = обгортка / 'перевірка'
    оболонка = Path(os.environ.get('ProgramFiles', 'C:/Program Files')) / 'Git/bin/bash.exe'
    запуски = []
    for файл in sorted(стенди.glob('сценарії_*.sh')):
        запуски.append((файл.name, [str(оболонка), (стенди / 'запустити_стенд.sh').as_posix(), файл.name]))
    # Парні .ps1 викликаються з .sh, решта — самостійні стенди.
    for файл in sorted(стенди.glob('сценарії_*.ps1')):
        if not файл.with_suffix('.sh').exists():
            if файл.stem == 'сценарії_менше_прогонів' and план:
                файл = план.resolve()
            команда = ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(файл)]
            if файл.stem == 'сценарії_коду_збірки':
                команда += ['-WrapperRoot', str(обгортка), '-Phase', 'ПІСЛЯ']
            else:
                команда += ['-SourceDir', str(обгортка)]
            запуски.append((файл.name, команда))
    нічний = нічний or дерево / 'аудит/проби/перевірити_нічний_маркер.ps1'
    запуски.append(('перевірити_нічний_маркер.ps1', ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass',
                  '-File', str(нічний.resolve()), '-WrapperRoot', str(обгортка)]))
    запуски.append(('перевірити_хеші.py', [sys.executable, '-X', 'utf8', str(стенди / 'перевірити_хеші.py')]))
    return запуски


def зібрати(журнали, очікувані):
    """Червонить збирач за провал, пропуск, дубль чи чужий результат серед артефактів частин."""
    результати, помилки = [], []
    for файл in sorted(журнали.rglob('результати.json')):
        try:
            записи = json.loads(файл.read_text(encoding='utf-8'))
            if not isinstance(записи, list):
                raise ValueError('очікується список результатів')
            for запис in записи:
                if not isinstance(запис, dict) or not isinstance(запис.get('стенд'), str):
                    raise ValueError('результат без назви стенда')
                результати.append(запис)
                if (запис.get('код') != 0 or запис.get('код_процесу') != 0
                        or not isinstance(запис.get('тверджень'), int) or запис['тверджень'] <= 0
                        or запис.get('провалів') != 0):
                    помилки.append(f'стенд {запис["стенд"]}: провал або неповний результат')
        except (OSError, ValueError) as помилка:
            помилки.append(f'{файл}: {помилка}')
    лічба = Counter(запис['стенд'] for запис in результати)
    for назва in sorted(очікувані | set(лічба)):
        if назва not in очікувані or лічба[назва] != 1:
            помилки.append(f'стенд {назва}: запусків {лічба[назва]}, очікується {int(назва in очікувані)}')
    for помилка in помилки:
        print('ПОМИЛКА ' + помилка, file=sys.stderr)
    print(f'збирач: стендів {len(очікувані)}, результатів {len(результати)}, помилок {len(помилки)}')
    return int(bool(помилки))


def виконати():
    """Запускає повний перелік чи вибрану частину або звіряє повноту результатів усіх частин."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--дерево', type=Path, required=True)
    парсер.add_argument('--журнали', type=Path, required=True)
    парсер.add_argument('--нічний', type=Path)
    парсер.add_argument('--план', type=Path)
    парсер.add_argument('--лише', nargs='+')
    парсер.add_argument('--зібрати', action='store_true')
    аргументи = парсер.parse_args()
    дерево = аргументи.дерево.resolve()
    журнали = аргументи.журнали.resolve()
    запуски = перелік_запусків(дерево, аргументи.нічний, аргументи.план)
    назви = {назва for назва, _ in запуски}
    if аргументи.зібрати:
        if аргументи.лише:
            парсер.error('--зібрати звіряє повний набір, без --лише')
        return зібрати(журнали, назви)
    if аргументи.лише:
        зайві = set(аргументи.лише) - назви
        if зайві or len(set(аргументи.лише)) != len(аргументи.лише):
            парсер.error('невідомі чи повторені стенди --лише: ' + ', '.join(sorted(зайві)))
    журнали.mkdir(parents=True, exist_ok=True)
    середовище = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PWSH='')
    середовище['TMPDIR'] = str(журнали / 'tmp').replace('\\', '/')
    Path(середовище['TMPDIR']).mkdir(exist_ok=True)
    воркфлоу = (дерево / '.github/workflows/obhortka.yml').read_text(encoding='utf-8')
    for назва in re.findall(r'запустити_стенд.sh (сценарії_\w+\.sh)', воркфлоу):
        assert назва in {назва for назва, _ in запуски}, назва
    результати = []
    for назва, команда in запуски:
        if аргументи.лише and назва not in аргументи.лише:
            continue
        print('ВИКОНУЄТЬСЯ ' + назва, flush=True)
        початок = time.monotonic()
        результат = subprocess.run(команда, cwd=дерево, env=середовище, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        секунд = time.monotonic() - початок
        вивід = результат.stdout.decode('utf-8', errors='replace')
        (журнали / (назва + '.log')).write_text(вивід, encoding='utf-8', newline='\n')
        тверджень = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✓ |ok\s)', вивід, re.M))
        провалів = len(re.findall(r'^\s*(?:[a-z][0-9a-z]*: +)?(?:✗ |FAIL\s|ПОМИЛКА\s)', вивід, re.M))
        код = результат.returncode or int(bool(провалів) or тверджень == 0)
        запис = dict(стенд=назва, команда=команда, код_процесу=результат.returncode, код=код,
                     тверджень=тверджень, провалів=провалів, секунд=round(секунд, 3))
        результати.append(запис)
        # Діагностика ACL потрібна і в зеленому CI: локальний токен не доводить властивостей раннера.
        for рядок in вивід.splitlines():
            if рядок.startswith(('ACL ДІАГНОСТИКА ', 'ACL ТОКЕН ', 'ACL ЧИТАННЯ ', 'ACL ЧИТАЧ ')):
                print(рядок, flush=True)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
        if код:
            print(вивід, file=sys.stderr, flush=True)
    (журнали / 'результати.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return int(any(запис['код'] for запис in результати))


if __name__ == '__main__':
    sys.exit(виконати())
