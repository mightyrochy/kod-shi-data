import json,sys,os
B=sys.argv[1]; вих=['# Покроковий облік викликів моделі — Н2 7f5e9d88, ZHYVA=sonnet','',
'Джерело — `<режим>/<сцена>/обміни.jsonl`: рядок на виклик; кожен виклик — окремий процес `claude -p` (CLI 2.1.332, `--model sonnet`), тож `modelUsage` виклику — це і є його сума. cc — cache_creation, cr — cache_read. Модель і вікно — з `modelUsage` (ключ, `contextWindow`). `max_tokens` сторінки (4000) CLI не передається (`стеля_сторінки`). Вікно 1 000 000 — вікно CLI, не Cloudflare.','']
разом={}
for реж in ['типове','вікно1м']:
  for сц in ['с3','с5','с8']:
    f=f'{B}/{реж}/{сц}/обміни.jsonl'
    if not os.path.exists(f): continue
    вих+=[f'## {реж} / {сц}','','| # | час UTC | етап | статус | с | фото | input | cc | cr | output | модель | contextWindow | stop | $ |','|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    S=[0,0,0,0,0.0]; моделі=set()
    for i,l in enumerate(open(f),1):
      o=json.loads(l); mu=o.get('modelUsage') or {}; k=list(mu)[0] if mu else '—'; m=mu.get(k,{}) if mu else {}
      u=o.get('usage') or {}
      r=[u.get('input_tokens') or 0,u.get('cache_creation_input_tokens') or 0,u.get('cache_read_input_tokens') or 0,u.get('output_tokens') or 0, m.get('costUSD') or 0]
      for j in range(5): S[j]+=r[j]
      моделі.add(k)
      вих.append(f"| {i} | {o['час'][11:19]} | {o['тип']} | {o['статус']} | {o['с']} | {o.get('фото',0)} | {r[0]} | {r[1]} | {r[2]} | {r[3]} | {k} | {m.get('contextWindow','—')} | {o.get('stop_reason')} | {r[4]:.4f} |")
    вих+=[f'| Σ | | | | | | {S[0]} | {S[1]} | {S[2]} | {S[3]} | {", ".join(sorted(моделі))} | | | {S[4]:.4f} |','']
    разом[(реж,сц)]=(i,S[4])
вих+=['## Разом','']+[f'- {р}/{с}: викликів {n}, ${v:.4f}' for (р,с),(n,v) in разом.items()]+[f'- усього: викликів {sum(n for n,_ in разом.values())}, ${sum(v for _,v in разом.values()):.4f}']
print('\n'.join(вих))
