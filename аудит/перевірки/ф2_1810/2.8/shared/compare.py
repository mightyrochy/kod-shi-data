from pathlib import Path
import json,hashlib
root=Path('/workspace/work/f2-28-results');a=[json.loads(s) for s in (root/'before/snapshot/знімок.jsonl').read_text().splitlines()];b=[json.loads(s) for s in (root/'after-final/snapshot/знімок.jsonl').read_text().splitlines()]
assert a[0]==b[0];assert len(a)==len(b)==125
missing=object()
def diff(a,b,p=''):
 if a==b:return []
 if isinstance(a,dict) and isinstance(b,dict):
  out=[]
  for k in sorted(a.keys()|b.keys()):
   q=p+'/'+str(k).replace('~','~0').replace('/','~1')
   if k not in a:out.append(dict(path=q,change='added',after=b[k]))
   elif k not in b:out.append(dict(path=q,change='removed',before=a[k]))
   else:out+=diff(a[k],b[k],q)
  return out
 if isinstance(a,list) and isinstance(b,list) and len(a)==len(b):
  return [d for i,(x,y) in enumerate(zip(a,b)) for d in diff(x,y,p+'/'+str(i))]
 return [dict(path=p,change='value',before=a,after=b)]
changes=[]
for x,y in zip(a[1:],b[1:]):
 d=diff(x,y)
 if d:changes.append(dict(n=x['н'],name=x['ім'],diff=d))
out=dict(calls=124,same=124-len(changes),changed=len(changes),header=a[0],before_sha256=hashlib.sha256((root/'before/snapshot/знімок.jsonl').read_bytes()).hexdigest(),after_sha256=hashlib.sha256((root/'after-final/snapshot/знімок.jsonl').read_bytes()).hexdigest(),changes=changes)
(root/'comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False)[:5000])
