"""Послідовне завершення плану; кожний дочірній прогін чекається до кінця."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

тека = Path(__file__).resolve().parent
корінь = тека.parents[2]
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')
збірка = корінь.parent / 'tmp/збірка'
кеш = Path(r'C:\Users\gemini\pyodide')

def запис(назва, команда, змінні=None):
    початок = datetime.now(timezone.utc).isoformat()
    print('Початок: ' + назва, flush=True)
    with (тека / ('команда_' + назва + '.txt')).open('w', encoding='utf-8') as лог:
        р = subprocess.run(команда, cwd=корінь, env=змінні or env, stdout=лог, stderr=subprocess.STDOUT)
    з = {'крок': назва, 'команда': команда, 'початок_utc': початок,
         'кінець_utc': datetime.now(timezone.utc).isoformat(), 'rc': р.returncode}
    if змінні:
        з['змінні'] = {к: змінні.get(к) for к in ['MODEL_CTX', 'NODE_OPTIONS']}
    with (тека / 'команди.jsonl').open('a', encoding='utf-8') as лог:
        лог.write(json.dumps(з, ensure_ascii=False) + '\n')
    print('Кінець: ' + назва + '; rc=' + str(р.returncode), flush=True)
    return р.returncode

def коміт(тема):
    subprocess.run(['git', 'add', '--', str(тека.relative_to(корінь))], cwd=корінь, check=True)
    subprocess.run(['git', 'commit', '-m', тема], cwd=корінь, check=True)

assert (тека / 'ж2_довга_розмова_слова/результат.json').exists()
коміт('прогін: запис довгої розмови та підготовка решти плану')
запис('помічниця', [sys.executable, str(тека / 'помічниця_після.py'), str(збірка)])
коміт('прогін: питання помічниці після довгої розмови')
for сцена in ['ж1_оціни_образ_6б', 'б1_концерт_стримано']:
    змінні = dict(env)
    if сцена == 'б1_концерт_стримано':
        змінні['MODEL_CTX'] = '52000'
        змінні['NODE_OPTIONS'] = env.get('NODE_OPTIONS', '') + ' --require "' + str(тека / 'вікно-52000.cjs') + '"'
    код = запис(сцена, [sys.executable, str(корінь / 'аудит/проби/записати_сцену.py'),
        str(збірка), str(кеш), str(тека / сцена), '--сцена', сцена], змінні)
    коміт('прогін: записано ' + сцена + ', код виходу ' + str(код))
запис('аналіз', [sys.executable, str(тека / 'аналіз_записів.py')])
запис('нова_база', ['node', str(корінь / 'аудит/проби/нова_база.js'), str(тека)])
print('План завершено; потрібен підсумковий огляд доказів.', flush=True)
