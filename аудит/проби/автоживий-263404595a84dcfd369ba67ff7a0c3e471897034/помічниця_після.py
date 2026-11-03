"""Одне питання помічниці за фактичними репліками першої сцени."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import urllib.request

КОРІНЬ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
if '--міст' in sys.argv:
    from міст_помічниця import помічниця
    print(помічниця(sys.stdin.read()))
    raise SystemExit(0)

тека = Path(__file__).parent
сцена = тека / 'ж2_довга_розмова_слова'
ходи = []
for файл in sorted((сцена / 'VIDPOVIDI/обмін').glob('*.json')):
    запис = json.loads(файл.read_text(encoding='utf-8'))
    for повідомлення in запис['запит'].get('messages', []):
        for ч in повідомлення.get('content', []):
            if ч.get('type') != 'text':
                continue
            try:
                п = json.loads(ч['text'])
            except ValueError:
                continue
            if isinstance(п, dict) and 'her_new_message' in п and 'conversation' in п:
                ходи.append(п)
останній = next(п for п in ходи if п['her_new_message'] == 'У залі завжди холодно')
історія = []
for репліка in останній['conversation']:
    хто, текст = репліка.split(': ', 1)
    історія.append({'хто': 'людина' if хто == 'She' else 'ші', 'текст': текст})
репліки = re.findall(r'^   ВОНА: (.*?)\n   СТИЛІСТКА: (.*?)\n   ПАСПОРТ:',
    (сцена / 'лог.txt').read_text(encoding='utf-8'), re.M | re.S)
assert len(репліки) == 9, len(репліки)
for вона, ші in репліки:
    історія.extend([{'хто': 'людина', 'текст': вона}, {'хто': 'ші', 'текст': ші}])
assert len(історія) == 20, len(історія)
файл_історії = тека / 'історія_помічниці.json'
файл_історії.write_text(json.dumps(історія, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

def api(суфікс='', дані=None):
    запит = urllib.request.Request('http://127.0.0.1:1234/api/v1/models' + суфікс,
        data=None if дані is None else json.dumps(дані).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(запит, timeout=300) as р:
        return json.load(р)

assert not any(м['loaded_instances'] for м in api()['models'])
env = dict(os.environ, LMS_MODE='http', PORT='1235', CTX=json.dumps({
    'qwen/qwen3.5-9b': 57344, 'mamaylm-gemma-3-12b-it-v2.0': 16384}))
with (тека / 'помічниця_проксі.txt').open('w', encoding='utf-8') as лог:
    проксі = subprocess.Popen(['node', str(КОРІНЬ / 'аудит/ноутбук_стенд_2/проксі_почергове.js')],
        env=env, stdout=лог, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        import socket
        for _ in range(50):
            try:
                with socket.create_connection(('127.0.0.1', 1235), timeout=.2):
                    break
            except OSError:
                time.sleep(.1)
        код = subprocess.call(['node', str(тека / 'помічниця_після.js'), sys.argv[1],
            str(тека / 'помічниця_після.json'), str(файл_історії), sys.executable], env=env)
    finally:
        проксі.terminate()
        проксі.wait(timeout=30)
        власні = set(re.findall(r'HTTP власний екземпляр (.+)', (тека / 'помічниця_проксі.txt').read_text(encoding='utf-8')))
        for м in api()['models']:
            for екз in м['loaded_instances']:
                if екз['id'] in власні:
                    api('/unload', {'instance_id': екз['id']})
raise SystemExit(код)
