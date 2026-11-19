import json,sys,datetime as D,re
def т(x): return D.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
for ф in sys.argv[1:]:
    print('==',ф.split('/')[-1])
    rows=[]
    for л in open(ф):
        о=json.loads(л); q=json.loads(о['запит']); m=q['messages'][0]['content']
        з=m if isinstance(m,str) else ' '.join(b.get('text','') for b in m if isinstance(b,dict))
        nimg=0 if isinstance(m,str) else sum(1 for b in m if isinstance(b,dict) and b.get('type')!='text')
        role=''
        try:
            j=json.loads(з); role=(j.get('task') or {}).get('role','')[:90]; hasp='person' in j
        except Exception: hasp=None
        rows.append((т(о['час']),float(о['с']),з[:70].replace('\n',' '),role,nimg,len(з),hasp, q.get('model','')))
    rows.sort(); t0=rows[0][0]
    for r in rows: print(f"{r[0]-t0:7.0f} {r[1]:6.1f} img{r[4]} len{r[5]:6d} p={r[6]} | {r[2]!r} | {r[3]}")
