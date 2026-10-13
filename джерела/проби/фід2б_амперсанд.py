# -*- coding: utf-8 -*-
"""Рядок 1984 (3): адреса з `&` у `переписати_picture` на справжньому офері brenda — XML після запису читається?"""
import gzip, os, sys, xml.etree.ElementTree as ET
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "zhnyvarka"))
import перезняти_галереї as Г
текст = gzip.open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "каталог_повний.xml.gz")).read().decode()
ід = next(o.get("id") for o in ET.fromstring(текст.encode()).iter("offer")
          if any(p.get("name") == "магазин" and p.text == "brenda.ua" for p in o.findall("param")))
нове = {ід: ["https://brenda.ua/image/a.jpg?v=1&w=900&h=1200"]}
після, замін = Г.переписати_picture(текст, нове, "brenda.ua")
try:
    корінь = ET.fromstring(після.encode()); кадр = next(o for o in корінь.iter("offer") if o.get("id") == ід).findtext("picture")
    print("ПІСЛЯ: переписано %d, XML читається, picture = %s" % (замін, кадр))
except ET.ParseError as e:
    print("ПІСЛЯ: XML не читається:", e)
Г.xml_escape = lambda т: т          # ДО: без екранування
до, _ = Г.переписати_picture(текст, нове, "brenda.ua")
try:
    ET.fromstring(до.encode()); print("ДО: XML читається")
except ET.ParseError as e:
    print("ДО: XML не читається:", e)
