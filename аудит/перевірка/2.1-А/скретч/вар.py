# -*- coding: utf-8 -*-
"""Скретч 2.1-А: пари річ × дуга з силою зараз (`сила_в_дузі`) і варіантами; кеш — вар.pkl. Запуск із джерела/."""
import sys, json, glob, math, pickle, os, collections as K
sys.path.insert(0, ".")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС, palettes as ПЛ, річ_з_фото as РФ
SP = os.path.dirname(os.path.abspath(__file__)) + "/"
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); B.виклик("запити", json.dumps(вх0, ensure_ascii=False))
речі = [r for r in B.каталог_останнього_пакета() if КР.межі_кольору(r) and КР.нейтраль_меж(r) == "ні"]
ролі = {}
for i in range(12):
    for сх, з in ПС.СХЕМИ.items():
        for роль, д in з["тон"](cs.з_кола_художника(30.0 * i)).items():
            if isinstance(д, tuple): ролі.setdefault(д, (сх, роль))
жінки = [вх0] + [dict(вх0, шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) for Ж in
                 (json.load(open(f, encoding="utf-8")) for f in sorted(glob.glob("../аудит/проби/жінки/ж*.json")))]
П = [ПЛ.палітра_практична(B._features(вх)[0]) for вх in жінки]
вікна = {tuple(д): ("вікно", с) for п in П for с, дд in п["вікна"]["сім_ї"].items() if с != "очі" for д in дд}
очі = []
for вх in жінки:
    L, C, h = cs.lch(cs.hx(вх["очі"])); очі.append((вх["очі"], ПЛ.дуга_очей(h), ПЛ.колір_очей(dict(L=L, C=C, h=h))))
пари = []
for x in речі:
    р = КР.запис_кольору(x); L, C, h = cs.lch(tuple(x["lab"]))
    for д, (мн, ім) in list(ролі.items()) + list(вікна.items()):
        с = КВ.сила_в_дузі(р, д)
        if с[1] < 0.005: continue
        ц, пів = КВ._параметри_дуги(д)
        пари.append(dict(ід=x["id"], вим=КР.не_вимір(x) is None, L=L, C=C, h=h, lab=tuple(x["lab"]), д=д, мн=мн, ім=ім, ц=ц, пів=пів, с=с,
                         в05=КР.у_дугах_кола(x, [д], 0.5), в005=КР.у_дугах_кола(x, [д], КВ.КІНЕЦЬ_ЗГАСАННЯ),
                         фото=(x.get("фото") or [None])[0], кч=РФ._дуга_членство(h, [д]) if КР.не_вимір(x) is None else None))
очні = []
for x in речі:
    if КР.не_вимір(x) is not None: continue
    р = КР.запис_кольору(x); L, C, h = cs.lch(tuple(x["lab"]))
    for hx_, д, з in очі:
        очні.append(dict(ід=x["id"], L=L, C=C, h=h, lab=tuple(x["lab"]), очі=hx_, д=д, кч=РФ._дуга_членство(h, [д]),
                         суд=КР.у_сім_ї_очей(x, з), сила=КВ.сила_сім_ї_очей(р, з), фото=(x.get("фото") or [None])[0]))
pickle.dump(dict(пари=пари, очні=очні, n=len(речі)), open(SP + "вар.pkl", "wb"))
print("речей", len(речі), "пар із силою > 0.005", len(пари), "очних", len(очні))
