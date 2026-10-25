# -*- coding: utf-8 -*-
"""каталог_сусіди_розбіжності.py — МІРИЛО 1–2 НАРЯДУ 5.4-С НА ФАЙЛІ КОДІВ (без моделі).

У групах сусідів (`каталог_розбір_сусіди.розбити`: крамниця + усі слова, крім кольору й розміру), де щонайменше двох
членів повністю розібрано у файлі кодів `каталог_розбір_коди.json.gz`: таблиця розбіжностей КОД-ПРОТИ-КОДУ за полями
(пари всередині групи; поле — шлях у відповіді). Поля, що залежать від кольору (`color_*`, `pattern`, `veto.*`,
`features`, `decor`), окремо. Потім — `--групи N --сід S`: N випадкових груп для огляду очима (назва, опис, картка
без кольору й розміру, і що різниться між членами).
Запуск: python3 джерела/проби/каталог_сусіди_розбіжності.py [коди.json.gz] [--групи 20] [--сід 1]"""
import argparse
import collections
import gzip
import itertools
import json
import os
import random
import sys
import warnings

warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ТУТ, ".."))
import фід_каталог as ФК                      # noqa: E402
import фід_розбір as ФР                       # noqa: E402
import каталог_розбір as КР                   # noqa: E402
import каталог_розбір_сусіди as С             # noqa: E402

КОЛІРНІ = ("color_", "pattern", "veto.", "features", "decor")


def плоско(в, шлях=""):
    if isinstance(в, dict):
        for к, п in в.items():
            yield from плоско(п, шлях + ("." if шлях else "") + к)
    else:
        yield шлях, json.dumps(в, ensure_ascii=False, sort_keys=True)


def групи_розібраних(коди, офери):
    г = collections.defaultdict(list)
    for o in офери:
        if o["id"] in коди:
            г[(o.get("магазин"), С.розбити(o)[0])].append(o)
    return {к: v for к, v in г.items() if len(v) > 1}


if __name__ == "__main__":
    р = argparse.ArgumentParser()
    р.add_argument("коди", nargs="?", default=os.path.join(ТУТ, "..", "каталог_розбір_коди.json.gz"))
    р.add_argument("--групи", type=int, default=0)
    р.add_argument("--сід", type=int, default=1)
    а = р.parse_args()
    коди = json.load(gzip.open(а.коди))
    офери, _ = ФР.читати_yml(ФК.каталог_на_диску(), показ=False)
    за_ід = {o["id"]: o for o in офери}
    все = collections.defaultdict(list)
    for o in офери:
        все[(o.get("магазин"), С.розбити(o)[0])].append(o)
    г = групи_розібраних(коди, офери)
    пар = 0
    різниці = collections.Counter()
    поля = collections.Counter()
    роди = collections.Counter()
    for члени in г.values():
        for x, y in itertools.combinations(члени, 2):
            пар += 1
            fx, fy = dict(плоско(коди[x["id"]])), dict(плоско(коди[y["id"]]))
            for ш in fx:
                поля[ш] += 1
                if fx[ш] != fy.get(ш):
                    різниці[ш] += 1
                    рід = ("unknown↔not_applicable" if {fx[ш], fy.get(ш)} == {'"unknown"', '"not_applicable"'}
                           else "unknown↔код" if '"unknown"' in (fx[ш], fy.get(ш))
                           else "not_applicable↔код" if '"not_applicable"' in (fx[ш], fy.get(ш))
                           else "код↔код")
                    роди[(ш.startswith(КОЛІРНІ), ш.startswith("evidence."), рід)] += 1
    print("розібрано у файлі: %d · груп сусідів із ≥2 розібраними: %d (членів %d, пар %d)"
          % (len(коди), len(г), sum(len(v) for v in г.values()), пар))
    пара_без = lambda ш: not ш.startswith(КОЛІРНІ)           # noqa: E731
    коди_ = lambda ш: пара_без(ш) and not ш.startswith("evidence.")        # noqa: E731
    цитати = lambda ш: пара_без(ш) and ш.startswith("evidence.")           # noqa: E731
    for назва, відбір in (("НЕКОЛІРНІ КОДИ (без evidence.*)", коди_), ("НЕКОЛІРНІ evidence.* (цитати й джерела, не коди)", цитати),
                          ("КОЛІРНІ (color_*, pattern, veto.*, features, decor)", lambda ш: not пара_без(ш))):
        рядки = [(ш, n) for ш, n in різниці.items() if відбір(ш)]
        усього = sum(n for ш, n in поля.items() if відбір(ш))
        print("\n%s: полів-порівнянь %d, розбіжностей %d (%.2f%%), полів із розбіжністю %d"
              % (назва, усього, sum(n for _, n in рядки), 100 * sum(n for _, n in рядки) / max(усього, 1), len(рядки)))
        for ш, n in sorted(рядки, key=lambda т: -т[1])[:15]:
            print("  %-26s %4d з %d" % (ш, n, поля[ш]))
    print("\nрозбіжності за родом (колірне, evidence, рід → кількість):")
    for (кл, ев, рід), n in sorted(роди.items(), key=lambda т: (т[0][0], т[0][1], -т[1])):
        print("  %-9s %-9s %-20s %d" % ("колірне" if кл else "некол.", "evidence" if ев else "код", рід, n))
    if а.групи:
        вибір = random.Random(а.сід).sample(sorted(г, key=str), min(а.групи, len(г)))
        for і, к in enumerate(вибір, 1):
            члени = г[к]
            o = члени[0]
            print("\n=== група %d · %s · розібраних %d з %d у каталозі" % (і, к[0], len(члени), len(все[к])))
            print("назва:", o.get("назва"))
            print("опис :", (o.get("опис") or "")[:220].replace("\n", " "))
            print("картка без кольору й розміру:", json.dumps(
                {k: v for k, v in КР.вхід(o).get("params", {}).items() if k not in С.ПОЛЯ_КОЛЬОРУ | С.ПОЛЯ_РОЗМІРУ},
                ensure_ascii=False)[:300])
            for m in члени:
                print("  ", m["id"], "колір:", С.розбити(m)[1], "→", коди[m["id"]].get("color_main"),
                      "| тип:", коди[m["id"]].get("item_type"), коди[m["id"]].get("slot"))
            fs = [dict(плоско(коди[m["id"]])) for m in члени]
            печ = [ш for ш in fs[0] if пара_без(ш) and len({f.get(ш) for f in fs}) > 1]
            print("   різні некольорові поля:", печ or "—")
