import subprocess,pathlib,os,json,time,hashlib
p=pathlib.Path('/dev/shm/broken5571/r3');r=pathlib.Path('/dev/shm/broken5571/repo/джерела');e={**os.environ,'TMPDIR':str(p/'tmp'),'NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','PYTHONDONTWRITEBYTECODE':'1','GIT_NO_LAZY_FETCH':'1'}
checks=[['python3','проби/рука2_хибні_контекст.py'],['python3','проби/рука2_хибні_суд.py'],['python3','проби/рука2_хибні_каталог.py'],['python3','проби/рука2_хибні_каталог.py','/dev/shm/broken5571/before/джерела'],['python3','стенд_знімок.py','--дим'],['python3','тест_живого_шляху.py'],['python3','тест_протоколу.py'],['python3','прилади/розділи_гейтів.py'],['python3','audit_contracts.py'],['node','тест_показу.js'],['python3','проби/поділ_суд_ast.py']]
state=[];sha=(p/'SHA').read_text().strip();frozen=json.loads((p/'frozen-source.json').read_text())
for i,cmd in enumerate(checks):
 log=p/f'affected-{i}.log';t=time.time()
 with log.open('w') as f: rc=subprocess.run(cmd,cwd=r,env=e,stdout=f,stderr=subprocess.STDOUT).returncode
 state.append({'команда':cmd,'код':rc,'секунд':round(time.time()-t,2),'журнал':str(log)})
 (p/'affected-state.json').write_text(json.dumps(dict(SHA=sha,стан='running',перевірки=state),ensure_ascii=False,indent=2));print(i,rc,cmd,flush=True)
unchanged=all(hashlib.sha256((r.parent/f).read_bytes()).hexdigest()==h for f,h in frozen.items())
(p/'affected-final.json').write_text(json.dumps(dict(SHA=sha,tree='5c6c20d7d16360dd18f6c9077c6d51bd6a822890',стан='completed',source_unchanged=unchanged,перевірки=state,модельних_запусків=0,походження='Нова перевірка зачепленого producer/judge/контрактів і актуального показу. Старі afc20 завершені й не переносяться як нові; решта13 AST не зачеплена цим ремонтом.'),ensure_ascii=False,indent=2))
