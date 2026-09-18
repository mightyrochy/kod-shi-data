# -*- coding: utf-8 -*-
"""Речі магазинів, зібраних з домашнього IP, — ЧИ ДОХОДЯТЬ ВОНИ ДО ПУЛУ.

Влиття в каталог доводить лише те, що офери в XML. Питання інше: чи бачить їх
`feed` так само, як 10 770 старих — слот, колір, фото, ціна. Друкує по кожному
новому магазину: оферів у фіді, з них зі слотом (`feed.слот`), з кольором,
з фото, з ціною. Запуск: `cd джерела && python3 проби/zhnyva_нові_магазини.py`."""
import sys, os, pathlib, collections
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
os.chdir(str(pathlib.Path(__file__).resolve().parent.parent))
import feed as F

НОВІ = ("md-fashion.ua", "skripka.com.ua", "theoriginals.com.ua", "staff-clothes.com")
офери = F.читати_yml(F.каталог_на_диску("каталог_повний.xml"))
офери = офери[0] if isinstance(офери, tuple) else офери
по_магазину = collections.defaultdict(list)
for о in офери:
    по_магазину[о.get("магазин")].append(о)

print("каталог: %d оферів, %d магазинів" % (len(офери), len(по_магазину)))
print("%-22s %6s %6s %6s %6s %6s" % ("магазин", "оферів", "слот", "колір", "фото", "ціна"))
усього = 0
for м in НОВІ:
    сп = по_магазину.get(м) or []
    усього += len(сп)
    зі_слотом = sum(1 for о in сп if F.слот(о))
    print("%-22s %6d %6d %6d %6d %6d" % (м, len(сп), зі_слотом,
          sum(1 for о in сп if о.get("колір_назва")), sum(1 for о in сп if о.get("фото")),
          sum(1 for о in сп if о.get("ціна"))))
старі = [о for о in офери if о.get("магазин") not in НОВІ]
ч = lambda сп: (100.0 * sum(1 for о in сп if F.слот(о)) / len(сп)) if сп else 0.0
нові = [о for о in офери if о.get("магазин") in НОВІ]
print("ФАКТ · зі слотом: нові %.1f %% (%d речей), старі %.1f %% (%d речей)"
      % (ч(нові), len(нові), ч(старі), len(старі)))
assert нові, "жодного офера нових магазинів у каталозі"
assert ч(нові) >= ч(старі) - 10, "нові речі втрачають слот частіше за старі більш ніж на 10 в.п."
