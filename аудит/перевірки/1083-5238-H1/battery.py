import pathlib, subprocess, os, json, time, hashlib
p=pathlib.Path('/dev/shm/live5238');r=p/'repo/джерела';sha=(p/'SHA').read_text().strip();frozen=json.loads((p/'frozen-source-762ab830.json').read_text());state=[]
e={**os.environ,'TMPDIR':str(p/'tmp'),'NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','PYTHONDONTWRITEBYTECODE':'1','GIT_NO_LAZY_FETCH':'1'}
checks=[['python3','стенд_знімок.py','--дим'],['python3','тест_живого_шляху.py'],['python3','тест_протоколу.py'],['python3','прилади/розділи_гейтів.py'],['python3','audit_contracts.py'],['node','тест_показу.js'],['python3','проби/повнота_вибір_прийняття.py']]
assert subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip()==sha
for i,cmd in enumerate(checks):
    unchanged=all(hashlib.sha256((p/'repo'/f).read_bytes()).hexdigest()==h for f,h in frozen.items());assert unchanged
    log=p/f'батарея-{i}.log';start=time.time()
    with log.open('w') as out:rc=subprocess.run(cmd,cwd=r,env=e,stdout=out,stderr=subprocess.STDOUT).returncode
    state.append(dict(команда=cmd,код=rc,секунд=round(time.time()-start,2),журнал=str(log),source_unchanged=unchanged))
    (p/'батарея-стан.json').write_text(json.dumps(dict(SHA=sha,стан='running',перевірки=state),ensure_ascii=False,indent=2));print(i,rc,cmd,flush=True)
unchanged=all(hashlib.sha256((p/'repo'/f).read_bytes()).hexdigest()==h for f,h in frozen.items())
(p/'батарея-фінал.json').write_text(json.dumps(dict(SHA=sha,tree='e3289a378bdd1ecb204dc15d3f1231dad445df0b',стан='completed',source_unchanged=unchanged,перевірки=state,модельних_запусків=0),ensure_ascii=False,indent=2))
