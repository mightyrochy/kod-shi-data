# -*- coding: utf-8 -*-
"""Рядок 142: колір коду проти кадру картки — ДО (каталог main, код без `фід_варіант`, тобто main) і ПІСЛЯ (гілка).
«Суперечить» — сім'я слова моделі з кадру, який показує картка, ≠ сім'ї кольору запису (`колір_назва`).
Запуск: cd джерела && python3 проби/foto_kolir_142.py"""
import collections, gzip, os, subprocess, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_каталог as FK, фід_збагачення as FZ, verify as V
сире = subprocess.run(["git", "show", "44bc13f:каталог_повний.xml.gz"], capture_output=True, check=True).stdout
open("/tmp/каталог_142_до.xml", "wb").write(gzip.decompress(сире))
зб, сім = FZ.читати_збагачення(), lambda н: V.сім_я_слова((V.слово_крамниці(н or "") or {}).get("ім"))
def міра(кат):
    по = collections.defaultdict(collections.Counter)
    for r in кат:
        з = зб.get(r["id"])
        if FZ._збагачення_придатне(з) and not r.get("чуже_фото"):
            по[r["магазин"]]["n"] += 1; по[r["магазин"]]["≠"] += сім(r["колір_назва"]) not in (None, V.сім_я_слова(FZ.колір_збагачення(з)[0]))
    return по
після = FK._прочитати_каталог(feed.каталог_на_диску(), 0)["каталог"]
справжня, FK.слово_варіанта = FK.слово_варіанта, lambda *а: None
до = FK._прочитати_каталог(feed.каталог_на_диску(перевага="/tmp/каталог_142_до.xml"), 0)["каталог"]
FK.слово_варіанта = справжня
мд, мп = міра(до), міра(після)
print("ФАКТ · записів %d → %d; спорів кольору %d → %d; з кадром картки %d → %d" % (
    len(до), len(після), sum(1 for r in до if r.get("колір_спір")), sum(1 for r in після if r.get("колір_спір")),
    sum(c["n"] for c in мд.values()), sum(c["n"] for c in мп.values())))
print("ФАКТ · колір коду суперечить кадру картки: %d → %d" % (sum(c["≠"] for c in мд.values()), sum(c["≠"] for c in мп.values())))
for м in ("sunwin-store.com", "wearme.ua", "maxa.ua", "sarahberlin.com", "bella-bicchi.com", "favoriteshoes.com.ua", "rito.ua"):
    print("   %-21s записів з кадром %4d · суперечить %3d → %3d · згода %3d%% → %3d%%" % (
        м, мп[м]["n"], мд[м]["≠"], мп[м]["≠"], 100 - 100 * мд[м]["≠"] // мд[м]["n"], 100 - 100 * мп[м]["≠"] // мп[м]["n"]))
вар = collections.Counter((r["колір_варіант"]["джерело"], r["магазин"]) for r in після if r.get("колір_варіант"))
print("ФАКТ · слово крамниці для запису змінено: %d · %s" % (sum(вар.values()), dict(вар.most_common())))
за_ід = {r["id"]: r for r in після}
for і in ("ж-02157@maxa.ua", "ж-05028@maxa.ua", "ж-00047@sunwin-store.com", "ж-02566@sunwin-store.com", "ж-04578@wearme.ua", "ж-00559@sarahberlin.com"):
    р = за_ід[і]; в = р.get("колір_варіант") or {}
    print("ФАКТ · %s: поле %r → колір %r (%s)" % (і, в.get("поле"), р["колір_назва"], в.get("джерело")))
