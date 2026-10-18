"""Знаходить у *.py джерел (без проб/аудиту) усі літерали-переліки (tuple/list/set/frozenset, ключі dict),
що містять >= N рядків зі словника поняття, і порівнює множиною з еталоном.
Запуск: cd wt/джерела && python3 p_literals.py"""
import ast, glob, sys, json, collections as K
sys.path.insert(0, ".")
import внутрішня_мова as ВМ
SLOT = set(ВМ.ТАБЛИЦЯ["slot"].values())
ZONE = set(ВМ.ТАБЛИЦЯ["goal_zone"].values()) | set(ВМ.ТАБЛИЦЯ["zone"].values()) | {"коліна","високе_стегно","талія","шия","обличчя"}
OCC = set(ВМ.ТАБЛИЦЯ["occasion"].values())
PREC = {"ні","немає","нема","можливий_дощ","дощ","мокрий_сніг","злива","сніг","так"}
CONC = dict(slot=(SLOT,4), zone=(ZONE,4), occasion=(OCC,3), precip=(PREC,3))
def strs(node):
    if isinstance(node,(ast.Tuple,ast.List,ast.Set)): els=node.elts
    elif isinstance(node,ast.Dict): els=[k for k in node.keys if k is not None]
    elif isinstance(node,ast.Call) and getattr(node.func,"id","") in ("frozenset","set","tuple") and node.args: return strs(node.args[0])
    elif isinstance(node,ast.Call) and getattr(node.func,"id","")=="dict": return [k.arg for k in node.keywords if k.arg]
    else: return None
    return [e.value for e in els if isinstance(e,ast.Constant) and isinstance(e.value,str)]
out = K.defaultdict(list)
for f in sorted(glob.glob("*.py")):
    try: tree = ast.parse(open(f,encoding="utf-8").read())
    except Exception as e: continue
    for node in ast.walk(tree):
        s = strs(node)
        if not s: continue
        ss=set(s)
        for c,(voc,n) in CONC.items():
            hit = ss & voc
            if len(hit) >= n and len(hit) >= 0.6*len(ss):
                out[c].append((f, node.lineno, frozenset(ss)))
res={}
for c,items in out.items():
    voc=CONC[c][0]
    # дедуп вкладених вузлів (dict(...) + tuple)
    uniq=K.OrderedDict()
    for f,l,ss in items: uniq.setdefault((f,ss),l)
    distinct=K.Counter(ss for (f,ss) in uniq)
    print("== %s: літералів %d, різних множин %d, файлів %d" % (c, len(uniq), len(distinct), len({f for f,_ in uniq})))
    res[c]=[dict(f=f,l=l,n=len(ss),items=sorted(ss)) for (f,ss),l in uniq.items()]
    for (f,ss),l in sorted(uniq.items(), key=lambda x:-len(x[0][1]))[:60]:
        print("   %s:%d n=%d  -еталон=%s  +поза=%s" % (f,l,len(ss), len(voc-ss) if c!="zone" else "", sorted(ss-voc)[:6]))
json.dump(res, open(sys.argv[1],"w"), ensure_ascii=False, indent=0)
