from pathlib import Path
import subprocess,os,json,time,hashlib
root=Path('/workspace/work/f2-28-after');out=Path('/workspace/work/f2-28-results/after');env=dict(os.environ,NODE_PATH='/workspace/work/f1-final/джерела/node_modules')
meta=json.loads((out/'метадані.json').read_text());meta['initial_build_failure']='test-only adapter Cannot redefine property містП; product HTML completed, fixed by1142fe83; no repeat build';meta['target_test_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
with (out/'target-jsdom.log').open('w') as log:r=subprocess.run(['node','джерела/тест_показу.js',str(out/'index.html')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta['target_jsdom_rc']=r.returncode;(out/'метадані.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');assert r.returncode==0
meta['html_sha256']=hashlib.sha256((out/'index.html').read_bytes()).hexdigest()
with (out/'snapshot.log').open('w') as log:r=subprocess.run(['node','джерела/прилади/знімок_мосту_pyodide.js',str(out/'index.html'),'/workspace/work/pyodide','аудит/проби/знімок_входи_сід3.jsonl.gz',str(out/'snapshot')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta['snapshot_rc']=r.returncode;meta['snapshot_sha256']=hashlib.sha256((out/'snapshot/знімок.jsonl').read_bytes()).hexdigest();(out/'метадані.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');assert r.returncode==0
