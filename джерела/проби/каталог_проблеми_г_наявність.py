# -*- coding: utf-8 -*-
"""Рядок 5620 (реєстр 5616, клас Г1): наявність речі — на день знімання, і більше її ніхто не перевіряє.
Факт: записи з `available="false"` уже в день жнив (по крамницях) і скільки з них доходить до фіду; записи крамниць
уживаних речей (є поле «Стан» — одна річ в одному розмірі); `наявність` нових жнив. Запуск: python3 джерела/проби/каталог_проблеми_г_наявність.py"""
import collections, gzip, os, re, sys                                          # noqa: E401
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, Д); os.chdir(Д)                                             # noqa: E702
import feed as F                                                               # noqa: E402
xml = gzip.open(os.path.join(Д, "..", "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
зз = [(і, д, re.search(r'<param name="магазин">([^<]*)<', о).group(1), 'name="Стан"' in о,
       (re.findall(r'<param name="наявність">([^<]*)<', о) or [None])[0])
      for і, д, о in re.findall(r'<offer id="([^"]+)" available="([^"]*)"(.*?)</offer>', xml, re.S)]
нема = [з for з in зз if з[1] == "false"]
print("записів %d · available=false у день знімання %d (%.1f %%) · %s" % (len(зз), len(нема), 100 * len(нема) / len(зз),
      collections.Counter(з[2] for з in нема).most_common(5)))
у_фіді = {o["id"].split("@")[0] for o in F.читати_yml(F.каталог_на_диску("каталог_повний.xml"))[0]}
print("з них доходить до фіду (жінці показують як річ каталогу): %d" % sum(1 for з in нема if з[0] in у_фіді))
вж = collections.Counter(з[2] for з in зз if з[3])
print("записи вживаних речей (поле «Стан», одна річ — один примірник): %d · %s" % (sum(вж.values()), dict(вж)))
print("поле «наявність» нових жнив: %s" % dict(collections.Counter(з[4] for з in зз if з[4])))
