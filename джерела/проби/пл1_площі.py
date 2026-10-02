# -*- coding: utf-8 -*-
"""ПЛ-1 (рядок 690): скільки образів стенда (руки 1–2) мають `джерело_площі` в усіх речей і що судять K-COL-02/05, K-COMP-03.
Запуск: python3 проби/пл1_площі.py <ZVIT_OUT рв6_стенда.txt>   (профіль РВ-6: 168 см, 98/92/74/99; сценарій «дощ·ресторан·вечір»)"""
import sys, os, json, collections
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import bridge as B, composer as КМ, fit as ПС, outfit as O, pipeline as PL, colorspace as cs, gate_площі as G
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json")), сценарій=G.СЦЕНАРІЇ["офіс·18°C"], випадок="пл1")))
кат = {x["id"]: x for x in B.каталог_останнього_пакета()}
T = ПС.тіло(168.0, dict(плечі=98., груди=92., талія=74., стегна=99.))
F = cs.features(cs.hx("#deb295"), cs.hx("#f1dbaa"), cs.hx("#759087"))
ПРАВИЛА = ("K-COL-01", "K-COL-02", "K-COL-05", "K-COL-06", "K-COMP-03", "площа")
def знахідки(o):
    if isinstance(o, dict):
        if o.get("правило") in ПРАВИЛА: yield o
        for x in o.values(): yield from знахідки(x)
    elif isinstance(o, list):
        for x in o: yield from знахідки(x)
ч, без_виміру, джерела, прав = collections.Counter(), collections.Counter(), collections.Counter(), collections.Counter()
for в in json.load(open(sys.argv[1], encoding="utf-8"))["прогони"][0]["вердикти"]:
    if в["рука"] not in ("1", "2"): continue
    for к in в["етапи"]["виклики"]:
        for о in к.get("образи_кроку") or []:
            речі = [КМ._у_річ(dict(кат[i]), о["слоти_н"][n], T) for i, n in zip(о["ід"], о["речі_н"])]
            ч["образів"] += 1
            без_виміру.update((r["слот"], r.get("край_джерело")) for r in речі if not O.край_виміряний(r))
            вих = PL.перевірити_образ(F, речі, тіло=T, **G.СЦЕНАРІЇ["дощ·ресторан·вечір"])
            ч["джерело_площі в усіх речей"] += all(r.get("джерело_площі") for r in речі)
            джерела.update(str(sorted({r.get("джерело_площі") or "—" for r in речі})) for _ in [0])
            прав.update((z["правило"], z.get("регістр"), z.get("сила"), bool(z.get("сила_нп"))) for z in знахідки(вих["стани"]))
print("ФАКТ ·", dict(ч), "· походження площ:", dict(джерела))
print("ФАКТ · речі без виміряного краю (слот, край_джерело):", dict(без_виміру))
print("ФАКТ · знахідки (правило, регістр, сила, є сила_нп) за всі стани:", dict(прав))
