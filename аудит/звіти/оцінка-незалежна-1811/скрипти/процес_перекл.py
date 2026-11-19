import json,datetime as D,re
def т(x): return D.datetime.fromisoformat(x.replace('Z','+00:00')).timestamp()
for s in ('с5_весілля_сестри','с8_мінус_десять_сніг'):
    d=json.load(open(f'/tmp/звірка_дані/{s}.verd.json'))
    snip={}
    for пi,п in enumerate(d['прогони']):
        for v in п['вердикти']:
            key=(пi+1,v.get('рука'))
            ss=set()
            for c in (v.get('етапи') or {}).get('виклики') or []:
                raw=c.get('відповідь_сира') or ''
                for m in re.findall(r'"([^"\\]{40,})"',raw): ss.add(m[:40])
            snip[key]=ss
    rows=[]
    for л in open(f'/tmp/звірка_дані/{s}.jsonl'):
        о=json.loads(л); q=json.loads(о['запит']); m=q['messages'][0]['content']
        з=m if isinstance(m,str) else ' '.join(b.get('text','') for b in m if isinstance(b,dict))
        if not з.startswith('Ти — перекладачка'): continue
        hits=[k for k,ss in snip.items() if any(x in з for x in ss)]
        rows.append((т(о['час']),float(о['с']),hits))
    rows.sort()
    print('==',s,[(round(r[1]),r[2]) for r in rows])
