import ast, os, re, sys, tokenize, io, collections, json
ROOT=sys.argv[1]; SP=sys.argv[2]
J=os.path.join(ROOT,'джерела')
sys.path.insert(0,J)
import склад
core=set(склад.модулі_системи(J))
# files
pyfiles=[]
for dp,dn,fn in os.walk(J):
    dn[:]=[d for d in dn if d not in('node_modules','__pycache__')]
    for f in fn:
        if f.endswith('.py'): pyfiles.append(os.path.join(dp,f))
for dp,dn,fn in os.walk(os.path.join(ROOT,'аудит','проби')):
    for f in fn:
        if f.endswith('.py'): pyfiles.append(os.path.join(dp,f))
other=[]
for dp,dn,fn in os.walk(ROOT):
    dn[:]=[d for d in dn if d not in('node_modules','__pycache__','.git')]
    for f in fn:
        if f.endswith(('.js','.html','.yml','.ps1')) or f=='README.md': other.append(os.path.join(dp,f))
rel=lambda p: os.path.relpath(p,ROOT)
def group(p):
    r=rel(p)
    if r.startswith('джерела/проби/') or r.startswith('аудит/проби/'): return 'проби'
    if r.startswith('джерела/лабораторія/'): return 'лабораторія'
    if r.startswith('джерела/прилади/'): return 'прилади'
    if r.startswith('джерела/аудит/'): return 'аудит'
    if r.startswith('джерела/') and r.count('/')==1:
        return 'ядро' if os.path.basename(p)[:-3] in core else 'кореневі'
    return 'інше'
def comment_strip_js(t):
    t=re.sub(r'/\*.*?\*/','',t,flags=re.S)
    t=re.sub(r'(^|\s)//[^\n]*','\\1',t)
    return t
ID=re.compile(r'\w+',re.U)
# parse py
F={}  # path -> dict
for p in pyfiles:
    try: src=open(p,encoding='utf-8').read(); tree=ast.parse(src)
    except Exception as e: print('PARSEFAIL',rel(p),e,file=sys.stderr); continue
    doclines=set(); implines=set(); imports=set(); alias={}
    for n in ast.walk(tree):
        if isinstance(n,ast.Expr) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str):
            doclines.update(range(n.lineno,n.end_lineno+1))
        if isinstance(n,(ast.Import,ast.ImportFrom)):
            implines.update(range(n.lineno,n.end_lineno+1))
            if isinstance(n,ast.Import):
                for a in n.names: imports.add(a.name.split('.')[0])
            else:
                if n.module: imports.add(n.module.split('.')[0])
                for a in n.names:
                    imports.add(a.name)
                    if a.asname and a.asname!=a.name: alias[a.asname]=a.name
    toks=[]  # (name,line)
    try:
        for t in tokenize.generate_tokens(io.StringIO(src).readline):
            if t.type==tokenize.NAME and t.start[0] not in implines: toks.append((t.string,t.start[0]))
            elif t.type==tokenize.STRING and t.start[0] not in doclines:
                s=t.string.strip('rbfuRBFU').strip('\'"')
                if len(s)<80 and re.fullmatch(r'[\w.]+',s,re.U):
                    for w in s.split('.'): 
                        if w: toks.append((w,t.start[0]))
                if re.search(r'__import__|import_module',t.string): pass
    except Exception as e: print('TOKFAIL',rel(p),e,file=sys.stderr)
    # string mentions for import_module / __import__("x") captured as string tokens above
    # top-level owners
    owners=[]  # (name(s),lo,hi,kind)
    defs={}
    def visit(body):
        for n in body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                lo=min([n.lineno]+[d.lineno for d in n.decorator_list])
                owners.append(((n.name,),lo,n.end_lineno,'class' if isinstance(n,ast.ClassDef) else 'def'))
            elif isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                tg=n.targets if isinstance(n,ast.Assign) else [n.target]
                names=[]
                for t0 in tg:
                    for x in ast.walk(t0):
                        if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Store): names.append(x.id)
                if isinstance(n,ast.AugAssign): continue
                if names: owners.append((tuple(names),n.lineno,n.end_lineno,'const'))
            elif isinstance(n,(ast.If,ast.Try,ast.With,ast.For,ast.While)):
                # defs inside conditionals
                subs=[n.body,getattr(n,'orelse',[]),getattr(n,'finalbody',[])]+[h.body for h in getattr(n,'handlers',[])]
                isMain= isinstance(n,ast.If) and '__main__' in ast.dump(n.test)
                if not isMain:
                    for s in subs: visit(s)
    visit(tree.body)
    toks=[(alias.get(w,w),l) for w,l in toks]
    F[p]=dict(src=src,toks=toks,owners=owners,imports=imports,group=group(p),mod=os.path.basename(p)[:-3],lines=src.count('\n')+1)
# symbol table
SYM={}  # (path,name)->dict
bymod=collections.defaultdict(list)
for p,d in F.items():
    for names,lo,hi,kind in d['owners']:
        for nm in names:
            if nm.startswith('__') and nm.endswith('__'): continue
            k=(p,nm)
            if k in SYM: SYM[k]['hi']=max(SYM[k]['hi'],hi); SYM[k]['ranges'].append((lo,hi)); continue
            SYM[k]=dict(path=p,name=nm,lo=lo,hi=hi,kind=kind,ranges=[(lo,hi)],owner=names)
byname=collections.defaultdict(list)
for (p,nm),s in SYM.items(): byname[nm].append(s)
# mentions of module stems
modpath={}
for p in F:
    if group(p) in('ядро','кореневі','лабораторія','прилади','аудит') : modpath.setdefault(F[p]['mod'],[]).append(p)
def ownerof(p,line):
    d=F[p]; best=None
    for names,lo,hi,kind in d['owners']:
        if lo<=line<=hi:
            if best is None or (hi-lo)<(best[2]-best[1]): best=(names,lo,hi,kind)
    return best
# edges: (srcnode, dst symbol key); srcnode = ('ROOT',group,path) or (path,ownername)
edges=collections.defaultdict(set)  # dst key -> set of (src descriptor)
refcnt=collections.Counter()
extrefs=collections.defaultdict(lambda: collections.Counter()) # key -> group counts
selfrefs=collections.Counter()
srcs=collections.defaultdict(set)
def addref(dst,srcnode,g,selff):
    srcs[dst].add(srcnode)
    if selff: selfrefs[dst]+=1
    else: extrefs[dst][g]+=1
IMP=collections.defaultdict(set)
for p,d in F.items():
    for i in d['imports']: IMP[i].add(d['mod'])
REACH={}
for m in set(d['mod'] for d in F.values()):
    r={m}|IMP[m]
    for x in list(r): r|=IMP[x]
    REACH[m]=r
for p,d in F.items():
    stemset=set(d['imports'])|{w for w,_ in d['toks']}
    for nm,line in d['toks']:
        cands=byname.get(nm)
        if not cands: continue
        ow=ownerof(p,line)
        # is this the def token itself?
        for s in cands:
            same = s['path']==p
            if same:
                # def site tokens: skip tokens on the owner's first line equal to its name when owner is s
                if ow and nm in ow[0] and ow[1]==line and (ow[3] in('def','class') or True):
                    # def/store site (first line of its own definition)
                    # but allow use on same line RHS? ignore
                    if ow[3] in('def','class'): continue
                    if ow[3]=='const': 
                        continue
            else:
                m=F[s['path']]['mod']
                if len(byname[nm])>1 and not (REACH[m]&stemset): continue
            if ow is None: node=('ROOT',p)
            else:
                node=(p,ow[0][0]) if ow[3]!='const' or True else None
            if ow is not None and same and nm in ow[0]: 
                continue  # self-recursion / self-assign
            addref((s['path'],nm),node,d['group'],same)
for p in other:
    t=open(p,encoding='utf-8',errors='replace').read()
    if p.endswith(('.js','.html')): t=comment_strip_js(t)
    g='js-прод' if os.path.basename(p) in('показ.html','worker.js','показ_шаблон.js','worker_джерело.js') else ('yml' if p.endswith('.yml') else 'js/інше')
    words=collections.Counter(ID.findall(t))
    for w in words:
        for s in byname.get(w,[]):
            addref((s['path'],w),('ROOT',p),g,False)
# liveness
def live(rootfilter):
    L=set(); changed=True
    def isroot(n): return n[0]=='ROOT' and rootfilter(n[1])
    # initial
    for k in SYM:
        if any(isroot(n) for n in srcs[k]): L.add(k)
    while changed:
        changed=False
        for k in SYM:
            if k in L: continue
            for n in srcs[k]:
                if n[0]!='ROOT' and (n[0],n[1]) in L:
                    L.add(k); changed=True; break
    return L
prodjs=lambda p: os.path.basename(p) in('показ.html','worker.js','показ_шаблон.js')
def rf_prod(p):
    if prodjs(p): return True
    return p in F and F[p]['group']=='ядро'
def rf_all(p): return True
L1=live(rf_prod); L2=live(rf_all)
# ROOT for py file = module-level code outside any owner; but module-level code of non-core in all.
# note: ROOT edges from core module-level code: included via rf_prod.
rows=[]
for k,s in sorted(SYM.items(),key=lambda x:(rel(x[0][0]),x[1]['lo'])):
    g=F[k[0]]['group']
    lines=sum(h-l+1 for l,h in s['ranges'])
    st='жива'
    if g=='ядро':
        if k in L1: st='жива_в_продукті'
        elif k in L2: st='лише_прилади_проби'
        else: st='МЕРТВА'
    else:
        st='жива' if k in L2 else 'МЕРТВА'
    ec=dict(extrefs[k]); 
    rows.append((rel(k[0]),g,s['kind'],s['name'],s['lo'],lines,st,selfrefs[k],json.dumps(ec,ensure_ascii=False)))
with open(os.path.join(SP,'мертві_повні.tsv'),'w') as f:
    f.write('файл\tгрупа\tвид\tім\'я\tрядок\tрядків\tстатус\tсамопосилань\tзовнішні_за_групами\n')
    for r in rows: f.write('\t'.join(map(str,r))+'\n')
with open(os.path.join(SP,'мертві.tsv'),'w') as f:
    f.write('файл\tгрупа\tвид\tім\'я\tрядок\tрядків\tстатус\tсамопосилань\tзовнішні_за_групами\n')
    for r in rows:
        if r[6] in('МЕРТВА','лише_прилади_проби'): f.write('\t'.join(map(str,r))+'\n')
agg=collections.defaultdict(lambda:[0,0,0,0])
for r in rows:
    a=agg[(r[1],r[6])]; a[0]+=1; a[1]+=r[5]
for (g,st),a in sorted(agg.items()): print(g,st,a[0],'символів',a[1],'рядків')
tot=collections.defaultdict(lambda:[0,0,0])
for p,d in F.items(): tot[d['group']][0]+=1; tot[d['group']][1]+=d['lines']
for g,a in tot.items(): print('ГРУПА',g,'файлів',a[0],'рядків',a[1])
# modules: mentions
print('--- модулі без жодного імпорту/згадки')
allp={p:d for p,d in F.items()}
texts={}
for p in list(F)+other:
    texts[p]=open(p,encoding='utf-8',errors='replace').read()
out=[]
for p,d in F.items():
    g=d['group']
    if g in('проби',):continue
    m=d['mod']
    if m=='__init__': continue
    pat=re.compile(r'(?<![\w])'+re.escape(m)+r'(?![\w])',re.U)
    hits=collections.Counter()
    for q,t in texts.items():
        if q==p: continue
        gq=F[q]['group'] if q in F else ('yml' if q.endswith('.yml') else 'js/html/README')
        if pat.search(t if not q.endswith(('.js','.html')) else comment_strip_js(t)): hits[gq]+=1
    imported_by=[rel(q) for q in F if q!=p and m in F[q]['imports']]
    out.append((rel(p),g,d['lines'],len(imported_by),dict(hits)))
with open(os.path.join(SP,'модулі.tsv'),'w') as f:
    f.write('файл\tгрупа\tрядків\tімпортує_файлів\tзгадки_за_групами\n')
    for o in out: f.write('\t'.join(map(str,[o[0],o[1],o[2],o[3],json.dumps(o[4],ensure_ascii=False)]))+'\n')
nz=[o for o in out if o[3]==0 and not o[4]]
print('модулів без імпорту і без згадок:',len(nz),sum(o[2] for o in nz))
for o in nz: print(o[0],o[1],o[2])
