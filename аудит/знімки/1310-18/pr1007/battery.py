import os,sys,json,subprocess,time,hashlib
from pathlib import Path
root=Path('/workspace/reasons4390');src=root/'джерела';proof=Path('/workspace/reasons4390-evidence');head='c15ce2c41cb1e2ac7df586ca9ad0a497d299e052'
env=dict(os.environ,TMPDIR='/workspace/reasons4390-tmp',PYTHONDONTWRITEBYTECODE='1',PYTHONPYCACHEPREFIX='/workspace/reasons4390-tmp/pycache',NODE_PATH=str(src/'node_modules'))
stages=[('syntax-python',['python3','-c',"import pathlib,py_compile;[py_compile.compile(str(p),doraise=True) for p in pathlib.Path('.').rglob('*.py') if 'node_modules' not in p.parts]"]),('syntax-js',['python3','-c',"import pathlib,subprocess;[subprocess.run(['node','--check',str(p)],check=True) for p in pathlib.Path('.').rglob('*.js') if 'node_modules' not in p.parts]"]),('ast',['python3','-c',"import pathlib,subprocess;[subprocess.run(['python3',str(p)],check=True) for p in sorted(pathlib.Path('проби').glob('поділ_*_ast.py'))]"]),('prepare',['python3','-c',"import чистка_каталогу as Ч,feed as Ф;print(Ч.забезпечити_чистим('каталог_повний.xml'));print(Ф.каталог_на_диску('каталог_brief.xml'))"]),('snapshot',['python3','стенд_знімок.py','--дим']),('live-path',['python3','тест_живого_шляху.py']),('protocol',['python3','тест_протоколу.py']),('gates',['python3','прилади/розділи_гейтів.py']),('contracts',['python3','audit_contracts.py']),('display',['node','тест_показу.js'])]
check=proof/'battery-checkpoints.jsonl'
def record(**d):
 d.update(head=head,time=time.time(),runner_pid=os.getpid());check.open('a').write(json.dumps(d,ensure_ascii=False)+'\n')
record(state='start')
for name,cmd in stages:
 actual=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
 if actual!=head:record(stage=name,state='head_changed',actual=actual);sys.exit(2)
 with (proof/('battery-'+name+'.log')).open('w') as log:
  p=subprocess.Popen(cmd,cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT);record(stage=name,state='running',pid=p.pid,command=cmd)
  rc=p.wait();record(stage=name,state='completed',pid=p.pid,rc=rc)
 print(name,'rc',rc,flush=True)
 if rc:sys.exit(rc)
record(state='done',rc=0)
