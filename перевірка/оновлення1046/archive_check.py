from pathlib import Path
import os,json,subprocess,hashlib
p=Path('/workspace/scratch/update1046');out=Path('/workspace/scratch/qa-update1046-independent');repo='/workspace/scratch/update999/repo';main='0ccb8dbfa1b97ab3ac2ed189139a7bcfbe9ba3bc';os.environ['GIT_NO_LAZY_FETCH']='1';os.environ['GIT_ALTERNATE_OBJECT_DIRECTORIES']=os.pathsep.join(json.loads((p/'alternates.json').read_text()))
def git(*a,input=None):return subprocess.check_output(['git','-C',repo,*a],input=input)
def entries(ref):
 d={}
 for x in git('ls-tree','-rz',ref).split(b'\0'):
  if x:a,b=x.split(b'\t',1);d[b.decode()]=tuple(a.decode().split())
 return d
prep=json.loads((p/'archive-prep.json').read_text());remote=json.loads((out/'archive-remote-commit.json').read_text());assert remote['sha']=='f1f41f74c69d4047524b2335baa031756356b85e';assert remote['tree']['sha']==prep['tree'];assert [x['sha'] for x in remote['parents']]==[main]
expected=entries(main);data={}
for e in prep['entries']:
 b=e['content'].encode();sha=git('hash-object','--stdin',input=b).decode().strip();expected[e['path']]=(e['mode'],e['type'],sha);assert git('cat-file','blob',sha)==b;data[e['path'].split('/')[-1]]=b
assert entries(prep['tree'])==expected
manifest=json.loads(data['SHA256.json']);assert len(manifest)==37 and len(data)==38 and set(manifest)==set(data)-{'SHA256.json'}
for name,sha in manifest.items():assert hashlib.sha256(data[name]).hexdigest()==sha
summary=json.loads(data['summary.json']);before=json.loads((p/'remote-before.json').read_text());bodychecks={}
for n,rec in summary.items():
 t=data[f'body-{n}.txt'].decode();assert t==(p/f'body-{n}.txt').read_text();assert hashlib.sha256(t.encode()).hexdigest()==rec['body_sha256'];assert rec['sha']==json.loads((out/f'{n}.json').read_text())['head'];assert rec['sha'] in t.split('<details>')[0]
 oldbody=before[n]['pr']['body'];marker='<details><summary>Архів попереднього опису й доказів; наведені там поточні HEAD/CI/готовність стосуються попередніх SHA</summary>\n\n';archived=t.split(marker,1)[1];assert archived==oldbody.replace('\r','')+'\n\n</details>\n\n',(n,'historicalbody altered')
 top=t.split('<details>')[0];assert 'не заявлена' in top and 'новий CI' in top
 for run in rec['ci']['runs']:assert run['head_sha']==rec['sha'] and run['conclusion'] is None
 bodychecks[n]={'frozen_body_sha256':rec['body_sha256'],'old_body_text_preserved_CR_removed':True,'head_exact':True,'ci_snapshot_pending_not_green':True}
assert '6188269531' in data['body-1045.txt'].decode().split('<details>')[0] and 'не приймає' in data['body-1045.txt'].decode().split('<details>')[0]
for word in ['d085d7f855a88b5ca3537d6233dc276162004314','6188692161','38709278609']:assert word in data['body-1056.txt'].decode().split('<details>')[0]
result={'verdict':'HISTORICAL BODY/ARCHIVE PASS','scope':'checkpoint main0ccb; після main2fb809 не current-ready','archive':remote['sha'],'tree_remote_exact':True,'parent_exact':main,'proof_only_full_tree_exact':True,'files':38,'manifest_entries':37,'all_manifest_hashes_and_local_git_blobs_exact':True,'all_bodies_old_history_text_preserved':True,'old_991_CR_removed':754,'body_checks':bodychecks,'ci_acceptance':False,'product_tests_repeated':False};(out/'archive-result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
