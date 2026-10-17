import ast,os,re,sys,tokenize,io,json,warnings
warnings.filterwarnings("ignore")
from radon.complexity import cc_visit
R="/home/user/kod-shi-data/"
SP=os.environ["SP"]
ядро=set(open(SP+"/ядро.txt").read().split())
HIST=re.compile(r"(рядк\w*\s*#?\d{2,}|#\d{3,}|\bПР\s*#?\d+|\bН-[\w-]+|\b\d{1,2}\.\d{2}(\.\d{4})?\b|раніше|до правки|було:|тепер\b|більше нема|СПІЙМАНО|ЧОМУ ЦЕ ЗʼЯВИЛОСЬ|Н-V?\d)",re.I)
HIST2=re.compile(r"(рядк\w*\s*#?\d{2,}|#\d{3,}|\bН-[\w-]+|\b\d{1,2}\.\d{2}\.20\d\d\b|\b\d{1,2}\.\d{2}\b|раніше|до правки)",re.I)
def глиб(n,d=0):
    m=d
    for ch in ast.iter_child_nodes(n):
        if isinstance(ch,(ast.If,ast.For,ast.While,ast.Try,ast.With,ast.AsyncFor,ast.AsyncWith,getattr(ast,'TryStar',ast.Try),ast.Match if hasattr(ast,'Match') else ast.If)):
            m=max(m,глиб(ch,d+1))
        else: m=max(m,глиб(ch,d))
    return m
def аналіз(p):
    s=open(p,encoding="utf-8",errors="replace").read()
    lines=s.split("\n"); tot=len(lines)
    r=dict(рядків=tot,порожніх=sum(1 for l in lines if not l.strip()))
    try:
        t=ast.parse(s)
    except Exception as e:
        return None
    # docstring lines
    doc=set()
    for n in ast.walk(t):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant) and isinstance(n.body[0].value.value,str):
            e=n.body[0]; doc|=set(range(e.lineno,e.end_lineno+1))
    com=set(); hist=0; comtext=[]
    try:
        for tk in tokenize.generate_tokens(io.StringIO(s).readline):
            if tk.type==tokenize.COMMENT:
                com.add(tk.start[0]); 
                if HIST2.search(tk.string): hist+=1
    except Exception: pass
    # only whole-line comments
    сам=sum(1 for i in com if lines[i-1].strip().startswith("#"))
    dh=0
    for i in doc:
        if HIST2.search(lines[i-1]): dh+=1
    r.update(коментарі=сам,докстрінги=len(doc),код=tot-r["порожніх"]-сам-len(doc),іст_коментарів=hist,іст_рядків_докстрінгів=dh)
    # functions
    fs=[]
    try: cc={(b.lineno,b.name):b.complexity for b in cc_visit(s)}
    except Exception: cc={}
    # radon includes methods separately in cc_visit? flatten
    def rad():
        d={}
        for b in cc_visit(s):
            d[(b.lineno,b.name)]=b.complexity
            for m in getattr(b,'methods',[]): d[(m.lineno,m.name)]=m.complexity
            for m in getattr(b,'closures',[]): d[(m.lineno,m.name)]=m.complexity
        return d
    try: cc=rad()
    except Exception: pass
    for n in ast.walk(t):
        if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)):
            L=n.end_lineno-n.lineno+1
            fs.append((n.name,n.lineno,L,cc.get((n.lineno,n.name),0),глиб(n)))
    r["функцій"]=len(fs)
    r["найдовша"]=max(fs,key=lambda f:f[2]) if fs else ("",0,0,0,0)
    cs=[f[3] for f in fs if f[3]]
    r["сер_cc"]=round(sum(cs)/len(cs),2) if cs else 0
    r["макс_cc"]=max(cs) if cs else 0
    r["сума_cc"]=sum(cs)
    r["глиб"]=глиб(t)
    # keys
    k=0
    for n in ast.walk(t):
        if isinstance(n,ast.Dict): k+=sum(1 for x in n.keys if isinstance(x,ast.Constant) and isinstance(x.value,str))
        elif isinstance(n,ast.Subscript) and isinstance(n.slice,ast.Constant) and isinstance(n.slice.value,str): k+=1
        elif isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args and isinstance(n.args[0],ast.Constant) and isinstance(n.args[0].value,str): k+=1
    r["ключів"]=k
    ex=bare=0
    for n in ast.walk(t):
        if isinstance(n,ast.ExceptHandler):
            if n.type is None: bare+=1
            elif (isinstance(n.type,ast.Name) and n.type.id in("Exception","BaseException")) : ex+=1
            elif isinstance(n.type,ast.Tuple) and any(isinstance(e,ast.Name) and e.id=="Exception" for e in n.type.elts): ex+=1
    r["except_Exception"]=ex; r["bare"]=bare
    r["_fs"]=fs
    return r
групи={}
def група(rel):
    if rel.startswith("джерела/проби/"): return "джерела/проби"
    if rel.startswith("джерела/прилади/"): return "джерела/прилади"
    if rel.startswith("джерела/лабораторія/"): return "джерела/лабораторія"
    if rel.startswith("джерела/аудит/"): return "джерела/аудит"
    if rel.startswith("джерела/"):
        b=os.path.basename(rel)[:-3]
        if b in ядро: return "ядро"
        if re.match(r"(тест|стенд_знімок|pair_test)",b): return "тести/стенд (верх)"
        return "джерела/інше верх"
    if rel.startswith("аудит/проби/"): return "аудит/проби"
    if rel.startswith("open-source-stylist"): return "open-source-stylist"
    if rel.startswith("zhnyvarka"): return "zhnyvarka"
    return "аудит/інше"
рядки=[];функції=[]
for root,ds,fs in os.walk(R):
    ds[:]=[d for d in ds if d not in(".git","node_modules","__pycache__")]
    for f in fs:
        if f.endswith(".py"):
            p=os.path.join(root,f); rel=os.path.relpath(p,R)
            a=аналіз(p)
            if a is None: print("ПАРС-ПОМИЛКА",rel); continue
            a["файл"]=rel; a["група"]=група(rel)
            рядки.append(a)
            for (n,l,L,c,g) in a["_fs"]: функції.append((n,rel,l,L,c,g,a["група"]))
import pickle; pickle.dump((рядки,функції),open(SP+"/дані.pkl","wb"))
print(len(рядки),len(функції))
