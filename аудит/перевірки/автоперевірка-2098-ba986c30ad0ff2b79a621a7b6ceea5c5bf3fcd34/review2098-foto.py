"""Знімки Р2 з фото крамниць; відповіді моделі — штатна заглушка."""
import json
import os
from pathlib import Path
import subprocess
import time

ROOT=Path(r'C:\Users\gemini\gemini-runs\w\review-2098-ba986c30')
OUT=Path(r'C:\Users\gemini\gemini-runs\review2098-evidence')
NODE=r'C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe'
env=dict(os.environ,NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules',
    NODE_USE_SYSTEM_CA='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',FOTO='1',
    LYUSTERKO_CATALOG='повний',LYUSTERKO_PYC_PYTHON=r'C:\Users\gemini\tools\python-3.12.1\python.exe',
    CHROMIUM=r'C:\Users\gemini\AppData\Local\ms-playwright\chromium-1248\chrome-win64\chrome.exe',
    ZNIMKY=str(OUT/'фото-знімки'),ZVIT_OUT=str(OUT/'фото-вердикти.txt'))
for key in ['MODEL','MODEL_MOVA','ZHYVA','DO','OTSINKA','SCENA','CHAT_TEXT','ZHINKA','COMFY_FREE_LLM']:
    env.pop(key,None)
stand=OUT/'фото-стенд'
stand.mkdir(exist_ok=True)
build=[os.sys.executable,'-X','utf8','джерела/build_артефакт.py','джерела',str(stand/'index.html'),'показ-повний']
with (OUT/'фото-збірка.txt').open('wb') as f:
    subprocess.run(build,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT,check=True)
print('Збірка для FOTO=1 завершена',flush=True)
cmd=[NODE,str(ROOT/'аудит/проби/рв6_стенд.js'),'http://127.0.0.1:8765',str(stand),r'C:\Users\gemini\pyodide','3']
start=time.monotonic()
with (OUT/'фото.txt').open('wb') as f:
    p=subprocess.run(cmd,cwd=ROOT,env=env,stdout=f,stderr=subprocess.STDOUT)
result=dict(команда=cmd,збірка=build,cwd=str(ROOT),FOTO='1',rc=p.returncode,секунд=round(time.monotonic()-start,1))
(OUT/'фото-результат.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
print('\n'.join((OUT/'фото.txt').read_text(encoding='utf-8').splitlines()[-5:]))
raise SystemExit(p.returncode)
