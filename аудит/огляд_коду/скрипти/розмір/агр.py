import pickle,os,collections
SP=os.environ["SP"]
рядки,функції=pickle.load(open(SP+"/дані.pkl","rb"))
G=collections.OrderedDict()
for r in рядки: G.setdefault(r["група"],[]).append(r)
out=[]
def S(rs,k): return sum(r[k] for r in rs)
print("група\tфайлів\tрядків\tкод\tком\tдок\tфункцій\tсума_cc\tсер_cc\tmax_cc\t>1500\texcept_Exc\tbare\tключів")
for g,rs in sorted(G.items(),key=lambda x:-S(x[1],"рядків")):
    fn=S(rs,"функцій"); 
    print(g,len(rs),S(rs,"рядків"),S(rs,"код"),S(rs,"коментарі"),S(rs,"докстрінги"),fn,S(rs,"сума_cc"),round(S(rs,"сума_cc")/max(fn,1),2),max(r["макс_cc"] for r in rs),sum(1 for r in rs if r["рядків"]>1500),S(rs,"except_Exception"),S(rs,"bare"),S(rs,"ключів"),sep="\t")
# tsv modules
with open(SP+"/модулі.tsv","w") as f:
    f.write("файл\tгрупа\tрядків\tкод\tкоментарі\tдокстрінги\tфункцій\tнайдовша(ім'я:рядок:довж)\tсер_cc\tмакс_cc\tсума_cc\tмакс_вкладеність\tключів_str\texcept_Exception\tbare_except\tіст_коментарів\n")
    for r in sorted(рядки,key=lambda r:-r["рядків"]):
        n=r["найдовша"]
        f.write("\t".join(map(str,[r["файл"],r["група"],r["рядків"],r["код"],r["коментарі"],r["докстрінги"],r["функцій"],"%s:%s:%s"%(n[0],n[1],n[2]),r["сер_cc"],r["макс_cc"],r["сума_cc"],r["глиб"],r["ключів"],r["except_Exception"],r["bare"],r["іст_коментарів"]]))+"\n")
with open(SP+"/функції_топ.tsv","w") as f:
    f.write("ранг\tcc\tрядків\tвкладеність\tфункція\tфайл:рядок\tгрупа\n")
    for i,x in enumerate(sorted(функції,key=lambda x:(-x[4],-x[3]))[:150],1):
        f.write("%d\t%d\t%d\t%d\t%s\t%s:%d\t%s\n"%(i,x[4],x[3],x[5],x[0],x[1],x[2],x[6]))
def роз(fs,tag):
    print("==",tag,"функцій",len(fs),">100р",sum(1 for x in fs if x[3]>100),">200р",sum(1 for x in fs if x[3]>200),"cc>20",sum(1 for x in fs if x[4]>20),"cc>50",sum(1 for x in fs if x[4]>50),"cc>10",sum(1 for x in fs if x[4]>10),"вклад>=6",sum(1 for x in fs if x[5]>=6))
роз(функції,"усе"); роз([x for x in функції if x[6]=="ядро"],"ядро")
for g in G: 
    if g not in("ядро",): роз([x for x in функції if x[6]==g],g)
print("--модулі>1500:")
for r in sorted(рядки,key=lambda r:-r["рядків"]):
    if r["рядків"]>1500: print(r["файл"],r["рядків"],r["група"])
print("--модулі >1000 по групах:",collections.Counter(r["група"] for r in рядки if r["рядків"]>1000))
