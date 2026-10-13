import json,gzip,re,os,glob,statistics as st,collections as C,sys
R='/tmp/a6/runs'
runs=sorted(d for d in os.listdir(R) if re.match(r'ж\d_',d))
LINE=re.compile(r'↔ модель #(\d+) (.+?) \((\d+) симв\., разом (\d+)(?:, фото (\d+)(?: \(не дійшло (\d+)\))?)?\) → ([\d.]+) с · HTTP (\d+) · (\d+) симв\.(.*)$')
calls=[]; per_run={}
layer=C.Counter(); layer_runs=C.defaultdict(set); fails=C.Counter(); fail_runs=C.defaultdict(list)
for r in runs:
    log=gzip.open(f'{R}/{r}/лог.txt.gz','rt',encoding='utf8').read().split('\n')
    try: j=json.load(gzip.open(f'{R}/{r}/модель_виклики.json.gz','rt',encoding='utf8'))['виклики']
    except Exception as e: j=[]
    L=[m for m in (LINE.search(l) for l in log) if m]
    if len(L)!=len(j): print('!! розбіжність', r, len(L), len(j), file=sys.stderr)
    for i,m in enumerate(L):
        jj=j[i] if i<len(j) else {}
        t=m.group(2)
        if jj and jj.get('тип')!=t: print('!! тип', r, i, t, jj.get('тип'), file=sys.stderr)
        calls.append(dict(run=r,typ=t,ch=int(m.group(3)),tot=int(m.group(4)),foto=int(m.group(5) or 0),drop=int(m.group(6) or 0),
            s=float(m.group(7)),http=int(m.group(8)),out=int(m.group(9)),tail=m.group(10),
            tin=jj.get('вхід',0),tout=jj.get('вихід',0),stop=jj.get('стоп'),err=jj.get('помилка'),over=jj.get('понад_стелю_продукту')))
    for l in log:
        mm=re.search(r'· (hand_\w+(?:\.\w+)*) · layer · dir=(\w+).*?(?:texts=(\d+) · changed=(\d+)|messages=(\d+) · said=(\d+))(.*)',l)
        if mm:
            who=mm.group(1)
            for suf in ('retry','latin_retry'):
                if who.endswith('.'+suf): layer[suf]+=1; layer_runs[suf].add(r)
            if 'several_json_merged' in (mm.group(7) or ''): layer['several_json_merged']+=1; layer_runs['several_json_merged'].add(r)
            a,b=(mm.group(3),mm.group(4)) if mm.group(3) else (mm.group(5),mm.group(6))
            if a and b and int(b)<int(a): layer['changed<texts']+=1; layer_runs['changed<texts'].add(r)
        if 'completeness_repair' in l and 'attempt=' in l:
            layer['completeness_repair']+=1; layer_runs['completeness_repair'].add(r)
        if '✗' in l:
            k=re.sub(r'\s+→.*','',l.split('✗',1)[1]).strip()[:90]; fails[k]+=1; fail_runs[k].append(r)
    per_run[r]=dict(n=len(L))
json.dump(calls,open('/tmp/a6/calls.json','w'),ensure_ascii=False)
print('прогонів',len(runs),'викликів',len(calls))
by=C.defaultdict(list)
for c in calls: by[c['typ']].append(c)
def q(v,p): v=sorted(v); return v[min(len(v)-1,int(p*len(v)))]
print('| тип | викл. | у прогонів | промпт симв. сер/макс | вхід т. сер/макс | вихід симв. сер | вихід т. CLI сер | с сер/p95/макс | HTTP≠200 | фото не дійшло |')
for t,v in sorted(by.items(),key=lambda x:-len(x[1])):
    print(f"| {t} | {len(v)} | {len(set(c['run'] for c in v))} | {int(st.mean(c['ch'] for c in v))}/{max(c['ch'] for c in v)} | {int(st.mean(c['tin'] for c in v))}/{max(c['tin'] for c in v)} | {int(st.mean(c['out'] for c in v))} | {int(st.mean(c['tout'] for c in v))} | {st.mean(c['s'] for c in v):.1f}/{q([c['s'] for c in v],.95):.1f}/{max(c['s'] for c in v):.1f} | {sum(c['http']!=200 for c in v)} | {sum(c['drop'] for c in v)} |")
print('шар:',dict(layer),{k:len(v) for k,v in layer_runs.items()})
print('помилки:',[(c['run'],c['typ'],c['http'],(c['err'] or '')[:120]) for c in calls if c['http']!=200])
print('понад стелю продукту:',C.Counter(c['typ'] for c in calls if c['over']), 'макс-стоп:',C.Counter(c['typ'] for c in calls if c['stop']=='max_tokens'))
print('✗:'); [print(' ',n,k,len(set(fail_runs[k]))) for k,n in fails.most_common()]
tot=C.Counter(); 
for c in calls: tot[c['run']]+=c['tin']
print('вхід т. на прогін сер/мін/макс', int(st.mean(tot.values())), min(tot.values()), max(tot.values()))
s=C.Counter()
for c in calls: s[c['run']]+=c['s']
print('сек. моделі на прогін (сума) сер/макс', int(st.mean(s.values())), int(max(s.values())))
