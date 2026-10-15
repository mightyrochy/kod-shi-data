import pathlib,os,signal,subprocess,json,time,hashlib
p=pathlib.Path('/dev/shm/broken5571/r3');r=pathlib.Path('/dev/shm/broken5571/repo/джерела');pid=795568;child=796358
assert b'/dev/shm/broken5571/r3/affected.py' in pathlib.Path(f'/proc/{pid}/cmdline').read_bytes()
s=pathlib.Path(f'/proc/{child}/stat').read_text();a=s[s.rfind(')')+2:].split();assert a[0]=='Z' and int(a[49])==0
st=json.loads((p/'affected-state.json').read_text());state=st['перевірки'];assert len(state)==5
state.append(dict(команда=['python3','тест_живого_шляху.py'],код=0,секунд=None,журнал=str(p/'affected-5.log'),примітка='Exit status0 independently read from own finished child /proc field52; 6/6 log. Parent paused before wait collected status.'))
(p/'continuation-provenance.json').write_text(json.dumps(dict(SHA=st['SHA'],parent=pid,child=child,child_exit_code=0,reason='RAM coordination: parent paused; finished child exit0 verified before ending only own runner; logical battery continues unrun Python stages then pauses before node. No stage repeated.',completed=list(range(6))),ensure_ascii=False,indent=2));os.kill(pid,signal.SIGKILL)
e={**os.environ,'TMPDIR':str(p/'tmp'),'NODE_PATH':'/workspace/kod-shi-data/джерела/node_modules','PYTHONDONTWRITEBYTECODE':'1','GIT_NO_LAZY_FETCH':'1'}
checks=[(6,['python3','тест_протоколу.py']),(7,['python3','прилади/розділи_гейтів.py']),(8,['python3','audit_contracts.py']),(10,['python3','проби/поділ_суд_ast.py'])]
for i,cmd in checks:
 log=p/f'affected-{i}.log';t=time.time()
 with log.open('w') as f:rc=subprocess.run(cmd,cwd=r,env=e,stdout=f,stderr=subprocess.STDOUT).returncode
 state.append(dict(команда=cmd,код=rc,секунд=round(time.time()-t,2),журнал=str(log)))
 (p/'affected-state.json').write_text(json.dumps(dict(SHA=st['SHA'],стан='running-python-continuation',перевірки=state),ensure_ascii=False,indent=2));print(i,rc,cmd,flush=True)
st.update(стан='paused-before-node9-memory-token',перевірки=state);(p/'affected-state.json').write_text(json.dumps(st,ensure_ascii=False,indent=2));print('PAUSED before node9; all Python complete',flush=True)
