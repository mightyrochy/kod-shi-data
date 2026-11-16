import pathlib,subprocess,os,json,sys
repo=pathlib.Path(sys.argv[1]); build=pathlib.Path(sys.argv[2]); out=pathlib.Path(sys.argv[3]); out.mkdir(exist_ok=True)
scenes=sys.argv[4:] or ['ж7_мінус_вісім_пішки','ж2_різдвяна_вечеря','ж7_робота_можливо_дощ']
for scene in scenes:
 d=out/scene;d.mkdir(exist_ok=True);(d/'знімки').mkdir(exist_ok=True);(d/'VIDPOVIDI').mkdir(exist_ok=True)
 baseenv=dict(os.environ,PYTHONIOENCODING='utf-8',PYTHONUTF8='1')
 config=json.loads(subprocess.check_output([sys.executable,str(repo/'аудит/проби/записати_сцену.py'),'--сцена',scene,'--режим','розмова','--лише-змінні'],cwd=repo,env=baseenv,encoding='utf-8'))
 server=subprocess.Popen([sys.executable,'-u',str(repo/'аудит/проби/replay_сцени.py'),str(repo/'аудит/проби/Корені-нуль-живе-мірило-1511'/scene),'0'],cwd=repo/'аудит/проби',env=baseenv,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,encoding='utf-8')
 with (d/'повтор.log').open('w',encoding='utf-8') as replaylog:
  try:
   for line in server.stdout:
    replaylog.write(line);replaylog.flush()
    if line.startswith('REPLAY_READY '): address=line.split()[1];break
   else: raise RuntimeError('replay server failed')
   import threading
   def read_server():
    for line in server.stdout: replaylog.write(line);replaylog.flush()
   reader=threading.Thread(target=read_server);reader.start()
   env=dict(baseenv,**{k:v for k,v in config.items() if k not in ('MODEL','MODEL_MOVA')})
   env.update(MODEL='claude-sonnet-5-5',MODEL_MOVA='claude-sonnet-5-5',MODEL_URL=address,VIDPOVIDI=str(d/'VIDPOVIDI'),ZNIMKY=str(d/'знімки'),ZVIT_OUT=str(d/'вердикти.txt'),NODE_PATH='C:/Users/gemini/kod-shi-test-node/node_modules',FOTO='1')
   env.pop('CHROMIUM',None)
   with (d/'лог.txt').open('w',encoding='utf-8') as log:
    r=subprocess.run(['node',str(repo/'аудит/проби/рв6_стенд.js'),'http://127.0.0.1:18849',str(build),'C:/Users/gemini/pyodide','3'],cwd=repo,env=env,stdout=log,stderr=subprocess.STDOUT)
   print(json.dumps(dict(scene=scene,code=r.returncode,tail=(d/'лог.txt').read_text(encoding='utf-8').splitlines()[-10:]),ensure_ascii=False),flush=True)
  finally:
   server.terminate();server.wait()
   if 'reader' in locals(): reader.join()
