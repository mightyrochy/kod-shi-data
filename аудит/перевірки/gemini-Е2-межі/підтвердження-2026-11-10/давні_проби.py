"""Звірити давні очікування на тих самих базі й голові, без моделі."""
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / 'джерела'
ДО = КОРІНЬ.parent / 'tmp/confirmation-before'
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONPATH=str(КОД))
підсумок = []
for версія, код in (('до', ДО), ('після', КОД)):
    for ім in ('картка_replay', 'картка_події', 'картка_живий'):
        запуск = ('import sys,runpy;sys.path[:0]=' + repr([str(код), str(КОД)]) +
                  ';import мовний_шар,картка_запиту;runpy.run_path(' +
                  repr(str(КОД / 'проби' / (ім + '.py'))) + ",run_name='__main__')")
        with (ТЕКА / ('давні-' + ім + '-' + версія + '.txt')).open('w', encoding='utf-8') as журнал:
            р = subprocess.run([sys.executable, '-c', запуск], cwd=КОРІНЬ,
                               stdout=журнал, stderr=subprocess.STDOUT)
        підсумок.append(dict(проба=ім, версія=версія, код=р.returncode))
        print(ім, версія, р.returncode, flush=True)
    команда = [sys.executable, str(КОД / 'прилади/replay_картки_живий.py'), '--код', str(код),
               '--запис', str(ТЕКА / ('шість-сцен-' + версія + '.json'))]
    with (ТЕКА / ('шість-сцен-' + версія + '.txt')).open('w', encoding='utf-8') as журнал:
        р = subprocess.run(команда, cwd=КОРІНЬ, stdout=журнал, stderr=subprocess.STDOUT)
    підсумок.append(dict(проба='шість-сцен', версія=версія, код=р.returncode))
(ТЕКА / 'давні-підсумок.json').write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
