import json, math, sys
from collections import Counter, defaultdict
L='/home/user/kod-shi-data/джерела/лабораторія/'
вх=json.load(open(L+'колір_сім_ї_межі.json')); а=json.load(open(L+'колір_сім_ї_зшивання.json'))
inf=math.inf
num=lambda x: inf if x=='+inf' else x
print('простір',вх['простір'],'порядок',вх['порядок_інтервалів'])
Hs=[num(x) for g in вх['межі'] for p in g['інтервали'] for x in p]
Hmin=1.0;Hmax=101.0
# визначити діапазон H із граней осі H
hk=sorted({g['координата'] for g in вх['межі'] if g['вісь']=='H'});print('H-площини',hk[:3],hk[-3:])
def canon(p):
    p=list(p); p[0]=Hmin if p[0]==Hmax else p[0]; return tuple(p)
# еталонні краї: для кожної грані CCW-обхід (u,v,n правий тріпл.)
еталон=[]  # per face: dict (axis, fixed tuple, a,b)->sign as atomic using global splitting later
кр=[]
for g in вх['межі']:
    n='HVC'.index(g['вісь']); u,v=(n+1)%3,(n+2)%3
    ін=dict(zip((i for i in range(3) if i!=n),[tuple(map(num,p)) for p in g['інтервали']]))
    (u0,u1),(v0,v1)=ін[u],ін[v]
    # CCW у (u,v): v=v0 від u0->u1 (+u); u=u1 від v0->v1 (+v); v=v1 u1->u0 (-u); u=u0 v1->v0 (-v)
    s=[]
    for ось,fix,fa,lo,hi,sg in ((u,v,v0,u0,u1,1),(v,u,u1,v0,v1,1),(u,v,v1,u0,u1,-1),(v,u,u0,v0,v1,-1)):
        if math.isinf(fa): continue
        s.append((ось,fix,fa,lo,hi,sg,n,g['координата']))
    кр.append(s)
print('еталон країв (скінч. фікс.):',sum(map(len,кр)))
# побудувати набір атомарних вузлів по осях з усіх координат
осі=[set(),set(),set()]
for g in вх['межі']:
    n='HVC'.index(g['вісь']); осі[n].add(g['координата'])
    for i,p in zip((i for i in range(3) if i!=n),g['інтервали']): осі[i].update(map(num,p))
осі=[sorted(x) for x in осі]
ат={} # ребро ключ -> (вісь, фікс tuple,a,b)
def key(ось,fixed,a,b):
    pt=[0]*3
    j=0
    for i in range(3):
        if i!=ось: pt[i]=fixed[j]; j+=1
    pt[ось]=0; pt=canon(pt) if False else pt
    # канонізація H у фікс.
    f=list(fixed)
    return (ось,tuple(f),a,b)
def fixedtuple(ось,n,u,v,fa_axis,fa,face_n,face_c):
    pt=[None]*3; pt[face_n]=face_c; pt[fa_axis]=fa; pt=canon([0 if x is None else x for x in pt]) if False else pt
    # H-канон: якщо H фіксована і =101 → 1
    if pt[0]==Hmax: pt[0]=Hmin
    return tuple(pt[i] for i in range(3) if i!=ось)
діл=defaultdict(int)  # (ось,fixed,a,b) -> суми знаків за гранями
вик=[]
for fi,s in enumerate(кр):
    fl=[]
    for (ось,fa_axis,fa,lo,hi,sg,n,c) in s:
        ft=fixedtuple(ось,n,0,0,fa_axis,fa,n,c)
        pts=[x for x in осі[ось] if lo<=x<=hi]
        for a,b in zip(pts,pts[1:]):
            fl.append(((ось,ft,a,b),sg))
    вик.append(fl)
# порівняння з артефактом
вер=[tuple(x) for x in а['вершини']]
ок=True
for fi,(fl,конт) in enumerate(zip(вик,а['контури'])):
    got=Counter()
    for р in конт:
        i=abs(р)-1; sg=1 if р>0 else -1; e=а['ребра'][i]
        ось='HVC'.index(e['вісь']); iv=(e['інтервал'][0],num(e['інтервал'][1]))
        got[((ось,tuple(e['фіксовані']),iv[0],iv[1]),sg)]+=1
    exp=Counter(fl)
    if got!=exp:
        ок=False; print('РОЗБІЖНІСТЬ грань',fi, set(exp)-set(got), set(got)-set(exp)); break
print('контури = незалежний CCW-обхід для всіх граней:',ок)
# унікальність ребер, ребра цілі: чи кожне ребро має ≥1 грань і incidence узгоджена
inc=defaultdict(list)
for fi,fl in enumerate(вик):
    for k,sg in fl: inc[k].append((fi,sg))
ek=set(inc);ae=set()
for e in а['ребра']:
    ae.add(('HVC'.index(e['вісь']),tuple(e['фіксовані']),e['інтервал'][0],num(e['інтервал'][1])))
print('множини ребер збігаються:',ek==ae,len(ek),len(ae))
# покриття: для кожного вихідного (неатомарного) краю атоми підряд без прогалин
# вершини: кожна скінч. вершина = точка кінця ребра; перевірка геометрії
бад=0
for e in а['ребра']:
    ось='HVC'.index(e['вісь'])
    for k,x in enumerate(e['інтервал'] ):
        v=e['вершини'][k]
        if v is None:
            if not math.isinf(num(x)): бад+=1
            continue
        pt=list(e['фіксовані']); pt.insert(ось,num(x)); pt=list(pt)
        if pt[0]==Hmax: pt[0]=Hmin
        if tuple(вер[v])!=tuple(pt): бад+=1
print('вершини не збігаються з геометрією ребер:',бад)
print('вершини унікальні:',len(set(вер))==len(вер),len(вер))
# замикання сімей: незалежно — сума орієнтованих країв граней сім'ї по ребру
for код in а['оболонки']:
    z=Counter();m=Counter()
    for fi,g in enumerate(вх['межі']):
        for sgn,fam in zip((1,-1),g['сім_ї']):
            if fam==код:
                for k,sg in вик[fi]: z[k]+=sgn*sg; m[k]+=1
    print(код,'залишок≠0:',sum(1 for v in z.values() if v),'кратності',dict(Counter(m.values())))
# вибірка: чи є ребра з граней > 2 різних (нестандартні)
print('ребер з кількістю граней:',dict(Counter(len(v) for v in inc.values())))
# сім'ї граней: кожна грань має обидва боки? 
print('граней без сім\'ї з обох боків:',sum(1 for g in вх['межі'] if None in g['сім_ї']))
