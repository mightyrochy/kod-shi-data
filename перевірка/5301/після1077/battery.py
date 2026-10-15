import datetime,json,os,subprocess,time
from pathlib import Path
p=Path('/dev/shm/nested5301');repo=p/'repo';logs=p/'battery';logs.mkdir(exist_ok=True)
env=dict(os.environ,TMPDIR=str(p/'tmp'),PYTHONDONTWRITEBYTECODE='1',GIT_NO_LAZY_FETCH='1',NODE_PATH='/workspace/kod-shi-data/джерела/node_modules')
steps=[('snapshot',['python3','стенд_знімок.py','--дим']),('live_path',['python3','тест_живого_шляху.py']),('protocol',['python3','тест_протоколу.py']),('sections',['python3','прилади/розділи_гейтів.py']),('contracts',['python3','audit_contracts.py']),('display',['node','тест_показу.js'])]
results=[]
for name,cmd in steps:
 start=time.time();print(datetime.datetime.now(datetime.timezone.utc).isoformat(),name,'START',flush=True)
 with (logs/(name+'.log')).open('wb') as out:r=subprocess.run(cmd,cwd=repo/'джерела',env=env,stdout=out,stderr=subprocess.STDOUT)
 result={'name':name,'cmd':cmd,'rc':r.returncode,'seconds':round(time.time()-start,3)};results.append(result)
 (logs/'summary.json').write_text(json.dumps({'head':'3f84559993d3e79dc18d82c2d5ef9d3bbd1f24a4','source_identity':json.loads((p/'source-identity.json').read_text()),'results':results},ensure_ascii=False,indent=2))
 print(name,'END',result,flush=True)
print('COMPLETE',all(x['rc']==0 for x in results),flush=True)
raise SystemExit(any(x['rc']!=0 for x in results))
