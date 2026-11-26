import json,sys
def flat(o,p=''):
    if isinstance(o,dict):
        for k,v in o.items(): yield from flat(v,f'{p}.{k}')
    elif isinstance(o,list):
        for i,v in enumerate(o): yield from flat(v,f'{p}[{i}]')
    else: yield p,o
a=dict(flat(json.load(open(sys.argv[1])))); b=dict(flat(json.load(open(sys.argv[2]))))
for k in sorted(set(a)|set(b)):
    if a.get(k,'<нема>')!=b.get(k,'<нема>'):
        print(f'{k}: {json.dumps(a.get(k,"<нема>"),ensure_ascii=False)[:200]} → {json.dumps(b.get(k,"<нема>"),ensure_ascii=False)[:200]}')
