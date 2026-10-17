import sys, pickle, random
S="/tmp/claude-0/-home-user-kod-shi-data/9a5eb989-d513-548d-aefc-237879e686bd/scratchpad/"; sys.path.insert(0,S); sys.path.insert(0,"/home/user/kod-shi-data/джерела")
import foto, colorspace as cs
кат={x["id"]:x for x in pickle.load(open(S+"кат.pkl","rb"))}
З=pickle.load(open(S+sys.argv[1],"rb")); в=random.Random(int(sys.argv[2])).sample(З,40); рр=[]
for (сх,роль,ц,пів,ід,до,пс) in в:
    x=кат[ід]; L,C,h=cs.lch(x["lab"])
    рр.append(dict(ід=ід, фото=x["фото"], lab=x["lab"], центр_h=ц, до="так" if до else "ні", пс="так" if пс else "ні",
                   підпис="%s/%s h%.0f→ц%.0f±%.0f L%.0f C%.0f"%(сх[:6],роль[:4],h,ц,пів,L,C)))
foto.аркуш(рр, S+sys.argv[3]+"_%d.png")
