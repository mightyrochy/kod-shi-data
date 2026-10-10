# КОЛІР-ОЧИМА-40 (рядок 2697): вибірка 40 відкинутих порогом згоди вимірів (сід 7, по 10 з груп 0.8/0.75/0.6/0.55). Запуск із джерела/: python3 проби/колір_очима_40_вибірка.py [файл виводу, типово sample40.json].
import json,gzip,sys,collections as K,random
sys.path.insert(0,".")
import bridge as B, стенд_знімок as СЗ, колір_річ as КР
import фід_збагачення as ФЗ, verify as V
вх=json.load(open("стенд_вх.json",encoding="utf-8"))
B.виклик("запити",json.dumps(dict(вх,сценарій=СЗ.СЦЕНАРІЇ["офіс·18°C"],випадок="офіс"),ensure_ascii=False))
кат,зб=B.каталог_останнього_пакета(),json.load(gzip.open("каталог_збагачення.json.gz"))
G=K.defaultdict(list)
for r in кат:
    нв=КР.не_вимір(r); з=зб.get(r["id"]) or {}
    if not нв or нв["свідок"]!="shop_word" or з.get("версія")!=2 or not (з.get("колір_основний") or {}).get("hex"): continue
    сп=r.get("колір_спір") or {}
    if сп.get("чому")!="згода свідків нижча за поріг": continue
    сирий=ФЗ._lab_з_hex(з["колір_основний"]["hex"])
    if нв["слово"] not in V.ЛЕКСИКОН or V.перевірити(сирий,ім=нв["слово"])["вердикт"]!="прийнято": continue
    у=float(з.get("впевненість") or 0)
    g="0.8" if .795<=у<.9 and abs(у-.8)<.03 else "0.75" if abs(у-.75)<.03 else "0.6" if abs(у-.6)<.03 else "0.55" if abs(у-.55)<.03 else None
    if g: G[g].append((r["id"],нв["слово"],з["колір_основний"]["hex"],round(у,2),r.get("магазин"),r.get("назва")))
print({k:len(v) for k,v in G.items()})
rnd=random.Random(7); out=[]
for g in ["0.8","0.75","0.6","0.55"]:
    xs=sorted(G[g]); rnd.shuffle(xs); out+= [dict(id=a,слово=b,hex=c,згода=d,магазин=e,назва=f,група=g) for a,b,c,d,e,f in xs[:10]]
json.dump(out,open(sys.argv[1] if len(sys.argv)>1 else "sample40.json","w"),ensure_ascii=False,indent=0)
print(len(out))
