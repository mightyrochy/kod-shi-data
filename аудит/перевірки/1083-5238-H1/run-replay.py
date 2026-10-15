import pathlib, subprocess, os, sys, json, time
p=pathlib.Path('/dev/shm/live5238'); mode=sys.argv[1]; scene=sys.argv[2]; port=int(sys.argv[3]); src=p/('original' if mode=='original' else 'repo'); out=p/(mode+'-'+scene); out.mkdir(exist_ok=True)
record=next((p/'recorded/аудит/живі_1510_А').glob(scene+'_*')); build=p/('build-'+mode)
e={**os.environ,'TMPDIR':str(p/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','CHROMIUM':'/usr/bin/chromium','MODEL_URL':f'http://127.0.0.1:{port}/v1','MODEL':'qwen/qwen3.5-9b','MODEL_MOVA':'mamaylm-gemma-3-12b-it-v2.0','ZHINKA':str(src/('аудит/проби/жінки/'+('ж2' if scene=='07' else 'ж1')+'.json')),'CHAT_TEXT':'новорічний корпоратив у ресторані, дрес-код коктейльний' if scene=='07' else 'увечері урок вокалу, надворі +18, хочеться дуже просто і зручне взуття','ROZMOVA':str(src/'аудит/перевірки/rozbir_0210/R_vyd.json'),'OTSINKA':'0','ZNIMKY':str(out/'знімки'),'VIDPOVIDI':str(out/'VIDPOVIDI'),'FOTO':'0','ZVIT_OUT':str(out/'вердикти.txt')}
if scene != '07': e.pop('ROZMOVA', None)
with (out/'replay.log').open('w') as log, (out/'стенд.log').open('w') as st:
 replay=subprocess.Popen(['python3',str(p/'repo/аудит/проби/replay_сцени.py'),str(record),str(port)],env=e,stdout=log,stderr=subprocess.STDOUT)
 try:
  result=subprocess.run(['node',str(src/'аудит/проби/рв6_стенд.js'),'http://127.0.0.1:8765',str(build),'/workspace/scratch/liusterko-4944/.qa4944/pyodide','3'],cwd=src,env=e,stdout=st,stderr=subprocess.STDOUT)
 finally: replay.terminate();replay.wait()
(out/'стан.json').write_text(json.dumps({'mode':mode,'scene':scene,'returncode':result.returncode,'fresh_model_calls':0},ensure_ascii=False))
print(mode,scene,result.returncode,flush=True)
