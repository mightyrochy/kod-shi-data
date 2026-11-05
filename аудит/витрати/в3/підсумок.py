import csv,collections as C,re
import os as _os
В=_os.path.dirname(_os.path.abspath(__file__)); R=_os.path.abspath(_os.path.join(В,'../../..'))
О=R+'/аудит/витрати'
f=lambda x:float(x) if x not in('',None,'None') else 0.0
c=list(csv.DictReader(open(f'{О}/сесії_2905.csv')))
tot=sum(f(x['cost_у_вікні']) for x in c)
print('CLAUDE сесій',len(c),'без usage',sum(1 for x in c if x['cost_usd'] in('','None')),'$ у вікні',round(tot,2),'$ всього',round(sum(f(x['cost_usd']) for x in c),2))
g=C.defaultdict(lambda:[0,0.0,0,0]);
for x in c:
    k=x['вид']; g[k][0]+=1; g[k][1]+=f(x['cost_у_вікні']); g[k][2]+=int(x['злиттів']); g[k][3]+=int(x['злиттів_продукту'])
for k,v in sorted(g.items(),key=lambda z:-z[1][1]): print(f'  {k}: {v[0]} сес, ${v[1]:.1f} ({100*v[1]/tot:.1f}%), злиттів {v[2]}, продукту {v[3]}')
root=sum(f(x['cost_у_вікні']) for x in c if x['корінь_продукту']=='1' and x['вид'] in('корінь продукту: крок','корінь продукту: прилад','перевірка'))
rootd=sum(f(x['cost_у_вікні']) for x in c if x['корінь_продукту']=='1' and x['вид']=='доробка')
print(f'  корені продукту (крок+прилад+їхні перевірки): ${root:.1f} = {100*root/tot:.1f}%; +доробки коренів ${rootd:.1f}')
m=C.defaultdict(float)
for x in c: m[x['модель']+' '+x['зусилля']]+=f(x['cost_у_вікні'])
print('  моделі',{k:round(v,1) for k,v in sorted(m.items(),key=lambda z:-z[1])})
print('  токени (сесії цілком): in',sum(f(x['input']) for x in c),'out',sum(f(x['output']) for x in c),'cr',sum(f(x['cache_read']) for x in c),'cw',sum(f(x['cache_write']) for x in c))
n=list(csv.DictReader(open(f'{О}/наряди_ноутбука_2905.csv')))
for P in ('Codex','agy'):
    r=[x for x in n if x['постачальник']==P]; T=sum(int(x['без_кешу']) for x in r); TR=sum(int(x['разом']) for x in r)
    print(P,'нарядів',len(r),'запусків',sum(int(x['запусків']) for x in r),'сесій моделі',sum(int(x['сесій_моделі']) for x in r),'без кешу',T,'разом',TR)
    g=C.defaultdict(lambda:[0,0,0,0,0])
    for x in r:
        a=g[x['вид']]; a[0]+=int(x['запусків']); a[1]+=int(x['без_кешу']); a[2]+=int(x['разом']); a[3]+=int(x['разом_спроб2']); a[4]+=int(x['без_кешу_збоїв'])
    for k,v in sorted(g.items(),key=lambda z:-z[1][1]): print(f'  {k}: запусків {v[0]}, без кешу {v[1]} ({100*v[1]/max(T,1):.1f}%), разом {v[2]} ({100*v[2]/max(TR,1):.1f}%), спроби≥2 {v[3]}, збої {v[4]}')
    rt=sum(int(x['без_кешу']) for x in r if x['корінь_продукту']=='1' and x['вид'] in('корінь продукту: крок','корінь продукту: прилад','перевірка'))
    rd=sum(int(x['без_кешу']) for x in r if x['корінь_продукту']=='1' and x['вид']=='доробка')
    print(f'  корені продукту (крок+прилад+їхні перевірки): {rt} = {100*rt/max(T,1):.1f}%; доробки коренів {rd}')
    print('  спроби≥2 усього',sum(int(x['разом_спроб2']) for x in r),'збої',sum(int(x['без_кешу_збоїв']) for x in r))
    print('  злиттів продукту',sum(int(x['злиттів_продукту']) for x in r),'нарядів зі злиттям',sum(1 for x in r if x['злито_pr']))
z=list(csv.DictReader(open(f'{О}/злиття_2905.csv')))
print('ЗЛИТТЯ',len(z),'продукт',sum(1 for x in z if int(x['продукт'])))
print(C.Counter(x['постачальник'] for x in z if int(x['продукт'])))
print('усі за постачальником',C.Counter(x['постачальник'].split(':')[0] for x in z))
# ---- вади з дошки
import json
pr={x['number']:x for x in map(json.loads,open(В+'/pr.jsonl'))}
d=list(csv.DictReader(open(В+'/дошка_нові.csv')))
zz={int(n):x for x in z for n in x['prs'].split()}
def пост(n):
    p=pr.get(n); g=p['head_ref'] if p else ''
    x=zz.get(n)
    return x['постачальник'] if x else ('gemini' if g.startswith('gemini/') else 'claude' if g.startswith('claude/') else '?')
прод={int(n) for x in z if int(x['продукт']) for n in x['prs'].split()}
print('ДОШКА нових',len(d),C.Counter(x['клас'] for x in d))
після=[x for x in d if x['клас']=='після злиття']
print(' після злиття: усі',len(після),'на продуктових PR',sum(1 for x in після if int(x['внесено_pr']) in прод))
print('  за постачальником (продукт):',C.Counter(пост(int(x['внесено_pr'])) for x in після if int(x['внесено_pr']) in прод))
print('  PR продукт:',sorted({int(x['внесено_pr']) for x in після if int(x['внесено_pr']) in прод}))
print('  хто знайшов (продукт):',C.Counter(x['виявлено'][:12] for x in після if int(x['внесено_pr']) in прод))
print(' до злиття, виявлено перевіркою:',sum(1 for x in d if x['клас']=='до злиття' and x['виявлено']=='перевірка'))
# ---- злиття продукту за постачальником (пачка — частками за вкладеними гілками)
def частки(x):
    p=x['постачальник']
    if not p.startswith('пачка:'): return {p:1.0}
    пари=[(k.rsplit(' ',1)[0],int(k.rsplit(' ',1)[1])) for k in p[len('пачка: '):].split(', ')]
    n=sum(v for _,v in пари); return {k:v/n for k,v in пари}
зл=C.Counter()
for x in z:
    if int(x['продукт']):
        for k,v in частки(x).items(): зл[k]+=v
print('ЗЛИТТЯ ПРОДУКТУ (частками):',{k:round(v,2) for k,v in зл.items()},'разом',round(sum(зл.values()),2))
# ---- місця коренів за відрізками
import os
if os.path.exists(В+'/корені_відрізки.csv'):
    k=list(csv.DictReader(open(В+'/корені_відрізки.csv')))
    за=C.defaultdict(list)
    for x in k: за[x['корінь']].append(x)
    прибр=C.Counter(); дод=C.Counter(); без=[]
    for імя,xs in за.items():
        for a,b in zip(xs,xs[1:]):
            g=b['точка'].split(':',1)[-1] if ':' in b['точка'] else b['точка']
            if a['місць']=='' or b['місць']=='': без.append((імя,b['точка'])); continue
            d=int(a['місць'])-int(b['місць'])
            if d>0: прибр[g]+=d
            elif d<0: дод[g]+=-d
        print(f"  {імя}: "+' → '.join(x['місць'] or '—' for x in xs))
    print('МІСЦЬ ПРИБРАНО за групою відрізків:',dict(прибр),'разом',sum(прибр.values()))
    print('МІСЦЬ ДОДАНО:',dict(дод),'разом',sum(дод.values()))
    print('без числа:',без[:12])
