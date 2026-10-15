from pathlib import Path
import json,hashlib,sys
ROOT=Path('/dev/shm/qa-updates-1077');A=Path('/dev/shm/update-after-1077/archive');sys.path.insert(0,str(ROOT));from composition import tree
r=json.loads((ROOT/'final-author-tree.json').read_text());assert not r['truncated'];prefix='перевірка/оновлення-1510-1077/';remote={x['path'][len(prefix):]:x for x in r['tree'] if x['type']=='blob' and x['path'].startswith(prefix)};local={p.name:p for p in A.iterdir() if p.is_file()};assert len(remote)==47 and set(remote)==set(local)
m=json.loads((A/'SHA256.json').read_text());assert len(m)==46 and set(m)==set(local)-{'SHA256.json'}
for n,p in local.items():
 b=p.read_bytes();assert remote[n]['sha']==hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest() and remote[n]['mode']=='100644' and remote[n]['size']==len(b),(n,'remote bytes')
 if n in m:assert m[n]==dict(sha256=hashlib.sha256(b).hexdigest(),bytes=len(b)),(n,'manifest')
main=tree('32395d4239a2758c3293ee4e605364e28bc8dc94');foreign={x['path']:(x['mode'],x['type'],x['sha']) for x in r['tree'] if x['type']=='blob' and not x['path'].startswith(prefix)};assert main==foreign,(len(main),len(foreign),'product changed')
current=json.loads((ROOT/'final-current17.json').read_text());old={d['pr']:d for d in json.loads((ROOT/'initial17.json').read_text())};fm=json.loads((A/'FROZEN-map.json').read_text());rows=[]
for d in current:
 n=d['pr'];b=d['body'].encode();expected=(A/f'body-{n}.txt').read_bytes();prior=(A/f'body-before-{n}.txt').read_bytes();assert b==expected,(n,'actual body bytes');assert prior==old[n]['body'].encode(),(n,'original old body history');assert b.count(prior)==1,(n,'history occurrence');assert d['head']==fm[str(n)]['sha'] and d['base']=='32395d4239a2758c3293ee4e605364e28bc8dc94';assert d['draft']==old[n]['draft'];intro=d['body'].split('\n---\n',1)[0];assert d['head'] in intro and '32395d4239a2758c3293ee4e605364e28bc8dc94' in intro and 'CI' in intro
 if n==1083:assert all(s in intro for s in ['НЕ ПРИЙНЯТО','5238','07','10','поза пачками']) and ('пауз' in intro.lower() or 'PAUSE' in intro)
 if n==1074:assert '5571' in intro and ('partial' in intro.lower() or 'частков' in intro.lower())
 if n==1048:assert 'UNGRADABLE' in intro and ('0/40' in intro or 'PHOTO0' in intro)
 if n==965:assert ('TECH' in intro or 'HOLD #965' in intro) and '4960' in intro and 'ВІДКРИТО' in intro
 if n in [1088,1089]:assert 'LIVE pending' in intro and 'поза продуктовими пачками' in intro
 if n==1088:assert 'ВІДКРИТО' in intro
 rows.append(dict(pr=n,head=d['head'],body_bytes=len(b),body_sha256=hashlib.sha256(b).hexdigest(),body_CR_count=b.count(b'\r'),actual_utf8_exact=True,old_history_utf8_exact=True,draft_exact=True))
proof=dict(archive_commit='322c266217abb462338127da642e52d8fcfcdc7f',archive_tree=r['sha'],files=47,sha256_entries=46,all_remote_blobs_bytes_modes_exact=True,nonproof_product_files_main_exact=len(main),body_rows=rows,heads_unchanged=True,old_history17_exact=True,ci='не оцінено; окремий exact-head гейт координатора',new_tests_build_native=0)
(ROOT/'final-metadata.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(dict(PASS=True,archive=47,SHA256=46,actualbody=17,oldhistory=17,nonproofmain=len(main))))
