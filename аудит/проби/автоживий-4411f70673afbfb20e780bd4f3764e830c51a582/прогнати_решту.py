"""Послідовні записи решти сцен наряду; реалізації продукту не змінює."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
РЕПО = ТЕКА.parents[2]
ЗБІРКА = РЕПО.parent / 'tmp' / 'збірка'
СЦЕНИ = ['ж3_кафе_13', 'ж3_кафе_20', 'ж7_вечеря_сьомій', 'ж1_весілля_гостя', 'ж3_театр_тріада']
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
           NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')

for сцена in СЦЕНИ:
    команда = [sys.executable, str(ЗБІРКА / 'аудит/проби/записати_сцену.py'),
               str(ЗБІРКА), r'C:\Users\gemini\pyodide', str(ТЕКА / сцена), '--сцена', сцена]
    запис = {'початок': datetime.now(timezone.utc).isoformat(), 'команда': команда}
    with (ТЕКА / (сцена + '_запуск.txt')).open('w', encoding='utf-8') as лог:
        запис['rc'] = subprocess.run(команда, cwd=РЕПО, env=env, stdout=лог, stderr=subprocess.STDOUT).returncode
    запис['кінець'] = datetime.now(timezone.utc).isoformat()
    with (ТЕКА / 'done.txt').open('a', encoding='utf-8') as лог:
        лог.write(json.dumps(dict(запис, сцена=сцена), ensure_ascii=False) + '\n')
    print(сцена + ': rc=' + str(запис['rc']), flush=True)
    subprocess.run(['git', 'add', '--', str(ТЕКА)], cwd=РЕПО, check=True)
    subprocess.run(['git', 'commit', '-m', 'проба: записати сцену ' + сцена], cwd=РЕПО, check=True)
    if запис['rc'] >= 2:
        raise SystemExit(запис['rc'])
