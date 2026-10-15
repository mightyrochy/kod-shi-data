from pathlib import Path
import subprocess,hashlib,json,os
root=Path('/workspace/scratch/pachka-1510-2');repo=root/'repo';out=root/'evidence';head='f2e099e85f8b2238e9898ec3833d6c80f6f5ba20';archive='d085d7f855a88b5ca3537d6233dc276162004314';prefix='перевірка/пачка-1510-2/'
os.environ['GIT_NO_LAZY_FETCH']='1'
def git(*args):return subprocess.check_output(['git','-c','core.quotepath=false','-C',str(repo),*args])
manifest=json.loads((out/'SHA256.json').read_text());names={p.name for p in out.iterdir() if p.is_file()};assert names==set(manifest)|{'SHA256.json'}
for name in names:
 data=(out/name).read_bytes();assert git('show',archive+':'+prefix+name)==data
 if name!='SHA256.json':assert hashlib.sha256(data).hexdigest()==manifest[name]
assert git('hash-object',str(out/'SHA256.json')).decode().strip()=='a6d17c816677071de3b6376078760aced44bb855'
assert git('hash-object',str(out/'стан_батареї.json')).decode().strip()=='56efcf9244fb2112940ddb2cd6ea665520fdda59'
assert git('rev-parse',archive+'^').decode().strip()==head
changed=git('diff','--name-only',head,archive).decode().splitlines();assert set(changed)=={prefix+n for n in names}
state=json.loads((out/'стан_батареї.json').read_text());assert state['head']==head and state['status']=='finished' and state['current'] is None and state['finished']>state['started']
steps=state['steps'];assert len(steps)==11 and len({s['name'] for s in steps})==11
log=(out/'батарея.log').read_text()
for s in steps:
 assert s['finished'] is True and s['rc']==0 and s['command'] and s['seconds']>0
 assert (out/(s['name']+'.log')).stat().st_size>0
 assert log.count('ПОЧАТОК '+s['name']+'\n')==1 and log.count('КІНЕЦЬ '+s['name']+' rc 0\n')==1
assert 'ПРОЙДЕНО 575, ВПАЛО 0, БЕЗ ВХОДУ 0' in (out/'розділи_гейтів.log').read_text()
assert 'ВИКОНАНО ЗВІРОК: 731 у 64 розділах' in (out/'показ.log').read_text()
assert '«НІХТО» = 0' in (out/'досяжність.log').read_text()
provenance=json.loads((out/'походження.json').read_text());assert provenance['head']==head
for p,v in provenance['files'].items():
 data=git('show',head+':'+p);assert hashlib.sha256(data).hexdigest()==v['sha256'] and git('rev-parse',head+':'+p).decode().strip()==v['git_blob']
assert not git('status','--porcelain')
result={'head':head,'archive':archive,'archive_parent_exact':True,'archive_files':len(names),'manifest_entries':len(manifest),'all_archive_blobs_local_and_hash_exact':True,'remote_manifest_and_checkpoint_blobs_exact':True,'proof_only_diff':True,'steps':len(steps),'finished_rc0':True,'elapsed_seconds':round(state['finished']-state['started'],2),'no_repeat_steps_in_log':True,'source_provenance_exact':True,'worktree_clean':True,'ci_acceptance':'окремий гейт root','verdict':'FINAL BODY/ARCHIVE PASS'}
Path('/workspace/scratch/qa1056-independent/final-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
