from pathlib import Path
import sys,json,hashlib,importlib.util
spec=importlib.util.spec_from_file_location('h','/workspace/scratch/update1046/hydrate.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
r=Path('/dev/shm/qa-update1064-independent');p=Path('/workspace/scratch/update1064');sha=sys.argv[1];outline=json.loads((p/'archive-outline.json').read_text());prefix=next(e['path'][:-len(e.get('archive_name',e['name']))] for e in outline['entries'] if e.get('archive_name',e['name'])=='SHA256.json')
assert h.git('rev-parse',sha+'^{tree}').decode().strip()==outline['tree'];actual={}
for line in h.git('ls-tree','-rz',sha,'--',prefix).split(b'\0'):
 if line:
  meta,path=line.split(b'\t',1);mode,typ,blob=meta.decode().split();assert mode=='100644' and typ=='blob';actual[path.decode()]=blob
assert len(actual)==outline['files'];manifest=json.loads(h.git('show',sha+':'+prefix+'SHA256.json'));assert len(manifest)==outline['manifest_entries']
for e in outline['entries']:
 assert actual[e['path']]==e['git_blob'];b=h.git('cat-file','blob',e['git_blob']);assert b==Path(e['source']).read_bytes();assert len(b)==e['bytes'];name=e.get('archive_name',e['name'])
 if name!='SHA256.json':assert hashlib.sha256(b).hexdigest()==manifest[name]
summary=json.loads(h.git('show',sha+':'+prefix+'summary.json'));receipt=json.loads((r/'receipt.json').read_text())
for e in receipt['comments']:
 n=str(e['pr']);d=summary[n];b=h.git('show',sha+':'+prefix+f'body-{n}.txt');assert b==Path(p/f'body-{n}.txt').read_bytes();assert hashlib.sha256(b).hexdigest()==d['body_sha256'];assert len(b)==d['body_bytes'];assert b.count(b'\r')==d['body_cr_count'];assert d['sha']==e['head'];assert str(e['id']).encode() in b;assert receipt['proof'].encode() in b
result={'archive':sha,'tree':outline['tree'],'prefix':prefix,'files':len(actual),'manifest_entries':len(manifest),'all_archive_blobs_bytes_modes_sha256_exact':True,'bodies19_exact_including_CRLF_and_current_CONTENT_links':True,'heads19_match_independent_CONTENT':True,'1074':'excluded; OTHER QA','remote_readback':'required separately','CI':'not evaluated; root exact-head gate separate','new_tests':0}
(r/'metadata-local.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result))
