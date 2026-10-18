import json,re,collections as C,itertools as I,sys,datetime as D
SP=sys.argv[1]
info={int(k):v for k,v in json.load(open(SP+'/prinfo.json')).items()}
hist=json.load(open(SP+'/hist.json'))
CODE=re.compile(r'^(джерела/[^/]+\.(py|js|html)|джерела/(прилади|аудит)/[^/]+\.py|zhnyvarka/[^/]+\.(py|js)|аудит/проби/рв6_стенд\.js)$')
DOC=re.compile(r'^(аудит/|CLAUDE\.md|AGENTS\.md|README\.md|джерела/аудит/.*\.md)')
def cat(f):
    if f=='аудит/БЕКЛОГ.md': return 'дошка'
    if CODE.match(f): return 'код'
    if f.startswith('джерела/проби/') or f.startswith('аудит/проби/'): return 'проби'
    if DOC.match(f): return 'документи/звіти'
    return 'інше'
churn=C.Counter(); 
for p,v in info.items():
    for f in set(v['files']): churn[f]+=1
N=len(info); print('PR',N)
print('files touched',len(churn),'; touched by >=10 PR',sum(1 for c in churn.values() if c>=10))
print('TOP20');[print(f'{c}\t{f}') for f,c in churn.most_common(20)]
print('TOP15 CODE');[print(f'{c}\t{f}') for f,c in [(f,c) for f,c in churn.most_common() if cat(f)=='код'][:15]]
# PR categories
board=sum(1 for v in info.values() if 'аудит/БЕКЛОГ.md' in v['files'])
code=[p for p,v in info.items() if any(cat(f)=='код' for f in v['files'])]
print('PR touching board',board,'; touching code',len(code))
FEAT=re.compile(r'адаптер|Складальник|маніфест|SHOPIFY|Shopify|КАДРИ-5697|Айдентика|прилад порядкового|ПЕРЕЛІК \(|ОЦІНИ-ОБРАЗ-ПЕРЕЛІК|захист CI',re.I)
DOCT=re.compile(r'ЧИСТКА|Чистка|Дошка|Слово власника|ЖИВІ-10|ОЦІНКА-Ж|Оцінка живого|розбір скарг|ПРОМПТИ-ПЕРЕЛІК|ОЧІ-|Рядок 5661')
cls={}
for p,v in info.items():
    if p in code: cls[p]='фіча' if FEAT.search(v['title']) else 'виправлення'
    else: cls[p]='документ/оцінка' if not any(cat(f) in('проби',) for f in v['files']) else 'проби/прилади'
print('PR classes',C.Counter(cls.values()))
# pairs among code+probe files (excluding board/docs)
pc=C.Counter()
for p,v in info.items():
    fs=sorted({f for f in v['files'] if cat(f)=='код'})
    for a,b in I.combinations(fs,2): pc[(a,b)]+=1
print('TOP PAIRS (code)');
for (a,b),c in pc.most_common(15):
    j=c/(churn[a]+churn[b]-c); print(f'{c}\tJ={j:.2f}\t{a.split("/")[-1]} + {b.split("/")[-1]}')
# average code files per code PR
print('code files per code PR: mean',round(sum(len({f for f in info[p]['files'] if cat(f)=="код"}) for p in code)/len(code),1),
      'median',sorted(len({f for f in info[p]['files'] if cat(f)=="код"}) for p in code)[len(code)//2])
print('files per PR all: mean',round(sum(len(v['files']) for v in info.values())/N,1))
# function repeats: for each PR, funcs touched in main commits within 30 days before its pack commit
def dt(s): return D.datetime.fromisoformat(s)
hidx={h['sha']:i for i,h in enumerate(hist)}
rep=0; repf=C.Counter(); tot=0; detail={}
for p,v in info.items():
    if not v['funcs']: continue
    tot+=1; d=dt(v['date'])
    prior=set()
    for h in hist:
        hd=dt(h['date'])
        if d-D.timedelta(days=30)<=hd<d and h['sha']!=v['pack']:
            prior|={tuple(x) for x in h['funcs']}
    same={tuple(x) for x in v['funcs']}&prior
    detail[p]=len(same)
    if same: rep+=1
print('PR touching functions',tot,'; repeats (≥1 same func edited in main ≤30 d before)',rep, f'{rep/tot:.0%}')
fr=C.Counter(); 
for p,v in info.items():
    for x in v['funcs']: fr[tuple(x)]+=1
print('TOP FUNCS among 150 PR');[print(c,'\t',f.split('/')[-1]+':'+fn) for (f,fn),c in fr.most_common(15)]
hf=C.Counter()
for h in hist:
    for x in h['funcs']: hf[tuple(x)]+=1
print('TOP FUNCS main first-parent since 10.09 (',len(hist),'commits)');[print(c,'\t',f.split('/')[-1]+':'+fn) for (f,fn),c in hf.most_common(15)]
# dates span
ds=sorted(v['date'] for v in info.values()); print('pack dates',ds[0],ds[-1])
json.dump(dict(cls=cls,detail=detail),open(SP+'/a3.json','w'))
PSEUDO={'_список','$','_з','помилка_формату','_суддя','_коди_розмови','_РЕ_кандидата'}
rep2=0;tot2=0
for p,v in info.items():
    fs={tuple(x) for x in v['funcs'] if x[1] not in PSEUDO}
    if not fs: continue
    tot2+=1; d=dt(v['date']); prior=set()
    for h in hist:
        hd=dt(h['date'])
        if d-D.timedelta(days=30)<=hd<d and h['sha']!=v['pack']: prior|={tuple(x) for x in h['funcs'] if x[1] not in PSEUDO}
    if fs&prior: rep2+=1
print('without pseudo-functions: PR',tot2,'repeats',rep2,f'{rep2/tot2:.0%}')
# share of functions touched by PR that were touched before (function-level)
a=b=0
for p,v in info.items():
    d=dt(v['date']); prior=set()
    for h in hist:
        if d-D.timedelta(days=30)<=dt(h['date'])<d and h['sha']!=v['pack']: prior|={tuple(x) for x in h['funcs']}
    for x in v['funcs']:
        if x[1] in PSEUDO: continue
        b+=1; a+= tuple(x) in prior
print('function-touches previously edited ≤30d:',a,'/',b,f'{a/b:.0%}')
