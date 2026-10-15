import os,pathlib,subprocess,json,time,hashlib
p=pathlib.Path('/dev/shm/qa5238-r3');s=p/'frozen';a=pathlib.Path('/dev/shm/live5238');states=[]
for mode,scene,port in [('before','07',1241),('after','07',1242),('before','10',1243),('after','10',1244)]:
 out=p/(mode+'-'+scene);out.mkdir(exist_ok=True);record=next((a/'recorded/аудит/живі_1510_А').glob(scene+'_*'));build=a/'build-before' if mode=='before' else p/'build-after'
 e={**os.environ,'TMPDIR':str(p/'tmp'),'PYTHONDONTWRITEBYTECODE':'1','NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','CHROMIUM':'/usr/bin/chromium','MODEL_URL':f'http://127.0.0.1:{port}/v1','MODEL':'qwen/qwen3.5-9b','MODEL_MOVA':'mamaylm-gemma-3-12b-it-v2.0','ZHINKA':str(s/('аудит/проби/жінки/'+('ж2' if scene=='07' else 'ж1')+'.json')),'CHAT_TEXT':'новорічний корпоратив у ресторані, дрес-код коктейльний' if scene=='07' else 'увечері урок вокалу, надворі +18, хочеться дуже просто і зручне взуття','OTSINKA':'0','ZNIMKY':str(out/'знімки'),'VIDPOVIDI':str(out/'VIDPOVIDI'),'FOTO':'0','ZVIT_OUT':str(out/'вердикти.txt')}
 e.pop('ROZMOVA',None)
 if scene=='07':e['ROZMOVA']=str(s/'аудит/перевірки/rozbir_0210/R_vyd.json')
 start=time.time()
 with (out/'replay.log').open('w') as log,(out/'стенд.log').open('w') as st:
  server=subprocess.Popen(['python3',str(s/'аудит/проби/replay_сцени.py'),str(record),str(port)],env=e,stdout=log,stderr=subprocess.STDOUT)
  try:
   result=subprocess.run(['node',str(s/'аудит/проби/рв6_стенд.js'),'http://127.0.0.1:8765',str(build),'/workspace/scratch/liusterko-4944/.qa4944/pyodide','3'],cwd=s,env=e,stdout=st,stderr=subprocess.STDOUT)
  finally:server.terminate();server.wait()
 state=dict(mode=mode,scene=scene,returncode=result.returncode,seconds=round(time.time()-start,2),fresh_model_calls=0,actor='/root/review_live_a_h1_5238_r3',code='b02ef36e2d42f089c7c9366ebd9bdeabf00c45e3' if mode=='before' else '83d632c8a756cad5e882bf5a97829b35c08e42c7',build_sha256=hashlib.sha256((build/'index.html').read_bytes()).hexdigest())
 (out/'стан.json').write_text(json.dumps(state,ensure_ascii=False,indent=2));states.append(state);(p/'replay-state.json').write_text(json.dumps(states,ensure_ascii=False,indent=2));print(mode,scene,result.returncode,flush=True)
