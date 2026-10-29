# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «чистка каталогу». ФАКТ: чистка лагодить дані
# ПІСЛЯ збирання, правилом на кожен діалект крамниці. (1) правил-функцій у `чистка_каталогу`
# (`_зняти_*`, `_розекранувати*`, `мовні_двійники` …); (2) сирий архів → чистий каталог:
# оферів знято, назв змінено, `param` змінено; (3) крамниць, для яких чистка тримає окреме
# рішення (коди моделі, коди кольору). Сирий архів розпаковується в тимчасову теку.
import os, re, sys, gzip, shutil, tempfile, collections as C
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed, чистка_каталогу as ЧК
чистий = feed.каталог_на_диску()
архів = os.path.join(os.path.dirname(чистий), os.pardir, "каталог_повний.xml.gz")
текст = open(ЧК.__file__, encoding="utf-8").read()
правила = re.findall(r"^def (_зняти_\w+|_розекранувати\w*|мовні_двійники|_правка_назви|_дописати_\w+)", текст, re.M)
print("правил чистки (функцій): %d — %s" % (len(правила), ", ".join(правила)))
сирий = os.path.join(tempfile.mkdtemp(), "сирий.xml")
with gzip.open(архів, "rb") as вх, open(сирий, "wb") as вих:
    shutil.copyfileobj(вх, вих)
с = {o["id"]: o for o in feed.читати_yml(сирий)[0]}
ч = {o["id"]: o for o in feed.читати_yml(чистий)[0]}
спільні = set(с) & set(ч)
print("сирий %d → чистий %d оферів · знято %d · назву змінено %d · param змінено %d"
      % (len(с), len(ч), len(set(с) - set(ч)), sum(1 for i in спільні if с[i]["назва"] != ч[i]["назва"]),
         sum(1 for i in спільні if (с[i].get("параметри") or {}) != (ч[i].get("параметри") or {}))))
змін = C.Counter(ч[i]["магазин"] for i in спільні if с[i]["назва"] != ч[i]["назва"])
print("крамниць зі зміненими назвами %d · найбільші %s" % (len(змін), змін.most_common(5)))
оферти = list(с.values())
коди, кольори = ЧК.коди_крамниць(оферти), ЧК.кольори_крамниць(оферти)
print("крамниць з окремим рішенням: коди моделі %d %s · коди кольору %d %s"
      % (sum(1 for v in коди.values() if v), sorted(k for k, v in коди.items() if v)[:5],
         sum(1 for v in кольори.values() if v), sorted(k for k, v in кольори.items() if v)[:5]))
шлях = os.path.dirname(сирий)
shutil.rmtree(шлях, ignore_errors=True)
