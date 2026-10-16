# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «дублікати й варіанти». ФАКТ на чистому каталозі:
# (1) групи «та сама крамниця + та сама назва показу» і скільки в них зайвих оферів;
# (2) з них — повні двійники (той самий колір крамниці: розмір окремим офером чи той самий товар
# двома адресами) і кольорові варіанти; (3) group_id: груп і речей у них; (4) мовні двійники,
# яких чистка не бачить: та сама крамниця й той самий перший кадр, а назви різні мовою.
import os, re, sys, collections as C
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed, фід_слот as ФС, чистка_каталогу as ЧК
оф = [o for o in feed.читати_yml(sys.argv[1] if len(sys.argv) > 1 else feed.каталог_на_диску())[0]
      if o.get("available") is not False]
гр = C.defaultdict(list)
for o in оф:
    гр[(o["магазин"], ФС.назва_для_людини(o).lower())].append(o)
повт = [г for г in гр.values() if len(г) > 1]
зайві = sum(len(г) - 1 for г in повт)
двійн = sum(len(г) - len({(x.get("колір_назва") or "").lower() for x in г}) for г in повт)
кадр1 = lambda x: ЧК._адреса_кадру((x.get("фото") or [""])[0])
стоїть = C.Counter((o["магазин"], кадр1(o)) for o in оф)        # кадр на ≥ 3 записах — службовий, ключем не є
тойкадр = sum(len(г) - len({кадр1(x) for x in г}) for г in повт
              if all(стоїть[(x["магазин"], кадр1(x))] < 3 for x in г))
print("наявних оферів %d · груп «крамниця+назва» з повтором %d · зайвих оферів %d"
      % (len(оф), len(повт), зайві))
print("  з них з тим самим словом кольору крамниці %d (інше слово — %d) · з тим самим першим кадром %d "
      "(повні двійники) · крамниці %s" % (двійн, зайві - двійн, тойкадр,
                                         dict(C.Counter(г[0]["магазин"] for г in повт).most_common(4))))
g = C.Counter(o.get("group_id") for o in оф if o.get("group_id"))
print("group_id: груп із > 1 офером %d · оферів у них %d"
      % (sum(1 for v in g.values() if v > 1), sum(v for v in g.values() if v > 1)))
кадр = C.defaultdict(list)
for o in оф:
    if o.get("фото"):
        кадр[(o["магазин"], ЧК._адреса_кадру(o["фото"][0]))].append(o)
мова = lambda н: "лат" if not re.search("[а-яіїєґ]", н, re.I) else "кир"
мд = [г for г in кадр.values() if 1 < len(г) <= 3 and len({мова(x["назва"]) for x in г}) > 1]
print("мовних двійників повз чистку (той самий кадр, назва іншою абеткою): %d пар · %s"
      % (len(мд), dict(C.Counter(г[0]["магазин"] for г in мд).most_common(3))))
