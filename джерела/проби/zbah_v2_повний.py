# -*- coding: utf-8 -*-
"""Проба повного прогону v2: що вже лежить у `каталог_збагачення_v2.json`.

Факт, не вердикт: скільки речей пройшло, чия маска, скільки записів ВІЗЬМЕ ФІД
(`feed._збагачення_придатне`: впевненість ≥ 0.5 і слово з ЛЕКСИКОНУ) і на чому
падають ті, що падають. Файл росте на ходу — пробу можна кликати посеред прогону.
Інший файл — першим аргументом (нею ж міряна проба 30 речей).
"""
import collections, io, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ)
import feed as F

шлях = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ТУТ, "каталог_збагачення_v2.json")
if not os.path.exists(шлях):
    print("файла нема: %s — прогін ще не писав" % шлях)
    raise SystemExit(0)
д = json.load(io.open(шлях, encoding="utf-8"))
ок = [з for з in д.values() if "помилка" not in з]
збої = [з for з in д.values() if "помилка" in з]
беру = [з for з in ок if F._збагачення_придатне(з.get("запис") or {})]
ні = [з for з in ок if not F._збагачення_придатне(з.get("запис") or {})]
доля = lambda n: 100.0 * n / max(len(д), 1)
print("речей %d · збоїв %d (%.1f %%) · виміряно %d · фід візьме %d (%.1f %%)"
      % (len(д), len(збої), доля(len(збої)),
         sum(1 for з in ок if (з.get("вимір") or {}).get("кластери")), len(беру), доля(len(беру))))
print("маска за джерелом: %s"
      % dict(collections.Counter((з.get("маска") or {}).get("джерело") or "—" for з in ок)))
print("спір вимір↔модель %d · другий колір %d · поправка експозиції %d"
      % (sum(1 for з in ок if з.get("спір")),
         sum(1 for з in ок if (з.get("запис") or {}).get("колір_другий")),
         sum(1 for з in ок if "експозиція" in ((з.get("маска") or {}).get("чому") or ""))))
print("пройшли, але фід не візьме: %d (нема кольору %d, впевненість < 0.5 %d)"
      % (len(ні), sum(1 for з in ні if not (з.get("запис") or {}).get("колір_основний")),
         sum(1 for з in ні if ((з.get("запис") or {}).get("впевненість") or 0) < 0.5)))
for причина, n in collections.Counter(з["помилка"][:60] for з in збої).most_common(4):
    print("  збій ×%-5d %s" % (n, причина))
крамниці = collections.Counter(з.get("магазин") for з in збої)
print("крамниць зі збоями %d: %s" % (len(крамниці),
      ", ".join("%s ×%d" % (м, n) for м, n in крамниці.most_common(6))))
