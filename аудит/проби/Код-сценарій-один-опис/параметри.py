import ast, pathlib, sys
root = pathlib.Path(sys.argv[1] if len(sys.argv)>1 else '.')
res=[]
for p in sorted(root.rglob('*.py')):
    if 'node_modules' in p.parts: continue
    try: t=ast.parse(p.read_text(encoding='utf-8'))
    except Exception: continue
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            a=n.args
            k=len(a.posonlyargs)+len(a.args)+len(a.kwonlyargs)+(1 if a.vararg else 0)+(1 if a.kwarg else 0)
            if a.args and a.args[0].arg in ('self','cls'): k-=1
            if k>=10: res.append((k,str(p),n.name,n.lineno))
for r in sorted(res,reverse=True): print(*r)
print(len(res), len({r[1] for r in res}))
