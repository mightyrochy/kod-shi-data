import sys, ast, os
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import status
Д="/home/user/kod-shi-data/джерела"
М=set(status.МОДУЛІ_ПРОДУКТУ)
верх={m:set() for m in М}; усі={m:set() for m in М}; рядки={}
def головний(n):
    t=n.test
    return isinstance(t,ast.Compare) and isinstance(t.left,ast.Name) and t.left.id=="__name__"
for m in М:
    src=open(f"{Д}/{m}.py",encoding="utf-8").read(); рядки[m]=src.count("\n")+1
    дерево=ast.parse(src)
    def цілі(n):
        if isinstance(n,ast.Import): return [a.name.split(".")[0] for a in n.names]
        if isinstance(n,ast.ImportFrom) and n.level==0 and n.module: return [n.module.split(".")[0]]
        return []
    def обхід(n, глиб, у_main):
        for д in ast.iter_child_nodes(n):
            if isinstance(д,ast.If) and глиб==0 and головний(д): у_main2=True
            else: у_main2=у_main
            for ц in цілі(д):
                if ц in М and ц!=m and not у_main2:
                    усі[m].add(ц)
                    if глиб==0: верх[m].add(ц)
            новa = глиб+1 if isinstance(д,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda,ast.ClassDef)) else глиб
            обхід(д, новa, у_main2)
    обхід(дерево,0,False)
def scc(G):
    idx={};low={};st=[];on=set();res=[];i=[0]
    sys.setrecursionlimit(10000)
    def s(v):
        idx[v]=low[v]=i[0];i[0]+=1;st.append(v);on.add(v)
        for w in G[v]:
            if w not in idx: s(w);low[v]=min(low[v],low[w])
            elif w in on: low[v]=min(low[v],idx[w])
        if low[v]==idx[v]:
            c=[]
            while True:
                w=st.pop();on.discard(w);c.append(w)
                if w==v:break
            res.append(c)
    for v in G:
        if v not in idx: s(v)
    return res
for наз,G in (("верхній рівень",верх),("усі імпорти",усі)):
    к=sorted(scc(G),key=len,reverse=True)
    пар=sum(len(v) for v in G.values())
    big=к[0]; р=sum(рядки[x] for x in big)
    print(наз,"пар",пар,"найбільша СЗК",len(big),"рядків",р,f"{100*р/sum(рядки.values()):.0f}% з {sum(рядки.values())}", "інші >1:",[len(c) for c in к[1:] if len(c)>1])
