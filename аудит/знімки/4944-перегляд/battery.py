import json, os, pathlib, subprocess, time
root=pathlib.Path('/workspace/scratch/4944-aa-next-evidence');repo=pathlib.Path('/workspace/scratch/4944-aa-next/repo');src=repo/'джерела'
env=dict(os.environ,TMPDIR='/workspace/scratch/4944-aa-next-tmp',NODE_PATH='/workspace/kod-shi-data/джерела/node_modules',GIT_NO_LAZY_FETCH='1',PYTHONDONTWRITEBYTECODE='1')
head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip();(root/'battery-head.txt').write_text(head+'\n')
steps=[
('prepare',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print('фід:', ч.забезпечити_чистим('каталог_повний.xml')); print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]),
('syntax',['python3','-c',"import pathlib,subprocess,sys,ast; paths=list(pathlib.Path('.').rglob('*')); py=[p for p in paths if p.suffix=='.py' and 'node_modules' not in p.parts]; js=[p for p in paths if p.suffix=='.js' and 'node_modules' not in p.parts]; [ast.parse(p.read_text(),filename=str(p)) for p in py]; checks=[subprocess.run(['node','--check',str(p)]).returncode for p in js]; print('Python',len(py),'JavaScript',len(js),'fails',sum(checks)); sys.exit(bool(sum(checks)))"]),
('split',['bash','-c','failed=0; for f in проби/поділ_*_ast.py; do python3 "$f" || failed=$((failed+1)); done; echo "ВПАЛО $failed"; test "$failed" -eq 0']),
('smoke',['python3','стенд_знімок.py','--дим']),('path',['python3','тест_живого_шляху.py']),('protocol',['python3','тест_протоколу.py']),('gates',['python3','прилади/розділи_гейтів.py']),('contracts',['python3','audit_contracts.py']),('display',['node','тест_показу.js']),('bridge',['node','тест_мосту.js']),('reach',['python3','досяжність.py'])]
state={'head':head,'started':time.time(),'steps':[]};status=root/'battery-status.json'
for name,cmd in steps:
 item={'name':name,'command':cmd,'cwd':str(src),'started':time.time(),'status':'running'};state['steps'].append(item);status.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n')
 with (root/f'battery-{name}.log').open('w') as log:
  result=subprocess.run(cmd,cwd=src,env=env,stdout=log,stderr=subprocess.STDOUT)
 item.update(status='finished',returncode=result.returncode,finished=time.time());status.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');print(name,result.returncode,flush=True)
state.update(finished=time.time(),success=all(s['returncode']==0 for s in state['steps']));status.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');raise SystemExit(not state['success'])
