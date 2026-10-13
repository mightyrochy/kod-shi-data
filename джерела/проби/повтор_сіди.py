# -*- coding: utf-8 -*-
"""Д-1: та сама сцена на п'ятьох сідах — скільки РІЗНИХ речей бачить модель.

Проба ганяє одну сцену стенда п'ятьма сідами (10 пулів: руки 1 і 2 кожного прогону)
і по слотах друкує: скільки речей було доступно після `відсікти_пул` (найбільше з
десяти прогонів), скільки модель бачить за раз, скільки РІЗНИХ речей дали всі
десять пулів і скільки речей стоїть у ВСІХ десяти — тобто не міняється ніколи.
Прогін: python3 проби/повтор_сіди.py       (~2 хв: п'ять повних збирань)
"""
import collections, itertools, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, pipeline as PL
СІДИ, дост, пули = (1, 7, 42, 4242, 31337), {}, []
_від = PL.відсікти_пул
def _відс(канд, кат, *а, **к):
    р = _від(канд, кат, *а, **к)
    for с, v in (р[0] or {}).items(): дост[с] = max(дост.get(с, 0), len(v))   # найбільше з десяти прогонів
    return р
PL.відсікти_пул = _відс
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), каталог=Ф.каталог_на_диску("каталог_повний.xml"))
for сід in СІДИ:
    json.loads(B.виклик("запити", json.dumps(dict(вх, сід=сід), ensure_ascii=False)))
    пули += [{с: [r.get("id") for r in v] for с, v in p["кандидати"].items()}
             for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")]
print("сцена стенда, сіди %s → %d пулів" % (list(СІДИ), len(пули)))
print("%-14s %9s %8s %8s %9s %9s" % ("слот", "доступно", "за раз", "союз10", "з доступн", "у всіх 10"))
for с in sorted(дост, key=lambda к: -дост[к]):
    лічба = collections.Counter(i for п in пули for i in п.get(с, []))
    за_раз = sum(len(п.get(с, [])) for п in пули) / len(пули)
    print("%-14s %9d %8.1f %8d %8.0f %% %9d" % (с, дост[с], за_раз, len(лічба),
          100.0 * len(лічба) / max(дост[с], 1), sum(1 for v in лічба.values() if v == len(пули))))
всі = collections.Counter(i for п in пули for v in п.values() for i in v)
print("РАЗОМ: доступно %d, за раз %.0f, союз %d (%.0f %% доступного), у всіх 10 пулах %d речей"
      % (sum(дост.values()), sum(sum(len(v) for v in п.values()) for п in пули) / len(пули), len(всі),
         100.0 * len(всі) / sum(дост.values()), sum(1 for v in всі.values() if v == len(пули))))
ж = [len(a & b) / len(a | b) for a, b in itertools.combinations(
     [{i for v in п.values() for i in v} for п in пули], 2)]
print("схожість двох пулів (Жаккар) на %d парах: мін %.2f, медіана %.2f, макс %.2f"
      % (len(ж), min(ж), sorted(ж)[len(ж) // 2], max(ж)))
