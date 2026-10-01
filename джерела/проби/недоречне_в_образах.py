# -*- coding: utf-8 -*-
"""Наряд ЖП-а (01.10): чи бере ЖИВА стилістка недоречну річ, коли в пулі є доречна. Мірило — той самий
`композитор_придатні.нижче_смуги`, що відсіває пул (#486), але тут ним міряють ВІДПОВІДЬ моделі, не пул.
Запуск: python3 джерела/проби/недоречне_в_образах.py <тека VIDPOVIDI> (поруч — звіт.txt або сцена.txt зі сценою)."""
import os, sys, re, json, glob, gzip, collections
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."); sys.path.insert(0, Д); os.chdir(Д)
import feed as F; F.каталог_на_диску("каталог_повний.xml")
import фід_каталог as ФК, фід_слот as ФС, композитор_придатні as КП
ТЕКА = os.path.abspath(sys.argv[1]); ID = re.compile(r"#\d+·\d+")
def читати(ш):
    т = (gzip.open if ш.endswith(".gz") else open)(ш, "rt", encoding="utf-8").read(); і = т.index("── ВІДПОВІДЬ")
    п = т[т.index("\n") + 1:і].strip()
    return (json.loads(п) if п.startswith("{") else {}), п, т[т.index("\n", і) + 1:]
def файли(мітка): return sorted(glob.glob(os.path.join(ТЕКА, "seed*_" + мітка + "*.txt*")), key=lambda ш: int(re.search(r"seed\d+_(\d+)_", ш).group(1)))
звіт = next(open(ш, encoding="utf-8").read() for ш in (os.path.join(ТЕКА, "..", "звіт.txt"), os.path.join(ТЕКА, "..", "сцена.txt")) if os.path.exists(ш))
сцен = json.loads(re.search(r'"сценарій":\s*(\{[^{}]*\})', звіт).group(1)); lo, hi, _ = КП._ФОРМ.смуга_ошатності(сцен)
за = collections.defaultdict(list)
for r in ФК._прочитати_каталог("каталог_повний.xml", 0)["каталог"]: за[(ФС.назва_для_людини(r), r.get("ціна"))].append(r)
пакети = [читати(ш) for ш in файли("ПАКЕТ_V1")]; ру1 = max(пакети, key=lambda x: len(x[0]["style_rules"]))   # рука 2 = рука 1 без правил
пул = {р["n"]: за.get((р["name"], р.get("price"))) or [] for р in ру1[0]["pool"]}
def вирок(н):   # (слот, код нижче_смуги | None); різні записи під однією назвою й ціною — береться перший
    рр = пул.get(н) or [{}]; return рр[0].get("слот"), КП.нижче_смуги(рр[0], lo) if рр[0] else None
в_смузі = collections.Counter(вирок(н)[0] for н in пул if вирок(н)[1] is None and пул[н])
print("сцена %s · смуга нагоди %s–%s · пул %d речей, з них нижче смуги %d" % (сцен, lo, hi, len(пул), sum(1 for н in пул if вирок(н)[1])))
def образ(мітка, id_, речі):
    нев = [(н, вирок(н)) for н in речі if вирок(н)[1]]
    print("  %-10s %d/%d нижче смуги%s" % (мітка, len(нев), len(речі), "".join("\n      %s «%s» · слот %s · %s · доречних того слота в пулі: %d" % (н, next(p["name"] for p in ру1[0]["pool"] if p["n"] == н)[:45], с, к, в_смузі[с]) for н, (с, к) in нев)))
print("РУКА 1 · складання (10 образів):"); [образ(о["id"], о["id"], о["items"]) for о in json.loads(ру1[2])["outfits"]]
ру2 = min(пакети, key=lambda x: len(x[0]["style_rules"])) if len(пакети) > 1 else ру1
def схожість(в, ру):   # образи, яких склав вибір, — ремонт образів складання; рука 1 ↔ рука 2 розрізняються тим, чиї образи ближчі
    return sum(max(len(set(х["n"] for х in о["your_outfit"]["items"]) & set(с["items"])) / max(1, len(с["items"])) for с in json.loads(ру[2])["outfits"]) for о in в["verdict"])
вибори = [читати(ш) for ш in файли("ВЕРДИКТ_V1_ВИБІР")]; в1 = max(вибори, key=lambda в: схожість(в[0], ру1) - схожість(в[0], ру2))
обр = json.loads(в1[2])["chosen"]; о = next(о["your_outfit"] for о in в1[0]["verdict"] if о["your_outfit"]["id"] == обр)
print("РУКА 1 · обраний образ %s (з %d образів ремонту):" % (обр, len(в1[0]["verdict"]))); образ("обраний", обр, [х["n"] for х in о["items"]])
