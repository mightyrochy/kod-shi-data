import pickle, collections as C
к = pickle.load(open("/tmp/скрипти_звірки/дані/каталог.pkl","rb"))
ОД = {"верх","низ","сукня","комплект","верхній_шар"}
def пок(назва, рядки):
    n=len(рядки); print(f"== {назва}: {n}")
    for поле in ("колір_тип","колір_джерело","джерело_кольору","тип_джерело","крій_джерело"):
        c=C.Counter(str(r.get(поле)) for r in рядки); print(" ",поле, [(k,v,round(100*v/n,1)) for k,v in c.most_common(8)])
    c=C.Counter(bool(r.get("колір_не_вимір")) for r in рядки); print("  колір_не_вимір непорожнє", c[True], round(100*c[True]/n,1))
    for поле in ("крій","довжина_рівень","довжина_виробу_см","посадка","матеріал","обхвати_виробу"):
        m=sum(1 for r in рядки if r.get(поле) not in (None,"",[],{},0)); print(f"  {поле}: {m} ({100*m/n:.1f}%)")
    c=C.Counter(r.get("тип") for r in рядки if (r.get("тип") or "").endswith("без_уточнення") or not r.get("тип")); print("  тип невідомий/без_уточнення", sum(c.values()), c.most_common(6))
пок("весь", к)
пок("одяг", [r for r in к if r["слот"] in ОД])
c=C.Counter(r["слот"] for r in к); print(c)
# зв'язок колір_тип vs колір_не_вимір vs lab
print(C.Counter((r["колір_тип"], bool(r.get("колір_не_вимір")), r.get("lab") is not None, r.get("колір_джерело")) for r in к).most_common(15))
