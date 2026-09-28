# -*- coding: utf-8 -*-
"""Проба #409: чи не несе картка ЧУЖОГО фото в стані «свій_кадр».

Друкує лічбу станів і вирок по п'яти записах, на яких ручна перевірка 28.09.2026 побачила
хибне фото (чужий товар, інший колірний варіант, майже-білий кадр під хроматичним словом).
Кожен із них має бути «інший_колір» — тобто чесна заява замість хибного знімка."""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as F
import фід_кадр_колір as ФКК
from фід_фото import _спільні_фото, чужий_кадр
from фід_збагачення import _збагачення_придатне

ХИБНІ = ("ж-01320@stolyarchuk.com.ua", "ж-01430@wearme.ua", "ж-03249@25union.com.ua",
         "ж-06159@andretan.ua", "ж-08271@25union.com.ua")

offers = F.читати_yml(F.каталог_на_диску())[0]
зб = F.читати_збагачення()
сп = _спільні_фото(offers)
к = ФКК.контекст(offers, зб, сп)
ФКК.КЛАС_ПОТРІБЕН = True                      # виробничий режим: кадр без класу на картку не йде
стани, вирок = collections.Counter(), {}
for o in offers:
    з = зб.get(o.get("id"))
    if not (з and _збагачення_придатне(з)) or чужий_кадр(з.get("фото"), сп.get(o.get("магазин")) or {}):
        continue
    р = ФКК.рішення(o, з, к)
    стани[р["стан"]] += 1
    if o["id"] in ХИБНІ:
        вирок[o["id"]] = р["стан"]
рівні = к["рівні_папок"]
папки = collections.defaultdict(set)
for o in offers:
    мг = o.get("магазин") or str(o.get("id") or "").split("@")[-1]
    for u in o.get("фото") or ():
        папки[мг].add(ФКК.папка_товару(ФКК._файл_фото(u), рівні.get(мг, 0)))
діє = sum(1 for мг, п in папки.items() if рівні.get(мг) and len(п - {None}) > 1)
print("рівень папки товару знайдено в %d крамницях із %d; папки РІЗНІ (правило може відсікати) — у %d"
      % (sum(1 for d in рівні.values() if d), len(рівні), діє))
print("стани: " + ", ".join("%s %d" % (с, н) for с, н in sorted(стани.items(), key=lambda x: str(x[0]))))
for ід in ХИБНІ:
    print("  %-28s %s" % (ід, вирок.get(ід, "нема в каталозі")))
погано = [і for і, с in вирок.items() if с == "свій_кадр"]
print("ХИБНИХ ЛИШИЛОСЬ: %d" % len(погано) + ("" if not погано else " — " + ", ".join(погано)))
