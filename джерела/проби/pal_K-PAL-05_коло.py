# -*- coding: utf-8 -*-
"""КОЛО-1, рядок 1611: K-PAL-05 впізнає комплемент на колі художника.
Запуск із `джерела`: `python3 проби/pal_K-PAL-05_коло.py` (потрібен повний каталог)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import colorspace as cs
import реєстр_правил as Р
from проби import pal_вердикт as ПВ

вх, _, кат, _ = ПВ.стенд(гілка=0, намір="statement")
гучно = Р.C["hi_C"]
речі = [x for x in кат.values() if x.get("lab") and not x.get("колір_не_вимір") and x.get("слот") in ("верх", "низ", "сукня")]
дані = lambda x: ПВ.lch(кат, x["id"])
кут = lambda a, b: min(abs(a - b) % 360, 360 - abs(a - b) % 360)

def взяти(умова, слот=None):
    return next(x for x in речі if (слот is None or x.get("слот") != слот) and умова(*дані(x), x))

бордо = взяти(lambda L, C, h, x: C >= гучно and 20 <= h <= 40)
хвоя = взяти(lambda L, C, h, x: C >= гучно and 145 <= h <= 170, бордо.get("слот"))
# Стара пара: у CIELAB ≥165°, на колі художника <150° (каталог гучних 190–230° не має — беремо 330°↔150°).
рожева = взяти(lambda L, C, h, x: C >= гучно and 320 <= h <= 350)
зелена = взяти(lambda L, C, h, x: C >= гучно and 140 <= h <= 160 and кут(h, дані(рожева)[2]) >= 165
               and кут(cs.у_коло_художника(h), cs.у_коло_художника(дані(рожева)[2])) < 150,
               рожева.get("слот"))

def судить(a, b):
    зн, _ = ПВ.знахідки(вх, [a["id"], b["id"]])
    return any(z.get("правило") == "K-PAL-05" for z in зн)

assert судить(бордо, хвоя) and not судить(рожева, зелена)
print("ФАКТ · бордо+хвоя — комплемент, K-PAL-05 судить; стару 180°-пару CIELAB — ні")
print("ФАКТ · бордо+хвоя — комплемент, K-PAL-05 судить; стару 180°-пару CIELAB — ні")
