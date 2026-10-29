"""Батарея наряду й той самий браузерний стенд, який запускає CI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
NODE = r'C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe'


def головна():
    env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_USE_SYSTEM_CA='1',
        NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules', LYUSTERKO_CATALOG='повний',
        LYUSTERKO_PYC_PYTHON=r'C:\Users\gemini\tools\python-3.12.1\python.exe',
        CHROMIUM=r'C:\Users\gemini\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe')
    env['PATH'] = str(Path(NODE).parent) + os.pathsep + env['PATH']
    for к in ['MODEL', 'MODEL_MOVA', 'ZHYVA', 'DO', 'OTSINKA', 'FOTO', 'SCENA', 'CHAT_TEXT', 'ZHINKA']:
        env.pop(к, None)
    вихід = ТЕКА / 'перевірки'
    вихід.mkdir(exist_ok=True)
    env.update(ZNIMKY=str(вихід / 'знімки'), ZVIT_OUT=str(вихід / 'вердикти.txt'))
    команди = [
        ('дим', [sys.executable, '-X', 'utf8', 'стенд_знімок.py', '--дим']),
        ('живий-шлях', [sys.executable, '-X', 'utf8', 'тест_живого_шляху.py']),
        ('протокол', [sys.executable, '-X', 'utf8', 'тест_протоколу.py']),
        ('розділи', [sys.executable, '-X', 'utf8', 'прилади/розділи_гейтів.py']),
        ('контракти', [sys.executable, '-X', 'utf8', 'audit_contracts.py']),
        ('показ', [NODE, 'тест_показу.js']),
        ('кадр', [NODE, str(КОРІНЬ / 'аудит/проби/кадр_моделі_стенд.js')]),
        ('проксі', [NODE, str(КОРІНЬ / 'аудит/ноутбук_стенд_2/тест_проксі.js')]),
        ('стенд-CI', [NODE, str(КОРІНЬ / 'аудит/проби/рв6_стенд.js'),
            'http://127.0.0.1:8765', str(КОРІНЬ.parent / 'стенд-webp'), r'C:\Users\gemini\pyodide', '3']),
    ]
    результати = []
    for назва, команда in команди:
        початок = time.monotonic()
        with (вихід / (назва + '.txt')).open('wb') as лог:
            р = subprocess.run(команда, cwd=КОРІНЬ / 'джерела', env=env, stdout=лог, stderr=subprocess.STDOUT)
        результати.append({'назва': назва, 'команда': команда, 'rc': р.returncode,
            'секунд': round(time.monotonic() - початок, 1)})
        (вихід / 'результат.json').write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding='utf-8')
        print(назва, р.returncode, flush=True)
    return int(any(р['rc'] for р in результати))


if __name__ == '__main__':
    sys.exit(головна())
