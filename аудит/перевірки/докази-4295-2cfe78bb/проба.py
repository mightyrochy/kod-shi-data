"""Незалежні проби голови #4295; правки мутанта лише в тимчасовому дереві."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import time

дерево = Path(sys.argv[1]).resolve()
докази = Path(__file__).resolve().parent
підсумок = []


def запуск(назва, аргументи, очікуваний=0):
    команда = [sys.executable, '-X', 'utf8', '-W', 'ignore', *аргументи]
    початок = time.monotonic()
    вихід = subprocess.run(команда, cwd=дерево, capture_output=True, encoding='utf-8', errors='replace', timeout=1800)
    час = round(time.monotonic() - початок, 3)
    текст = f'команда: {команда!r}\nкод: {вихід.returncode}; секунд: {час}\n' + вихід.stdout + вихід.stderr
    with gzip.open(докази / (назва + '.log.gz'), 'wt', encoding='utf-8') as файл:
        файл.write(текст)
    підсумок.append(dict(назва=назва, код=вихід.returncode, очікуваний=очікуваний, секунд=час))
    print(назва, вихід.returncode, час, '\n' + '\n'.join(текст.splitlines()[-8:]), flush=True)
    return вихід


for назва in ('тест_річ_запис_її_річ', 'тест_корінь_річ_запис_речі', 'тест_походження_запису'):
    запуск(назва, ['джерела/прилади/' + назва + '.py'])
запуск('прилад', ['джерела/прилади/річ_запис_її_річ.py', '--json'])

файл = дерево / 'джерела/річ_з_фото.py'
оригінал = файл.read_bytes()
рядок = ('        назва = _ВМ.текст(назва_моделі.get("value", назва_моделі) if isinstance(назва_моделі, dict) '
         'else назва_моделі)\n')
текст = оригінал.decode('utf-8').replace('\r\n', '\n')
assert текст.count(рядок) == 1
try:
    файл.write_text(текст.replace(рядок, рядок.replace('назва = ', 'назва = _ВМ.текст(р.get("quote")) or ', 1)), encoding='utf-8')
    мутант = запуск('мутант', ['джерела/прилади/тест_річ_запис_її_річ.py', 'Клас.test_дерево'], 1)
    assert мутант.returncode == 1 and 'FAILED (failures=1)' in мутант.stderr
finally:
    файл.write_bytes(оригінал)

(докази / 'підсумок.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
assert all(п['код'] == п['очікуваний'] for п in підсумок), підсумок
