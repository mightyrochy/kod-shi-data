import ast, os, re, sys, json, warnings
warnings.simplefilter('ignore')
os.chdir(sys.argv[1]); g=json.load(open(sys.argv[2])); Я=set(g['ядро'])
пи=[]
for м in sorted(Я):
  t=ast.parse(open(м+'.py',encoding='utf-8').read())
  for n in ast.walk(t):
    if isinstance(n,(ast.Tuple,ast.List,ast.Set)):
      s=[e.value for e in n.elts if isinstance(e,ast.Constant) and isinstance(e.value,str)]
      if len(s)>=3 and len(s)==len(n.elts): пи.append((м,n.lineno,frozenset(s)))
    elif isinstance(n,ast.Dict):
      s=[k.value for k in n.keys if isinstance(k,ast.Constant) and isinstance(k.value,str)]
      if len(s)>=3: пи.append((м,n.lineno,frozenset(s)))
дж=[]
for f in ('показ.html','worker_джерело.js'):
  текст=open(f,encoding='utf-8').read()
  # прибрати коментарі /* */ і //
  чист=re.sub(r'/\*.*?\*/',lambda m: '\n'*m.group(0).count('\n'),текст,flags=re.S)
  for m in re.finditer(r'\[([^\[\]]{5,800})\]',чист):
    вміст=m.group(1)
    s=re.findall(r'[\'"]([^\'"\n]{1,40})[\'"]',вміст)
    if len(s)>=3 and not re.sub(r'[\'"][^\'"\n]{1,40}[\'"]|[\s,]','',вміст):
      дж.append((f,чист.count('\n',0,m.start())+1,frozenset(s)))
  for m in re.finditer(r'\{([^{}]{10,800})\}',чист):
    s=re.findall(r'(?:^|[,{])\s*[\'"]?([\w\u0400-\u04FF]+)[\'"]?\s*:(?!:)',m.group(1))
    if len(s)>=3 and any(re.search('[\u0400-\u04FF]',x) for x in s): дж.append((f,чист.count('\n',0,m.start())+1,frozenset(s)))
print('JS-переліків',len(дж),'Python-переліків',len(пи))
пари=[]
for jf,jl,js in дж:
  if not any(re.search('[Ѐ-ӿ]',x) for x in js): continue
  best=None
  for м,л,ps in пи:
    i=len(js&ps)
    if i>=3 and (i/len(js)>=0.75):
      j=i/len(js|ps)
      if not best or j>best[0]: best=(j,м,л,i,len(ps))
  if best: пари.append((jf,jl,len(js),best,sorted(js)[:8]))
пари.sort(key=lambda x:-x[3][0])
seen=set()
for p in пари:
  key=(p[3][1],p[3][2])
  print(f"{p[0]}:{p[1]} ({p[2]} ел.) ≈ {p[3][1]}.py:{p[3][2]} ({p[3][4]} ел., спільних {p[3][3]}, Жаккар {p[3][0]:.2f}) {p[4]}")
print('усього пар',len(пари))
