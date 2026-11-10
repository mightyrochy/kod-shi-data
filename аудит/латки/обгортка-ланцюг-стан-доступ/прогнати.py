"""Виконує стенди послідовно до кінця, зберігаючи команди, коди й повний вивід."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


def main():
    """Запускає кожен самостійний стенд один раз; обгортки запускають свої вкладені стенди."""
    дерево = Path(sys.argv[1]).resolve()
    тека = Path(__file__).resolve().parent
    корінь = дерево / 'аудит/адаптери/gemini'
    стенди = корінь / 'перевірка'
    tmp = дерево.parent
    оточення = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                    PYTHONDONTWRITEBYTECODE='1', PWSH='powershell',
                    TMPDIR=tmp.as_posix(), TEMP=str(tmp), TMP=str(tmp))
    # Вкладені worktree на довгому шляху обгортки перевищують 260 знаків Windows.
    н = int(оточення.get('GIT_CONFIG_COUNT', '0'))
    оточення.update(GIT_CONFIG_COUNT=str(н + 1))
    оточення[f'GIT_CONFIG_KEY_{н}'] = 'core.longpaths'
    оточення[f'GIT_CONFIG_VALUE_{н}'] = 'true'
    bash = 'C:/Program Files/Git/bin/bash.exe'
    команди = []
    вкладені = set()
    for файл in стенди.glob('*.ps1'):
        вкладені.update(re.findall(r"(?:сценарії_|повтор_|бюджет_)[\w]+\.ps1", файл.read_text(encoding='utf-8-sig')))
    for файл in sorted(стенди.glob('сценарії_*.sh')):
        текст = файл.read_text(encoding='utf-8-sig')
        вкладені.update(re.findall(r'(?:сценарії_|повтор_|бюджет_)[\w]+\.ps1', текст))
        команди.append((файл.name, [bash, файл.as_posix()]))
    for файл in sorted(стенди.glob('*.ps1')):
        if not (файл.name.startswith('сценарії_') or файл.name in ('повтор_позначок.ps1', 'бюджет_живих_pr.ps1')):
            continue
        if файл.name in вкладені or файл.name == 'сценарії_бандлів.ps1':
            continue
        команди.append((файл.name, ['powershell', '-NoProfile', '-File', str(файл), '-SourceDir', str(корінь)]))
    команди.append(('перевірити_хеші.py', [sys.executable, str(стенди / 'перевірити_хеші.py')]))
    # Python-стенд моделей сам запускає worker з підробними LM Studio й агентом.
    команди.append(('сценарії_gpu_моделі.py', [sys.executable, str(стенди / 'сценарії_gpu_моделі.py'), '--source-dir', str(корінь)]))
    фільтр = sys.argv[2:]
    if фільтр:
        команди = [(назва, команда) for назва, команда in команди if назва in фільтр]
    підтека = os.environ.get('STATE_DIAGNOSTIC_LOG_SUBDIR', 'стенди')
    if Path(підтека).name != підтека:
        raise ValueError('Тека журналів має бути безпосередньою підтекою латки')
    журнали = тека / підтека
    журнали.mkdir(exist_ok=True)
    підсумки = []
    for назва, команда in команди:
        початок = time.monotonic()
        середовище_стенда = оточення.copy()
        if назва == 'сценарії_копії.ps1':
            # Цей стенд міряє повне дерево, а production свідомо не міряє promisor-клон.
            # Спершу доводимо локальну наявність усіх блобів коміту без lazy fetch.
            обʼєкти = subprocess.check_output(['git', 'ls-tree', '-r', '--format=%(objectname)', 'HEAD'], cwd=дерево)
            перевірка = subprocess.check_output(['git', 'cat-file', '--batch-check=%(objecttype)'],
                input=обʼєкти, cwd=дерево, env=dict(оточення, GIT_NO_LAZY_FETCH='1'))
            типи = перевірка.splitlines()
            повнота = dict(коміт=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=дерево, text=True).strip(),
                          блобів=len(типи), відсутніх=sum(тип != b'blob' for тип in типи))
            (журнали / 'повнота-бази.json').write_text(json.dumps(повнота, ensure_ascii=False, indent=2), encoding='utf-8')
            if повнота['відсутніх'] or len(типи) != len(обʼєкти.splitlines()):
                raise RuntimeError('Для стенда повної копії базові блоби не повністю локальні')
            індекс = int(середовище_стенда['GIT_CONFIG_COUNT'])
            середовище_стенда['GIT_CONFIG_COUNT'] = str(індекс + 1)
            середовище_стенда[f'GIT_CONFIG_KEY_{індекс}'] = 'remote.origin.promisor'
            середовище_стенда[f'GIT_CONFIG_VALUE_{індекс}'] = 'false'
        print(f'ЗАПУСК {назва}', flush=True)
        журнал = журнали / (назва + '.log')
        with журнал.open('wb') as вихід:
            результат = subprocess.run(команда, cwd=дерево, env=середовище_стенда, stdout=вихід, stderr=subprocess.STDOUT)
        дані = журнал.read_bytes()
        текст = дані.decode('utf-8', errors='replace')
        добрі = len(re.findall(r'(?m)^\s*(?:[a-z][0-9a-z]*:\s*)?(?:✓ |ok\s+)', текст))
        хибні = len(re.findall(r'(?m)^\s*(?:[a-z][0-9a-z]*:\s*)?✗ ', текст))
        рядок = dict(стенд=назва, команда=команда, код=результат.returncode,
                    успішних=добрі, провалів=хибні, секунд=round(time.monotonic()-початок, 1))
        підсумки.append(рядок)
        print(json.dumps(рядок, ensure_ascii=False), flush=True)
        (журнали / 'результати.json').write_text(json.dumps(підсумки, ensure_ascii=False, indent=2), encoding='utf-8')
    return int(any(р['код'] or р['провалів'] for р in підсумки))


if __name__ == '__main__':
    sys.exit(main())
