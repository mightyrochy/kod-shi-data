"""Повторює дві частини приймання CI на готових збірках голови й бази.

Вжиток: python -X utf8 відтворити.py <показ> <main-показ> <main-код> <кеш-Pyodide> <вихід>
Записи, стенд і продуктовий код не змінює; моделі не викликає.
"""

import hashlib
import gzip
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time


def зберегти_докази(output, summary):
    """Архівує повні виводи й порівнює результати кожної пари сцени."""
    destination = Path(__file__).resolve().parent
    scenes = []
    for part in range(2):
        part_dir = output / f'частина-{part}'
        report = part_dir / 'підсумок.json'
        if not report.exists():
            continue
        for row in json.loads(report.read_text(encoding='utf-8')):
            scene_dir = part_dir / row['сцена'].replace('/', '_').replace('\\', '_').replace(':', '_')
            pair = {}
            requests = {}
            for label, name in [('голова', 'звірки.json'), ('база', 'вимір-бази.json')]:
                source = scene_dir / name
                pair[label] = json.loads(source.read_text(encoding='utf-8')) if source.exists() else None
                error_file = scene_dir / ('main/' if label == 'база' else '') / 'знімки/помилка_відтворення.json'
                if error_file.exists():
                    requests[label] = json.loads(error_file.read_text(encoding='utf-8')).get('запит')
            stale = {label: value.get('застарілий') if value else None for label, value in pair.items()}
            scenes.append({**row, 'частина': part, 'голова': pair['голова'], 'база': pair['база'],
                           'однакові_запити': len(requests) == 2 and requests['голова'] is not None
                           and requests['голова'] == requests['база'],
                           'однакові_ключі': all(stale.values())
                           and bool(stale['голова'].get('вхід'))
                           and stale['голова'].get('вхід') == stale['база'].get('вхід')})
    manifest = []
    for source in sorted(output.rglob('*')):
        if source.is_file() and source.suffix in {'.log', '.json', '.txt'}:
            target = destination / 'докази' / f'{len(manifest):04d}-{source.name}.gz'
            target.parent.mkdir(parents=True, exist_ok=True)
            raw = source.read_bytes()
            target.write_bytes(gzip.compress(raw, mtime=0))
            manifest.append({'файл': target.relative_to(destination).as_posix(),
                             'джерело': source.relative_to(output).as_posix(),
                             'байтів_до': len(raw), 'sha256_до': hashlib.sha256(raw).hexdigest()})
    (destination / 'підсумок.json').write_text(json.dumps({**summary, 'сцени': scenes},
                                                       ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    (destination / 'архіви.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n',
                                           encoding='utf-8')
    print(f'Збережено сцен: {len(scenes)}, архівів: {len(manifest)}', flush=True)


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
    зберегти_докази(output, summary)
    return int(any(item['код'] for item in summary['запуски']))


if __name__ == '__main__':
    sys.exit(виконати())
