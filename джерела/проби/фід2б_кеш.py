# -*- coding: utf-8 -*-
"""Рядок 1985: 47 речей `no_photo_none_opened` з `каталог_показ.json.gz` — живий вимір їхніх кадрів проти кешу, що «пам'ятає» збій."""
import gzip, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")); sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "прилади"))
import feed as Ф, фід_фото as ФФ, показне_фото as П
показ = json.loads(gzip.open(os.path.join(os.path.dirname(P := os.path.abspath(__file__)), "..", "каталог_показ.json.gz")).read())
іди = {і for і, ч in показ["без_показу"].items() if ч == ФФ.ЧОМУ_НЕ_ВІДКРИЛОСЬ}
офери = [o for o in Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"), показ=False)[0] if o["id"] in іди]
спільні, хости = ФФ._спільні_фото(офери), ФФ._хости_крамниць(офери)
ряди = {o["id"]: ФФ.кадри_речі(o, спільні.get(o.get("магазин")) or {}, хости, None, заборонені=()) for o in офери}
адреси = sorted({u for р in ряди.values() for u in р})
кеш = {u: dict(код=-1, corp=None, картинка=False) for u in адреси}   # кеш, знятий коли крамниці не відповідали; без мітки часу
до = sum(1 for u in адреси if u not in кеш)     # стара умова: «є в кеші» → 0 вимірів
після = П.міряти(адреси, кеш, 32)
врятовано = [і for і, р in ряди.items() if any(П.показна(кеш.get(u)) for u in р)]
print("речей %d, адрес %d | ДО: вимірів %d, речей із показним кадром 0 (кеш пам'ятає збій)" % (len(ряди), len(адреси), до))
print("ПІСЛЯ: вимірів %d, речей із показним кадром %d: %s" % (після, len(врятовано), ", ".join(sorted(врятовано)[:6])))
