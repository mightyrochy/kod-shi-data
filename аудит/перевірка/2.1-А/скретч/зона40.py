# -*- coding: utf-8 -*-
"""Скретч: 40 пар зони 0.05–0.5 (одна пара на річ, сід) — аркуш «чи річ того самого тону, що роль». Запуск: python3 зона40.py <сід> <мітка> [фільтр]"""
import sys, os, pickle, random, json
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP); import foto
Д = pickle.load(open(SP + "вар.pkl", "rb")); сід, мітка = int(sys.argv[1]), sys.argv[2]
ф = sys.argv[3] if len(sys.argv) > 3 else "True"
кут = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)
з = [p for p in Д["пари"] if p["в05"] != p["в005"] and eval(ф, {}, p)]
по_речі = {}
for p in random.Random(сід).sample(з, len(з)): по_речі.setdefault(p["ід"], p)
вибір = list(по_речі.values())[:40]; рр = []
for p in вибір:
    lo, hi = p["д"]; край = lo if кут(p["h"], lo) < кут(p["h"], hi) else hi
    p["за"] = max(0.0, кут(p["h"], p["ц"]) - p["пів"])
    рр.append(dict(p, край_h=край, центр_h=p["ц"], до=p["в05"], пс=p["в005"],
                   підпис="%s/%s %s h%.0f ц%.0f±%.0f +%.1f° L%.0f C%.0f" % (p["мн"][:6], p["ім"][:4], "в" if p["вим"] else "с", p["h"], p["ц"], p["пів"], p["за"], p["L"], p["C"])))
foto.аркуш(рр, SP + мітка + "_%d.png")
json.dump([{k: v for k, v in р.items() if k not in ("с",)} for р in рр], open(SP + мітка + ".json", "w"), ensure_ascii=False, indent=0, default=list)
print(len(з), "пар у зоні;", len(по_речі), "речей; вибрано", len(рр))
