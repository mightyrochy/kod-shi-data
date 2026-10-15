import pathlib, subprocess, os, json, time, hashlib, datetime, sys
p=pathlib.Path('/dev/shm/live5238');r=p/'repo/джерела';sha=(p/'SHA').read_text().strip();frozen=json.loads((p/('frozen-source-'+sha[:8]+'.json')).read_text());state=[]
e={**os.environ,'TMPDIR':str(p/'tmp'),'NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','PYTHONDONTWRITEBYTECODE':'1','GIT_NO_LAZY_FETCH':'1'}
started=datetime.datetime.now(datetime.timezone.utc).isoformat()
checks=[['python3','стенд_знімок.py','--дим'],['python3','тест_живого_шляху.py'],['python3','тест_протоколу.py'],['python3','прилади/розділи_гейтів.py'],['python3','audit_contracts.py'],['node','тест_показу.js'],['python3','проби/повнота_вибір_прийняття.py']]
assert subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip()==sha
for i,cmd in enumerate(checks):
    unchanged=all(hashlib.sha256((p/'repo'/f).read_bytes()).hexdigest()==h for f,h in frozen.items());assert unchanged
    log=p/f'батарея-{i}.log';start=time.time()
    with log.open('w') as out:rc=subprocess.run(cmd,cwd=r,env=e,stdout=out,stderr=subprocess.STDOUT).returncode
    head=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD'],text=True).strip();assert head==sha
    state.append(dict(команда=cmd,код=rc,секунд=round(time.time()-start,2),журнал=str(log),source_unchanged=unchanged,SHA=head))
    (p/'батарея-стан.json').write_text(json.dumps(dict(SHA=sha,стан='running',перевірки=state),ensure_ascii=False,indent=2));print(i,rc,cmd,flush=True)
unchanged=all(hashlib.sha256((p/'repo'/f).read_bytes()).hexdigest()==h for f,h in frozen.items())
passed=unchanged and all(x['код']==0 for x in state)
(p/'батарея-фінал.json').write_text(json.dumps(dict(SHA=sha,tree=subprocess.check_output(['git','-C',str(r),'rev-parse','HEAD^{tree}'],text=True).strip(),стан='completed',passed=passed,source_unchanged=unchanged,почато=started,завершено=datetime.datetime.now(datetime.timezone.utc).isoformat(),перевірки=state,модельних_запусків=0),ensure_ascii=False,indent=2))
sys.exit(not passed)
