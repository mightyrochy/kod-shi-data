# -*- coding: utf-8 -*-
"""Скретч: K-PAL-17 ДО (main) → ПІСЛЯ (сила тону — `сила_в_дузі` варіанта а', очі — `сила_сім_ї_очей`) на 10 жінках × виміри."""
import sys, os, json, glob, pickle, collections as K
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP); sys.path.insert(0, ".")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, palettes as ПЛ, річ_з_фото as РФ, ва
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); B.виклик("запити", json.dumps(вх0, ensure_ascii=False))
речі = [r for r in B.каталог_останнього_пакета() if КР.межі_кольору(r) and КР.нейтраль_меж(r) == "ні" and КР.не_вимір(r) is None]
жінки = [вх0] + [dict(вх0, шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) for Ж in
                 (json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob("../аудит/проби/жінки/ж*.json")))]
старе, Л, зм, СТАН = РФ._дуга_членство, K.Counter(), [], {}
for вх in жінки:
    П = ПЛ.палітра_практична(B._features(вх)[0]); L, C, h = cs.lch(cs.hx(вх["очі"])); з = ПЛ.колір_очей(dict(L=L, C=C, h=h))
    очі_дуги = [tuple(д) for д in П["вікна"]["сім_ї"].get("очі") or []]
    for x in речі:
        до = РФ.членство_в_палітрі(x["lab"], П); р = КР.запис_кольору(x); Lx, Cx, hx = cs.lch(tuple(x["lab"]))
        РФ._дуга_членство = lambda hh, дуги: (ва.членство_очей(КВ.сила_сім_ї_очей(р, з)[0]) if [tuple(д) for д in дуги] == очі_дуги and дуги
                                               else ва.членство(max([ва.сила_точки(Cx, hh, tuple(д)) for д in дуги] or [0.0])))
        пс = РФ.членство_в_палітрі(x["lab"], П); РФ._дуга_членство = старе
        Л[(до["стан"], пс["стан"])] += 1; Л[("роль", до["роль"][:6], пс["роль"][:6])] += до["роль"] != пс["роль"]
        if до["стан"] != пс["стан"] or до["роль"] != пс["роль"]:
            зм.append(dict(ід=x["id"], lab=tuple(x["lab"]), L=Lx, C=Cx, h=hx, очі=вх["очі"], фото=(x.get("фото") or [None])[0],
                           до=до, пс=пс))
for k, v in sorted(Л.items(), key=str): print(k, v)
print("змін K-PAL-17", len(зм), "речей", len({z["ід"] for z in зм}))
pickle.dump(зм, open(SP + "зм_17.pkl", "wb"))
