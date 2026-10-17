import json,subprocess as S,re,collections as C,itertools as I,sys,datetime as D
SP=sys.argv[1]
G=['git','-c','core.attributesFile='+SP+'/attrs','-c',r'diff.jsfn.xfuncname=^[ \t]*((async[ \t]+)?function\*?[ \t]+[^ (]+.*|(const|let|var)[ \t]+[^ =]+[ \t]*=[ \t]*(async[ \t]*)?(function|\([^)]*\)[ \t]*=>|[A-Za-z_$]+[ \t]*=>).*)$','-c','core.quotepath=off']
def run(a): return S.run(G+a,capture_output=True,text=True).stdout
units=json.load(open(SP+'/units.json'))
packdate={}; packsha={}
for u in units:
    for c in (u['comps'] or [u['pr']]): packdate[c]=u['date']; packsha[c]=u['sha']
prs=[int(x) for x in open(SP+'/prlist.txt').read().split()]
CODE=re.compile(r'^(джерела/[^/]+\.(py|js|html)|джерела/(прилади|аудит)/[^/]+\.py|zhnyvarka/[^/]+\.(py|js)|аудит/проби/рв6_стенд\.js)$')
def funcs(diff):
    out=set(); cur=None
    for l in diff.splitlines():
        if l.startswith('+++ '): cur=l[6:] if l.startswith('+++ b/') else None
        elif l.startswith('@@') and cur and CODE.match(cur):
            h=l.split('@@',2)[2].strip()
            m=re.search(r'(?:def|class|function\*?)\s+([^\s(:]+)',h) or re.search(r'(?:const|let|var)\s+([^\s=]+)',h)
            if m: out.add((cur,m.group(1)))
    return out
info={}
for p in prs:
    v0=dict(pack=packsha[p]); head,base,_,_=open(f'{SP}/prf/{p}.sha').read().split('\t')
    mb=run(['merge-base',head,v0['pack']+'^1']).strip()
    files=[f for f in open(f'{SP}/prf/{p}.files').read().split('\n') if f]
    d=run(['diff','-U0','--no-color',mb,head,'--']+[f for f in files if CODE.match(f)]) if any(CODE.match(f) for f in files) else ''
    title=open(f'{SP}/prf/{p}.meta').read().split('\t')[0]
    info[p]=dict(files=files,funcs=sorted(funcs(d)),date=packdate[p],title=title,pack=packsha[p])
json.dump(info,open(SP+'/prinfo.json','w'),ensure_ascii=False)
# history of main first-parent since 2026-09-10: funcs per commit
log=run(['log','--first-parent','--since=2026-09-10','--format=%H|%aI|%s','origin/main']).splitlines()
hist=[]
for l in log:
    h,d,s=l.split('|',2)
    if s.startswith('збірка:'): continue
    par=run(['rev-parse',h+'^1']).strip()
    hist.append(dict(sha=h,date=d,subj=s,funcs=funcs(run(['diff','-U0','--no-color',par,h,'--','джерела','zhnyvarka','аудит/проби/рв6_стенд.js']))))
json.dump([dict(x,funcs=sorted(x['funcs'])) for x in hist],open(SP+'/hist.json','w'),ensure_ascii=False)
print('hist commits',len(hist))
