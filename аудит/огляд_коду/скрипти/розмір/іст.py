import os,re,io,tokenize,pickle,collections
SP=os.environ["SP"]; R="/home/user/kod-shi-data/"
рядки,_=pickle.load(open(SP+"/дані.pkl","rb"))
ядро=[r for r in рядки if r["група"]=="ядро"]
pats={
 "рядок_N":re.compile(r"рядк\w*\s*#?\d{2,}",re.I),
 "PR_#N":re.compile(r"(?<![\w&])#\d{3,}|\bПР\s*#?\d+|\bPR\s*#?\d+"),
 "наряд_Н-":re.compile(r"\bН-[\w]+-\d+|\bН-V?\d+"),
 "дата_ДД.ММ":re.compile(r"(?<![\d.])(0?[1-9]|[12]\d|3[01])\.(0[89]|10)(\.2026)?(?!\d)"),
 "раніше/до_правки/було":re.compile(r"\b(раніше|до правки|було:|ще донедавна|колись|більше нема|тепер замість)\b",re.I),
}
tot=collections.Counter(); per=[]
for r in ядро:
    s=open(R+r["файл"],encoding="utf-8").read(); L=s.split("\n")
    # comment+docstring text lines
    import ast
    t=ast.parse(s,); doc=set()
    for n in ast.walk(t):
        if isinstance(n,(ast.Module,ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)) and n.body and isinstance(n.body[0],ast.Expr) and isinstance(getattr(n.body[0],'value',None),ast.Constant) and isinstance(n.body[0].value.value,str):
            doc|=set(range(n.body[0].lineno,n.body[0].end_lineno+1))
    cm=set()
    for tk in tokenize.generate_tokens(io.StringIO(s).readline):
        if tk.type==tokenize.COMMENT: cm.add(tk.start[0])
    text=[i for i in sorted(cm|doc)]
    c=collections.Counter(); anyl=0
    for i in text:
        l=L[i-1]; hit=False
        for k,p in pats.items():
            if p.search(l): c[k]+=1; hit=True
        anyl+=hit
    per.append((r["файл"],r["коментарі"]+r["докстрінги"],anyl,c))
    tot.update(c); tot["_рядків_з_історією"]+=anyl; tot["_ком+док"]+=r["коментарі"]+r["докстрінги"]
print(dict(tot))
print("ядро рядків",sum(r["рядків"] for r in ядро),"код",sum(r["код"] for r in ядро),"ком",sum(r["коментарі"] for r in ядро),"док",sum(r["докстрінги"] for r in ядро))
print("частка ком+док/рядків %.1f%%; ком/рядків %.1f%%; код/рядків %.1f%%"%(100*(sum(r["коментарі"]+r["докстрінги"] for r in ядро))/sum(r["рядків"] for r in ядро),100*sum(r["коментарі"] for r in ядро)/sum(r["рядків"] for r in ядро),100*sum(r["код"] for r in ядро)/sum(r["рядків"] for r in ядро)))
print("топ10 за кількістю рядків з історією:")
for f,n,a,c in sorted(per,key=lambda x:-x[2])[:10]: print(f,"ком+док",n,"іст.рядків",a,"%.0f%%"%(100*a/max(n,1)),dict(c))
print("топ за часткою (ком+док>=200):")
for f,n,a,c in sorted([p for p in per if p[1]>=200],key=lambda x:-x[2]/x[1])[:5]: print(f,n,a,"%.0f%%"%(100*a/n))
