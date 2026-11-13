"""Повторює дві частини приймання CI на готових збірках голови й бази.

Вжиток: python -X utf8 відтворити.py <показ> <main-показ> <main-код> <кеш-Pyodide> <вихід>
Записи, стенд і продуктовий код не змінює; моделі не викликає.
"""

import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def виконати():
    """Зберігає команди, повні журнали й коди кожного завершеного запуску."""
    root = Path(__file__).resolve().parents[3]
    head_build, base_build, base_root, cache, output = map(Path, sys.argv[1:])
    output.mkdir(parents=True, exist_ok=False)
    env = dict(os.environ, NODE_PATH=str(root / 'джерела/node_modules'),
               REPLAY_BASE_BUILD=str(base_build.resolve()), REPLAY_BASE_ROOT=str(base_root.resolve()))
    summary = {
        'голова': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip(),
        'база': subprocess.check_output(['git', '-C', str(base_root), 'rev-parse', 'HEAD'], text=True).strip(),
        'ОС': platform.platform(), 'Python': platform.python_version(),
        'Node': subprocess.check_output(['node', '--version'], text=True).strip(),
        'Pyodide': '0.26.4',
        'sha256_показу': {name: hashlib.sha256((tree / 'index.html').read_bytes()).hexdigest()
                          for name, tree in [('голова', head_build), ('база', base_build)]},
        'запуски': [],
    }
    commands = [
        ('храповик', ['node', 'аудит/проби/перевірити_храповик.js']),
        ('нова-база', ['node', 'аудит/проби/перевірити_нову_базу.js']),
        *[(f'частина-{part}', ['node', 'аудит/проби/приймання_записів.js', str(head_build),
                              str(cache), str(output / f'частина-{part}'), str(part), '2'])
          for part in range(2)],
    ]
    for name, command in commands:
        start = time.monotonic()
        print('Запуск: ' + name, flush=True)
        with (output / f'{name}.log').open('wb') as log:
            process = subprocess.Popen(command, cwd=root, env=env, stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT)
            for line in iter(process.stdout.readline, b''):
                log.write(line)
                log.flush()
                print(line.decode('utf-8', errors='replace'), end='', flush=True)
            process.wait()
        summary['запуски'].append({'назва': name, 'команда': command, 'код': process.returncode,
                                   'секунд': round(time.monotonic() - start, 3)})
        (output / 'команди.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n',
                                           encoding='utf-8')
        print(f'Кінець: {name}, код {process.returncode}', flush=True)
    return int(any(item['код'] for item in summary['запуски']))


if __name__ == '__main__':
    sys.exit(виконати())
