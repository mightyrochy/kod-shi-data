from pathlib import Path
import json,hashlib,re,sys
ROOT=Path('/dev/shm/qa-updates-1045-1056');A=Path('/dev/shm/update-after-1045-1056/archive');sys.path.insert(0,str(ROOT));from composition import tree
remote=json.loads((ROOT/'final-author-tree.json').read_text());assert not remote['truncated'];prefix='перевірка/оновлення-1510-1045-1056/';files={x['path'][len(prefix):]:x for x in remote['tree'] if x['type']=='blob' and x['path'].startswith(prefix)};assert len(files)==48
local={p.name:p for p in A.iterdir() if p.is_file()};assert set(local)==set(files)
manifest=json.loads((A/'SHA256.json').read_text());assert len(manifest)==47 and set(manifest)==set(local)-{'SHA256.json'}
for n,p in local.items():
 b=p.read_bytes();assert files[n]['sha']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() and files[n]['mode']=='100644' and files[n]['size']==len(b),(n,'remote bytes')
 if n in manifest:assert manifest[n]==dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)),(n,'manifest')
main=tree('47ac855c51b249c6112f0ba0ca64924a50bc32e4');foreign={x['path']:(x['mode'],x['type'],x['sha']) for x in remote['tree'] if x['type']=='blob' and not x['path'].startswith(prefix)};assert main==foreign,('nonproof product changed',len(main),len(foreign))
current=json.loads((ROOT/'final-current15.json').read_text());old={d['pr']:d for d in json.loads((ROOT/'initial-old15.json').read_text())};fm=json.loads((A/'FROZEN-map.json').read_text());rows=[]
for d in current:
 n=d['pr'];b=d['body'].encode();expected=(A/f'body-{n}.txt').read_bytes();prior=(A/f'body-before-{n}.txt').read_bytes();assert b==expected,(n,'body bytes');assert prior==old[n]['body'].encode(),(n,'old history mismatch');assert b.count(prior)==1,(n,'history occurrence');assert d['head']==fm[str(n)]['sha'] and d['base']=='47ac855c51b249c6112f0ba0ca64924a50bc32e4';assert d['draft']==(n not in [1078,1079]);intro=d['body'].split('<details>',1)[0];assert d['head'] in intro;assert '741/65' in intro and ('не заявля' in intro or 'не зая' in intro);assert 'crop' in intro.lower() and 'transient' in intro.lower();assert 'pending' in intro or 'in_progress' in intro or 'CI' in intro
 if n==1083:assert all(t in intro for t in ['НЕ ПРИЙНЯТО','5238','6195210802','07','10','пауз','поза пачками'])
 if n==1074:assert '5571' in intro and ('частков' in intro.lower() or 'PARTIAL' in intro) and ('3' in intro or 'три' in intro)
 if n==991:assert '17' in intro and ('скасован' in intro or 'скасовано' in intro) and 'пауз' in intro
 if n==965:assert 'TECH' in intro and '4960' in intro
 if n==1048:assert 'UNGRADABLE' in intro and '0/40' in intro
 rows.append(dict(pr=n,head=d['head'],body_bytes=len(b),body_sha256=hashlib.sha256(b).hexdigest(),body_CR_count=b.count(b'\r'),body_utf8_exact=True,old_history_utf8_exact=True,body_before_bytes=len(prior),draft_exact=True))
result=dict(archive_commit='156ba1bf2fdf78759a94dde972d4ce0737e0f7c3',archive_tree=remote['sha'],files=48,sha256_entries=47,all_remote_blob_bytes_modes_exact=True,all_nonproof_product_files_main_exact=len(main),body_rows=rows,heads_unchanged=True,ci='не оцінено; окремий exact-head гейт координатора',tests_repeated=0)
(ROOT/'final-metadata.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(archive=48,sha256=47,body=15,old_history=15,product_files_main_exact=len(main),PASS=True)))
