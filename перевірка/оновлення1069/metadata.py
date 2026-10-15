from pathlib import Path
import sys,json,hashlib,importlib.util
spec=importlib.util.spec_from_file_location('h','/workspace/scratch/update1046/hydrate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
r=Path('/workspace/scratch/qa-update1069-independent');p=Path('/workspace/scratch/update1069');sha=sys.argv[1];outline=json.loads((p/'archive-outline.json').read_text());prefix='перевірка/оновлення-1510-1069/'
assert h.git('rev-parse',sha+'^{tree}').decode().strip()==outline['tree']
actual={}
for line in h.git('ls-tree','-rz',sha,'--',prefix).split(b'\0'):
 if line:
  meta,path=line.split(b'\t',1);mode,typ,blob=meta.decode().split();assert mode=='100644' and typ=='blob';actual[path.decode()]=blob
assert len(actual)==outline['files']==68
manifest=json.loads(h.git('show',sha+':'+prefix+'SHA256.json'));assert len(manifest)==67
for e in outline['entries']:
 assert actual[e['path']]==e['git_blob'];b=h.git('cat-file','blob',e['git_blob']);assert b==Path(e['source']).read_bytes();assert len(b)==e['bytes'];name=e['archive_name']
 if name!='SHA256.json':assert hashlib.sha256(b).hexdigest()==manifest[name]
if sha!='962b6f61848c491e5e70af9b8acfdf97afb7754a':
 changed=[x.decode() for x in h.git('diff','--name-only','-z','962b6f61848c491e5e70af9b8acfdf97afb7754a',sha).split(b'\0') if x];assert set(changed)=={prefix+f'body-{n}.txt' for n in [965,991,1037,1038,1039,1040,1045,1047,1048,1049,1056,1058,1059,1060,1067]}|{prefix+'summary.json',prefix+'SHA256.json'}
summary=json.loads(h.git('show',sha+':'+prefix+'summary.json'))
for n,d in summary.items():
 b=h.git('show',sha+':'+prefix+f'body-{n}.txt');assert b==Path(p/f'body-{n}.txt').read_bytes();assert hashlib.sha256(b).hexdigest()==d['body_sha256'];assert len(b)==d['body_bytes'];assert b.count(b'\r')==d['body_cr_count'];assert d['sha']==json.loads((r/f'{n}.json').read_text())['head']
if sha!='962b6f61848c491e5e70af9b8acfdf97afb7754a':
 receipt=json.loads((r/'receipt.json').read_text())
 for entry in receipt['comments']:
  b=h.git('show',sha+':'+prefix+f"body-{entry['n']}.txt");assert str(entry['id']).encode() in b and receipt['proof'].encode() in b
result={'archive':sha,'tree':outline['tree'],'files':68,'manifest_entries':67,'all_archived_blobs_and_bytes_exact':True,'all_manifest_sha256_exact':True,'body15_bytes_including_CRLF_exact':True,'heads15_match_independent_CONTENT':True,'remote_heads_bodies':'separate readback required','CI':'not evaluated; exact-head root gate separate','new_tests':0}
(r/'metadata-local.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
