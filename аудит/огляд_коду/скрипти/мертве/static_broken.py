import ast,os,sys,glob,json,collections,builtins
W=sys.argv[1]; J=W+'/джерела'
mods={}
def ns(path):
    t=ast.parse(open(path,encoding='utf-8').read()); names=set(); star=False; dyn=False
    for n in ast.walk(t):
        pass
    def top(body):
        nonlocal star
        for n in body:
            if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): names.add(n.name)
            elif isinstance(n,(ast.Assign,ast.AnnAssign,ast.AugAssign,ast.For,ast.With)):
                for x in ast.walk(n):
                    if isinstance(x,ast.Name) and isinstance(x.ctx,ast.Store): names.add(x.id)
            if isinstance(n,(ast.Import,ast.ImportFrom)):
                for a in n.names:
                    if a.name=='*': star=True
                    names.add((a.asname or a.name).split('.')[0])
            for f in ('body','orelse','finalbody'):
                if isinstance(n,(ast.If,ast.Try,ast.With,ast.For,ast.While)): top(getattr(n,f,[]))
            if isinstance(n,ast.Try):
                for h in n.handlers: top(h.body)
    top(t.body)
    # globals()[...] = / setattr(sys.modules) => dynamic
    src=open(path,encoding='utf-8').read()
    dyn = star or 'globals()[' in src or 'setattr(' in src and 'modules' in src
    return names,dyn
for f in os.listdir(J):
    if f.endswith('.py'):
        try: mods[f[:-3]]=ns(J+'/'+f)
        except Exception as e: pass
res={}
for f in sorted(glob.glob(J+'/проби/*.py')):
    b=os.path.basename(f)
    try: t=ast.parse(open(f,encoding='utf-8').read())
    except SyntaxError as e: res[b]=['SyntaxError']; continue
    issues=[]; alias={}
    for n in ast.walk(t):
        if isinstance(n,ast.Import):
            for a in n.names:
                m=a.name.split('.')[0]
                if m in mods: alias[(a.asname or a.name).split('.')[0]]=m
        elif isinstance(n,ast.ImportFrom) and n.module and n.level==0:
            m=n.module.split('.')[0]
            if m in mods and '.' not in n.module:
                for a in n.names:
                    if a.name!='*' and a.name not in mods[m][0] and not mods[m][1]: issues.append('ImportError:%s.%s'%(m,a.name))
            elif m=='лабораторія' or m in('прилади','аудит'): pass
    for n in ast.walk(t):
        if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name) and n.value.id in alias:
            m=alias[n.value.id]
            if n.attr not in mods[m][0] and not mods[m][1] and not n.attr.startswith('__'): issues.append('AttributeError:%s.%s'%(m,n.attr))
    if issues: res[b]=sorted(set(issues))
json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False,indent=0)
print(len(res),'проб зі статично зламаними посиланнями на модулі джерел')
c=collections.Counter(i.split(':')[0] for v in res.values() for i in v); print(c)
