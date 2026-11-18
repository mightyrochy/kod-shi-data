import sys, pickle, collections as C, xml.etree.ElementTree as ET
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import status
текст = "".join(open(f"/home/user/kod-shi-data/джерела/{m}.py", encoding="utf-8").read() for m in status.МОДУЛІ_ПРОДУКТУ)
ids = {r["id"].split("@")[0] for r in pickle.load(open("/tmp/скрипти_звірки/дані/каталог.pkl","rb"))}
усі=C.Counter(); лише_тильда=C.Counter()
for ev, el in ET.iterparse("/tmp/скрипти_звірки/дані/каталог_повний.xml"):
    if el.tag == "offer":
        if el.get("id") in ids:
            for p in el.findall("param"):
                if (p.text or "").strip() or len(p): усі[p.get("name") or ""] += 1
        el.clear()
for назва, нб in (("у слотах", list(усі)),):
    for ім, f in (("дослівно", lambda n:n in текст), ("без~", lambda n:n.lstrip("~") in текст)):
        зн=[n for n in нб if f(n)]; т=sum(усі.values()); п=sum(усі[n] for n in зн)
        print(назва, len(нб), ім, len(зн), f"{100*п/т:.0f}%", т-п)
