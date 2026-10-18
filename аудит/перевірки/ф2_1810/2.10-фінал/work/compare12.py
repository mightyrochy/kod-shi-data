import json,collections,sys
sys.path.insert(0,'джерела')
import пакет_моделі as П,збирач_промптів as ЗП
base=json.load(open('work/baseline12.json'))
initial=next(json.loads(s)['результат'] for s in open('work/after/snapshot.jsonl') if json.loads(s).get('н')==12)
fixed=json.load(open('work/compact/call12.json'))
canon=lambda r:json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))
metrics={}
for field in ['кандидати','кандидати_донора']:
 rows=lambda r:[v for group in r[field].values() for v in group]
 olds={r['id']:r for r in rows(base)}; news={r['id']:r for r in rows(fixed)}
 metrics[field]={'before':len(rows(base)), 'initial':len(rows(initial)), 'fixed':len(rows(fixed)), 'unique_before':len(olds),'unique_after':len(news),'common':len(olds.keys()&news.keys()),'changed_old_fields':sum(canon({k:v for k,v in news[i].items() if k!='знання'})!=canon(olds[i]) for i in olds.keys()&news.keys()), 'slots':{s:[len(base[field][s]),len(initial[field][s]),len(fixed[field][s])] for s in base[field]},'old_n_shifted':sum(olds[i].get('н')!=news[i].get('н') for i in olds.keys()&news.keys())}
for name,r in [('before',base),('initial',initial),('fixed',fixed)]:
 metrics[name]={}
 for hand in ['B','C']:
  text=r[hand];d=json.loads(text)
  # Historical budget was pool alone. New budget includes all knowledge cost.
  metrics[name][hand]={'bytes':len(text.encode()),'tokens':П.токенів(text),'pool_bytes':len(canon(d['pool']).encode()),'pool_tokens':П.токенів(json.dumps(d['pool'],ensure_ascii=False,separators=(',',':'))),'charged_tokens':П.вага_пулу(text)}
for k in ['стеля','відсічено','пул_речей','різноманітність']:
 metrics[k]={n:r.get(k) for n,r in [('before',base),('initial',initial),('fixed',fixed)]}
json.dump(metrics,open('work/compact/causal12.json','w'),ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in metrics.items() if k not in ['стеля','відсічено','різноманітність']},ensure_ascii=False,indent=2))
