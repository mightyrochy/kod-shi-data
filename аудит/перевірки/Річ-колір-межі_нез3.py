import json, math, csv, re, itertools
R='/home/user/kod-shi-data/'; L=R+'джерела/лабораторія/'
вх=json.load(open(L+'колір_сім_ї_межі.json'))
num=lambda x: math.inf if x=='+inf' else x
txt=open(R+'джерела/дані_корпусу/ISCC-NBS_вікна.txt',encoding='utf-8').read()
кл=[]
for r in csv.DictReader([r for r in txt.splitlines() if r.strip() and not r.startswith('#')],delimiter='\t'):
    кл.append((int(r['Number']),tuple((float(r[x+'min']),float(r[x+'max'])) for x in 'HVC')))
таб=open(R+'джерела/колір_сім_ї_вікна.md',encoding='utf-8').read()
вл={}
for код,ном in re.findall(r"^\| `([a-z_]+)` \| [^|]+ \| ([\d–, ]+) \|",таб,re.M):
    for ч in ном.split(','):
        k=[int(x) for x in ч.strip().split('–')]
        for n in range(k[0],k[-1]+1): вл[n]=код
осі=[sorted({x for _,m in кл for x in m[i]}) for i in range(3)]
idx=lambda i,x: осі[i].index(x)
# сім'я кожної атомарної комірки
fam={}
for n,m in кл:
    rng=[range(idx(i,m[i][0]),idx(i,m[i][1])) for i in range(3)]
    for c in itertools.product(*rng): fam[c]=вл[n]
size=[len(o)-1 for o in осі]; print('комірок',len(fam),'розмір',size, 'покрито',len(fam)==size[0]*size[1]*size[2])
# множина покритих (вісь, площина_idx, комірка у двох інших) від граней
покр=set()
for g in вх['межі']:
    n='HVC'.index(g['вісь']); p=idx(n,g['координата']); free=[i for i in range(3) if i!=n]
    rs=[range(idx(i,num(lo)),idx(i,num(hi))) for i,(lo,hi) in zip(free,g['інтервали'])]
    for c in itertools.product(*rs):
        k=(n,p,c)
        if k in покр: print('ДУБЛЬ',k)
        покр.add(k)
# очікувані: суміжні різні сім'ї + домен-межа
очік=set()
for n in range(3):
    free=[i for i in range(3) if i!=n]
    for p in range(size[n]+1):
        for c in itertools.product(range(size[free[0]]),range(size[free[1]])):
            def cell(pp):
                q=[0]*3;q[n]=pp;q[free[0]],q[free[1]]=c;return tuple(q)
            lo=cell(p-1) if p>0 else (cell(size[0]-1) if n==0 else None)
            hi=cell(p) if p<size[n] else (cell(0) if n==0 else None)
            if n==0 and p==size[0]: continue  # H=101 ототожнено з H=1
            fl=fam.get(lo) if lo else None; fh=fam.get(hi) if hi else None
            if fl!=fh: очік.add((n,p,c))
print('очікуваних атомів грані',len(очік),'покрито гранями',len(покр),'різниця',len(очік-покр),len(покр-очік))
від=очік-покр
from collections import Counter
print(Counter((n, 'край' if p in (0,size[n]) else 'внутр') for n,p,c in від))
print('внутрішні непокриті:',[x for x in від if x[1] not in (0,size[x[0]])][:5])
