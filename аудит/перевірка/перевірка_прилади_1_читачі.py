import ast,os,re,sys
корінь=sys.argv[1]
ТИП=re.compile(r"тип_кольору|не_вимір|точка_кольору|межі_кольору|колір_тип|явний_тип|позначено_невідомим|має_колір|вікно_кольору|провенанс_кольору|hex_кольору|lab_входу|перевірити_запис")
КЛ={"lab","hex","колір_lab","колір_hex"}
out=[]
for dp,dn,fn in os.walk(os.path.join(корінь,"джерела")):
  dn[:]=[d for d in dn if d not in("проби","прилади","node_modules","open-source-stylist","__pycache__","лабораторія","аудит")]
  for f in sorted(fn):
    if not f.endswith(".py") or f.startswith("тест_"): continue
    p=os.path.join(dp,f); src=open(p,encoding="utf-8").read()
    try:t=ast.parse(src)
    except Exception: continue
    lines=src.splitlines()
    for fnode in ast.walk(t):
      if not isinstance(fnode,(ast.FunctionDef,ast.AsyncFunctionDef)):continue
      body="\n".join(lines[fnode.lineno-1:fnode.end_lineno])
      typed=bool(ТИП.search(body))
      for n in ast.walk(fnode):
        k=None
        if isinstance(n,ast.Subscript) and isinstance(n.ctx,ast.Load) and isinstance(n.slice,ast.Constant) and n.slice.value in КЛ: k=n.slice.value
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args and isinstance(n.args[0],ast.Constant) and n.args[0].value in КЛ: k=n.args[0].value
        if k: out.append((os.path.relpath(p,корінь),n.lineno,fnode.name,k,typed))
seen=set()
for r,l,fn_,k,ty in out:
  if (r,l) in seen: continue
  seen.add((r,l)); print("ТИП" if ty else "БЕЗ",f"{r}:{l}",fn_,k)
