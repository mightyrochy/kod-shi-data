import os, sys, ast, json
Д=sys.argv[1]; sys.path.insert(0,Д); os.chdir(Д)
import прилади, склад
t=ast.parse(open('status.py').read())
for n in ast.walk(t):
  if isinstance(n,ast.Assign) and any(getattr(x,'id','')=='МОДУЛІ_ПРОДУКТУ' for x in n.targets):
    ЯДРО=set(ast.literal_eval(n.value))
закр=склад.модулі_системи('.')
print('ядро заявлено',len(ЯДРО),'замикання',len(закр),'різниця',ЯДРО^закр)
рядки=lambda f: sum(1 for _ in open(f,encoding='utf-8',errors='replace'))
рядки_код=lambda f: sum(1 for l in open(f,encoding='utf-8',errors='replace') if l.strip() and not l.strip().startswith('#'))
рез={}
for f in sorted(os.listdir('.')):
  if not os.path.isfile(f): continue
  ext=f.rsplit('.',1)[-1] if '.' in f else ''
  if ext=='py':
    м=f[:-3]
    if м in ЯДРО: р='ядро'
    elif м.startswith(('тест_','батарея_','test_')) or м in('gate_e2e',): р='батарея/тест'
    elif прилади.прилад(f): р='прилад'
    else: р='інше'
  elif ext in('js','html'): р='js/html'
  else: р='дані/документ'
  рез[f]=(р,рядки(f) if ext in('py','js','html','md','txt','tsv','json','ps1') else os.path.getsize(f), рядки_код(f) if ext=='py' else None)
json.dump(рез,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
from collections import Counter
c=Counter(); l=Counter(); lk=Counter()
for f,(р,n,k) in рез.items():
  c[р]+=1
  if f.endswith(('.py','.js','.html')): l[р]+=n
  if k: lk[р]+=k
for р in c: print(р,c[р],'файлів', l[р],'рядків', lk[р] or '', 'непорожніх некоментарних')
print('ІНШЕ:',' '.join(f for f,(р,_,_) in рез.items() if р=='інше'))
print('JS/HTML:',[(f,n) for f,(р,n,_) in рез.items() if р=='js/html'])
