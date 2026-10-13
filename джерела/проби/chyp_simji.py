# -*- coding: utf-8 -*-
"""Скільки чипів-основ у кожній сім'ї і чи лишився хоч один без сім'ї.

Факт, який вирішує розкладку екрана палітри: групи мусять бути непорожні й
покривати ВЕСЬ ряд, інакше «групування за сім'ями» ховає частину вибору.
Прогін: cd джерела && python3 проби/chyp_simji.py
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as cs, bridge as B

F = cs.features(cs.hx("#f0d5c8"), cs.hx("#4a4644"), cs.hx("#6b8cae"))
о = B._основи(F)
ряди = {"рекомендовані": о["нейтралі"] + о["кольори"], "не рекомендовані": о["інші"]}
for ім, ряд in ряди.items():
    л = collections.Counter(str(x.get("сім_я")) for x in ряд)
    print("%-18s усього %3d · сімей %d · %s"
          % (ім, len(ряд), len(л), ", ".join("%s:%d" % кв for кв in л.most_common())))
усі = ряди["рекомендовані"] + ряди["не рекомендовані"]
без = [x["ключ"] for x in усі if x.get("сім_я") is None]
print("без сім'ї: %d%s" % (len(без), (" — " + "; ".join(без[:6])) if без else ""))
по_смугах = collections.Counter(
    (x["ключ"].split("·")[-1], str(x.get("сім_я"))) for x in усі)
for смуга in ("приглушені", "середні", "насичені"):
    с = sorted({с for (сму, с) in по_смугах if сму == смуга})
    print("смуга %-11s сімей на екрані: %d · %s" % (смуга, len(с), ", ".join(с)))
