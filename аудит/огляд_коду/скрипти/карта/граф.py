import os, sys, ast, json
Д=sys.argv[1]; os.chdir(Д)
t=ast.parse(open('status.py').read())
for n in ast.walk(t):
  if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='МОДУЛІ_ПРОДУКТУ' for x in n.targets): Я=set(ast.literal_eval(n.value))
всі={f[:-3] for f in os.listdir('.') if f.endswith('.py')}
ребра={}; внутр={}; динам={}
import warnings; warnings.simplefilter('ignore')
for м in sorted(всі):
  д=ast.parse(open(м+'.py',encoding='utf-8').read())
  # mark function-level
  верх=set(); фн=set()
  def walk(n, in_fn):
    for ch in ast.iter_child_nodes(n):
      f2 = in_fn or isinstance(ch,(ast.FunctionDef,ast.AsyncFunctionDef))
      names=set()
      if isinstance(ch,ast.Import): names={a.name.split('.')[0] for a in ch.names}
      elif isinstance(ch,ast.ImportFrom) and ch.level==0 and ch.module: names={ch.module.split('.')[0]}
      names&=всі
      (фн if f2 else верх).update(names)
      if isinstance(ch,ast.Call) and getattr(ch.func,'attr',getattr(ch.func,'id',''))in('import_module','__import__'):
        динам.setdefault(м,[]).append(ast.unparse(ch)[:80])
      walk(ch,f2)
  walk(д,False)
  ребра[м]=sorted((верх|фн)-{м}); внутр[м]=sorted(фн-верх-{м})
json.dump(dict(ребра=ребра,внутр=внутр,динам=динам,ядро=sorted(Я)),open(sys.argv[2],'w'),ensure_ascii=False)
# core subgraph
Е={м:[x for x in ребра[м] if x in Я] for м in Я}
print('ребер у ядрі',sum(len(v) for v in Е.values()),'з них лише всередині функцій',sum(1 for м in Я for x in внутр[м] if x in Я))
print('ядро -> не-ядро:',{м:[x for x in ребра[м] if x not in Я] for м in Я if any(x not in Я for x in ребра[м])})
print('динамічні імпорти в ядрі:',{м:v for м,v in динам.items() if м in Я})
from collections import Counter
fi=Counter(x for м in Я for x in Е[м])
print('fan-in топ15:',fi.most_common(15))
print('fan-out топ15:',sorted(((len(Е[м]),м) for м in Я),reverse=True)[:15])
# Tarjan
sys.setrecursionlimit(10000)
idx={};low={};st=[];on=set();comps=[];i=[0]
def sc(v):
  idx[v]=low[v]=i[0];i[0]+=1;st.append(v);on.add(v)
  for w in Е[v]:
    if w not in idx: sc(w);low[v]=min(low[v],low[w])
    elif w in on: low[v]=min(low[v],idx[w])
  if low[v]==idx[v]:
    c=[]
    while True:
      w=st.pop();on.discard(w);c.append(w)
      if w==v:break
    comps.append(c)
for v in sorted(Я):
  if v not in idx: sc(v)
big=[c for c in comps if len(c)>1]
print('SCC>1:',[(len(c)) for c in big])
for c in big: print(' ',len(c),' '.join(sorted(c)) if len(c)<60 else '...')
G=max(big,key=len); json.dump(sorted(G),open(sys.argv[2]+'.scc','w'),ensure_ascii=False)
print('ребер всередині найбільшої SCC',sum(1 for м in G for x in Е[м] if x in G))
# without function-level imports
Е2={м:[x for x in Е[м] if x not in внутр[м]] for м in Я}
idx.clear();low.clear();st.clear();on.clear();comps.clear();i[0]=0
Е_b=Е; Е=Е2
for v in sorted(Я):
  if v not in idx: sc(v)
print('SCC>1 лише верхньорівневі імпорти:',sorted([len(c) for c in comps if len(c)>1],reverse=True))
