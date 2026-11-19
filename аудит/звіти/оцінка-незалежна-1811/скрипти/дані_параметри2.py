import sys, re, collections as C, xml.etree.ElementTree as ET
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import status
текст = "".join(open(f"/home/user/kod-shi-data/джерела/{m}.py", encoding="utf-8").read() for m in status.МОДУЛІ_ПРОДУКТУ)
імена = C.Counter(); усі=C.Counter()
for ev, el in ET.iterparse("/tmp/скрипти_звірки/дані/каталог_повний.xml"):
    if el.tag == "offer":
        for p in el.findall("param"):
            усі[p.get("name") or ""] += 1
            if (p.text or "").strip(): імена[p.get("name") or ""] += 1
        el.clear()
з = [n for n in усі if n.startswith("~")]; без = [n for n in усі if not n.startswith("~")]
print("усіх назв (з порожніми)", len(усі), "з ~", len(з), "без ~", len(без))
for нб in (з, без):
    зн = [n for n in нб if n in текст]; зн2=[n for n in нб if n.lstrip("~") in текст]
    v=sum(усі[n] for n in нб); print(" група", len(нб), "дослівно", len(зн), "без ~", len(зн2), "знач", v, "покрито(без ~)", sum(усі[n] for n in зн2))
print("без ~ приклади", sorted(без, key=lambda n:-усі[n])[:40])
# регістр-незалежно
low = текст.lower()
зн3=[n for n in усі if n.lstrip("~").strip().lower() in low]; print("регістр-незалежно без ~", len(зн3), "покриття", round(100*sum(усі[n] for n in зн3)/sum(усі.values())), "поза", sum(усі.values())-sum(усі[n] for n in зн3))
