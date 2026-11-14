"""Незалежно перелічує повний аркуш кадрів без завантаження каталогу мостом."""
import collections
import gzip
import json
import pathlib
import statistics
import sys

записи = json.load(gzip.open(sys.argv[1]))["записи"]
міряні = {к: [ф for ф in вв if isinstance(ф.get("частка_маски"), (float, int))]
           for к, вв in записи.items()}
print("Записів:", len(записи), "з виміром:", sum(bool(в) for в in міряні.values()),
      "кадрів із виміром:", sum(map(len, міряні.values())))
різниці = []
класи = 0
for кадри in міряні.values():
    групи = collections.defaultdict(list)
    for кадр in кадри:
        шлях = pathlib.PurePosixPath(кадр["файл"].lower())
        групи[(шлях.parent.name, шлях.stem)].append(кадр)
    for група in групи.values():
        if len(група) > 1:
            різниці.append(max(к["частка_маски"] for к in група) - min(к["частка_маски"] for к in група))
            класи += len({к.get("клас") for к in група}) > 1
кв = lambda в, п: round(sorted(в)[round(п * (len(в) - 1))], 3)
print("Повторів фото:", len(різниці), "p90 різниці:", кв(різниці, .9), "різний клас:", класи)
for клас in ["на_моделі", "ціла_річ", "деталь"]:
    групи = [[ф["частка_маски"] for ф in вв if ф.get("клас") == клас] for вв in міряні.values()]
    групи = [г for г in групи if len(г) > 1]
    розмахи = [max(г) - min(г) for г in групи]
    print(клас, len(групи), "розмах p50/p90:", кв(розмахи, .5), кв(розмахи, .9))
