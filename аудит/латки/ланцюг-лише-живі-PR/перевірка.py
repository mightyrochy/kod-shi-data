from pathlib import Path
import subprocess, os, json, sys
root=Path(r'C:/Users/gemini/gemini-runs/w/codex-3')
work=Path(r'C:/Users/gemini/gemini-runs/w/live-pr-patch')
out=root/'аудит/латки/ланцюг-лише-живі-PR'; logs=out/'журнали';logs.mkdir(exist_ok=True)
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
bash=r'C:/Program Files/Git/bin/bash.exe'
results=[]
def run(name,args,cwd):
 p=subprocess.run(args,cwd=cwd,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 s=p.stdout.decode('utf-8',errors='replace');(logs/(name+'.txt')).write_text(s,encoding='utf-8',newline='\n')
 item={'назва':name,'код':p.returncode,'✓':s.count('✓'),'✗':s.count('✗')};results.append(item)
 print(json.dumps(item,ensure_ascii=False),flush=True)
 if p.returncode: print(s[-3000:],flush=True)
 return p.returncode
mode=sys.argv[1]
if mode=='проби':
 for phase,source in [('ДО',root),('ПІСЛЯ',work)]:
  script=out/'проба.ps1'; src=source/'аудит/адаптери/gemini'
  quote=lambda s:"'"+str(s).replace("'","''")+"'"
  cmd="[Console]::OutputEncoding = New-Object Text.UTF8Encoding($false); & "+quote(script)+' -SourceDir '+quote(src)+' -Phase '+quote(phase)
  run(phase,['powershell','-NoProfile','-ExecutionPolicy','Bypass','-Command',cmd],root)
else:
 temp=Path(r'C:/Users/gemini/gemini-runs/w/live-pr-stend');temp.mkdir(exist_ok=True)
 env['TMPDIR']='/c/Users/gemini/gemini-runs/w/live-pr-stend'
 tests=sorted((work/'аудит/адаптери/gemini/перевірка').glob('сценарії_*.sh'))
 assert len(tests)==12,len(tests)
 for script in tests:
  path=script.relative_to(work).as_posix()
  run(script.stem,[bash,'-lc',"bash '"+path+"'"],work)
(out/('результати-'+mode+'.json')).write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
sys.exit(any(r['код'] or r['✗'] for r in results))
