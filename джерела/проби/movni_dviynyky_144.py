# -*- coding: utf-8 -*-
"""Рядок 144 (доповнення 23.09): мовний двійник — той самий товар у каталозі двічі.
ДО — `каталог_повний.xml.gz` як його віддала жниварка, ПІСЛЯ — після `чистка_каталогу.почистити`.
Запуск: cd джерела && python3 проби/movni_dviynyky_144.py"""
import collections, gzip, os, shutil, sys, tempfile
import xml.etree.ElementTree as ET
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import чистка_каталогу as ЧК
тека = tempfile.mkdtemp(); до = os.path.join(тека, "до.xml"); після = os.path.join(тека, "після.xml")
with gzip.open(os.path.join(os.path.dirname(ТУТ), "каталог_повний.xml.gz"), "rb") as вх, open(до, "wb") as вих:
    shutil.copyfileobj(вх, вих)
ціна = lambda o: float((o.findtext("price") or "0").replace(",", ".") or 0)
маг = lambda o: next((p.text for p in o.findall("param") if (p.get("name") or "") == "магазин"), "—")
def безцінні(корінь):
    return collections.Counter(маг(o) for o in корінь.iter("offer") if not ціна(o))
корінь_до = ET.parse(до).getroot()
двійники = ЧК.мовні_двійники(корінь_до)
за_маг = collections.Counter(маг(o) for o, _, _ in двійники)
без_ціни = collections.Counter(маг(o) for o, _, _ in двійники if not ціна(o))
до_безцінних = безцінні(корінь_до)
звіт = ЧК.почистити(до, після)
корінь_після = ET.parse(після).getroot()
після_безцінних = безцінні(корінь_після)
print("ФАКТ · оферів ДО %d → ПІСЛЯ %d · мовних двійників знято %d (звіт чистки: %d)"
      % (len(list(корінь_до.iter("offer"))), len(list(корінь_після.iter("offer"))),
         len(двійники), звіт["двійників_знято"]))
print("ФАКТ · двійники по крамницях: %s" % dict(за_маг.most_common()))
print("ФАКТ · без ціни ДО %d %s" % (sum(до_безцінних.values()), dict(до_безцінних.most_common())))
print("ФАКТ · без ціни ПІСЛЯ %d %s" % (sum(після_безцінних.values()), dict(після_безцінних.most_common())))
print("ФАКТ · зняті двійники, що були без ціни: %d %s" % (sum(без_ціни.values()), dict(без_ціни.most_common())))
за_url = {(o.findtext("url") or "").strip(): o.get("id") for o in корінь_до.iter("offer")}
пари = [(o.get("id"), за_url.get(укр)) for o, _, укр in двійники]
лишились = {o.get("id") for o in корінь_після.iter("offer")}
print("ФАКТ · знято → лишився (перші 6): %s" % пари[:6])
print("ФАКТ · український запис лишився для %d пар із %d" % (sum(1 for _, u in пари if u in лишились), len(пари)))
print("ФАКТ · решта без ціни — записи БЕЗ українського двійника; пул їх відсіває окремо (#229, рядок 139)")
shutil.rmtree(тека)
