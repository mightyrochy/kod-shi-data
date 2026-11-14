"""Завершити вимір ДО/ПІСЛЯ та всю батарею без моделі й мережевих API."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / 'джерела'
ДО = КОРІНЬ.parent / 'tmp/confirmation-before'
ДО.mkdir(parents=True, exist_ok=True)
for ім in ('мовний_шар.py', 'картка_запиту.py'):
    (ДО / ім).write_bytes(subprocess.check_output(['git', 'show',
        'b6f0cb4187ba58a0de5ac450dcf07ffeab362f43:джерела/' + ім], cwd=КОРІНЬ))
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
                  PYTHONPATH=str(КОД), NODE_PATH=str(КОД / 'node_modules'))
перевірки = []
for версія, код in (('до', ДО), ('після', КОД)):
    виклик = ('import sys,runpy;sys.path[:0]=' + repr([str(код), str(КОД)]) +
              ';import мовний_шар,картка_запиту;runpy.run_path(' +
              repr(str(КОД / 'проби/картка_підтвердження.py')) + ",run_name='__main__')")
    перевірки += [('підтвердження-' + версія, [sys.executable, '-c', виклик], КОРІНЬ),
                  ('повтор-' + версія, [sys.executable, 'джерела/прилади/replay_картки.py',
                   'джерела/проби/дані/картка_запиту.json', '--код', str(код),
                   '--запис', str(ТЕКА / ('повтор-' + версія + '.json'))], КОРІНЬ)]
перевірки += [('каталог', [sys.executable, '-c', "import чистка_каталогу as ч,feed as ф;"
               "print(ч.забезпечити_чистим('каталог_повний.xml'));print(ф.каталог_на_диску('каталог_brief.xml'))"], КОД)]
for назва, команда in [('дим', ['стенд_знімок.py', '--дим']),
                       ('живий-шлях', ['тест_живого_шляху.py']),
                       ('протокол', ['тест_протоколу.py']),
                       ('гейти', ['прилади/розділи_гейтів.py']),
                       ('контракти', ['audit_contracts.py'])]:
    перевірки.append((назва, [sys.executable] + команда, КОД))
перевірки.append(('показ', ['node', 'тест_показу.js'], КОД))
for проба in sorted((КОД / 'проби').glob('*.py')):
    if проба.name.startswith(('е2_', 'картка_')):
        перевірки.append((проба.stem, [sys.executable, str(проба)], КОД))
перевірки += [('межі-після', [sys.executable, 'джерела/прилади/корінь_е2_межі.py', '--json'], КОРІНЬ),
              ('промпти-після', [sys.executable, '-W', 'ignore', 'джерела/прилади/корінь_е2_промпти.py',
               '--база', 'аудит/корені/Е2-промпти-довжини.json', '--деталі'], КОРІНЬ)]
префікс = ''
if '--остаточно' in sys.argv:
    префікс = 'остаточно-'
    перевірки = перевірки[:4] + [
        ('дим', [sys.executable, 'стенд_знімок.py', '--дим'], КОД),
        ('компіляція', [sys.executable, '-m', 'py_compile', 'мовний_шар.py', 'картка_запиту.py',
         'проби/картка_підтвердження.py'], КОД)]
підсумок = []
for назва, команда, тека in перевірки:
    print('ПОЧАТО', назва, flush=True)
    початок = time.monotonic()
    with (ТЕКА / (префікс + назва + '.txt')).open('w', encoding='utf-8', newline='\n') as журнал:
        результат = subprocess.run(команда, cwd=тека, stdout=журнал, stderr=subprocess.STDOUT)
    підсумок.append(dict(назва=назва, команда=команда, код=результат.returncode,
                         секунд=round(time.monotonic() - початок, 2)))
    (ТЕКА / (префікс + 'підсумок.json')).write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('ЗАВЕРШЕНО', назва, результат.returncode, flush=True)
sys.exit(int(any(п['код'] for п in підсумок if п['назва'] != 'підтвердження-до')))
