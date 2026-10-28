"""Незалежні проби голови PR #2098; без викликів живої моделі."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(r'C:\Users\gemini\gemini-runs\w\review-2098-ba986c30')
OUT = Path(r'C:\Users\gemini\gemini-runs\review2098-evidence')
OUT.mkdir(exist_ok=True)
NODE = r'C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe'
env = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8', NODE_USE_SYSTEM_CA='1',
    NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules', LYUSTERKO_CATALOG='повний',
    LYUSTERKO_PYC_PYTHON=r'C:\Users\gemini\tools\python-3.12.1\python.exe',
    CHROMIUM=r'C:\Users\gemini\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe')
env['PATH'] = str(Path(NODE).parent) + os.pathsep + env['PATH']
for key in ['MODEL','MODEL_MOVA','ZHYVA','DO','OTSINKA','FOTO','SCENA','CHAT_TEXT','ZHINKA','COMFY_FREE_LLM']:
    env.pop(key,None)
env.update(ZNIMKY=str(OUT/'знімки'), ZVIT_OUT=str(OUT/'вердикти.txt'))
commands = [
    ('кадр', [NODE,str(ROOT/'аудит/проби/кадр_моделі_стенд.js')],ROOT),
    ('лічильник', [NODE,str(ROOT/'аудит/проби/записи_шару_стенд.js')],ROOT),
    ('проксі', [NODE,str(ROOT/'аудит/ноутбук_стенд_2/тест_проксі.js')],ROOT),
    ('підсумок', [sys.executable,'-X','utf8',str(ROOT/'аудит/проби/обгортка-живий/webp/підсумувати.py')],ROOT),
    ('дошка', [sys.executable,'-X','utf8',str(ROOT/'джерела/прилади/згорнути_дошку.py'),'--лише-перевірити'],ROOT),
    ('дим',[sys.executable,'-X','utf8','стенд_знімок.py','--дим'],ROOT/'джерела'),
    ('живий-шлях',[sys.executable,'-X','utf8','тест_живого_шляху.py'],ROOT/'джерела'),
    ('протокол',[sys.executable,'-X','utf8','тест_протоколу.py'],ROOT/'джерела'),
    ('розділи',[sys.executable,'-X','utf8','прилади/розділи_гейтів.py'],ROOT/'джерела'),
    ('контракти',[sys.executable,'-X','utf8','audit_contracts.py'],ROOT/'джерела'),
    ('показ',[NODE,'тест_показу.js'],ROOT/'джерела'),
    ('записи-сусідні',[sys.executable,'-X','utf8','джерела/проби/шар845_записи.py',str(ROOT/'аудит/проби/обгортка-живий/webp/стенд-ПІСЛЯ/вердикти.txt'),str(ROOT/'аудит/проби/обгортка-живий/webp/б1_концерт_стримано/вердикти.txt')],ROOT),
    ('збірка',[sys.executable,'-X','utf8','джерела/build_артефакт.py','джерела',str(OUT/'стенд/index.html'),'показ-повний'],ROOT),
    ('браузер-CI',[NODE,str(ROOT/'аудит/проби/рв6_стенд.js'),'http://127.0.0.1:8765',str(OUT/'стенд'),r'C:\Users\gemini\pyodide','3'],ROOT),
]
(OUT/'стенд').mkdir(exist_ok=True)
results=[]
for name,cmd,cwd in commands:
    start=time.monotonic()
    print('ПОЧАТОК',name,datetime.datetime.now(datetime.timezone.utc).isoformat(),flush=True)
    with (OUT/(name+'.txt')).open('wb') as log:
        p=subprocess.run(cmd,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
    results.append(dict(назва=name,команда=cmd,cwd=str(cwd),rc=p.returncode,секунд=round(time.monotonic()-start,1)))
    (OUT/'результат.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('КІНЕЦЬ',name,'rc='+str(p.returncode),flush=True)
    for line in (OUT/(name+'.txt')).read_text(encoding='utf-8',errors='replace').splitlines()[-4:]:
        print(line,flush=True)
sys.exit(int(any(r['rc'] for r in results)))
