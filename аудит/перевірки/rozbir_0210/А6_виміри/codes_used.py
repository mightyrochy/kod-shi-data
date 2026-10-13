import json,re,glob,collections as C,statistics as st
res=C.defaultdict(list)
for fn in glob.glob('/tmp/a6/runs/*/x/VIDPOVIDI/*.txt'):
    t=open(fn,encoding='utf8').read()
    m=re.match(r'── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ',t,re.S)
    try: o=json.loads(m.group(2))
    except: continue
    task=o.get('task') or {}
    sc=task.get('statement_codes')
    if not sc: continue
    body=dict(o); body['task']={k:v for k,v in task.items() if k!='statement_codes'}
    s=json.dumps(body,ensure_ascii=False)
    used=[k for k in sc if re.search(r'"%s"'%re.escape(k),s)]
    typ=re.sub(r'^seed3_\d+_','',fn.split('/')[-1])[:-4]
    if typ.startswith('ВЕРДИКТ_V1_ОБРАЗИ') : typ+=('_big' if len(m.group(2))>20000 else '_small')
    res[typ].append((len(sc),len(used),len(json.dumps(sc,ensure_ascii=False)),sum(len(json.dumps(sc[k],ensure_ascii=False)) for k in sc if k not in used)))
for t,v in res.items():
    print(t, 'n',len(v),'кодів визн. сер',int(st.mean(x[0] for x in v)),'вжито сер',int(st.mean(x[1] for x in v)),'симв. словника сер',int(st.mean(x[2] for x in v)),'симв. невжитих сер',int(st.mean(x[3] for x in v)))
