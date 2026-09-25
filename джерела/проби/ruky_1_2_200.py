# -*- coding: utf-8 -*-
"""ЧИ ПОЛОМКА ПАЛІТРИ ВЗАГАЛІ ЗЛАМАЛА КОЛІР (рядок 200, доповнення №2). (А) пари образів рук 1 і 2 одного
прогону «Ір» за каталогом: спільні речі, сім'ї кольору, середня найближча ΔE76 між речами, шари верху.
(Б) на main, стенд без офісу, її прогулянка, сіди з поломкою «палітра»: куди ламається схема руки 2,
скільки речей пулів рук 1 і 2 спільні (`контроль.пул_спільних`) і скільки рядків брифа різняться.
Запуск: cd джерела && python3 проби/ruky_1_2_200.py"""
import json, sys, pathlib, math
sys.path[:0] = [str(pathlib.Path(__file__).resolve().parent.parent), str(pathlib.Path(__file__).resolve().parent)]
import bridge as B, колір_річ as КР
from sklad_virdyktiv_200 import В
from sud_shem_200 import ПРОГУЛЯНКА, вх0
вх = dict(вх0, паспорт=dict(ПРОГУЛЯНКА, намір="conventional"), вимоги=ПРОГУЛЯНКА["слова"])
for сід in (1, 14, 29, 30, 33):
    r = json.loads(B.виклик("запити", json.dumps(dict(вх, сід=сід), ensure_ascii=False)))
    s = json.dumps(r, ensure_ascii=False); i = s.find('"контроль"')
    кон = json.loads(s[i + 11: s.find("}", i) + 1])
    пул = [sum(len(v) for v in json.loads(r["руки"][h])["пул"].values()) for h in ("1", "2")]
    print("(Б) сід %2d · %s · пул р1 %d / р2 %d · спільних %s · рядків брифа різних %s із %s"
          % (сід, r["поломка"]["що_змінено"], *пул, кон["пул_спільних"], кон["різних"], кон["різних"] + кон["сліпих"]))
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
dE = lambda a, b: math.dist(a["lab"], b["lab"])
for прог in ("0", "3", "4"):
    р = {н: (рука, в, [кат["ж-" + x] for x in с.split()]) for н, (п, рука, в, с) in enumerate(В) if п == прог}
    for н1, (р1, в1, x1) in р.items():
        for н2, (р2, в2, x2) in р.items():
            if р1 == 1 and р2 == 2:
                сп = {a["id"] for a in x1} & {b["id"] for b in x2}
                ср = (sum(min(dE(a, b) for b in x2) for a in x1) + sum(min(dE(b, a) for a in x1) for b in x2)) / (len(x1) + len(x2))
                сім = lambda xs: sorted({КР.сім_я(a["lab"]) for a in xs})
                шари = lambda xs: sum(1 for a in xs if a["слот"] in ("верх", "верхній_шар"))
                print("(А) прогін %s · р1 «%s» ↔ р2 «%s» · спільних речей %d · ΔE76 середня найближча %.0f · шарів верху %d/%d\n"
                      "      сім'ї р1 %s\n      сім'ї р2 %s" % (прог, в1, в2, len(сп), ср, шари(x1), шари(x2), сім(x1), сім(x2)))
