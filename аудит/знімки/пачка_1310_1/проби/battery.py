import os, subprocess, pathlib, json, time, py_compile
root=pathlib.Path('/tmp/liusterko-pachka-1310-1'); src=root/'джерела'; out=pathlib.Path('/tmp/pachka-1310-evidence/батарея'); out.mkdir(parents=True,exist_ok=True)
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()=='09ff6b7b5a46327666d633e1ba798f249941bb4d'
env=dict(os.environ,NODE_PATH='/tmp/959-node-deps/node_modules:'+os.environ.get('NODE_PATH',''))
steps=[]
def run(name,command,cwd=src):
    t=time.time()
    with (out/(name+'.log')).open('w') as log:
        p=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
    row=dict(етап=name,код=p.returncode,секунди=round(time.time()-t,1)); steps.append(row)
    (out/'результати.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2)); print(row,flush=True)
    if p.returncode: raise SystemExit(p.returncode)
start=time.time()
for file in src.rglob('*.py'):
    if 'node_modules' not in file.parts: py_compile.compile(str(file),doraise=True)
for file in src.rglob('*.js'):
    if 'node_modules' not in file.parts: subprocess.run(['node','--check',str(file)],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,check=True)
print('Синтаксис Python/JS: 0 помилок',flush=True)
for file in sorted((src/'проби').glob('поділ_*_ast.py')): run(file.stem,['python3',str(file)])
run('каталоги',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print(ч.забезпечити_чистим('каталог_повний.xml')); print(Ф.каталог_на_диску('каталог_brief.xml'))"])
for name,command in [('дим',['python3','стенд_знімок.py','--дим']),('живий_шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('міст',['node','тест_мосту.js']),('досяжність',['python3','досяжність.py'])]: run(name,command)
assert '«НІХТО» = 0' in (out/'досяжність.log').read_text()
print('Повна батарея ОДИН раз на frozen HEAD: усі етапи0; «НІХТО»0; секунд',round(time.time()-start,1),flush=True)
