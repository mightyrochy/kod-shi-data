"""Повторює докази двох зауважень і записує коди виходу без оболонки."""
import json
import os
import pathlib
import subprocess
import sys

тека = pathlib.Path(__file__).resolve().parent
голова = pathlib.Path(sys.argv[1]).resolve()
база = pathlib.Path(sys.argv[2]).resolve()
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
команди = [
    ('перебір.json', [sys.executable, str(тека / 'перебір.py'), str(голова)]),
    ('перебір-до.json', [sys.executable, str(тека / 'перебір.py'), str(база)]),
    ('перебір-без-стелі.json', [sys.executable, str(тека / 'перебір.py'), str(голова), '--без-стелі']),
    ('ціль-факт.json', [sys.executable, str(тека / 'ціль.py'), str(голова), str(тека / 'ціль-вхід.json')]),
    ('ціль-вихід.json', ['node', str(тека / 'ціль.cjs'), str(голова), str(тека / 'ціль-вхід.json')]),
    ('ціль-факт-до.json', [sys.executable, str(тека / 'ціль.py'), str(база), str(тека / 'ціль-вхід-до.json'), '--до']),
    ('ціль-вихід-до.json', ['node', str(тека / 'ціль.cjs'), str(база), str(тека / 'ціль-вхід-до.json')]),
]
підсумок = []
for файл, команда in команди:
    результат = subprocess.run(команда, capture_output=True, encoding='utf-8')
    (тека / файл).write_text(результат.stdout, encoding='utf-8', newline='\n')
    if результат.stderr:
        (тека / (файл + '.помилка')).write_text(результат.stderr, encoding='utf-8')
    підсумок.append(dict(команда=команда, код=результат.returncode, вивід=файл))
    print(файл, результат.returncode)
(тека / 'прицільні.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding='utf-8')
