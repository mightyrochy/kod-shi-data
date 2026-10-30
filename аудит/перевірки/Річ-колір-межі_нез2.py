import json, math, csv, re, itertools
from collections import defaultdict
R='/home/user/kod-shi-data/'; L=R+'джерела/лабораторія/'
a=json.load(open(L+'колір_сім_ї_зшивання.json')); вх=json.load(open(L+'колір_сім_ї_межі.json'))
num=lambda x: math.inf if x=='+inf' else x
# 1) жодних часткових перекриттів ребер на одній прямій
лінії=defaultdict(list)
for i,e in enumerate(a['ребра']): лінії[(e['вісь'],tuple(e['фіксовані']))].append((e['інтервал'][0],num(e['інтервал'][1]),i))
bad=0
for k,l in лінії.items():
    l.sort()
    for (a0,a1,_),(b0,b1,_) in zip(l,l[1:]):
        if b0<a1: bad+=1
print('часткових перекриттів ребер на лінії:',bad,'ліній',len(лінії))
# T-стик: вершина будь-якого ребра не лежить усередині чужого ребра
вер=[tuple(v) for v in a['вершини']]
bad=0
for i,e in enumerate(a['ребра']):
    ось='HVC'.index(e['вісь'])
    for v in вер:
        if tuple(v[j] for j in range(3) if j!=ось)==tuple(e['фіксовані']) and e['інтервал'][0]<v[ось]<num(e['інтервал'][1]): bad+=1
print('вершин усередині чужого ребра:',bad)
# 2) боки граней з сирих клітинок джерела
txt=open(R+'джерела/дані_корпусу/ISCC-NBS_вікна.txt',encoding='utf-8').read()
рядки=[r for r in txt.splitlines() if r.strip() and not r.lstrip().startswith('#')]
кл=[]
for r in csv.DictReader(рядки,delimiter='\t'):
    кл.append((int(r['Number']),tuple((float(r[x+'min']),float(r[x+'max'])) for x in 'HVC')))
таб=open(R+'джерела/колір_сім_ї_вікна.md',encoding='utf-8').read()
вл={}
for код,ном in re.findall(r"^\| `([a-z_]+)` \| [^|]+ \| ([\d–, ]+) \|",таб,re.M):
    for ч in ном.split(','):
        k=[int(x) for x in ч.strip().split('–')]
        for n in range(k[0],k[-1]+1): вл[n]=код
def сім_я(p):  # точка у відкритій комірці
    for n,m in кл:
        if all(lo<=p[i]<hi if True else 0 for i,(lo,hi) in enumerate(m)):
            return вл[n]
    return None
def mid(lo,hi): return (lo+hi)/2 if math.isfinite(hi) else lo+1
осі=[sorted({x for _,m in кл for x in m[i]}) for i in range(3)]
pr=lambda lo,hi:(lo,hi)
bad=0;N=0
for g in вх['межі']:
    n='HVC'.index(g['вісь']); c=g['координата']
    ін=[tuple(map(num,p)) for p in g['інтервали']]; free=[i for i in range(3) if i!=n]
    # перевірити кілька точок усередині грані (всі атомарні комірки)
    ат=[]
    for i,(lo,hi) in zip(free,ін):
        pts=[x for x in осі[i] if lo<=x<=hi]; ат.append([mid(p,q) for p,q in zip(pts,pts[1:])])
    for u,v in itertools.product(*ат):
        p=[0]*3;p[free[0]]=u;p[free[1]]=v
        осі_n=осі[n]
        # лівий/правий боки
        def fam(side):
            q=list(p)
            if side<0:
                prev=[x for x in осі_n if x<c]
                if not prev:
                    if n==0: q[0]=101-1e-6 if False else (осі_n[-1]+осі_n[-2])/2  # обертання
                    else: return None
                else: q[n]=(prev[-1]+c)/2
            else:
                nxt=[x for x in осі_n if x>c]
                if not nxt:
                    if n==0: q[0]=(осі_n[0]+осі_n[1])/2
                    else: return None
                else: q[n]=(c+nxt[0])/2 if math.isfinite(nxt[0]) else c+1
            return сім_я(q)
        exp=[fam(-1),fam(1)]; N+=1
        if exp!=g['сім_ї']: bad+=1; print('розбіжність бока',g,exp) if bad<4 else 0
print('атомарних комірок граней перевірено:',N,'розбіжностей боків:',bad)
