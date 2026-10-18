"""Точні артефакти та всі зміни фінального 0.2 без повторного виконання продукту."""
from pathlib import Path
import json,hashlib,re,base64,zipfile,io,gzip,collections
root=Path('/workspace/work/f2-210');out=root/'work/final-after'
canon=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
old=[json.loads(s) for s in Path('/workspace/work/baseline-results/main-1.jsonl').read_text().splitlines()]
new=[json.loads(s) for s in (out/'snapshot.jsonl').read_text().splitlines()]
assert old[0]==new[0] and len(old)==len(new)==125
changes=[]
for a,b in zip(old[1:],new[1:]):
 assert (a['н'],a['ім'])==(b['н'],b['ім'])
 assert 'помилка' not in b,(b['н'],b)
 if a!=b:
  va,vb=a['результат'],b['результат']
  keys=sorted(k for k in va.keys()|vb.keys() if va.get(k)!=vb.get(k)) if isinstance(va,dict) and isinstance(vb,dict) else ['<value>']
  changes.append({'н':a['н'],'ім':a['ім'],'changed_top_keys':keys})
baseline12=next(r['результат'] for r in old[1:] if r['н']==12)
final12=next(r['результат'] for r in new[1:] if r['н']==12)
cp=json.loads((root/'work/compact/call12.json').read_text())
fields={}
for field in ['кандидати','кандидати_донора']:
 rows=lambda r:[v for group in r[field].values() for v in group]
 before={r['id']:r for r in rows(baseline12)};after={r['id']:r for r in rows(final12)}
 fields[field]={'before_rows':len(rows(baseline12)),'after_rows':len(rows(final12)),'before_unique':len(before),'after_unique':len(after),'common':len(before.keys()&after.keys()),'changed_old_fields':sum(canon({k:v for k,v in after[i].items() if k!='знання'})!=canon(before[i]) for i in before.keys()&after.keys()),'cp_identical':canon(final12[field])==canon(cp[field])}
artifacts=[];zs=[]
for p in [Path('/workspace/work/p1-before/index.html'),out/'index.html']:
 raw=base64.b64decode(re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"',p.read_text())[1]);z=zipfile.ZipFile(io.BytesIO(raw));zs.append(z)
 artifacts.append({'path':str(p),'html_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'html_bytes':p.stat().st_size,'zip_sha256':hashlib.sha256(raw).hexdigest(),'zip_entries':len(z.namelist()),'py_modules':sum(s.endswith('.py') for s in z.namelist())})
zipdiff=[]
for k in sorted(set(zs[0].namelist())|set(zs[1].namelist())):
 a=zs[0].read(k) if k in zs[0].namelist() else None;b=zs[1].read(k) if k in zs[1].namelist() else None
 if a!=b:zipdiff.append(k)
ca,cb=[json.loads(gzip.decompress(z.read('каталог_таблиця.json.gz'))) for z in zs]
catkeys=[k for k in ca if ca[k]!=cb[k]]
assert catkeys==['ключ'];ca.pop('ключ');cb.pop('ключ');assert ca==cb
proof={'source_head':(out/'source-head.txt').read_text().strip(),'input_header':old[0],'calls':124,'different_calls':len(changes),'by_endpoint':dict(collections.Counter(c['ім'] for c in changes)),'changes':changes,'fields':fields,'artifacts':artifacts,'zip_changed_entries':zipdiff,'catalog_changed_keys':catkeys,'same_catalog_payload_sha256':hashlib.sha256(canon(ca).encode()).hexdigest(),'snapshot_sha256':hashlib.sha256((out/'snapshot.jsonl').read_bytes()).hexdigest(),'cp_B_equal':final12['B']==cp['B'],'cp_C_equal':final12['C']==cp['C']}
aliases=json.loads((out/'actual-wire-aliases.json').read_text())
proof['actual_alias_summary']={h:{k:v for k,v in a.items() if isinstance(v,int)}|{'same_alias_different_sku':len(a['same_alias_different_sku'])} for h,a in aliases.items()}
proof['instrument_error']='Хибне n0 порівнювало відсутнє поле н кандидатів; actual maps виправлено окремо, початковий невдалий вимір збережено.'
for h in ['B','C']:
 a=json.loads(cp[h]);b=json.loads(final12[h]);assert a['pool']==b['pool'] and a['knowledge_legend']==b['knowledge_legend']
 a['person'].pop('palette');b['person'].pop('palette');assert a==b
proof['cp_prompt_delta_only_person_palette']=True
(out/'proof.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2))
print(json.dumps(proof,ensure_ascii=False,indent=2))
