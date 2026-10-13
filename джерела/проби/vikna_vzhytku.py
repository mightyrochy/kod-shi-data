# -*- coding: utf-8 -*-
"""Л-10: вікна вжитку слів кольору (`verify.ВЖИТОК`) — перерахунок із каталогу тим самим методом
(`verify.вікно_з_вжитку`) і звірка з таблицею. Точки — дизайни (кадр жнив), чиє поле кольору — одна частина
з одним кольором, колір — hex жнив v2 з кадру, що не є спільною картинкою крамниці.
Запуск: cd джерела && python3 проби/vikna_vzhytku.py [--таблиця]   (--таблиця — рядки для verify.py)"""
import collections, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as CS
from фід_фото import _спільні_фото, чужий_кадр, _файл_фото; from фід_розбір import _СЕП_КОЛЬОРУ
оф = FR.читати_yml(feed.каталог_на_диску())[0]; зб, сп = FZ.читати_збагачення(), _спільні_фото(оф)
ТОК = re.compile(r"[a-zа-яёєіїґ']+")
одне = lambda ч: not re.search(r"[\[(]", ч) and sum(1 for x in ТОК.findall(ч.lower().replace("-", " "))
                                                     if V.назва_кольору(x) or V.слово_крамниці(x)) <= 1
т = collections.defaultdict(dict)
for o in оф:
    z = зб.get(o["id"]); ч = [x.strip() for x in _СЕП_КОЛЬОРУ.split(o.get("колір_сирий") or o.get("колір_назва") or "") if x.strip()]
    if not FZ._збагачення_придатне(z) or (z.get("версія") or 1) < 2 or len(ч) != 1 or not одне(ч[0]):
        continue
    lab, ск = FZ._lab_з_hex(z["колір_основний"].get("hex")), V.слово_крамниці(ч[0])
    if lab is not None and ск and not чужий_кадр(z.get("фото"), сп.get(o.get("магазин") or o["id"].split("@")[-1]) or {}):
        т[ск["ім"]].setdefault(_файл_фото(z["фото"]), CS.lch(lab))
нові, мало = {}, []
for сл, в in V.ЛЕКСИКОН.items():
    if сл in V.МЕТАЛИ:
        continue
    нв, лч = V.вікно_з_вжитку(list(т.get(сл, {}).values()), в)
    if нв is None:
        continue
    if "огорта" not in лч:
        мало.append("%s %d" % (сл, лч["дизайнів"] - лч["поза_дугою"]))
    if tuple(нв) != tuple(в):
        нові[сл] = нв
        if "--таблиця" in sys.argv:
            print(' %-15s %-27s # %d: нейтр. %d (+%d поза дугою), поза дугою %d, викидів %d; %s%s' % (
                '"%s":' % сл, "%s," % (нв,), лч["дизайнів"], лч["нейтральних"], лч["нп_поза_дугою"],
                лч["поза_дугою"], лч["викидів"],
                "огорта L%d–%d C%d–%d" % лч["огорта"] if "огорта" in лч else "межі лексикону",
                ", тон %d–%d" % лч["дуга_вжитку"] if лч["дуга_вжитку"] else ""))
print("ФАКТ · дизайнів у вжитку %d (слів %d); вікно вжитку ширше за лексикон — %d слів; таблиця verify.ВЖИТОК %s" % (
    sum(len(x) for x in т.values()), len(т), len(нові), "збігається" if нові == {к: tuple(v) for к, v in V.ВЖИТОК.items()}
    else "РОЗХОДИТЬСЯ: %s" % sorted(set(нові.items()) ^ set((к, tuple(v)) for к, v in V.ВЖИТОК.items()))))
print("ФАКТ · слова, чиї межі L*/C* лишились лексиконові (< %d дизайнів у дузі), — дуга в них однаково з вжитку: %s"
      % (V.ВЖИТОК_МІН, ", ".join(мало)))
