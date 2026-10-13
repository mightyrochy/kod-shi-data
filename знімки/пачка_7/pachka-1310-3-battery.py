import os,subprocess,pathlib,json,time,py_compile
root=pathlib.Path('/tmp/liusterko-pachka-1310-3');src=root/'джерела';out=pathlib.Path('/tmp/pachka-1310-3-evidence/батарея');head='af1ab8c37eeb45469646e715c8640f5ab5b86c2d'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()==head
assert len(list((root/'.github/workflows').glob('*.yml')))==4
env=dict(os.environ,NODE_PATH='/tmp/959-node-deps/node_modules',LYUSTERKO_CATALOG='повний');steps=[]
def run(name,command,cwd=src):
 start=time.time()
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
 row={'етап':name,'команда':command,'код':p.returncode,'секунди':round(time.time()-start,1)};steps.append(row);(out/'результати.json').write_text(json.dumps({'head':head,'steps':steps},ensure_ascii=False,indent=2));print(row,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
start=time.time();py=0;js=0
with (out/'синтаксис.log').open('w') as log:
 for f in src.rglob('*.py'):
  if 'node_modules' not in f.parts:py_compile.compile(str(f),doraise=True);py+=1
 for f in src.rglob('*.js'):
  if 'node_modules' not in f.parts:subprocess.run(['node','--check',str(f)],stdout=log,stderr=log,check=True);js+=1
 log.write(f'Python {py}; JS {js}; помилок0\n')
print(f'Синтаксис Python{py}/JS{js}:0 помилок',flush=True)
for f in sorted((src/'проби').glob('поділ_*_ast.py')):run(f.stem,['python3',str(f)])
run('каталоги',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print('фід:',ч.забезпечити_чистим('каталог_повний.xml'));print('фікстура:',Ф.каталог_на_диску('каталог_brief.xml'))"])
for name,command in [('дим',['python3','стенд_знімок.py','--дим']),('живий_шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('міст',['node','тест_мосту.js']),('досяжність',['python3','досяжність.py']),('holos5205',['node','проби/holos_5205.js']),('holos167',['node','проби/holos_167.js'])]:run(name,command)
assert '«НІХТО» = 0' in (out/'досяжність.log').read_text()
run('повна_збірка',['python3','build_артефакт.py','.',str(pathlib.Path('/tmp/pachka-1310-3-full.html')),'показ-повний'])
summary={'head':head,'успіх':True,'syntax':{'python':py,'js':js,'errors':0},'elapsed_seconds':round(time.time()-start,1),'steps':steps,'own_background_jobs_after_completion':0}
(out/'результати.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('ЗАВЕРШЕНО: одна повна батарея FINALHEAD, усі етапи0; секунд',summary['elapsed_seconds'],flush=True)
