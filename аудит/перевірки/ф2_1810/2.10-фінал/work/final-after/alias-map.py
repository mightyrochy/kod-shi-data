"""Відновити actual wire alias→SKU за точними старими полями, не відсутнім н кандидата."""
import json,sys,collections
from pathlib import Path
sys.path.insert(0,'джерела')
import пакет_моделі as П,дріт_моделі as Д,збирач_промптів as ЗП
old={r['н']:r['результат'] for r in map(json.loads,open('/workspace/work/baseline-results/main-1.jsonl')) if 'н'in r}[12]
new={r['н']:r['результат'] for r in map(json.loads,open('work/final-after/snapshot.jsonl')) if 'н'in r}[12]
canon=lambda r:json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def fp(r):return canon({k:v for k,v in r.items() if k not in ['n','knowledge','color_range','metal'] and v is not None})
summary={}
for field,hand in [('кандидати','B'),('кандидати_донора','C')]:
 maps=[]
 for x,label in [(old,'before'),(new,'after')]:
  lookup=collections.defaultdict(set)
  for slot,rs in x[field].items():
   for r in rs:
    wire=Д._легше(Д.річ(П._річ_пулу(r,{},slot),пул=True,слот=slot))
    if slot=='комплект':
     wire['two_piece']=True
     import суд_від_моделі as СМ
     if СМ.комплект_з_шаром(П._річ_пулу(r,{},slot)):wire['top_is_layer']=True
    lookup[fp(wire)].add(r['id'])
  mapping={};amb=[]
  for row in ЗП.рядки_таблиці(json.loads(x[hand])['pool']):
   ids=lookup[fp(row)]
   if len(ids)==1:mapping[row['n']]=next(iter(ids))
   else:amb.append({'n':row['n'],'matches':list(ids),'row':row})
  idslots=collections.defaultdict(set)
  for slot,rs in x[field].items():
   for r in rs:idslots[r['id']].add(slot)
  order=[]
  for row in ЗП.рядки_таблиці(json.loads(x[hand])['pool']):
   slots=idslots.get(mapping.get(row['n']),set())
   if len(slots)==1:
    slot=next(iter(slots))
    if slot not in order:order.append(slot)
  assert len(order)==sum(bool(v) for v in x[field].values()),(hand,label,order,list(x[field]))
  numbers=П.номери_речей({slot:x[field][slot] for slot in order})[0]
  fresh={'#%d·%s'%n:i for i,n in numbers.items()}
  assert all(fresh.get(n)==i for n,i in mapping.items()),(hand,label,'known rows disagree')
  for unknown in amb:
   assert fresh.get(unknown['n']) in unknown['matches'],unknown
   mapping[unknown['n']]=fresh[unknown['n']]
  print(hand,label,'mapped',len(mapping),'resolved exact duplicates',len(amb),'slot_order',order)
  maps.append(mapping)
  Path(f'work/final-after/aliases-{hand}-{label}.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2))
  Path(f'work/final-after/aliases-{hand}-{label}-unresolved.json').write_text(json.dumps(amb,ensure_ascii=False,indent=2))
 a,b=maps;ai={v:k for k,v in a.items()};bi={v:k for k,v in b.items()};common=ai.keys()&bi.keys()
 summary[hand]={'mapped_before':len(a),'mapped_after':len(b),'common':len(common),'changed_n':sum(ai[i]!=bi[i] for i in common),'same_alias_different_sku':[{'n':n,'before':a[n],'after':b[n]} for n in sorted(a.keys()&b.keys()) if a[n]!=b[n]],'removed_sku':sorted(ai.keys()-bi.keys()),'renumbered':[{'id':i,'before':ai[i],'after':bi[i]} for i in sorted(common) if ai[i]!=bi[i]]}
Path('work/final-after/actual-wire-aliases.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
print({k:{a:b for a,b in v.items() if isinstance(b,int)} for k,v in summary.items()})
