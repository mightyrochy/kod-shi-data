# -*- coding: utf-8 -*-
"""ВАРІАНТ-234: два кольори в полі → одне слово варіанта.
Запуск: cd джерела && python3 проби/варіант_234.py [каталог.xml]
"""
import collections, gzip, os, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from фід_розбір import читати_yml
from фід_варіант import _двоколірні_частини, сестри_варіантів, слово_варіанта
from фід_збагачення import читати_збагачення, _збагачення_придатне

ш = sys.argv[1] if len(sys.argv) > 1 else "../каталог_повний.xml.gz"
if ш.endswith(".gz"):
    with gzip.open(ш, "rb") as src, tempfile.NamedTemporaryFile(suffix=".xml") as dst:
        dst.write(src.read()); dst.flush(); offers, _ = читати_yml(dst.name)
else: offers, _ = читати_yml(ш)
зб, сестри = читати_збагачення(), сестри_варіантів(offers)
два = [o for o in offers if _двоколірні_частини(o.get("колір_назва"))]
def вар(o):
    z = зб.get(o["id"]); return слово_варіанта(o, z if _збагачення_придатне(z) else None, сестри)
р = {o["id"]: вар(o) for o in два}; нові = {"список варіантів"}
до = sum(bool(x) and x["джерело"] not in нові for x in р.values()); після = sum(bool(x) for x in р.values())
причини = collections.Counter("нема однозначного артикула/списку/сестер" for x in р.values() if not x)
print("двоколірних %d · одне слово ДО %d → ПІСЛЯ %d · без %d %s" % (len(два), до, після, len(два)-після, dict(причини)))
print("одноколірних змінено новим правилом: %d" % sum(bool(вар(o)) and вар(o)["джерело"] in нові for o in offers if o not in два))
for i in ("ж-08471", "ж-08623", "ж-05287", "ж-04883"):
    o = next(o for o in offers if o["id"].split("@")[0] == i); x = вар(o)
    print("%s: %s · %s · %s" % (o["id"], x and x["слово"], x and x["джерело"], x and x["за_чим"]))
