#!/usr/bin/env python3
"""Доповнення до п.5 (менеджер 26.11 09:35): ходи, що почались повним перезаписом кешу (пауза понад годину).
Запуск: python3 кеш.py <каталог_подій> <ключ_сесії> <список_csv> <вихід_json>   (подія-сторінки — як у вимір.py)
Хід = перший запит після повідомлення/події (вимір.parse/turn_kind). «Повний перезапис» — перший запит ходу, де cache_creation ≥ ПОРІГ × контекст.
Ціни токенів — найменші квадрати за рядками Opus зі списку (cost = pin·input + pcr·cache_read + pcw·cache_write + pout·output)."""
import sys,os,json,csv,re,datetime,importlib.util
here=os.path.dirname(os.path.abspath(__file__))
sp=importlib.util.spec_from_file_location('v',os.path.join(here,'вимір.py')); v=importlib.util.module_from_spec(sp); sp.loader.exec_module(v)
ROOT,KEY,CSV,OUT=sys.argv[1:5]; v.ROOT=ROOT
def ts(s): return datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
rows=list(csv.DictReader(open(CSV)))
v.NAMES.update({r['id']:r['назва'] for r in rows})
# ціни: співвідношення 5 : 0,5 : 6,25 : 25 $/Мтокенів (вхід : читання кешу : запис кешу : вивід) × один множник, підібраний за Opus-рядками списку
# (рядки без ДИСПЕТЧЕРА-31 дають cost/розрахунок = 0,56–0,61; повний МНК за чотирма цінами вироджений — від'ємні ціни)
base=dict(input=5.0,cache_read=0.5,cache_write=6.25,output=25.0); xs=[];cs=[]
for r in rows:
    if r['usage'] and 'opus' in r['модель'] and 'ДИСПЕТЧЕР-31' not in r['назва']:
        u=json.loads(r['usage']); xs.append((u['input_tokens']*base['input']+u['cache_read_tokens']*base['cache_read']+u['cache_write_tokens']*base['cache_write']+u['output_tokens']*base['output'])/1e6); cs.append(float(r['cost_usd']))
scale=sum(x*c for x,c in zip(xs,cs))/sum(x*x for x in xs); resid=max(abs(scale*x-c)/c for x,c in zip(xs,cs))
price={k:scale*v for k,v in base.items()}
reqs,order,prompts,tools,res,others=v.parse(KEY)
R=[reqs[m] for m in order]; main=[r for r in R if r['parent'] is None]
cutoff=sys.argv[5] if len(sys.argv)>5 else None
if cutoff: main=[r for r in main if r['ts']<=cutoff]
idx={r['id']:i for i,r in enumerate(main)}
ctx=v.ctx
# ходи: початок = індекс у order
turns=[]
for j,p in enumerate(prompts):
    if p['pt'] is not None: continue
    turns.append(dict(kind=v.refine(v.turn_kind(p,j==0),p['head']),after=p['after'],head=p['head'][:90],ts=p['ts']))
for o in others: turns.append(dict(kind=v.refine('подія: лист сесії' if 'cross-session' in o['head'] else 'подія: лист/сповіщення (тригер, черга)',o['head']),after=o['after'],head=o['head'][:90],ts=o['ts']))
turns.sort(key=lambda t:(t['after'],t['kind']!='старт (наряд)'))
# перший основний запит після кожного ходу
pos={m:i for i,m in enumerate(order)}
seen=set(); T=[]
for t in turns:
    first=next((r for r in main if pos[r['id']]>=t['after'] and r['id'] not in seen),None)
    if first is None: continue
    seen.add(first['id']); i=idx[first['id']]
    prev=main[i-1] if i>0 else None
    c=ctx(first); cw=first['u'].get('cache_creation_input_tokens',0); cr=first['u'].get('cache_read_input_tokens',0)
    pause=(ts(first['ts'])-ts(prev['ts'])).total_seconds()/60 if prev else None
    comp=bool(prev and c<0.65*ctx(prev)) or bool(prev and ctx(first)<0.65*ctx(prev))
    T.append(dict(kind=t['kind'],head=t['head'],req=first['id'],ts=first['ts'],ctx=c,cw=cw,cr=cr,frac=cw/max(1,c),pause_min=pause,after_compaction=comp,prev_ctx=ctx(prev) if prev else 0))
tot_cw=sum(r['u'].get('cache_creation_input_tokens',0) for r in main); tot_cr=sum(r['u'].get('cache_read_input_tokens',0) for r in main)
tot_cost=sum(r['u'].get('input_tokens',0)*price['input']+r['u'].get('cache_read_input_tokens',0)*price['cache_read']+r['u'].get('cache_creation_input_tokens',0)*price['cache_write'] for r in main)/1e6
out=dict(price_per_mtok=price,price_fit_max_rel_err=resid,requests=len(main),turns=len(T),total_cache_write=tot_cw,total_cache_read=tot_cr,cost_in_cache_usd=tot_cost,
  cost_cache_write_usd=tot_cw*price['cache_write']/1e6)
for th in (0.5,0.8):
    F=[x for x in T if x['frac']>=th]; Fp=[x for x in F if (x['pause_min'] or 0)>60]; Fc=[x for x in F if x['after_compaction']]
    out[f'thr{th}']=dict(turns=len(F),share_turns=len(F)/max(1,len(T)),cw=sum(x['cw'] for x in F),share_cw=sum(x['cw'] for x in F)/max(1,tot_cw),usd=sum(x['cw'] for x in F)*price['cache_write']/1e6,
        extra_usd_vs_read=sum(x['cw'] for x in F)*(price['cache_write']-price['cache_read'])/1e6,pause_over60=len(Fp),after_compaction=len(Fc))
out['rewrites']=[x for x in T if x['frac']>=0.5]
slow=[x for x in T if (x['pause_min'] or 0)>60]
out['pauses_over_60']=[dict(kind=x['kind'],ts=x['ts'],pause_min=x['pause_min'],frac=x['frac'],ctx=x['ctx'],cw=x['cw']) for x in slow]
json.dump(out,open(OUT,'w'),ensure_ascii=False,indent=1)
print(json.dumps({k:v_ for k,v_ in out.items() if k not in('rewrites','pauses_over_60')},ensure_ascii=False,indent=1))
