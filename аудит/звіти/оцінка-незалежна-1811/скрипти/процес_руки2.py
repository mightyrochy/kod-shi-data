import json,datetime as D,collections
def т(x): return D.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
for s in ('с5_весілля_сестри','с8_мінус_десять_сніг'):
    d=json.load(open(f'/tmp/звірка_дані/{s}.verd.json'))
    idx=collections.defaultdict(set)
    for пi,п in enumerate(d['прогони']):
        for v in п['вердикти']:
            for i,c in enumerate((v.get('етапи') or {}).get('виклики') or []):
                t=(c.get('запит') or {}).get('текст') or ''
                idx[t].add((пi+1,v.get('рука'),c.get('крок'),(c.get('запит') or {}).get('чого','')[:25]))
    rows=[]
    for л in open(f'/tmp/звірка_дані/{s}.jsonl'):
        о=json.loads(л); q=json.loads(о['запит']); m=q['messages'][0]['content']
        texts=[m] if isinstance(m,str) else [b.get('text','') for b in m if isinstance(b,dict) and b.get('type')=='text']
        hit=set()
        for t in texts+[' '.join(texts),'\n'.join(texts),''.join(texts)]: hit|=idx.get(t,set())
        rows.append((т(о['час']),float(о['с']),texts[0][:30],sorted(hit)))
    rows.sort(); t0=rows[0][0]
    print('==',s)
    for r in rows:
        if r[3] or 'version' in r[2] or 'Photo' in r[2]: print(f"{r[0]-t0:6.0f} {r[1]:6.1f} {r[3]} | {r[2]}")
