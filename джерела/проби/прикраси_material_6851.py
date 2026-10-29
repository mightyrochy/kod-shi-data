# -*- coding: utf-8 -*-
"""Проба Х25-Н.4 (рядок 6851): `material` на прикрасах — друкує факт. Каблучка ж-11728 («жовте золото 750») і сережка
ж-11794 («срібло 925») з відповіддю моделі `leather`/`suede` і справжньою цитатою; «до» — таблиця допустимих кодів
порожня, «після» — `ДОПУСТИМІ_КОДИ`. Контроль: `fabric` чобіт лишається. Запуск: python3 джерела/проби/прикраси_material_6851.py"""
import json, os, sys  # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import каталог_розбір as КР, фід_каталог as ФК, фід_розбір as ФР  # noqa: E401,E402
речі = {x["id"].split("@")[0]: x for x in ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]}
п = lambda в, ц: {"quote": ц, "value": в}  # noqa: E731
def розібрати(ід, відп):
    return КР.з_відповіді(json.dumps(відп), КР.вхід(речі[ід]))
таблиця = dict(КР.ДОПУСТИМІ_КОДИ)
for ід, тип, цитата, матеріал in (("ж-11728", "ring", "жовте золото 750 проби", "leather"),
                                  ("ж-11794", "earrings", "срібло 925 проби", "suede")):
    відп = {"item_type": п(тип, цитата), "material": п(матеріал, цитата)}
    КР.ДОПУСТИМІ_КОДИ.clear()
    до = розібрати(ід, відп)[0]
    КР.ДОПУСТИМІ_КОДИ.update(таблиця)
    після, причини = розібрати(ід, відп)
    print("%s slot=%-8s material до → %-8s після → %-8s вигадок material %d" % (ід, після["slot"], до["material"],
          після["material"], sum("invented" in т and "field=material" in т for т in причини)))
чоботи = next(x for x in речі if (речі[x].get("назва") or "").lower().startswith("чоботи"))
res = розібрати(чоботи, {"item_type": п("boots", "Чоботи"), "fabric": п("leather", "Чоботи")})[0]
print("контроль %s: slot=%s fabric=%s" % (чоботи, res["slot"], res["fabric"]))
