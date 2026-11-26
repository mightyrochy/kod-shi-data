#!/usr/bin/env python3
"""Вимір «куди йдуть токени сесії» за подіями list_events (наряд Сесії-куди-токени-вимір, 26.11).
Вхід: каталог з вивантаженими сторінками подій (`<каталог>/<сесія>/NNN.txt`, 001 — найновіша сторінка,
кожен файл — відповідь list_events із ключем "ccr"). Сирих сторінок у репозиторії нема (там тексти сесій).
Запуск: python3 вимір.py <каталог_подій> <вихід_json>
Токени запиту — з `usage` кожної відповіді моделі (exact): ctx = input + cache_read + cache_creation.
Знаки відповідей інструментів — довжина тексту tool_result; оцінка токенів знаків — K знак/токен, виміряне нижче."""
import json,glob,os,re,sys,statistics,collections
SESS={ # каталог: (id, назва)
 'H3a':('session_01FPQuiaJQVMdGdzUFkpdjJS','Н3-1'),'H3b':('session_01FPQuiYiZVXZxcH5FxTVszZ','Н3-2'),
 'H3c':('session_01FPQuibcrYGv5hw43P2Gpu6','Н3-3'),'H3d':('session_01FPQuib1v5vtAWCkXFr3c23','Н3-4'),
 'H4':('session_01FPQuiZZ3nkhzBzRrSoFYeM','Н4'),'Zapys':('session_01FPQuiYvgGKrxq2yvQmVuoV','Запис-речі'),
 'Rich':('session_01FPQuibcyUiLRWxVCs4QvAg','Річ-ознаки'),'Kupivlya':('session_01FPQuiZyQFTb7A9H3hSS3eo','Купівля'),
 'Disp32':('session_01FPQuib1p8NqBuAfK2npZWR','ДИСПЕТЧЕР-32'),'Perev4743':('session_01FPQuiY5Sajtf6h6tD143qZ','Перевірка #4743 (Sonnet)'),
 'Fasady':('session_01FPQuia6FGDWsaJJLWcxgHW','Код-фасади (Sonnet)')}
POLL_TOOLS=re.compile(r'(pull_request_read|get_check_run|actions_get|actions_list|get_job_logs|TaskOutput|TaskList|TaskGet|list_events|get_session|list_sessions|get_trigger|list_triggers|ListAgents|Monitor|ReadNotifications|get_commit|list_commits|list_pull_requests)$')
POLL_BASH=re.compile(r'\bsleep\b|\buntil\b|gh run |gh pr checks|--watch')
TEST_CMD=re.compile(r'unittest|pytest|python3? [^|;&]*тест|\bnode [^|;&]*тест|стенд_знімок|тест_[а-яіїєґa-z_]+\.(py|js)|батаре')
CATPATH=re.compile(r'(?:^|[;&|]\s*|&&\s*)(?:cat|head(?: -n? ?\d+)?|tail(?: -n? ?\d+)?|sed -n \'[^\']*\'|nl)\s+"?([^\s|;&"\'<>]+\.(?:md|py|js|json|txt|csv|yml|yaml|html|css))"?\s*(?:\||;|&&|$|2>)')
def txt(c):
    if isinstance(c,str): return c
    if isinstance(c,list): return ''.join(txt(b.get('text',b.get('content',''))) if isinstance(b,dict) else str(b) for b in c)
    return ''
CUT={}
def load(d):
    ev={}
    for f in sorted(glob.glob(f'{ROOT}/{d}/*.txt')):
        t=open(f).read()
        try: j=json.loads(t[t.index('{"ccr"'):t.rindex('}')+1])['ccr'].get('data',[])
        except Exception as e: print('ПОГАНИЙ ФАЙЛ',f,e,file=sys.stderr); continue
        for e in j:
            k=next((x for x in e if x!='created_at'),None); v=e.get(k) or {}
            ev[(v.get('uuid') if isinstance(v,dict) else None) or id(e)]=e
    cut=CUT.get(d)
    return sorted((e for e in ev.values() if not cut or e['created_at']<=cut),key=lambda e:e['created_at'])
READV=re.compile(r'^(cat|head|tail|nl|less|sed -n)\b')
PATHT=re.compile(r'(?<![\w./-])((?:/|\.{0,2}/)?[\w.а-яіїєґА-ЯІЇЄҐ/{}-]+\.(?:md|py|js|json|txt|csv|yml|yaml|html|css|sh))(?![\w])')
def read_paths(c):
    """Шляхи файлів, якщо команда лише читає файли (cat/head/tail/sed -n/nl, можна з cd, echo, ; && і |head); інакше None."""
    c=re.sub(r'2>&1|2>/dev/null','',c)
    parts=[x.strip() for x in re.split(r'&&|;|\n',c) if x.strip()]
    paths=[]; got=False
    for x in parts:
        if x.startswith('cd ') or x.startswith('echo') or x.startswith('printf'): continue
        first=re.split(r'\|',x)[0].strip()
        if READV.match(first):
            got=True; paths+=[m.group(1) for m in PATHT.finditer(first) if not first.startswith("sed -n '") or True]
        else: return None
    return paths if got else None
def cat_tool(name,inp):
    if name=='Bash':
        c=inp.get('command','')
        if POLL_BASH.search(c): return 'Bash:чекання'
        if TEST_CMD.search(c): return 'Bash:тести'
        if read_paths(c): return 'Bash:читання файлу'
        if re.search(r'\bgit (diff|log|show|status|fetch|checkout|push|commit|merge|rebase|add|branch|ls-tree|cat-file|rev-parse|reset|stash)\b',c): return 'Bash:git'
        if re.search(r'<<|sed -i|cat >|tee |python3? -|\bpython3? -c|node -e',c): return 'Bash:скрипт/правка'
        if re.search(r'\b(grep|rg|find|ls|wc|awk|diff)\b',c): return 'Bash:пошук/ls'
        return 'Bash:інше'
    if name.startswith('mcp__'): return 'MCP:'+name.split('__',1)[1]
    return name
def parse(d):
    ev=load(d); reqs={}; order=[]; users=[]; tools={}; res={}; prompts=[]; others=[]
    for e in ev:
        ts=e['created_at']
        if 'assistant' in e:
            a=e['assistant']['internal_anthropic_catchall']; m=a['message']; mid=m['id']
            r=reqs.get(mid)
            if r is None:
                r=reqs[mid]=dict(id=mid,ts=ts,model=m.get('model'),parent=a.get('parent_tool_use_id'),u={},tu=[],out_chars=0,seq=len(order)); order.append(mid)
            u=m.get('usage') or {}
            for k in('input_tokens','cache_read_input_tokens','cache_creation_input_tokens','output_tokens'):
                r['u'][k]=max(r['u'].get(k,0),u.get(k,0) or 0)
            for b in m.get('content',[]):
                if b.get('type')=='tool_use':
                    r['tu'].append((b['id'],b['name'],b.get('input',{}))); tools[b['id']]=(mid,b['name'],b.get('input',{}))
                elif b.get('type')=='text': r['out_chars']+=len(b.get('text',''))
        elif 'user' in e:
            u=e['user']['internal_anthropic_catchall']; c=u['message']['content']
            if isinstance(c,list) and c and isinstance(c[0],dict) and c[0].get('type')=='tool_result':
                for b in c:
                    if b.get('type')=='tool_result': res[b['tool_use_id']]=dict(chars=len(txt(b.get('content',''))),after=len(order),ts=ts)
            else:
                s=txt(c); prompts.append(dict(ts=ts,after=len(order),chars=len(s),head=s[:300],origin=u.get('inbound_origin'),synth=u.get('isSynthetic'),pt=u.get('parent_tool_use_id')))
        else:
            k=next((x for x in e if x!='created_at'),None)
            if k=='internal_anthropic_catchall':
                v=e[k]
                if v.get('type')=='queued_notification' or 'notification' in v:
                    others.append(dict(ts=ts,after=len(order),head=json.dumps(v.get('notification',v),ensure_ascii=False)[:300]))
    return reqs,order,prompts,tools,res,others
def ctx(r): u=r['u']; return u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0)
NAMES={}
def refine(kind,h):
    if kind=='подія: лист сесії':
        m=re.search(r'from-session=\\?"(session_\w+)',h); n=NAMES.get(m.group(1),'') if m else ''
        if re.search(r'ВИКОНАВЕЦЬ',n): return 'подія: лист виконавця'
        if re.search(r'ПЕРЕВІРКА|Перевірка',n): return 'подія: лист перевірки'
        if re.search(r'менеджер',n): return 'подія: лист менеджера'
        return 'подія: лист іншої сесії'
    if kind=='подія: лист/сповіщення (тригер, черга)':
        c=re.sub(r'^\{"content": "','',h)
        if c.startswith('ПУЛЬС'): return 'подія: пульс (тригер)'
        if re.search(r'^(ТАКТ|НАГАДУВАННЯ|Нагадування|Звір)',c): return 'подія: самонагадування (тригер)'
    return kind
def turn_kind(p,first=False):
    h=p['head']
    if first or p['origin']=='mcp_create_session': return 'старт (наряд)'
    if h.startswith('This session is being continued'): return 'продовження після стиснення'
    if h.startswith('<task-notification>'): return 'подія: фонове завдання/субагент завершились'
    if 'Stop hook feedback' in h: return 'подія: хук зупину'
    if h.startswith('GEMINI ОБГОРТКА'): return 'подія: обгортка ноутбука (пульс/простій/збій)'
    if "hasn't heard from you" in h: return 'подія: нагадування CLI'
    if re.search(r'github-webhook|<github|webhook|check_run|workflow run',h[:300],re.I): return 'подія: GitHub (CI/PR)'
    if 'cross-session-message' in h or 'Another Claude session sent' in h or re.search(r'^(ДИСПЕТЧЕР|ВИКОНАВЕЦЬ|МЕНЕДЖЕР|ПЕРЕВІРКА|НОУТБУК)',h): return 'подія: лист сесії'
    return 'слово власника (або невідоме)'
def analyze(d,K):
    reqs,order,prompts,tools,res,others=parse(d)
    R=[reqs[m] for m in order]; main=[r for r in R if r['parent'] is None]; sub=[r for r in R if r['parent'] is not None]
    out=dict(requests_total=len(R),requests_main=len(main),requests_sub=len(sub))
    out['sum_cache_read']=sum(r['u'].get('cache_read_input_tokens',0) for r in R)
    out['sum_cache_write']=sum(r['u'].get('cache_creation_input_tokens',0) for r in R)
    out['sum_input']=sum(r['u'].get('input_tokens',0) for r in R); out['sum_output']=sum(r['u'].get('output_tokens',0) for r in R)
    out['sum_ctx']=sum(ctx(r) for r in R)
    out['models']=dict(collections.Counter(r['model'] for r in R))
    cs=[ctx(r) for r in main]; 
    out['ctx_first']=cs[0] if cs else 0; out['ctx_mean']=int(statistics.mean(cs)) if cs else 0; out['ctx_max']=max(cs) if cs else 0
    # стиснення: падіння контексту головної нитки більш ніж на 35 %
    comp=[]; seg0=[0]
    for i in range(1,len(main)):
        if cs[i]<0.65*cs[i-1]: comp.append(i); seg0.append(i)
    out['compactions']=len(comp); out['compaction_post_ctx']=[cs[i] for i in comp]; out['compaction_pre_ctx']=[cs[i-1] for i in comp]
    # перше навантаження: перший запит без першого повідомлення
    p0=prompts[0] if prompts else None
    out['first_prompt_chars']=p0['chars'] if p0 else 0
    # --- виклики інструментів
    byk=collections.defaultdict(lambda:[0,0]); big=[]; reads=collections.defaultdict(list); cmds=collections.defaultdict(list)
    for tid,(mid,name,inp) in tools.items():
        k=cat_tool(name,inp); ch=res.get(tid,{}).get('chars',0)
        byk[k][0]+=1; byk[k][1]+=ch
        big.append((ch,mid,tid,name,(inp.get('command') or inp.get('file_path') or inp.get('pattern') or json.dumps(inp,ensure_ascii=False))[:110].replace('\n',' ')))
        if name=='Read': reads[inp.get('file_path','')+'|'+str(inp.get('offset',''))+'|'+str(inp.get('limit',''))].append(ch)
        elif name=='Bash':
            ps=read_paths(inp.get('command',''))
            if ps:
                for pth in ps: reads[pth.lstrip('./')+'|cat'].append(ch/len(ps))
        cmds[name+'|'+json.dumps(inp,sort_keys=True,ensure_ascii=False)].append(ch)
    out['tools_by_kind']={k:v for k,v in sorted(byk.items(),key=lambda x:-x[1][1])}
    out['tools_total']=[sum(v[0] for v in byk.values()),sum(v[1] for v in byk.values())]
    big.sort(reverse=True); out['top20']=[dict(chars=c,req=m,tool_use=t,tool=n,what=w) for c,m,t,n,w in big[:20]]
    # повтори
    rf=[(k,v) for k,v in reads.items() if len(v)>1]
    out['repeat_file_reads']=dict(files=len(rf),extra_reads=sum(len(v)-1 for k,v in rf),extra_chars=sum(sum(v[1:]) for k,v in rf),
        top=[(k,len(v),sum(v[1:])) for k,v in sorted(rf,key=lambda kv:-sum(kv[1][1:]))[:5]])
    rc=[(k,v) for k,v in cmds.items() if len(v)>1 and not k.startswith('Bash|{"command": "sleep')]
    out['repeat_same_call']=dict(calls=len(rc),extra=sum(len(v)-1 for k,v in rc),extra_chars=sum(sum(v[1:]) for k,v in rc))
    tr=[(tid,v) for tid,v in tools.items() if v[1]=='Bash' and TEST_CMD.search(v[2].get('command',''))]
    full=[t for t in tr if not re.search(r'\|\s*(head|tail|grep|wc)\b',t[1][2].get('command',''))]
    trunc=0
    out['test_runs']=dict(total=len(tr),unfiltered=len(full),filtered=len(tr)-len(full),chars=sum(res.get(t[0],{}).get('chars',0) for t in tr))
    # --- чекання
    waitreq=[]
    for r in main:
        if r['tu'] and all(POLL_TOOLS.search(n) or (n=='Bash' and POLL_BASH.search(i.get('command',''))) for _,n,i in r['tu']): waitreq.append(r)
    out['wait']=dict(requests=len(waitreq),share_req=len(waitreq)/max(1,len(main)),ctx=sum(ctx(r) for r in waitreq),share_ctx=sum(ctx(r) for r in waitreq)/max(1,out['sum_ctx']))
    # --- ходи (пробудження)
    idx={m:i for i,m in enumerate(order)}
    turns=[]
    for j,p in enumerate(prompts):
        if p['pt'] is not None: continue
        turns.append(dict(kind=refine(turn_kind(p,j==0),p['head']),start=p['after'],head=p['head'][:80]))
    for o in others: turns.append(dict(kind=refine('подія: лист сесії' if 'cross-session' in o['head'] else 'подія: лист/сповіщення (тригер, черга)',o['head']),start=o['after'],head=o['head'][:80]))
    turns.sort(key=lambda t:(t['start'],t['kind']!='старт (наряд)'))
    for i,t in enumerate(turns):
        end=next((u['start'] for u in turns[i+1:] if u['start']>t['start']),len(order))
        same_before=i>0 and turns[i-1]['start']==t['start']
        rr=[] if same_before else [r for r in R[t['start']:end] if r['parent'] is None]
        t['requests']=len(rr); t['ctx']=sum(ctx(r) for r in rr)
    agg=collections.defaultdict(lambda:[0,0,0])
    for t in turns: a=agg[t['kind']]; a[0]+=1; a[1]+=t['requests']; a[2]+=t['ctx']
    out['turns']={k:dict(turns=v[0],requests=v[1],ctx=v[2],mean_req=v[1]/v[0],mean_ctx_req=v[2]/max(1,v[1])) for k,v in agg.items()}
    wake=[t for t in turns if t['kind'].startswith('подія')]
    out['wake']=dict(turns=len(wake),requests=sum(t['requests'] for t in wake),ctx=sum(t['ctx'] for t in wake),share_req=sum(t['requests'] for t in wake)/max(1,len(main)),share_ctx=sum(t['ctx'] for t in wake)/max(1,out['sum_ctx']))
    out['turns_list']=turns if d=='Disp32' else []
    # --- розкладка контексту: старт / ріст за видами (оцінка за знаками, K знак/токен)
    cat={'старт: система+інструменти+правила+наряд':0,'після стиснення: підсумок і відновлене':0}
    segstarts=set(seg0)
    base=0; items=[]  # (кат,знаки)
    ptr=0
    # події між запитами: результати інструментів, відповіді моделі
    res_by_req=collections.defaultdict(list)
    for tid,v in res.items():
        mid,name,inp=tools.get(tid,(None,'?',{}))[0:3] if tid in tools else (None,'?',{})
        res_by_req[v['after']].append((cat_tool(name,inp) if tid in tools else '?',v['chars'],tid))
    for i,r in enumerate(main):
        gi=idx[r['id']]
        if i in segstarts: base=cs[i]; items=[]
        # додати елементи, що з'явились до цього запиту (після попереднього)
        if i>0 and i not in segstarts:
            pg=idx[main[i-1]['id']]
            items.append(('відповідь моделі',reqs[main[i-1]['id']]['out_chars']+sum(len(json.dumps(x[2])) for x in reqs[main[i-1]['id']]['tu'])))
            for after in range(pg+1,gi+1):
                for k,ch,tid in res_by_req.get(after,[]): items.append((k,ch))
            for p in prompts:
                if pg<p['after']<=gi and p['pt'] is None: items.append(('повідомлення користувача/подій',p['chars']))
        growth=max(0,cs[i]-base); tot=sum(c for _,c in items) or 1
        core=cs[0]; b=min(base,cs[i]); cat['старт: система+інструменти+правила+наряд']+=min(b,core); cat['після стиснення: підсумок і відновлене']+=max(0,b-core)
        for k,c in items: cat[k]=cat.get(k,0)+growth*c/tot
    out['attrib']={k:v for k,v in sorted(cat.items(),key=lambda x:-x[1])}
    sr=[]; 
    for tid,(mid,name,inp) in tools.items():
        if tid in res and res[tid]['after']<=12 and reqs[mid]['parent'] is None:
            ps=[inp.get('file_path','')] if name=='Read' else (read_paths(inp.get('command','')) if name=='Bash' else None)
            if ps: sr.append((res[tid]['chars'],[q.replace('/home/user/kod-shi-data/','') for q in ps]))
    out['start_reads']=dict(chars=sum(c for c,_ in sr),files=sorted({q for _,ps in sr for q in ps}))
    out['sub_ctx']=sum(ctx(r) for r in sub)
    return out,(reqs,order,prompts,tools,res)
def calibrate(all_parsed):
    xs=[]
    for d,(reqs,order,prompts,tools,res) in all_parsed.items():
        main=[reqs[m] for m in order if reqs[m]['parent'] is None]; idx={m:i for i,m in enumerate(order)}
        for i in range(1,len(main)):
            a,b=main[i-1],main[i]; ga,gb=idx[a['id']],idx[b['id']]
            if len(main) and ctx(b)>ctx(a):
                ch=sum(v['chars'] for t,v in res.items() if ga<v['after']<=gb and t in tools and tools[t][0]==a['id'])
                if ch>6000 and len([1 for t,v in res.items() if ga<v['after']<=gb])==1: xs.append(ch/(ctx(b)-ctx(a)-0))
    return statistics.median(xs) if xs else 3.0, len(xs)
if __name__=='__main__':
    ROOT=sys.argv[1]; outp=sys.argv[2]
    import csv,datetime
    csvp=sys.argv[3] if len(sys.argv)>3 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'../../витрати/сесії_2611_0806.csv')
    ids={v[0]:k for k,v in SESS.items()}; CSVU={}
    NAMES.update({r['id']:r['назва'] for r in csv.DictReader(open(csvp))})
    OVR={'H4':'2026-11-26T07:21:30'} # зріз usage у списку для Н4 відстає від «оновлено» на ~30 хв: накопичена cache_read сягає значення списку о 07:21:08
    for r in csv.DictReader(open(csvp)):
        if r['id'] in ids:
            # події після зрізу списку («оновлено», UTC) не беремо: список знято о 08:06, сесії тривали далі
            d=datetime.datetime.fromisoformat(r['оновлено'])+datetime.timedelta(seconds=90); CUT[ids[r['id']]]=d.strftime('%Y-%m-%dT%H:%M:%S'); CSVU[ids[r['id']]]=json.loads(r['usage'])
            if ids[r['id']] in OVR: CUT[ids[r['id']]]=OVR[ids[r['id']]]
    parsed={}; results={}
    for d in SESS:
        if not os.path.isdir(f'{ROOT}/{d}'): continue
        o,p=analyze(d,3.0); parsed[d]=p; results[d]=o
    K,n=calibrate(parsed)
    # Н3: пункт 6 — що кожна наступна сесія прочитала наново з прочитаного попередніми
    h3=['H3a','H3b','H3c','H3d']; seen=set(); p6={}
    for d in h3:
        if d not in parsed: continue
        reqs,order,prompts,tools,res=parsed[d]; main=[reqs[m] for m in order if reqs[m]['parent'] is None]
        idx={m:i for i,m in enumerate(order)}; local=set(); reps=[]; rep=0; carry=0.0; readc=0
        for tid,(mid,name,inp) in tools.items():
            if name=='Read': keys=[inp.get('file_path','')]
            elif name=='Bash':
                ps=read_paths(inp.get('command','')) or []
                keys=[(q if q.startswith('/') else '/home/user/kod-shi-data/'+q.lstrip('./')) for q in ps]
            else: continue
            if not keys or tid not in res: continue
            ch=res[tid]['chars']/len(keys); readc+=res[tid]['chars']
            after=res[tid]['after']; left=len([1 for r in main if idx[r['id']]>=after])
            for k in keys:
                k=k.replace('/home/user/kod-shi-data/','')
                if k in seen and k not in local:  # прочитано в одній з попередніх сесій наряду, у цій — уперше
                    rep+=ch; reps.append((k,int(ch))); carry+=ch/K*left
                local.add(k)
        seen|=local
        tot_ch=sum(v['chars'] for v in res.values())
        p6[d]=dict(read_chars=readc,tool_chars=tot_ch,repeat_chars=int(rep),repeat_files=len(set(k for k,_ in reps)),
                   repeat_share_of_read=rep/max(1,readc),repeat_share_of_tool_chars=rep/max(1,tot_ch),carry_tokens=int(carry),
                   carry_share_ctx=carry/max(1,results[d]['sum_ctx']),top=sorted(reps,key=lambda x:-x[1])[:6])
    json.dump(dict(K_chars_per_token=K,K_n=n,sessions={SESS[d][0]:dict(name=SESS[d][1],dir=d,csv_usage=CSVU[d],cut=CUT[d],**results[d]) for d in results},p6=p6),open(outp,'w'),ensure_ascii=False,indent=1)
    print('K',K,n)
