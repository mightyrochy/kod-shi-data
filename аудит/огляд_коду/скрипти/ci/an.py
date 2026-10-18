import json,glob,statistics as st,collections,datetime as dt
def t(s): return dt.datetime.fromisoformat(s.replace('Z','+00:00')) if s else None
runs=[l.rstrip("\n").split("\t") for l in open("runs_z.tsv") if l[0].isdigit()]
rows=[]; steps=collections.defaultdict(list); concl=collections.defaultdict(collections.Counter)
jobs_d=collections.defaultdict(list); queue=[]; gap=[]
for r in runs:
    rid,num,ev,co,cr,rs,up,br=r
    try: J=json.load(open(f'jobs/{rid}.json'))['jobs']
    except Exception: continue
    for j in J:
        if not j['started_at'] or not j['completed_at']: continue
        d=(t(j['completed_at'])-t(j['started_at'])).total_seconds()
        q=(t(j['started_at'])-t(j['created_at'])).total_seconds()
        if j['conclusion']=='success': jobs_d[j['name']].append(d)
        queue.append(q)
        for s in j['steps']:
            n=s['name']
            if n.startswith('Run actions/'): n=n.split('@')[0]
            if n.startswith('Post Run'): n='Post Run'
            if s['started_at'] and s['completed_at']:
                dd=(t(s['completed_at'])-t(s['started_at'])).total_seconds()
                if s['conclusion']=='success': steps[(j['name'],s['number'] if s['number']<30 else 99,n)].append(dd)
            concl[(j['name'],n)][s['conclusion']]+=1
    if co=='success':
        rows.append((ev,(t(up)-t(rs)).total_seconds(),rid))
        if len(J)==2: gap.append((t(J[1]['started_at'])-t(J[0]['completed_at'])).total_seconds())
def f(a): return f"{st.median(a):.0f} / {min(a):.0f} / {max(a):.0f} (n={len(a)})"
for ev in ('pull_request','push'):
    a=[x[1]/60 for x in rows if x[0]==ev]
    print(ev,'run wall min: median %.1f min %.1f max %.1f n=%d'%(st.median(a),min(a),max(a),len(a)))
for k,v in jobs_d.items(): print('JOB',k,f(v))
print('queue s',f(queue),'gap between jobs',f(gap))
print('| job | # | step | median/min/max s |')
for k in sorted(steps): print('|',k[0],'|',k[1],'|',k[2],'|',f(steps[k]),'|')
print('CONCL')
for k,v in sorted(concl.items()):
    if set(v)-{'success'}: print(k,dict(v))
