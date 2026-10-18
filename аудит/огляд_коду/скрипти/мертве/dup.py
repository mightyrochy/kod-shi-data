import ast,os,sys,hashlib,collections,difflib,json
ROOT=sys.argv[1]; SP=sys.argv[2]; J=ROOT+'/джерела'
files=[]
for dp,dn,fn in os.walk(J):
    dn[:]=[d for d in dn if d not in('node_modules','__pycache__','проби')]
    files+=[os.path.join(dp,f) for f in fn if f.endswith('.py')]
rel=lambda p: os.path.relpath(p,ROOT)
class Norm(ast.NodeTransformer):
    def __init__(s,strict): s.loc={}; s.strict=strict
    def nm(s,x):
        if x not in s.loc: s.loc[x]='v%d'%len(s.loc)
        return s.loc[x]
    def visit_arg(s,n): n.arg=s.nm(n.arg); n.annotation=None; return n
    def visit_Name(s,n):
        if isinstance(n.ctx,ast.Store) or n.id in s.loc: n.id=s.nm(n.id)
        return n
def strip_doc(f):
    b=f.body
    if b and isinstance(b[0],ast.Expr) and isinstance(b[0].value,ast.Constant) and isinstance(b[0].value.value,str): return b[1:]
    return b
funcs=[]
for p in files:
    try: tree=ast.parse(open(p,encoding='utf-8').read())
    except: continue
    for n in ast.walk(tree):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            lines=n.end_lineno-n.lineno+1
            body=strip_doc(n)
            if not body: continue
            import copy
            m=ast.Module(body=copy.deepcopy(body),type_ignores=[])
            nm=Norm(True)
            for a in copy.deepcopy(n.args.args+n.args.kwonlyargs+n.args.posonlyargs): nm.nm(a.arg)
            # args first
            m2=nm.visit(m)
            # strip string constants in non-structural? keep
            txt=ast.unparse(m2)
            # structural: all names stripped
            stru=ast.dump(m2,annotate_fields=False)
            import re
            stru=re.sub(r"Name\('[^']*'","Name('_'",stru); stru=re.sub(r"Attribute\((.*?), '[^']*'","Attribute(\\1, '_'",stru)
            funcs.append(dict(f=rel(p),name=n.name,line=n.lineno,lines=lines,txt=txt,h=hashlib.md5(txt.encode()).hexdigest(),hs=hashlib.md5(stru.encode()).hexdigest(),nstm=len(body)))
print('функцій всього',len(funcs))
out=open(SP+'/дублі.tsv','w')
out.write('вид\tгрупа\tрозмір_рядків\tфайл:рядок:ім\'я\n')
g=collections.defaultdict(list)
for x in funcs:
    if x['lines']>=5 and x['nstm']>=2: g[x['h']].append(x)
gi=0; ex_lines=0; exg=0
exact_keys=set()
for h,l in sorted(g.items(),key=lambda kv:-kv[1][0]['lines']*len(kv[1])):
    if len(l)<2: continue
    # dedupe identical (file,line)
    gi+=1; exact_keys.add(h)
    exg+=1; ex_lines+=sum(x['lines'] for x in l[1:])
    out.write('функція-точна\tG%d\t%d\t%s\n'%(gi,l[0]['lines'],' | '.join('%s:%d:%s'%(x['f'],x['line'],x['name']) for x in l)))
print('точні групи (після перейменування локальних, >=5 рядків,>=2 стм):',exg,'зайвих рядків',ex_lines)
# structural
gs=collections.defaultdict(list)
for x in funcs:
    if x['lines']>=8 and x['h'] not in exact_keys: gs[x['hs']].append(x)
sg=0;sl=0
for h,l in sorted(gs.items(),key=lambda kv:-kv[1][0]['lines']):
    if len(l)<2: continue
    if len({x['h'] for x in l})<2: continue
    sg+=1; sl+=sum(x['lines'] for x in l[1:])
    out.write('функція-структурна(імена атрибутів/змінних не рахуються)\tS%d\t%d\t%s\n'%(sg,l[0]['lines'],' | '.join('%s:%d:%s'%(x['f'],x['line'],x['name']) for x in l)))
print('структурні групи (>=8 рядків):',sg,'зайвих рядків',sl)
# fuzzy
big=[x for x in funcs if x['lines']>=8 and x['h'] not in exact_keys]
for x in big: x['L']=x['txt'].splitlines(); x['set']=set(x['L'])
big.sort(key=lambda x:len(x['L']))
pairs=[];seen=set()
for i,a in enumerate(big):
    for b in big[i+1:]:
        if len(b['L'])>len(a['L'])/0.88+2: break
        if a['hs']==b['hs']: continue
        if a['f']==b['f'] and a['line']==b['line']: continue
        inter=len(a['set']&b['set'])
        if inter/ max(1,len(a['set']|b['set']))<0.6: continue
        r=difflib.SequenceMatcher(None,a['L'],b['L'],autojunk=False).ratio()
        if r>=0.9: pairs.append((r,a,b))
print('нечіткі пари >=0.9:',len(pairs))
for r,a,b in sorted(pairs,key=lambda t:-t[0]):
    out.write('функція-нечітка\tF\t%d\tr=%.3f %s:%d:%s | %s:%d:%s\n'%(a['lines'],r,a['f'],a['line'],a['name'],b['f'],b['line'],b['name']))
# constants
cons=collections.defaultdict(list)
for p in files:
    try: tree=ast.parse(open(p,encoding='utf-8').read())
    except: continue
    for n in tree.body:
        if isinstance(n,(ast.Assign,ast.AnnAssign)) and n.value is not None and isinstance(n.value,(ast.Dict,ast.List,ast.Tuple,ast.Set)):
            ln=len(n.value.keys) if isinstance(n.value,ast.Dict) else len(n.value.elts)
            if ln<5: continue
            try: lit=ast.literal_eval(n.value)
            except: continue
            if isinstance(lit,(set,frozenset)): key=repr(sorted(map(repr,lit)))
            elif isinstance(lit,dict): key=repr(sorted((repr(k),repr(v)) for k,v in lit.items()))
            else: key=repr(lit)
            t=n.targets[0] if isinstance(n,ast.Assign) else n.target
            nm=t.id if isinstance(t,ast.Name) else '?'
            cons[(key)].append((rel(p),n.lineno,nm,ln,n.end_lineno-n.lineno+1))
cg=0;cl=0
for k,l in sorted(cons.items(),key=lambda kv:-kv[1][0][4]):
    if len({x[0] for x in l})<2: continue
    cg+=1; cl+=sum(x[4] for x in l[1:])
    out.write('константа\tC%d\t%d\t%s (елементів %d)\n'%(cg,l[0][4],' | '.join('%s:%d:%s'%(x[0],x[1],x[2]) for x in l),l[0][3]))
print('групи однакових констант у 2+ модулях:',cg,'зайвих рядків',cl)
