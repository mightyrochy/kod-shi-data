from pathlib import Path
import subprocess,os,json,time,hashlib
root=Path('/workspace/work/f2-28-base');out=Path('/workspace/work/f2-28-results/before');deps=Path('/workspace/work/f1-final/джерела/node_modules');assert deps.is_dir()
link=root/'джерела/node_modules'
if not link.exists():link.symlink_to(deps,target_is_directory=True)
env=dict(os.environ,LYUSTERKO_CATALOG='повний',NODE_PATH=str(deps))
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();assert head=='d649496442fbeac065201c3666ec53c172eff10f'
meta={'head':head,'purpose':'one shared DO for step2.8 A+B; no live/photo acceptance','inputs':'frozen seed3 124 calls','build_started':time.time()}
with (out/'build.log').open('w') as log:r=subprocess.run(['python3','build_артефакт.py','.',str(out/'index.html'),'показ-повний'],cwd=root/'джерела',env=env,stdout=log,stderr=subprocess.STDOUT)
meta.update(build_rc=r.returncode,build_seconds=time.time()-meta['build_started']);(out/'метадані.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');assert r.returncode==0
meta['html_sha256']=hashlib.sha256((out/'index.html').read_bytes()).hexdigest()
with (out/'snapshot.log').open('w') as log:r=subprocess.run(['node','джерела/прилади/знімок_мосту_pyodide.js',str(out/'index.html'),'/workspace/work/pyodide','аудит/проби/знімок_входи_сід3.jsonl.gz',str(out/'snapshot')],cwd=root,env=env,stdout=log,stderr=subprocess.STDOUT)
meta['snapshot_rc']=r.returncode;meta['snapshot_sha256']=hashlib.sha256((out/'snapshot/знімок.jsonl').read_bytes()).hexdigest();(out/'метадані.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n');assert r.returncode==0
