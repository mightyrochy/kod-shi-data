# -*- coding: utf-8 -*-
"""ПУЛ-НАМІР (02.10): чи сміливий намір ВИДНО в пулі, який бачить модель складання (рука 1, після бюджету).
3 сцени × intent conventional/statement на каталог_повний, сід стенда: склад пулу на слот (ядро/межа/розрив),
частка не-ядра, слоти з межею, слоти розриву (біля обличчя? — `колір_образу.NEAR_МІН`), розмір промпту складання
(символів), чи доступний полюс «розрив». Прогін: cd джерела && python3 проби/пул_намір.py [сцена…]"""
import json, sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import feed as Ф, bridge as B, колір_образу as КО
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); вх0["каталог"] = Ф.каталог_на_диску("каталог_повний.xml")
СЦЕНИ = dict(вечірка=dict(нагода="вечірка", місце="ресторан", година=19, темп_c=18, дрес_код="cocktail"),
             побачення=dict(нагода="побачення", місце="ресторан", година=19, темп_c=18),
             робота=dict(вх0["сценарій"]))
ГЛ = {"ядро": "c", "на межі": "e", "розрив": "b"}
for сц in (sys.argv[1:] or list(СЦЕНИ)):
    for намір in ("conventional", "statement"):
        р = json.loads(B.виклик("запити", json.dumps(dict(вх0, сценарій=СЦЕНИ[сц], намір=намір), ensure_ascii=False)))
        т = р["руки"]["1"]; п = json.loads(т[т.index("{"):])
        по = {с: collections.Counter(ГЛ.get(r.get("гілка") or "ядро", "?") for r in рч) for с, рч in р["кандидати"].items()}
        вс = sum(по.values(), collections.Counter()); n = sum(вс.values())
        розр = sorted(с for с, к in по.items() if к["b"])
        print("%-9s %-12s пул %3d: ядро %3d · межа %3d · розрив %2d · не-ядро %4.1f%% | слотів з межею %2d/%d | розрив у %s "
              "(біля обличчя: %s) | промпт складання %d симв., пул %s | полюс розрив: %s"
              % (сц, намір, n, вс["c"], вс["e"], вс["b"], 100.0 * (вс["e"] + вс["b"]) / max(1, n),
                 sum(1 for к in по.values() if к["e"]), len(по), розр or "—",
                 [с for с in розр if КО.SLOT_NEAR_FALLBACK.get(с, 1) >= КО.NEAR_МІН] or "ні", len(т),
                 (р.get("стеля") or {}).get("пул_символів"),
                 "недоступний" if "break" in (п.get("poles_unavailable") or []) else
                 ("є речі" if вс["b"] else "нема речей")))
        if намір != "conventional":
            print("    на слот c/e/b:", " ".join("%s %d/%d/%d" % (с, к["c"], к["e"], к["b"]) for с, к in по.items()))
