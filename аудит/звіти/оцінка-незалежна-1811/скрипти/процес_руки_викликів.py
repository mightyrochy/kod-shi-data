import json,sys,datetime as D,collections
def т(x): return D.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
for s in ('с5_весілля_сестри','с8_мінус_десять_сніг'):
    d=json.load(open(f'/tmp/звірка_дані/{s}.verd.json'))
    idx=collections.defaultdict(set)
    for пi,п in enumerate(d['прогони']):
        for v in п['вердикти']:
            h=v.get('рука')
            def walk(o,path):
                if isinstance(o,dict):
                    for k,x in o.items(): walk(x,path+'.'+k)
                elif isinstance(o,list):
                    for x in o: walk(x,path)
                elif isinstance(o,str) and len(o)>=300:
                    idx[o[:3000]].add((h,path.split('.')[1] if path.count('.')>0 else path))
            walk(v,'')
    rows=[]
    for л in open(f'/tmp/звірка_дані/{s}.jsonl'):
        о=json.loads(л); q=json.loads(о['запит']); m=q['messages'][0]['content']
        з=m if isinstance(m,str) else ' '.join(b.get('text','') for b in m if isinstance(b,dict) and b.get('type')=='text')
        hit=idx.get(з[:3000]) or set()
        if not hit:
            # try containment of text blocks
            for k,vv in idx.items():
                if len(k)>=1000 and k[:1000] in з: hit|=vv
        rows.append((т(о['час']),float(о['с']),з[:40].replace('\n',' '),sorted({h for h,_ in hit}),sorted({p for _,p in hit})[:3]))
    rows.sort(); t0=rows[0][0]
    print('==',s)
    for r in rows: print(f"{r[0]-t0:6.0f} {r[1]:6.1f} руки={','.join(map(str,r[3])) or '-':8s} {r[4]} | {r[2]}")
