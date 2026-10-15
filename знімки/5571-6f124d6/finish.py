import subprocess,pathlib,os,json,time,hashlib
p=pathlib.Path('/dev/shm/broken5571/r3');r=pathlib.Path('/dev/shm/broken5571/repo/джерела');e={**os.environ,'TMPDIR':str(p/'tmp'),'NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','PYTHONDONTWRITEBYTECODE':'1','GIT_NO_LAZY_FETCH':'1'}
st=json.loads((p/'affected-state.json').read_text());state=st['перевірки'];assert len(state)==7 and all(x['код']==0 for x in state)
checks=[(7,['python3','прилади/розділи_гейтів.py']),(8,['python3','audit_contracts.py']),(10,['python3','проби/поділ_суд_ast.py']),(9,['node','тест_показу.js'])]
for i,cmd in checks:
 log=p/('affected-7-resumed.log' if i==7 else f'affected-{i}.log');t=time.time()
 with log.open('w') as f:rc=subprocess.run(cmd,cwd=r,env=e,stdout=f,stderr=subprocess.STDOUT).returncode
 state.append(dict(команда=cmd,код=rc,секунд=round(time.time()-t,2),журнал=str(log)))
 (p/'affected-state.json').write_text(json.dumps(dict(SHA=st['SHA'],стан='running-remaining-after-root-memory-release',перевірки=state),ensure_ascii=False,indent=2));print(i,rc,cmd,flush=True)
frozen=json.loads((p/'source-sha256.json').read_text());unchanged=all(hashlib.sha256((r.parent/f).read_bytes()).hexdigest()==h['sha256'] for f,h in frozen.items())
(p/'affected-final.json').write_text(json.dumps(dict(SHA=st['SHA'],tree='5c6c20d7d16360dd18f6c9077c6d51bd6a822890',стан='completed',source_unchanged=unchanged,перевірки=state,модельних_запусків=0,походження='Одна логічна батарея11 зачеплених етапів із checkpoint-продовженням під RAM token. Stage7 interrupted до завершення за root explicit після фактичного OOM в іншій роботі, partial log збережено; повторено тільки його. Completed0–6 не повторено. Старі afc20 окремі історичні докази, решта13AST не зачеплена.'),ensure_ascii=False,indent=2))
