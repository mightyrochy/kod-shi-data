# -*- coding: utf-8 -*-
"""П.3: підлога рекомендації (bases.ПІДЛОГА_РЕКОМЕНДАЦІЇ=0.5) і поділ по смугах
(bridge.py:397-425): порожні смуги, «на волосину» від підлоги, L*-розкид ряду."""
import sys, os, json, statistics as st
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import colorspace as cs, bridge as B

вх = json.load(open("стенд_вх.json", encoding="utf-8"))
ПРОФІЛІ = [
    ("1 середня нейтральна", вх["шкіра"], вх["волосся"][0], вх["очі"]),
    ("2 світла холодна", "#eec2b0", "#e8d5b0", "#8a9bb0"),
    ("3 смаглява тепла", "#96632f", "#3a2a1a", "#4a3222"),
]
см = lambda x: x["ключ"].split("·")[-1]

for назва, шк, вл, оч in ПРОФІЛІ:
    F = cs.features(cs.hx(шк), cs.hx(вл), cs.hx(оч))
    о = B._основи(F, intent="conventional")
    рек, інші = о["рекомендовані"], о["інші"]
    print("\n=== %s: рекомендовано всього %d ===" % (назва, len(рек)))
    for смуга in ("приглушені", "середні", "насичені"):
        n_рек = sum(1 for x in рек if см(x) == смуга)
        топ_ні = max((x for x in інші if см(x) == смуга), key=lambda x: x["бал"], default=None)
        пор = ""
        if n_рек == 0 and топ_ні is not None:
            волосина = 0.5 - топ_ні["бал"] <= 0.05
            пор = " перший невзятий бал=%.3f%s" % (топ_ні["бал"], " ← НА ВОЛОСИНУ" if волосина else "")
        print("  смуга %-11s рекомендованих=%d%s" % (смуга, n_рек, пор))
    L_рек = [x["осі"]["L"] for x in рек]
    L_усі = [x["осі"]["L"] for x in рек + інші]
    if L_рек:
        print("  L* std: рекомендовані=%.1f, уся ґратка=%.1f" % (st.pstdev(L_рек), st.pstdev(L_усі)))
