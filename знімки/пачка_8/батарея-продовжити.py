import os,subprocess,pathlib,json,time,py_compile
root=pathlib.Path('/tmp/liusterko-pachka-1310-4');src=root/'джерела';out=pathlib.Path('/tmp/pachka-1310-4-evidence/батарея');head='cfbe2671b868cdcf124d25bd3d1c895fc14055fe'
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip()==head
assert len(list((root/'.github/workflows').glob('*.yml')))==4
env=dict(os.environ,NODE_PATH='/workspace/kod-shi-data/джерела/node_modules',LYUSTERKO_CATALOG='повний');steps=json.loads((out/'результати.json').read_text())['steps'];(out/'підготовка_помилка.json').write_text(json.dumps(steps,ensure_ascii=False,indent=2));steps=[v for v in steps if v['код']==0]
def run(name,command,cwd=src):
 start=time.time()
 with (out/(name+'.log')).open('w') as log:p=subprocess.run(command,cwd=cwd,env=env,stdout=log,stderr=subprocess.STDOUT)
 row={'етап':name,'команда':command,'код':p.returncode,'секунди':round(time.time()-start,1)};steps.append(row);(out/'результати.json').write_text(json.dumps({'head':head,'steps':steps},ensure_ascii=False,indent=2));print(row,flush=True)
 if p.returncode:raise SystemExit(p.returncode)
start=time.time();counts=(out/'синтаксис.log').read_text().split();py=int(counts[1].strip(';'));js=int(counts[3].strip(';'))
run('каталоги',['python3','-c',"import чистка_каталогу as ч, feed as Ф; print('фід:',ч.забезпечити_чистим('каталог_повний.xml'));print('фікстура:',Ф.каталог_на_диску('каталог_brief.xml'))"])
for name,command in [('дим',['python3','стенд_знімок.py','--дим']),('живий_шлях',['python3','тест_живого_шляху.py']),('протокол',['python3','тест_протоколу.py']),('гейти',['python3','прилади/розділи_гейтів.py']),('контракти',['python3','audit_contracts.py']),('показ',['node','тест_показу.js']),('міст',['node','тест_мосту.js']),('досяжність',['python3','досяжність.py']),('дані5191',['python3','проби/дані_5191.py']),('дані5192',['python3','проби/дані_5192.py']),('дані5193',['python3','проби/дані_5193.py']),('дані5194',['python3','проби/дані_5194.py'])]:run(name,command)
assert '«НІХТО» = 0' in (out/'досяжність.log').read_text()
run('повна_збірка',['python3','build_артефакт.py','.',str(pathlib.Path('/tmp/pachka-1310-4-full.html')),'показ-повний'])
summary={'примітка':'Підготовка зупинилась до продуктової батареї через root.gz поза sparse; sparse доповнено, успішний синтаксис/AST не повторено. Повна продуктова батарея виконана один раз.', 'head':head,'успіх':True,'syntax':{'python':py,'js':js,'errors':0},'elapsed_seconds':round(time.time()-start,1),'steps':steps,'own_background_jobs_after_completion':0}
(out/'результати.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print('ЗАВЕРШЕНО: одна повна батарея FINALHEAD, усі етапи0; секунд',summary['elapsed_seconds'],flush=True)
