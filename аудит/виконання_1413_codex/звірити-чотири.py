import hashlib,json,gzip,sys
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parent
paths={'main':root/'baseline/main-1.jsonl.gz', 'after12':root/'after12/snapshot.jsonl.gz', 'pre42':root/'pre42/snapshot.jsonl.gz', 'final':root/'final/snapshot.jsonl.gz'}
raw={k:gzip.decompress(p.read_bytes()) for k,p in paths.items()}
rows={k:[json.loads(s) for s in data.decode().splitlines()] for k,data in raw.items()}
assert all(len(v)==125 and v[0]['викликів']==124 for v in rows.values())
assert all(v[0]==rows['main'][0] for v in rows.values())
removed={'B','C','В','Г','кандидати','кандидати_донора'}
changed=[]
for a,b in zip(rows['main'][1:],rows['after12'][1:]):
 if a!=b:
  assert a['ім']==b['ім']=='запити'
  old=a['результат'];new=b['результат']
  assert set(old)-set(new)==removed and not set(new)-set(old)
  for k in removed:old.pop(k)
  assert a==b
  changed.append([a['н'],a['ім']])
assert changed==[[12,'запити']]
assert rows['main']==rows['after12']==rows['pre42']==rows['final']
errors={}
for k,v in rows.items():
 errors[k]=sum(bool(r.get('помилка') or (r.get('результат',{}).get('помилка') if isinstance(r.get('результат'),dict) else None)) for r in v[1:])
assert not any(errors.values())
report={'входів':124,'sha256':{k:hashlib.sha256(data).hexdigest() for k,data in raw.items()},'змінені_виклики_12':changed,'дозволені_вилучення':sorted(removed),'решта_чотирьох_станів_тотожна':True,'помилки':errors}
(root/'four-state-compare.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
