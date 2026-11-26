#!/usr/bin/env python3
"""Зведені таблиці з зведення.json (вихід вимір.py) → таблиці.md. Запуск: python3 таблиці.py зведення.json таблиці.md"""
import json,sys,collections
j=json.load(open(sys.argv[1])); S=j['sessions']; P=j['p6']
ORD=['session_01FPQuiaJQVMdGdzUFkpdjJS','session_01FPQuiYiZVXZxcH5FxTVszZ','session_01FPQuibcrYGv5hw43P2Gpu6','session_01FPQuib1v5vtAWCkXFr3c23','session_01FPQuiZZ3nkhzBzRrSoFYeM','session_01FPQuiYvgGKrxq2yvQmVuoV','session_01FPQuibcyUiLRWxVCs4QvAg','session_01FPQuiZyQFTb7A9H3hSS3eo','session_01FPQuib1p8NqBuAfK2npZWR','session_01FPQuiY5Sajtf6h6tD143qZ','session_01FPQuia6FGDWsaJJLWcxgHW']
EX=ORD[:8]
def g(k): # групи розкладки контексту
    if k.startswith('старт'): return '1 старт: система, інструменти, правила, наряд'
    if k.startswith('після стиснення'): return '2 після стиснення: підсумок і відновлене'
    if k in('Bash:читання файлу','Read'): return '3 читання файлів'
    if k in('Bash:пошук/ls','Bash:git','Bash:інше','Bash:скрипт/правка','Bash:тести','Edit','Write'): return '4 виводи команд (пошук, git, скрипти, тести)'
    if k=='відповідь моделі': return '6 відповіді моделі (вихід у контексті)'
    if k=='Bash:чекання': return '5 виклики стану (MCP, GitHub, сповіщення, чекання)'
    if k.startswith('MCP:') or k in('ReadNotifications','Monitor','TaskStop','ToolSearch','Agent','SubagentHandback'): return '5 виклики стану (MCP, GitHub, сповіщення, чекання)'
    return '7 повідомлення'
def f(x,d=0): return f'{x:,.{d}f}'.replace(',',' ')
L=[]
def row(*c): L.append('| '+' | '.join(str(x) for x in c)+' |')
def head(*c): row(*c); L.append('|'+'---|'*len(c))
L.append('# Зведені таблиці (генерує таблиці.py зі зведення.json)\n')
L.append(f"Знак/токен K = {j['K_chars_per_token']:.2f} (медіана за {j['K_n']} кроками, де між двома запитами додався один результат інструмента >6000 знаків). «Контекст» = input+cache_read+cache_write запиту; частки — від суми контекстів усіх запитів сесії.\n")
L.append('## П.1 Запити й контекст\n'); head('сесія','модель','запитів (осн+суб)','ctx 1-го','ctx сер.','ctx макс.','стиснень','Σ контексту, млн','звірка cache_read з usage списку')
for k in ORD:
    v=S[k]; u=v['csv_usage']['cache_read_tokens']; m=list(v['models'])[0].replace('claude-','')
    row(v['name'],m,f"{v['requests_main']}+{v['requests_sub']}",f(v['ctx_first']),f(v['ctx_mean']),f(v['ctx_max']),v['compactions'],f(v['sum_ctx']/1e6,1),f"{v['sum_cache_read']/u:.3f}")
L.append('\n## П.1 Розкладка контексту за змістом (частка Σ контексту, оцінка за знаками)\n'); G=sorted({g(a) for k in ORD for a in S[k]['attrib']}|{'8 субагенти (їхні власні запити)'})
head('сесія',*[x[2:] for x in G])
pool=collections.Counter(); poolx=collections.Counter()
for k in ORD:
    v=S[k]; c=collections.Counter()
    for a,b in v['attrib'].items(): c[g(a)]+=b
    c['8 субагенти (їхні власні запити)']+=v['sub_ctx']
    for a,b in c.items():
        pool[a]+=b
        if k in EX: poolx[a]+=b
    row(v['name'],*[f"{c[x]/v['sum_ctx']*100:.0f} %" for x in G])
T=sum(S[k]['sum_ctx'] for k in ORD); TX=sum(S[k]['sum_ctx'] for k in EX)
row('**разом 11 сесій**',*[f"**{pool[x]/T*100:.0f} %**" for x in G]); row('**8 виконавців Opus**',*[f"**{poolx[x]/TX*100:.0f} %**" for x in G])
L.append('\n## П.2 Виклики інструментів (число / знаків відповіді), топ видів\n')
agg=collections.defaultdict(lambda:[0,0]); 
for k in ORD:
    for a,b in S[k]['tools_by_kind'].items(): agg[a][0]+=b[0]; agg[a][1]+=b[1]
head('вид','викликів','знаків','сер. знаків')
for a,b in sorted(agg.items(),key=lambda x:-x[1][1])[:14]: row(a,b[0],f(b[1]),f(b[1]/max(1,b[0])))
L.append('\nПо сесіях (викликів / знаків): ')
head('сесія','усього викликів','знаків','найбільший вид')
for k in ORD:
    v=S[k]; a,b=next(iter(v['tools_by_kind'].items())); row(v['name'],v['tools_total'][0],f(v['tools_total'][1]),f"{a}: {b[0]} / {f(b[1])}")
L.append('\n### Двадцять найбільших відповідей (по сесіях — перші 5 тут; повний список у зведення.json, ключ top20)\n')
head('сесія','знаків','інструмент','що (команда/файл)','подія (msg · tool_use)')
for k in ORD:
    for t in S[k]['top20'][:5]: row(S[k]['name'],f(t['chars']),t['tool'],'`'+t['what'][:70].replace('|','/')+'`',f"{t['req']} · {t['tool_use']}")
L.append('\n## П.3 Повтори й тести\n'); head('сесія','файл прочитано знов: файлів','зайвих читань','знаків зайвих','однакових викликів зайвих','знаків','запусків тестів','з них без head/tail/grep','знаків виводу тестів')
for k in ORD:
    v=S[k]; r=v['repeat_file_reads']; s=v['repeat_same_call']; t=v['test_runs']
    row(v['name'],r['files'],r['extra_reads'],f(r['extra_chars']),s['extra'],f(s['extra_chars']),t['total'],t['unfiltered'],f(t['chars']))
L.append('\n## П.4 Чекання (запити, де всі виклики — лише перевірка стану: CI, PR, фонове завдання, sleep/until, get_session/list_events…)\n'); head('сесія','запитів','частка запитів','частка Σ контексту')
for k in ORD:
    w=S[k]['wait']; row(S[k]['name'],w['requests'],f"{w['share_req']*100:.0f} %",f"{w['share_ctx']*100:.0f} %")
L.append('\n## П.5 Пробудження: ходи, що почала подія (лист, сповіщення, пульс, хук, фонове завдання)\n'); head('сесія','ходів-подій','запитів у них','частка запитів','частка Σ контексту','з них: фонове завдання','хук зупину','лист/тригер/обгортка')
for k in ORD:
    v=S[k]; w=v['wake']; T_=v['turns']
    fb=T_.get('подія: фонове завдання/субагент завершились',{}).get('turns',0); hk=T_.get('подія: хук зупину',{}).get('turns',0)
    ot=sum(b['turns'] for a,b in T_.items() if a.startswith('подія') and 'фонове' not in a and 'хук' not in a)
    row(v['name'],w['turns'],w['requests'],f"{w['share_req']*100:.0f} %",f"{w['share_ctx']*100:.0f} %",fb,hk,ot)
L.append('\n### ДИСПЕТЧЕР-32: ходи за видом події (ціна ходу = запитів × контекст)\n'); head('вид ходу','ходів','запитів','запитів на хід','сер. контекст запиту','Σ контексту, млн','частка Σ')
v=S['session_01FPQuib1p8NqBuAfK2npZWR']
for a,b in sorted(v['turns'].items(),key=lambda x:-x[1]['ctx']): row(a,b['turns'],b['requests'],f"{b['mean_req']:.1f}",f(b['mean_ctx_req']),f(b['ctx']/1e6,1),f"{b['ctx']/v['sum_ctx']*100:.0f} %")
L.append('\n## П.6 Н3: що наступна сесія прочитала знов із прочитаного попередніми (читання файлів через Read і cat/head/sed)\n'); head('сесія','знаків прочитано','з них знов','частка прочитаного','частка всіх відповідей інструментів','токенів-запитів на утримання (≈)','частка Σ контексту сесії','найбільші')
for d,k in zip(['H3a','H3b','H3c','H3d'],ORD[:4]):
    p=P[d]; row(S[k]['name'],f(p['read_chars']),f(p['repeat_chars']),f"{p['repeat_share_of_read']*100:.0f} %",f"{p['repeat_share_of_tool_chars']*100:.1f} %",f(p['carry_tokens']),f"{p['carry_share_ctx']*100:.1f} %",'; '.join(f"{a} ({f(b)})" for a,b in p['top'][:3]))
open(sys.argv[2],'w').write('\n'.join(L)+'\n')
print('pool11',{a:round(b/T*100,1) for a,b in sorted(pool.items())}); print('pool8',{a:round(b/TX*100,1) for a,b in sorted(poolx.items())})
wa=sum(S[k]['wait']['ctx'] for k in ORD); wk=sum(S[k]['wake']['ctx'] for k in ORD); print('wait',wa/T,'wake',wk/T)
wa=sum(S[k]['wait']['ctx'] for k in EX); wk=sum(S[k]['wake']['ctx'] for k in EX); print('wait8',wa/TX,'wake8',wk/TX)
