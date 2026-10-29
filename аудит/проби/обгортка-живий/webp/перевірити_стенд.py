"""Повторює лише браузерну команду CI після виправлення лічильника доставки."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
NODE = r'C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe'
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_USE_SYSTEM_CA='1',
    NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules',
    CHROMIUM=r'C:\Users\gemini\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe',
    ZNIMKY=str(ТЕКА / 'стенд-ПІСЛЯ/знімки'), ZVIT_OUT=str(ТЕКА / 'стенд-ПІСЛЯ/вердикти.txt'))
for к in ['MODEL', 'MODEL_MOVA', 'ZHYVA', 'DO', 'OTSINKA', 'FOTO', 'SCENA', 'CHAT_TEXT', 'ZHINKA']:
    env.pop(к, None)
вихід = ТЕКА / 'стенд-ПІСЛЯ'
вихід.mkdir(exist_ok=True)
команди = [
    ('лічильник', [NODE, str(КОРІНЬ / 'аудит/проби/записи_шару_стенд.js')]),
    ('записи', [sys.executable, '-X', 'utf8', str(КОРІНЬ / 'джерела/проби/шар845_записи.py'),
        str(ТЕКА / 'перевірки/вердикти.txt'), str(ТЕКА / 'б1_концерт_стримано/вердикти.txt')]),
    ('стенд-CI', [NODE, str(КОРІНЬ / 'аудит/проби/рв6_стенд.js'),
        'http://127.0.0.1:8765', str(КОРІНЬ.parent / 'стенд-webp'), r'C:\Users\gemini\pyodide', '3']),
]
результати = []
for назва, команда in команди:
    початок = time.monotonic()
    with (вихід / (назва + '.txt')).open('wb') as лог:
        р = subprocess.run(команда, cwd=КОРІНЬ, env=env, stdout=лог, stderr=subprocess.STDOUT)
    результати.append({'назва': назва, 'команда': команда, 'rc': р.returncode,
        'секунд': round(time.monotonic() - початок, 1)})
    (вихід / 'результат.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
    print(назва, р.returncode, flush=True)
sys.exit(int(any(р['rc'] for р in результати)))
