"""Пояснити всі16 diff за фактичними wire aliases/SKU та окремими гілками/цілями."""
import json,re,gzip,collections
from pathlib import Path
old={r['н']:r['результат'] for r in map(json.loads,open('/workspace/work/baseline-results/main-1.jsonl')) if 'н'in r}
new={r['н']:r['результат'] for r in map(json.loads,open('work/final-after/snapshot.jsonl')) if 'н'in r}
inputs=list(map(json.loads,gzip.open('/workspace/work/baseline02/аудит/проби/знімок_входи_сід3.jsonl.gz','rt')))
maps={h:{t:json.load(open(f'work/final-after/aliases-{h}-{t}.json')) for t in ['before','after']} for h in ['B','C']}
changes=json.load(open('work/final-after/proof.json'))['changes']
canon=lambda r:json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
items=lambda r:[x.get('id') for x in r.get('речі',[]) if isinstance(x,dict)]
result=[]
for row in changes:
 n=row['н'];i=json.loads(inputs[n]['вхід']);branch='C' if i.get('донор') else 'B'
 aliases=sorted(set(re.findall(r'#\d+·\d+',canon(i))))
 refs=[]
 for alias in aliases:
  a=maps[branch]['before'].get(alias);b=maps[branch]['after'].get(alias)
  state='same' if a==b and a is not None else 'missing_after' if a is not None and b is None else 'different_sku' if a is not None and b is not None else 'not_in_recorded_query12'
  refs.append(dict(n=alias,before_sku=a,after_sku=b,state=state))
 before_items,after_items=items(old[n]),items(new[n])
 if n==12:reason='Новий договір і його оплачена ціна змінюють дозу та actual aliases B/C.'
 elif n in [13,14,17,20]:reason='Тільки схема_жінці.основа.одягу_у_пулі.невідомо:10→8; прозова/власна гілка без numeric aliases.'
 elif n in [18,23,24,27]:reason='Записана числова відповідь належить старому пулу; після оплаченої зміни дози її aliases відсутні/належать іншому SKU; fanout у розбір/блокери/ремонт.'
 elif n in [28,31]:reason='Вибір із записаних числових образів старого пулу; звірка з поточним пулом не відновлює попередній образ.'
 elif n in [33,39]:reason='Опис має явні ід: склад і реальні SKU збережені; diff у новому знанні/prompts/вітрині/самозвіті поточного пулу.'
 elif n in [35,42]:reason='ExplicitSKU збережені, але чинний ціновий суд змінився: сума_сил2.08→2.31; K-PRC-01 +0.23 для ж-13351@nyni.shop (cheaper17/of23,reach52), сумка ж-07981 cheaper94/101,reach37→71/77,reach28; ж-02374 поза_кандидатами[]→[id]. Це зміна суду через менший пул.'
 else:reason='Тільки зміни_звіт.крамниця.кандидатів: верх55→45, взуття63→50; оцінка/спроба/сума1.49 незмінні.'
 if n in [35,42]:
  price={'before_sum':old[n]['сума_сил'],'after_sum':new[n]['сума_сил'],'before_findings':[v for v in old[n]['знахідки'] if v.get('правило')=='K-PRC-01'],'after_findings':[v for v in new[n]['знахідки'] if v.get('правило')=='K-PRC-01'],'before_outside':old[n]['поза_кандидатами'],'after_outside':new[n]['поза_кандидатами']}
 else:price=None
 result.append(dict(price_judge=price,n=n,endpoint=inputs[n]['ім'],branch=branch,budget=i.get('бюджет_токенів'),reason=reason,alias_counts=dict(collections.Counter(x['state'] for x in refs)),aliases=refs,before_selected_sku=before_items,after_selected_sku=after_items,explicit_id=i.get('ід'),changed_top_keys=row['changed_top_keys']))
Path('work/final-after/causality.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for r in result:print(r['n'],r['branch'],r['budget'],r['alias_counts'],r['reason'])
