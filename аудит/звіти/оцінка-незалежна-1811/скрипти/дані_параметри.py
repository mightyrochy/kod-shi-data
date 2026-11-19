import sys, re, gzip, collections as C, xml.etree.ElementTree as ET
sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import status
М = list(status.МОДУЛІ_ПРОДУКТУ); print("модулів", len(М))
текст = "".join(open(f"/home/user/kod-shi-data/джерела/{m}.py", encoding="utf-8").read() for m in М)
for шлях, відкр in (("/home/user/kod-shi-data/каталог_повний.xml.gz", gzip.open), ("/tmp/скрипти_звірки/дані/каталог_повний.xml", open)):
    імена = C.Counter(); офери=0; крамниці=set()
    with відкр(шлях, "rb") as f:
        for ev, el in ET.iterparse(f):
            if el.tag == "offer":
                офери += 1
                for p in el.findall("param"):
                    if (p.text or "").strip(): імена[p.get("name") or ""] += 1
                el.clear()
    знає = {n for n in імена if n and n in текст}
    знає2 = {n for n in імена if n and n.lstrip("~").strip() in текст}
    всього = sum(імена.values()); пок = sum(імена[n] for n in знає)
    print(шлях.split("/")[-1], "оферів", офери, "назв", len(імена), "у коді", len(знає), f"({100*len(знає)/len(імена):.0f}%)", "покривають значень", f"{100*пок/всього:.0f}%", "поза", всього-пок, "| без ~:", len(знає2))
    print("  каблук:", [(n,c) for n,c in імена.most_common() if re.search("каблук|підбор", n, re.I)][:8])
