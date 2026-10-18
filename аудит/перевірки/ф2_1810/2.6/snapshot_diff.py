import json,pathlib,collections,gzip,difflib,hashlib
p=pathlib.Path('/workspace/work/f2-26-evidence');ap=pathlib.Path('/workspace/work/baseline-results/main-1.jsonl');bp=p/'after-02.jsonl';a=[json.loads(x) for x in ap.read_text().splitlines()];b=[json.loads(x) for x in bp.read_text().splitlines()];assert a[0]==b[0];changes=[]
def walk(a,b,path='',out=None):
 out=[] if out is None else out
 if a==b:return out
 if isinstance(a,dict) and isinstance(b,dict):
  for k in sorted(a.keys()|b.keys()):
   if k not in a or k not in b:out.append({'шлях':path+'.'+k,'до':a.get(k),'після':b.get(k),'наявність':(k in a,k in b)})
   else:walk(a[k],b[k],path+'.'+k,out)
 elif isinstance(a,list) and isinstance(b,list):
  if len(a)!=len(b):out.append({'шлях':path+'.довжина','до':len(a),'після':len(b)})
  for i,(x,y) in enumerate(zip(a,b)):walk(x,y,path+'[%d]'%i,out)
 else:out.append({'шлях':path,'до':a,'після':b})
 return out
for x,y in zip(a[1:],b[1:]):
 assert x['н']==y['н'] and x['ім']==y['ім']
 if x!=y:changes.append({'н':x['н'],'ім':x['ім'],'різниці':walk(x,y)})
report={'sourcehead':'9aea1afd019298f297697831a14f2a1fffcde794','викликів':len(a)-1,'база_sha256':hashlib.sha256(ap.read_bytes()).hexdigest(),'після_sha256':hashlib.sha256(bp.read_bytes()).hexdigest(),'змінені':len(changes),'незмінені':len(a)-1-len(changes),'за_іменем':dict(collections.Counter(x['ім'] for x in changes)),'виклики':[{'н':x['н'],'ім':x['ім'],'листкових_розходжень':len(x['різниці']),'кореневі_поля':dict(collections.Counter(r['шлях'].split('.')[2].split('[')[0] if len(r['шлях'].split('.'))>2 else r['шлях'] for r in x['різниці']))} for x in changes]}
(p/'snapshot-diff-full.json.gz').write_bytes(gzip.compress(json.dumps(changes,ensure_ascii=False,sort_keys=True).encode(),mtime=0));(p/'snapshot-diff-summary.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False))
