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
    bash = 'C:/Program Files/Git/bin/bash.exe'
    команди = []
    вкладені = set()
    for файл in sorted(стенди.glob('сценарії_*.sh')):
        текст = файл.read_text(encoding='utf-8-sig')
        вкладені.update(re.findall(r'сценарії_[\w]+\.ps1', текст))
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
    журнали = тека / 'стенди'
    журнали.mkdir(exist_ok=True)
    підсумки = []
    for назва, команда in команди:
        початок = time.monotonic()
        print(f'ЗАПУСК {назва}', flush=True)
        результат = subprocess.run(команда, cwd=дерево, env=оточення, capture_output=True)
        дані = результат.stdout + результат.stderr
        (журнали / (назва + '.log')).write_bytes(дані)
        текст = дані.decode('utf-8', errors='replace')
        добрі = len(re.findall(r'(?m)^\s*✓ ', текст))
        хибні = len(re.findall(r'(?m)^\s*✗ ', текст))
        рядок = dict(стенд=назва, команда=команда, код=результат.returncode,
                    успішних=добрі, провалів=хибні, секунд=round(time.monotonic()-початок, 1))
        підсумки.append(рядок)
        print(json.dumps(рядок, ensure_ascii=False), flush=True)
        (журнали / 'результати.json').write_text(json.dumps(підсумки, ensure_ascii=False, indent=2), encoding='utf-8')
    return int(any(р['код'] or р['провалів'] for р in підсумки))


if __name__ == '__main__':
    sys.exit(main())
