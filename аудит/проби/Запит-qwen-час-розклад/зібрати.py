"""З кореня: python -I аудит/проби/Запит-qwen-час-розклад/зібрати.py.
Лише записи main; номер виклику = номер ↔ / файлу обміну. p90 — найближчий ранг.
"""
import collections as C
import csv
import hashlib
import json
import math
import re
import statistics as S
import subprocess
from datetime import datetime
from pathlib import Path

BASE = '2feac15c7851139663e174310483568fa61a742c'
ROOT = Path('аудит/проби')
OUT = Path(__file__).resolve().parent
A = re.compile(r'^\s+↔ модель #(\d+) (.*?)(?: \((\d+) симв\.(.*?)(?: → ([\d.]+) с · HTTP (\d+)|$)| — (.*)$)', re.M)
B = re.compile(r'^\s+· (.*?) — HTTP (\d+) · ([\d.]+) с · вхід (\d+) т\. · вихід за лічильником CLI \(з міркуванням\) (\d+) т\.', re.M)
SW = re.compile(r'^перемикання #(\d+) → (.*?) · (\d+) мс', re.M)

def read(p):
    return p.read_text(encoding='utf-8') if p.exists() else ''

def obj(v):
    return json.loads(v) if isinstance(v, str) else v

def stats(v):
    v = sorted(x for x in v if isinstance(x, (int, float)))
    return {'n': len(v), 'медіана': S.median(v) if v else None,
            'p90': v[math.ceil(.9*len(v))-1] if v else None, 'середнє': S.mean(v) if v else None}

def fmt(v):
    s = stats(v)
    return f"{s['медіана']:.1f} / {s['p90']:.1f} ({s['n']})" if s['n'] else 'не виміряно (0)'

def table(header, rows):
    return '\n'.join(['| '+' | '.join(header)+' |', '| '+' | '.join(['---']*len(header))+' |']+
                     ['| '+' | '.join(str(x).replace('|','\\|') for x in row)+' |' for row in rows])

def writecsv(name, rows):
    with (OUT/name).open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

tracked = subprocess.check_output(['git','ls-tree','-rz','--name-only',BASE,'аудит/проби']).decode('utf-8').split('\0')
paths = {Path(p) for p in tracked if p and (p.split('/')[2].startswith(('автоживий-','Е1-нічний-живий-')) or p.split('/')[2]=='нічні')}
dirs = set()
for p in paths:
    if p.name in ('результат.json','лог.txt','проксі.txt'): dirs.add(p.parent)
    if p.parent.name=='обмін' and p.suffix=='.json': dirs.add(p.parents[2])
assert all(p.exists() for p in paths), 'Потрібні архіви не викладено sparse-checkout'
scenes, calls, excluded, checks, manifest = [], [], [], [], []
for dp in sorted(dirs):
    rel = dp.relative_to(ROOT).as_posix()
    r = json.loads(read(dp/'результат.json') or '{}')
    start = r.get('початок') or r.get('початок_utc') or ''
    date = start[:10]
    date_source = 'результат.json:початок' if r.get('початок') else 'результат.json:початок_utc'
    if not date:
        date_source = 'дата викликів відсутня; дата теки прогону'
        m = re.search(r'2026(\d\d)(\d\d)',rel)
        date = f'2026-{m[1]}-{m[2]}' if m else ''
    run = '/'.join(rel.split('/')[:2]) if rel.startswith('нічні/') else rel.split('/')[0]
    t = read(dp/'лог.txt'); aa = list(A.finditer(t))
    bb = list(B.finditer(t[t.find('ЖИВА МОДЕЛЬ'):])) if 'ЖИВА МОДЕЛЬ' in t else []
    ex = {int(p.stem):p for p in (dp/'VIDPOVIDI/обмін').glob('*.json') if p in paths and p.stem.isdigit()}
    ids = {int(m[1]) for m in aa} | set(ex)
    if not aa: ids |= set(range(1,len(bb)+1))
    if date < '2026-11-07':
        excluded.append({'тека':rel,'дата':date,'причина':'до 07.11' if date else 'нема дати','викликів':len(ids)})
        continue
    z = r.get('змінні',{}); dur = r.get('секунд',r.get('секунди'))
    if dur is None and start and r.get('кінець'):
        dur = (datetime.fromisoformat(r['кінець'])-datetime.fromisoformat(start)).total_seconds()
    proxy = read(dp/'проксі.txt'); sw = list(SW.finditer(proxy))
    assert len(sw)==sum(l.startswith('перемикання #') for l in proxy.splitlines()),rel
    sm = {'тека':rel,'прогін':run,'дата':date if start else 'невідома','дата_групи':date,'джерело_дати':date_source,
          'початок':start,'результат':bool(r),'секунд':dur,
          'режим':'розмова' if z.get('DO')=='rozmova' else 'палітра' if z.get('DO')=='palitra' else 'повне +фото' if z.get('FOTO')=='1' else 'повне',
          'обірвано':'прогін обірвався' in t,'rc':r.get('rc'),'sha':r.get('sha'),
          'повтор_запису':r.get('моделі_не_викликаються',False),
          'лог_викликів':len(aa) or len(bb),'обмінів':len(ex),'викликів':len(ids),
          'проксі':(dp/'проксі.txt').exists(),'перемикань':len(sw) if proxy else None,
          'перемикання_с':sum(int(m[3]) for m in sw)/1000 if proxy else None,
          'є_кроки':bool(re.search(r'чат → паспорт за [\d.]+ с',t)) and bool(re.search(r'збирання \(сід \d+\) за [\d.]+ с',t))}
    scenes.append(sm)
    amap = {int(m[1]):m for m in aa}; assert len(amap)==len(aa),f'Дублі номерів {rel}'
    assert set(amap)=={int(n) for n in re.findall(r'↔ модель #(\d+)',t)}, f'Нерозібраний виклик {rel}'
    bmap = {}
    if aa and bb:
        if len(aa)==len(bb) and all(a[2]==b[1] and (a[5] is None or abs(float(a[5])-float(b[3]))<.11) for a,b in zip(aa,bb)):
            bmap = {int(a[1]):b for a,b in zip(aa,bb)}
        else: checks.append({'тека':rel,'перевірка':'підсумок не зіставлено','A':len(aa),'B':len(bb)})
    elif not aa: bmap = dict(enumerate(bb,1))
    occurrence = C.Counter()
    for n in sorted(ids):
        a,b,p = amap.get(n),bmap.get(n),ex.get(n)
        kind = a[2] if a else b[1] if b else 'не названо в лог.txt'; occurrence[kind]+=1
        row = {'тека':rel,'прогін':run,'дата':date if start else 'невідома','дата_групи':date,'n':n,
               'повтор_запису':sm['повтор_запису'],
               'вид':kind,'порядковий_цього_виду':occurrence[kind],
               'рядок_логу':t.count('\n',0,a.start())+1 if a else None,
               'модель':None,'http':int(a[6]) if a and a[6] else int(b[2]) if b else None,
               'вхід':None,'вихід':None,'с':float(a[5]) if a and a[5] else float(b[3]) if b else None,
               'т_с':None,'ttft_с':None,'джерело_токенів':None,'файл_обміну':bool(p),
               'зіставлення':'номер' if a and p else 'порядок підсумку' if b and p else 'лише лог' if a or b else 'лише обмін'}
        if p:
            d = json.loads(read(p)); q = obj(d['запит']); response = d.get('відповідь',{}); body = obj(response.get('body',{}))
            if not isinstance(body,dict): body = {}
            usage = body.get('usage') or {}
            row['модель'] = q.get('model') or response.get('headers',{}).get('x-model')
            row['http'] = row['http'] or response.get('status')
            row['вхід'] = usage.get('input_tokens',usage.get('prompt_tokens'))
            row['вихід'] = usage.get('output_tokens',usage.get('completion_tokens'))
            row['джерело_токенів'] = 'відповідь.body.usage' if row['вихід'] is not None else None
            for container in (d,response,body,usage,body.get('stats',{})):
                if isinstance(container,dict):
                    for key in ('time_to_first_token','time_to_first_token_seconds','ttft','ttft_seconds'):
                        if isinstance(container.get(key),(int,float)): row['ttft_с']=container[key]
            if b and row['вихід'] is not None:
                assert row['вихід']==int(b[5]) and row['вхід']==int(b[4]),(rel,n,'токени логу != обміну')
        if row['вихід'] is None and b and int(b[2])==200:
            row['вхід'],row['вихід']=int(b[4]),int(b[5]); row['джерело_токенів']='лог.txt:ЖИВА МОДЕЛЬ'
        # У повторі обміну токени належать старій відповіді, а 0 с — відтворенню, не моделі.
        if sm['повтор_запису']:
            row['вхід']=row['вихід']=row['с']=None
            row['джерело_токенів']=None
        if row['вихід'] is not None and row['с'] and row['http']==200: row['т_с']=row['вихід']/row['с']
        calls.append(row)
    for p in [dp/'результат.json',dp/'лог.txt',dp/'проксі.txt',*sorted(ex.values())]:
        if p.exists(): manifest.append({'файл':p.as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})

writecsv('виклики.csv',calls); writecsv('сцени.csv',scenes); writecsv('виключені.csv',excluded); writecsv('джерела.csv',manifest)
groups = C.defaultdict(list); missing = C.defaultdict(list)
for c in calls:
    groups[(c['прогін'],c['дата'],c['модель'] or 'невідома')].append(c)
    missing[(c['тека'],c['модель'] or 'невідома')].append(c)
lines = ['# Таблиці виміру','','Поля: медіана / p90 (n); p90 — найближчий ранг. День UTC з результату; невідома дата окремо.','',
         table(['прогін','дата','модель','викликів','вхід, т.','вихід, т.','тривалість, с','вихід / час, т./с','TTFT, с'],
               [[*k,len(v),*[fmt(c[f] for c in v) for f in ('вхід','вихід','с','т_с','ttft_с')]] for k,v in sorted(groups.items())]),'',
         '## Перемикання по сцені','','Кількість включає початкове завантаження #1. None — не виміряно; 0 — відсутність рядків у записаному файлі.','',
         table(['сцена','дата','викликів','перемикань','сума, с'],[[s['тека'],s['дата'],s['викликів'],s['перемикань'],s['перемикання_с']] for s in scenes]),'',
         '## Відсутні поля: повний перелік','',table(['сцена','модель','поле','номери викликів'],
             [[*k,f,', '.join(str(c['n']) for c in v if c[f] is None)] for k,v in sorted(missing.items())
              for f in ('вхід','вихід','с','ttft_с') if any(c[f] is None for c in v)])]
qwen = [c for c in calls if c['модель']=='qwen/qwen3.5-9b']; dated=[c for c in qwen if c['дата']!='невідома']
types = C.defaultdict(lambda:[[],[]])
for c in dated: types[(c['вид'],c['порядковий_цього_виду'])][c['дата']>='2026-11-15'].append(c)
lines += ['','## Стилістка: точний вид і порядковий виклик цього виду в сцені','',
          'Порядковий 2+ не означає мережевий повтор: це може бути інша рука. Семантичний вид збережено дослівно.','',
          table(['вид','порядковий','до 15: вихід','з 15: вихід','до 15: с','з 15: с'],
                [[*k,fmt(c['вихід'] for c in b),fmt(c['вихід'] for c in a),fmt(c['с'] for c in b),fmt(c['с'] for c in a)] for k,(b,a) in sorted(types.items())])]
(OUT/'таблиці.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
summary = {'база_main':BASE,'сцен_наявних':len(dirs),'сцен_від_07':len(scenes),'сцен_виключено':len(excluded),
           'викликів_наявних':len(calls)+sum(s['викликів'] for s in excluded),'викликів_від_07':len(calls),
           'лог_і_обмін':sum(c['зіставлення'] in ('номер','порядок підсумку') for c in calls),
           'лише_лог':sum(c['зіставлення']=='лише лог' for c in calls),'лише_обмін':sum(c['зіставлення']=='лише обмін' for c in calls),
           'полів':{f:sum(c[f] is not None for c in calls) for f in ('вхід','вихід','с','т_с','ttft_с')},
           'не_зіставлені_підсумки':checks,'qwen_до_з':{},'швидкість_за_датами':{},'складники':{},'перемикання_за_датами':{}}
for after in (False,True):
    v=[c for c in dated if (c['дата']>='2026-11-15')==after]
    summary['qwen_до_з'][str(after)]={'прогони':sorted({c['прогін'] for c in v}),**{f:stats(c[f] for c in v) for f in ('вхід','вихід','с','т_с')}}
for dt in sorted({c['дата'] for c in dated}):
    v=[c for c in dated if c['дата']==dt]
    summary['швидкість_за_датами'][dt]={f:stats(c[f] for c in v) for f in ('вихід','с','т_с')}
for dt in sorted({s['дата'] for s in scenes}):
    v=[s for s in scenes if s['дата']==dt and s['перемикання_с'] is not None]
    summary['перемикання_за_датами'][dt]={'сцен':len(v),'число':stats(s['перемикань'] for s in v),'с':stats(s['перемикання_с'] for s in v)}
for mode in ('повне','повне +фото'):
    for dt in sorted({s['дата'] for s in scenes}):
        ss=[]
        for s in scenes:
            if s['дата']!=dt or s['режим']!=mode or not s['є_кроки'] or s['обірвано'] or not s['секунд']: continue
            v=[c for c in calls if c['тека']==s['тека']]
            if not v or not all(c['модель'] and c['с'] is not None for c in v): continue
            if any(c['модель']=='claude-sonnet-5-5' or c['с']>3000 for c in v): continue
            total=sum(c['с'] for c in v)
            if total>s['секунд']+1: continue
            ss.append({'тека':s['тека'],'сцена':s['секунд'],'запити':total,'поза':s['секунд']-total,
                       'qwen':sum(c['с'] for c in v if c['модель']=='qwen/qwen3.5-9b'),'перемикання':s['перемикання_с']})
        if ss: summary['складники'][mode+' '+dt]={'сцен':len(ss),'суми':{f:sum(s[f] for s in ss) for f in ('сцена','запити','поза','qwen')},
                    'середні':{f:S.mean(s[f] for s in ss) for f in ('сцена','запити','поза','qwen')},'сцени':ss}
full = {s['тека']:s for v in summary['складники'].values() for s in v['сцени']}
pairs = []
for s in scenes:
    if not s['тека'].startswith('Е1-нічний-живий-20261107/') or s['тека'].count('/')!=1: continue
    before = full.get(s['тека']); after = full.get(s['тека'].replace('20261107/','20261115/',1))
    if not before or not after: continue
    after_scene = next(x for x in scenes if x['тека']==after['тека'])
    if after_scene['режим']!=s['режим']: continue
    p={'до':before['тека'],'після':after['тека'],'режим':s['режим']}
    for field in ('сцена','запити','поза','qwen','перемикання'):
        p[field+'_до']=before[field]; p[field+'_після']=after[field]
    for model in ('qwen/qwen3.5-9b','mamaylm-gemma-3-12b-it-v2.0'):
        a=[c for c in calls if c['тека']==before['тека'] and c['модель']==model]
        b=[c for c in calls if c['тека']==after['тека'] and c['модель']==model]
        n1,n2=len(a),len(b); d1,d2=S.mean(c['с'] for c in a),S.mean(c['с'] for c in b)
        p[model+'_число_до']=n1; p[model+'_число_після']=n2
        p[model+'_с_до']=d1; p[model+'_с_після']=d2
        p[model+'_довший_виклик']=(n1+n2)/2*(d2-d1)
        p[model+'_число_викликів']=(d1+d2)/2*(n2-n1)
    pairs.append(p)
writecsv('пари.csv',pairs)
summary['пари']={'n':len(pairs),'середні':{f:S.mean(p[f] for p in pairs) for f in pairs[0] if isinstance(pairs[0][f],(int,float))}}
old=min(s['початок'] for s in scenes if s['прогін']=='Е1-нічний-живий-20261113' and s['початок'])
new=min(s['початок'] for s in scenes if s['прогін']=='Е1-нічний-живий-20261115' and s['початок'])
cmd=['git','log',BASE,'--first-parent','--reverse','--since='+old,'--until='+new,'--format=%H%x09%cI%x09%s']
prs=[r.split('\t') for r in subprocess.check_output(cmd).decode('utf-8').splitlines() if '(#' in r]
(OUT/'злиття.md').write_text('# Злиття між початками сусідніх прогонів\n\nКоманда: `'+' '.join(cmd)+'`\n\n'
    'Лише заголовки з номером PR `(#…)`; автоматичні коміти збірки пропущено. Перелік збігів у часі, без висновку про причину.\n\n'+
    table(['SHA','дата git зі зсувом','заголовок'],prs)+'\n',encoding='utf-8')
summary['злиттів_між_прогонами']=len(prs)
actual=[c for c in calls if not c['повтор_запису'] and c['http'] in (200,503,504)]
summary['фактичних_спроб_моделей']=len(actual)
summary['сцен_із_фактичними_спробами']=len({c['тека'] for c in actual})
summary['сцен_відтворення']=sum(s['повтор_запису'] for s in scenes)
(OUT/'зведення.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ('складники','qwen_до_з','швидкість_за_датами','перемикання_за_датами','не_зіставлені_підсумки')},ensure_ascii=False,indent=1))
print('Не зіставлено підсумків:',len(checks))
