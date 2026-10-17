# -*- coding: utf-8 -*-
"""Рядок 5697: черга галерей (скільки кадрів міряти) і приймач (групи кадрів навколо якоря) на наявних вимірах.
Запуск: cd джерела && python3 проби/кадри_групи_5697.py"""
import collections, gzip, json, os, sys, tempfile                              # noqa: E401
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import feed as F, жнива_кадри as К, кадри_групи as Г                             # noqa: E401
from фід_фото import _хости_крамниць
offers, зб = F.читати_yml(F.каталог_на_диску())[0], F.читати_збагачення()
кадри = json.load(gzip.open(Г.ВИХІД, "rt", encoding="utf-8"))["записи"]
цілі, сп = К.цілі(offers, зб)
черга = К.черга_галерей(offers, зб, кадри, сп, _хости_крамниць(offers), {o["id"] for o, _ in цілі}, К.читати_чергу_woo())
print("черга: речей %d, кадрів %d; пріоритет 0 (інший_колір): %d речей, %d кадрів" % (len(черга), sum(len(т[2]) for т in черга),
      sum(т[3] == 0 for т in черга), sum(len(т[2]) for т in черга if т[3] == 0)))
bez = [o["id"] for o, _ in цілі if o["id"] not in кадри and o["id"] not in {т[0]["id"] for т in черга}]
print("інший_колір: %d, без галереї й без черги (галерея з одного кадру жнив): %d" % (len(цілі), len(bez)))
u = К.відбиток_кадру("https://x/a/b-1000x1500.jpg?v=1"), К.відбиток_кадру("https://x/a/b-400x600.jpg?v=2")
print("відбиток: той самий файл, інший ?v= → змінений: %s" % (u[0][0] == u[1][0] and u[0] != u[1]))
за_ід = {o["id"]: o for o in offers}
показано = 0
for ід, зап in кадри.items():
    з = зб.get(ід)
    if not з or ід not in за_ід or sum(1 for в in зап if в.get("lab")) < 3:
        continue
    г = Г.групи_кадрів(з, зап)
    if len(г["групи"]) < 2:
        continue
    print(ід, "якір %s(%s)" % (г["слово_якоря"], г["якір"][-18:]), "|", "; ".join("%s%s:%d" % ("*" if x["якір"] else "", "/".join(x["слова"][:2]), len(x["кадри"])) for x in г["групи"]),
          "| службових %d, без виміру %d, на картку %d" % (len(г["службові"]), len(г["без_виміру"]), len(г["для_картки"])))
    показано += 1
    if показано == 5:
        break
з_п = {k: кадри[k] for k in list(кадри)[:5]}
з_п["x@y"] = [{"файл": "f", "url": "u", "клас": "кіт"}]
ф = os.path.join(tempfile.mkdtemp(), "р.json.gz")
json.dump({"мета": {}, "записи": з_п}, gzip.open(ф, "wt", encoding="utf-8"))
print("приймач (сухо) на 5 речах + 1 битий:", Г.прийняти(ф, Г.ВИХІД, сухо=True))
