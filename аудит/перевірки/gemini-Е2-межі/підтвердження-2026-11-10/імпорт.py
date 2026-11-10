"""Повторити предикат §117 на базі й голові, не змінюючи часу або приладу."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / 'джерела'
ДО = КОРІНЬ.parent / 'tmp/confirmation-before'
підсумок = []
for версія, код in (('до', ДО), ('після', КОД)):
    with tempfile.TemporaryDirectory(prefix='import117-', dir=КОРІНЬ.parent / 'tmp') as тека:
        до = {п.name for п in КОД.iterdir()}
        for модуль in ('траса_петлі', 'гейти_нові', 'measure_person_axis'):
            запуск = 'import sys;sys.path[:0]=' + repr([str(код), str(КОД)]) + ';import ' + модуль
            початок = time.perf_counter()
            р = subprocess.run([sys.executable, '-c', запуск], cwd=тека,
                               capture_output=True, text=True, encoding='utf-8', timeout=10)
            секунд = round(time.perf_counter() - початок, 3)
            запис = dict(версія=версія, модуль=модуль, код=р.returncode, секунд=секунд,
                         менше_двох=р.returncode == 0 and секунд < 2, stderr=р.stderr)
            підсумок.append(запис)
            print(json.dumps(запис, ensure_ascii=False), flush=True)
        нові = sorted(п.name for п in КОД.iterdir() if п.name not in до and п.name != '__pycache__')
        створені = sorted(п.name for п in Path(тека).iterdir() if п.name != '__pycache__')
        підсумок.append(dict(версія=версія, нові_в_коді=нові, створені_в_робочій_теці=створені))
підсумок.append(dict(джерела_117_незмінені=subprocess.run(['git', 'diff', '--quiet',
    'b6f0cb4187ba58a0de5ac450dcf07ffeab362f43', '--', 'джерела/траса_петлі.py',
    'джерела/прилади/розділи_гейтів.py'], cwd=КОРІНЬ).returncode == 0))
(ТЕКА / 'імпорт.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
