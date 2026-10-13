# -*- coding: utf-8 -*-
"""Рядок 1880: чи вмикається траурний регістр, коли мовна модель дала нагоду «траур», а місце — «дім».
Вхід — живий С5 ПІСЛЯ (ж5, «похорон дідуся в четвер зранку» + «прикраси хочу срібні»; шар: occasion
`mourning`, place `home`; `traur_nahoda_1880.json`), каталог повний. Друкує мітку траурного пулу,
чи лишились у пулі речі «Третього образу» руки 1 і суд того образу (K-OCC-01 і всі правила).
Запуск: cd джерела && python3 проби/traur_nahoda_1880.py"""
import collections, json, os, sys, tempfile
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import bridge as B, feed as Ф
з = json.load(open("проби/traur_nahoda_1880.json", encoding="utf-8"))
вх = dict(з["колір"], драп_сирий=з["драп"], сценарій=з["сценарій"], паспорт=з["паспорт"],
          намір=з["паспорт"]["намір"], каталог=Ф.каталог_на_диску("каталог_повний.xml"),
          кеш_кольорів=os.path.join(tempfile.gettempdir(), "кеш_живого_шляху.json"), **з["мірки"])
if not os.path.exists(вх["кеш_кольорів"]):
    json.dump({}, open(вх["кеш_кольорів"], "w"))
ОБРАЗ = ["ж-12150@theoriginals.com.ua", "ж-07631@likeangel.com.ua", "ж-04700@brenda.ua",
         "ж-09484@favoriteshoes.com.ua", "ж-11741@theoriginals.com.ua"]     # жакет, брошка-троянда, кюлоти, лофери, каблучка
р = json.loads(B.виклик("запити", json.dumps(dict(вх, пакети=1), ensure_ascii=False)))
from міст_пакет import _КЕШ_ПАКЕТА, _ОСТАННІЙ_ПАКЕТ
пак = _КЕШ_ПАКЕТА[_ОСТАННІЙ_ПАКЕТ[-1]]
у_пулі = {r.get("id") for рч in (р.get("кандидати") or {}).values() for r in рч}
тр = пак.get("_траур") or {}
print("пул %s · траурний пул: %s · знято регістром %s" % (р.get("пул_речей"), тр.get("випадок") or "—",
      sum((тр.get("знято") or {}).values()) if isinstance(тр.get("знято"), dict) else тр.get("знято")))
print("речі Третього образу в пулі: %s" % " ".join("%s:%s" % (і.split("@")[0], "так" if і in у_пулі else "ні") for і in ОБРАЗ))
вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ОБРАЗ), ensure_ascii=False)))
зн = вм.get("знахідки") or []
print("суд образу: K-OCC-01 %d · %s" % (sum(1 for x in зн if x.get("правило") == "K-OCC-01"),
      dict(collections.Counter(x.get("правило") for x in зн).most_common(8))))
for x in зн:
    if x.get("правило") == "K-OCC-01":
        print("   K-OCC-01 %s %s: %s · речі %s" % (x.get("сила"), x.get("регістр"), str(x.get("суть"))[:90],
              [str(і).split("@")[0] for і in x.get("речі") or []]))
