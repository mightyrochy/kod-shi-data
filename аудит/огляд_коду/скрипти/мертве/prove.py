import ast,collections,os,sys,glob
SP='/tmp/claude-0/-home-user-kod-shi-data/66b2c79f-d82f-57ad-bcfa-0413f82df806/scratchpad/V'
W2=SP+'/wt2/'
rows=[l.rstrip('\n').split('\t') for l in open(SP+'/мертві.tsv')][1:]
dead=collections.defaultdict(list); names=set()
for r in rows:
    if r[1]=='ядро' and r[6]=='МЕРТВА': dead[r[0]].append((int(r[4]),r[3])); names.add(r[3])
kill_total=0; reexp=set()
# 1. strip imports of dead names in all джерела/*.py
for p in glob.glob(W2+'джерела/**/*.py',recursive=True):
    src=open(p,encoding='utf-8').read()
    try: t=ast.parse(src)
    except: continue
    lines=src.split('\n'); edits=[]
    for n in ast.walk(t):
        if isinstance(n,ast.ImportFrom) and n.module and n.level==0 and any(a.name in names for a in n.names):
            mod=n.module
            # only strip when the name is imported from a module that defines it as dead
            keep=[a for a in n.names if not (a.name in names and any(f.endswith('/'+mod+'.py') and any(nm==a.name for _,nm in v) for f,v in dead.items()))]
            if len(keep)!=len(n.names):
                for a in n.names:
                    if a not in keep: reexp.add(a.name)
                edits.append((n.lineno,n.end_lineno,keep,n))
    for lo,hi,keep,n in sorted(edits,reverse=True):
        ind=re_ind=lines[lo-1][:len(lines[lo-1])-len(lines[lo-1].lstrip())]
        if keep:
            n2=ast.ImportFrom(module=n.module,names=keep,level=0)
            new=[ind+ast.unparse(n2)]
        else: new=[ind+'pass']
        lines[lo-1:hi]=new
    if edits: open(p,'w',encoding='utf-8').write('\n'.join(lines))
print('імен, що реекспортувались і були прибрані з import:',len(reexp),sorted(reexp)[:40])
# 2. delete definitions
for f,v in dead.items():
    p=SP+'/wt2/'+f
    src=open(p,encoding='utf-8').read(); t=ast.parse(src); lines=src.split('\n'); starts={s for s,_ in v}
    kill=set()
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.Assign,ast.AnnAssign)):
            lo=min([n.lineno]+[d.lineno for d in getattr(n,'decorator_list',[])])
            if lo in starts: kill.update(range(lo,n.end_lineno+1))
    kill_total+=len(kill)
    open(p,'w',encoding='utf-8').write('\n'.join(l for i,l in enumerate(lines,1) if i not in kill))
print('видалено рядків визначень',kill_total)
