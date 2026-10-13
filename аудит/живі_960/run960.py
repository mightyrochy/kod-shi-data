from pathlib import Path
import subprocess, os, json, time, datetime
root=Path(__file__).resolve().parents[1]
out=root/'аудит/живі_960'
node='C:/Users/Admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe'
env=os.environ.copy()
env.update(NODE_PATH='C:/Users/Admin/kod-shi-test-node/node_modules',
 CHROMIUM='C:/Users/Admin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe',
 MODEL_URL='http://127.0.0.1:1236/v1',MODEL='qwen/qwen3.5-9b',
 MODEL_MOVA='mamaylm-gemma-3-12b-it-v2.0',FOTO='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
sha=json.loads((out/'source.json').read_text())['source_sha']
scenes=[('01','ж1_оціни_образ_6б','ж1','робочий день в офісі',dict(DO='otsinka',OTSINKA_F2='L'),3),
 ('02','ж2_новорічна_мороз','ж2','Новорічна вечірка в ресторані, надворі мороз',dict(OTSINKA='0'),3),
 ('03','ж2_спорт_коментар','ж2','йога зранку, потім кава з подругою',dict(DO='rozmova'),4),
 ('04','ж7_мороз_без_відкритого','ж7',"йду на роботу пішки, на вулиці мінус п'ятнадцять і сніг, відкритого не хочу",dict(OTSINKA='0'),3)]
for num,sid,woman,text,extra,seed in scenes:
 if os.environ.get('SCENE_START') and num < os.environ['SCENE_START']: continue
 d=out/(num+'_'+sid); d.mkdir(exist_ok=True)
 e=env.copy(); e.update(extra,ZHINKA=str(out/(woman+'.json')),CHAT_TEXT=text,
  ZNIMKY=str(d/'знімки'),ZVIT_OUT=str(d/'вердикти.txt'),VIDPOVIDI=str(d/'VIDPOVIDI'))
 (d/'input.json').write_text(json.dumps(dict(scene=sid,seed=seed,extra=extra,CHAT_TEXT=text,ZHINKA=woman),ensure_ascii=False,indent=2),encoding='utf-8')
 (d/'код.txt').write_text(f'{sha} {sid} ПІСЛЯ {e["MODEL"]}+{e["MODEL_MOVA"]}\n',encoding='utf-8')
 for attempt in [1,2]:
  logfile=d/('лог.txt' if attempt==1 else 'лог_2.txt')
  started=time.monotonic(); now=datetime.datetime.now(datetime.timezone.utc).isoformat()
  print('START',sid,'attempt',attempt,now,flush=True)
  with (d/f'transport_{attempt}.log').open('w',encoding='utf-8') as plog, logfile.open('w',encoding='utf-8') as log:
   proxy=subprocess.Popen([node,str(root/'work/transport960.js'),str(d/f'transport_{attempt}')],cwd=root,stdout=plog,stderr=subprocess.STDOUT)
   process=None
   try:
    time.sleep(0.7)
    if proxy.poll() is not None: raise RuntimeError('telemetry proxy failed')
    process=subprocess.Popen([node,str(root/'аудит/проби/рв6_960_вимір.js'),'http://127.0.0.1:8765','C:/tmp/zh960/site','C:/tmp/pyodide',str(seed)],cwd=root,env=e,stdout=log,stderr=subprocess.STDOUT)
    try: rc=process.wait(timeout=3000)
    except subprocess.TimeoutExpired:
     process.kill(); process.wait(); rc=124
   finally:
    if process and process.poll() is None: process.kill(); process.wait()
    proxy.terminate(); proxy.wait(timeout=10)
  seconds=round(time.monotonic()-started,1)
  with (out/'done.txt').open('a',encoding='utf-8') as done:
   done.write(f'{sid} attempt={attempt} rc={rc} seconds={seconds} started={now}\n')
  print('DONE',sid,'rc',rc,seconds,'seconds',flush=True)
  if rc<=1 or any((d/'знімки').glob('kartka*')): break
 subprocess.run(['git','add','--','аудит/живі_960','аудит/проби/рв6_960_вимір.js'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['git','commit','-m',f'Ноутбук 960: ПІСЛЯ {sid}, rc {rc}, {seconds} с'],cwd=root,check=True,stdout=subprocess.DEVNULL)
 subprocess.run(['git','push','--no-thin','-u','origin','codex/znimky-960-pislia'],cwd=root,check=True)
print('ALLDONE',flush=True)
