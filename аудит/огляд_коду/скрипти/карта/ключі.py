import ast, os, sys, json, re, warnings
from collections import defaultdict, Counter
warnings.simplefilter('ignore')
Д=sys.argv[1]; os.chdir(Д); sys.path.insert(0,Д)
g=json.load(open(sys.argv[2])); Я=set(g['ядро'])
чит=defaultdict(lambda: defaultdict(int)); пис=defaultdict(lambda: defaultdict(int))
for м in Я:
  t=ast.parse(open(м+'.py',encoding='utf-8').read())
  for n in ast.walk(t):
    if isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str):
      (пис if isinstance(n.ctx,ast.Store) else чит)[n.slice.value][м]+=1
    elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in('get','pop','setdefault') and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str):
      чит[n.args[0].value][м]+=1
    elif isinstance(n,ast.Compare) and isinstance(n.left,ast.Constant) and isinstance(n.left.value,str) and any(isinstance(o,(ast.In,ast.NotIn)) for o in n.ops):
      чит[n.left.value][м]+=1
    elif isinstance(n,ast.Dict):
      for k in n.keys:
        if isinstance(k,ast.Constant) and isinstance(k.value,str): пис[k.value][м]+=1
    elif isinstance(n,ast.Call) and getattr(n.func,'id','')=='dict':
      for kw in n.keywords:
        if kw.arg: пис[kw.arg][м]+=1
html=open('показ.html',encoding='utf-8').read()
def js(k):
  return len(re.findall(r'(?<![\wЀ-ӿ])'+re.escape(k)+r'(?![\wЀ-ӿ])', html)) if re.match(r'^[\wЀ-ӿ]+$',k) else html.count(k)
import паспорт_нагоди as П, сценарій as С, протокол as ПР
сім={
 'паспорт': set(П.СХЕМА_ПАСПОРТА)|set(П.ПОЛЯ_ПОЗА_СХЕМОЮ_ПАСПОРТА)|set(П._ПОЛЯ_ЛИШЕ_КОДУ),
 'сценарій': set(С.ПОЛЯ),
}
r=json.load(open(sys.argv[3]))
річ=[v for v in r['кандидати'].values()][0][0]; сім['річ пулу']=set(річ)
сім['вихід запити']=set(r)
for k in ('ВЕРДИКТ_V1','ОБРАЗИ_V1','ПАКЕТ_V1','ОПИС_V1'):
  сім[k]=set(ПР.СХЕМИ[k]['поля'])
рез={}
for н,кл in сім.items():
  рядки=[]
  for k in sorted(кл):
    мч=len(чит[k]); сч=sum(чит[k].values()); мп=len(пис[k]); сп=sum(пис[k].values())
    рядки.append((k,мч,сч,мп,сп,js(k)))
  рез[н]=рядки
  print(f"== {н}: ключів {len(кл)}; модулів-читачів на ключ медіана {sorted(x[1] for x in рядки)[len(рядки)//2]}, макс {max(x[1] for x in рядки)}; місць читання {sum(x[2] for x in рядки)}; місць запису {sum(x[4] for x in рядки)}; згадок у показ.html {sum(x[5] for x in рядки)}")
  print('   топ за модулями-читачами:',[(x[0],x[1],x[2]) for x in sorted(рядки,key=lambda x:-x[1])[:8]])
  print('   ніким не читаються в ядрі:',[x[0] for x in рядки if x[1]==0])
# декларовані читачі сценарію vs фактичні
розб=[]
for k,(опис,чит_зая) in С.ПОЛЯ.items():
  факт=set(чит[k]); зая=set(чит_зая)
  розб.append((k,len(зая),len(факт),len(факт-зая)))
print('сценарій.ПОЛЯ: заявлених читачів',sum(x[1] for x in розб),'фактичних модулів-читачів літералом',sum(x[2] for x in розб),'незаявлених',sum(x[3] for x in розб))
print('  найбільші розбіжності',sorted(розб,key=lambda x:-x[3])[:8])
всі=set(чит)|set(пис)
print('усього різних рядкових ключів у ядрі (чит∪пис)',len(всі),'читаються',len(чит),'місць читання',sum(sum(v.values()) for v in чит.values()))
print('ключів, що читаються в ≥10 модулях',sum(1 for k in чит if len(чит[k])>=10),'≥20',sum(1 for k in чит if len(чит[k])>=20))
print('топ',sorted(((len(v),k) for k,v in чит.items()),reverse=True)[:20])
json.dump({н:р for н,р in рез.items()},open(sys.argv[4],'w'),ensure_ascii=False,indent=0)
