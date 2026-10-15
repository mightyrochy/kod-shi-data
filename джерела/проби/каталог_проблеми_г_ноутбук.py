# -*- coding: utf-8 -*-
"""Рядки 2500, 3352 (реєстр 5616, клас Г10): збагачення з фото і кадри живуть окремо від жнив — на ноутбуці, своїми прогонами.
Факт: id каталогу проти записів `каталог_збагачення`, `каталог_кадри`, `каталог_показ`: покриття, сироти (запис є,
речі нема), версії й дати знімання, записи з помилкою. Запуск: python3 джерела/проби/каталог_проблеми_г_ноутбук.py"""
import collections, gzip, json, os, re                                         # noqa: E401
К = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
Д = os.path.join(К, "джерела")
xml = gzip.open(os.path.join(К, "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
ід = {"%s@%s" % (і, м) for і, м in re.findall(r'<offer id="([^"]+)".*?<param name="магазин">([^<]*)<', xml, re.S)}
зб = json.load(gzip.open(os.path.join(Д, "каталог_збагачення.json.gz"), "rt", encoding="utf-8"))
кд = json.load(gzip.open(os.path.join(Д, "каталог_кадри.json.gz"), "rt", encoding="utf-8"))
пк = json.load(gzip.open(os.path.join(Д, "каталог_показ.json.gz"), "rt", encoding="utf-8"))
print("каталог: %d речей" % len(ід))
for ім, ключі in (("збагачення", set(зб)), ("кадри", set(кд["записи"])), ("показ: адреси", set(пк.get("адреси") or {})),
                  ("показ: без_показу", set(пк.get("без_показу") or {}))):
    print("  %-18s записів %5d · з них речі каталогу %5d (%4.1f %%) · сиріт %d" % (ім, len(ключі), len(ключі & ід),
          100 * len(ключі & ід) / len(ід), len(ключі - ід)))
вер = collections.Counter((з.get("версія"), (з.get("знято") or "")[:10]) for з in зб.values() if isinstance(з, dict))
print("збагачення за версією й датою: %s" % sorted(вер.items(), key=lambda т: -т[1])[:6])
пом = sum(1 for з in зб.values() if isinstance(з, dict) and з.get("помилка"))
print("збагачення з помилкою: %d · модель: %s" % (пом, collections.Counter(з.get("модель") for з in зб.values()
      if isinstance(з, dict)).most_common(3)))
print("кадри: %s · показ: речей %s, знято %s" % ({к: кд["мета"].get(к) for к in ("знято", "записів", "кадрів")},
      пк.get("речей"), пк.get("знято")))
