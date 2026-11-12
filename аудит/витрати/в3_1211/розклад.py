"""В.3: куди пішли токени Claude, Codex і agy за 29.10–05.11 і що дали. Входи — тека в3/ (див. аналіз_0511.md §1)."""
import csv,json,re,sys,subprocess,collections as C
from datetime import datetime
import os as _os
В=_os.path.dirname(_os.path.abspath(__file__)); R=_os.path.abspath(_os.path.join(В,'../../..'))
sys.path.insert(0,В); from вид import вид, про_корінь_продукту
T=В; О=R+'/аудит/витрати'
def git(*a): return subprocess.run(['git','-C',R,'-c','core.quotepath=off',*a],capture_output=True,text=True).stdout
def t(s): return datetime.fromisoformat(s.replace('Z','+00:00'))
A,B=open(f'{T}/межі.txt').read().split()
pr={x['number']:x for x in map(json.loads,open(f'{T}/pr.jsonl'))}
злиття=list(csv.DictReader(open(f'{T}/злиття.csv')))
запуски=list(csv.DictReader(open(R+'/аудит/витрати/токени_ноутбука_1211/запуски.csv')))
i=lambda x:int(x) if x not in ('',None) else 0
# ---------- рушій гілки обгортки за токенами запусків у вікні
рушій_гілки=C.defaultdict(C.Counter)
for x in запуски:
    if x['гілка']: рушій_гілки[x['гілка']][x['рушій']]+=i(x['разом_вікна'])+1
def постачальник_гілки(g,сесії):
    if g.startswith('gemini/'):
        c=рушій_гілки.get(g)
        return ('Codex' if c.most_common(1)[0][0]=='codex' else 'agy') if c else 'обгортка (запуск до вікна)'
    if g.startswith('claude/'): return 'Claude' if сесії else 'Claude (без сесії; ноутбук?)'
    return 'інше'
# ---------- злиття: постачальник, PR усередині пачок
for z in злиття:
    z['вкладені']=''
    if re.match(r'claude/pachka',z['гілка']):
        p1=git('rev-parse',z['sha']+'^1').strip()
        журнал=git('log','--format=%s',f"{p1}..{z['sha']}")
        внутр=set(re.findall(r"Merge remote-tracking branch 'origin/([^']+)' into (?:claude/)?pachka",журнал))
        номери=set()
        for рядок in журнал.split('\n')+[pr.get(int(z['pr']),{}).get('title','')]:
            if re.match(r'(Пачка|Pachka|пачка)',рядок): номери|={int(n) for n in re.findall(r'#(\d+)',рядок)}
        номери.discard(int(z['pr']))
        внутр|={pr[n]['head_ref'] for n in номери if n in pr and not pr[n]['head_ref'].startswith('claude/pachka')}
        внутр=sorted(g for g in внутр if g!='main')
        z['вкладені']=' '.join(внутр)
        пост=C.Counter(постачальник_гілки(g,'x') for g in внутр)
        z['постачальник']='пачка: '+', '.join(f'{k} {v}' for k,v in пост.items()) if внутр else 'Claude'
    else:
        z['постачальник']=постачальник_гілки(z['гілка'],z['claude_сесії'])
    z['prs']=' '.join(sorted(set(re.findall(r'#(\d+)',z['тема']))|({z['pr']} if z['pr'] else set())))
продукт_pr=set()
for z in злиття:
    if i(z['продукт']): продукт_pr|=set(map(int,z['prs'].split()))
w=csv.DictWriter(open(f'{О}/злиття_1211.csv','w',newline=''),fieldnames=['sha','час','pr','prs','гілка','постачальник','вкладені','файлів','продукт','прилади','обгортка','дошка','наряди','документи','claude_сесії','gemini_співавтор','тема'])
w.writeheader(); [w.writerow({k:z[k] for k in w.fieldnames}) for z in злиття]
# ---------- Claude: сесії
сесії=[json.loads(l) for l in open(f'{T}/дані.jsonl')]
ПОПРАВКА={ # $ поза вікном (див. аналіз §1)
 'session_01TctSEcetUWE1jcJWUpJjRY':142.7493, # до 29.10 — cost_у_вікні В.2 (сесії_2229.csv)
 'session_01FPQuiashigctm8vV4JXxd7':29.1476,  # до 29.10 — cost_у_вікні В.2
 'session_01FPQuiZyd9M1gnM6g7n3Gkn':68.6324-66.7463, # після 05.11: usage − total_cost_usd останнього result до межі
 'session_01FPQuiY6a3ufUCxKG2Naof8':222.1027-216.8689, # після 05.11: різниця total_cost_usd після межі
}
сесія_злиття=C.defaultdict(list)
for z in злиття:
    for s in z['claude_сесії'].split(): сесія_злиття[s].append(z)
рядки_c=[]
for s in сесії:
    c=s['cost_usd']; вік=round(c-ПОПРАВКА.get(s['id'],0),4) if c is not None else None
    зл=сесія_злиття.get(s['id'],[])
    рядки_c.append(dict(id=s['id'],назва=s['title'],створено=s['created_at'][:19],оновлено=s['updated_at'][:19],
      модель=(s['model'] or '').replace('claude-',''),зусилля=s['effort'] or '',вид=вид(s['title']),
      корінь_продукту=int(про_корінь_продукту(s['title'])),cost_usd=c,cost_у_вікні=вік,
      input=s['input_tokens'],output=s['output_tokens'],cache_read=s['cache_read_tokens'],cache_write=s['cache_write_tokens'],
      контекст=s['ctx_used'],злиттів=len(зл),злиттів_продукту=sum(1 for z in зл if i(z['продукт']))))
# перевірки: PR → чи корінь продукту
def pr_корінь(n):
    x=pr.get(n); 
    return int(bool(x and (про_корінь_продукту(x['head_ref'].split('/',1)[-1]) or про_корінь_продукту(x['title'])))) 
for r in рядки_c:
    if r['вид']=='перевірка':
        m=re.search(r'#(\d{4})',r['назва'])
        if m: r['корінь_продукту']=pr_корінь(int(m.group(1)))
w=csv.DictWriter(open(f'{О}/сесії_1211.csv','w',newline=''),fieldnames=list(рядки_c[0]))
w.writeheader(); w.writerows(sorted(рядки_c,key=lambda r:r['створено']))
# ---------- ноутбук: наряди
def наряд(p):
    ч=p.split('/'); n=ч[1] if len(ч)>1 else p
    return n
нр=C.OrderedDict()
for x in запуски:
    n=наряд(x['позначка']); ч=x['позначка'].split('/')
    спроба=i(ч[3]) if len(ч)>3 and ч[3].isdigit() else 1
    пост={'codex':'Codex','agy':'agy'}[x['рушій']]
    k=(пост,n)
    r=нр.setdefault(k,dict(постачальник=пост,наряд=n,вид=вид(n),корінь_продукту=int(про_корінь_продукту(n)),гілки=set(),
        запусків=0,сесій_моделі=0,спроб_понад_першу=0,разом=0,без_кешу=0,разом_спроб2=0,без_кешу_збоїв=0,коди=C.Counter(),моделі=C.Counter()))
    r['запусків']+=1; r['сесій_моделі']+=x['стадія']=='сесія моделі'
    tot=i(x['разом_вікна']); 
    нк=(i(x['вхід_вікна'])-i(x['кеш_вікна'])+i(x['вихід_вікна'])) if x['рушій']=='codex' else tot
    r['разом']+=tot; r['без_кешу']+=нк
    if спроба>1: r['спроб_понад_першу']+=1; r['разом_спроб2']+=нк
    if x['код'] in ('STALL','CRASH','AGY_ERROR','QUOTA','STALE','EMPTY_PLAN'): r['без_кешу_збоїв']+=нк
    r['коди'][x['код']]+=1; r['моделі'][x['модель']]+=нк
    if x['гілка']: r['гілки'].add(x['гілка'])
    m=re.match(r'(автоперевірка|перевірка)-(\d{4})',n)
    if m: r['корінь_продукту']=pr_корінь(int(m.group(2)))
for r in нр.values():
    злиті=[p for p in pr.values() if p['head_ref'] in r['гілки'] and p['merged_at'] and p['merged_at']<'2026-11-12T02']
    r['злито_pr']=' '.join(str(p['number']) for p in злиті)
    інші=[p for p in pr.values() if p['head_ref'] in r['гілки'] and p not in злиті]
    r['відкриті_pr']=' '.join(str(p['number']) for p in інші if p['state']=='open')
    r['закриті_без_злиття']=' '.join(str(p['number']) for p in інші if p['state']=='closed' and not p['merged_at'])
    r['злиттів_продукту']=sum(1 for p in злиті if p['number'] in продукт_pr)
    r['гілки']=' '.join(sorted(r['гілки'])); r['коди']=' '.join(f'{k}:{v}' for k,v in r['коди'].most_common())
    r['моделі']=' '.join(f'{k}:{v}' for k,v in r['моделі'].most_common() if v)
поля=['постачальник','наряд','вид','корінь_продукту','запусків','сесій_моделі','спроб_понад_першу','разом','без_кешу','разом_спроб2','без_кешу_збоїв','коди','моделі','гілки','злито_pr','відкриті_pr','закриті_без_злиття','злиттів_продукту']
w=csv.DictWriter(open(f'{О}/наряди_ноутбука_1211.csv','w',newline=''),fieldnames=поля)
w.writeheader(); w.writerows(sorted(нр.values(),key=lambda r:(r['постачальник'],-r['без_кешу'])))
print('ok',len(злиття),len(рядки_c),len(нр))
