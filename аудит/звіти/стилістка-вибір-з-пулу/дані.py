#!/usr/bin/env python3
"""Збирає рядки «річ у запиті» зі збережених обмінів моста (ті самі записи й зіставлення, що у звіті крамниць-рівна-черга).
Вихід: рядки.csv.gz (кожна річ кожного запиту складання), речі.csv (по речі за всіма запитами).
Запуск з кореня: python3 -I аудит/звіти/стилістка-вибір-з-пулу/дані.py"""
import csv, gzip, importlib.util, json, re, sys, xml.etree.ElementTree as XML
from collections import Counter, defaultdict
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory

ТЕКА = Path(__file__).resolve().parent
ПОПЕРЕДНІЙ = ТЕКА.parent / "крамниці-рівна-черга" / "вимір.py"
сп = importlib.util.spec_from_file_location("попередній", ПОПЕРЕДНІЙ)
П = importlib.util.module_from_spec(сп); sys.modules["попередній"] = П; сп.loader.exec_module(П)

НЕВІДОМО = ("L", "hex", "family", "fabric", "register", "cut", "length", "formality")


def фід_із_назвами():
    картки = {}
    with __import__("gzip").GzipFile(fileobj=BytesIO(П.файл("каталог_повний.xml.gz"))) as потік:
        for _, o in XML.iterparse(потік, events=("end",)):
            if o.tag != "offer":
                continue
            магазин = o.findtext("param[@name='магазин']")
            опис = " ".join(" ".join(x.itertext()) for x in o.findall("description"))
            опис = " ".join(re.sub(r"<[^>]+>", " ", опис).split())
            картки[f"{o.attrib['id']}@{магазин}"] = {
                "назва": len((o.findtext("name") or o.findtext("model") or "").strip()),
                "опис": len(опис), "фото": len({x.text for x in o.findall("picture") if x.text}),
            }
            o.clear()
    return картки


def головна():
    with TemporaryDirectory(prefix="вибір-") as т:
        копія = Path(т)
        П.код_з_коміту(копія)
        sys.path.insert(0, str(копія / "джерела"))
        фід = фід_із_назвами()
        каталог, _, _ = П.знімок(копія)
    кат = {r["id"]: r for r in каталог}
    зведено = П.звірені_траси()
    рядки, заяви = [], []
    джерела = П.git("ls-tree", "-r", "--name-only", "-z", П.BASE, П.МІСТ).decode().split("\0")
    for шлях in sorted(s for s in джерела if s.endswith("/обміни.jsonl")):
        сцена = Path(шлях).parent.name
        черга = Counter()
        for лінія, обмін in enumerate(П.рядки(шлях), 1):
            if not обмін.get("відповідь"):
                continue
            прохід = str(обмін["прохід"]); індекс = черга[прохід]; черга[прохід] += 1
            if обмін.get("статус") != 200:
                continue
            тіло = json.loads(обмін["запит"])
            try:
                пакет = П.розібрати_json(П.текст_запиту(тіло))
            except (ValueError, IndexError):
                continue
            if not (isinstance(пакет.get("pool"), dict) and "rows" in пакет["pool"]):
                continue
            blocks = json.loads(обмін["відповідь"]).get("content", [])
            try:
                відповідь = П.розібрати_json("".join(б["text"] for б in blocks if б.get("type") == "text"))
            except (ValueError, IndexError):
                continue
            if not isinstance(відповідь.get("outfits"), list):
                continue
            rs = П.записи_таблиці(пакет)
            if not rs:
                continue
            взято = {n for o in відповідь["outfits"] for x in o.get("items", []) if (n := П.номер(x))}
            збіг, відбитки, сід, _рівні = зведено.get((сцена, прохід, індекс), (None, {}, None, None))
            відп = П.кращі_відповідності(rs, відбитки)
            запит = f"{сцена}/{прохід}/{лінія}"
            заяви.append(dict(запит=запит, у_пулі=len(rs), outfits=відповідь["outfits"], needed=відповідь.get("needed"),
                              палітра=[a for a in ((пакет.get("person") or {}).get("palette") or {}).get("accents", [])],
                              схема=((пакет.get("person") or {}).get("palette") or {}).get("scheme"),
                              ролі=((пакет.get("person") or {}).get("palette") or {}).get("slot_roles"),
                              нагода=(пакет.get("day") or {}).get("formality")))
            for i, r in enumerate(rs):
                n = П.номер(r.get("n"))
                можливі = відп.get(n, set())
                ід = next(iter(можливі)) if len(можливі) == 1 else ""
                к = кат.get(ід, {}); ф = фід.get(ід, {})
                дод = r.get("extra") if isinstance(r.get("extra"), dict) else {}
                рядки.append(dict(
                    запит=запит, позиція=i, n=n, ід=ід, взято=int(n in взято), зі_слідом=int(збіг is not None),
                    слот=к.get("слот", ""), тип=r.get("type") or "", тип_укр=к.get("тип", ""),
                    колір=r.get("color") or "", family=r.get("family") or "", hex=r.get("hex") or "", колір_укр=к.get("колір_назва", ""), ціна=r.get("price"),
                    крамниця=П.крамниця(ід) if ід else "", in_arc=str(r.get("in_arc")),
                    невідомо=sum(r.get(k) is None for k in НЕВІДОМО),
                    **{f"н_{k}": int(r.get(k) is None) for k in НЕВІДОМО},
                    назва_довж=ф.get("назва", ""), опис_довж=ф.get("опис", ""), фото=ф.get("фото", ""),
                    гілка=(r.get("branch_source") or {}).get("kind", ""), L=r.get("L") if not isinstance(r.get("L"), list) else "діапазон",
                    дод=len(дод)))
    with gzip.open(ТЕКА / "заяви.jsonl.gz", "wt", encoding="utf-8") as f:
        for з in заяви:
            f.write(json.dumps(з, ensure_ascii=False) + "\n")
    поля = list(рядки[0])
    with gzip.open(ТЕКА / "рядки.csv.gz", "wt", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, поля, lineterminator="\n"); w.writeheader(); w.writerows(рядки)
    print(len(рядки), "рядків;", sum(bool(r["ід"]) for r in рядки), "з ід;", len({r["запит"] for r in рядки}), "запитів")


if __name__ == "__main__":
    головна()
