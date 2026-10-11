# -*- coding: utf-8 -*-
"""КОЛІР-АКЦЕНТ (рядки 4651, 4652). (1) Суд N образів стенда (сід 7, як `відношення_одне_4650.py -о`): «правило:сила» K-COL-02,
K-ACC-01, K-COL-05, K-PAL-04/05/15, K-COMP-05, K-CRA-02 і речі кожної сироти K-COL-05 default (колір виміру). (2) Пул того самого стенда, виміряні кольорові речі (не K-COL-06) з L* < 26: чи вони акцент K-COL-05 (`колір_річ.акцент_меж`, ISCC-NBS). (3) Пари пулу руки 1, обидва
виміри, C* 4–8 × C* ≥ 20, де сектор кола (без певності) не дає «той самий тон»: частка same_hue «так» (лише через ΔH*). Код без `акцент_меж` (ДО) —
(2) пропускається. Запуск із джерела/: python3 проби/акцент_база_4651.py [-о 600]"""
import json, random, sys, warnings, collections as K; warnings.filterwarnings("ignore"); sys.path.insert(0, "."); sys.path.insert(0, "проби")
import pal_вердикт as ПВ, bridge as B, стенд_знімок as СЗ, colorspace as cs, колір_річ as КР, колір_образу as КО, колір_відношення as КВ
N = int(sys.argv[sys.argv.index("-о") + 1]) if "-о" in sys.argv else 0
ПР, (вх, r, _, _) = ("K-COL-02", "K-ACC-01", "K-COL-05", "K-PAL-04", "K-PAL-05", "K-PAL-15", "K-COMP-05", "K-CRA-02"), ПВ.стенд(гілка=0, намір="statement")
к, rnd, С, Сир, зі0 = r["кандидати"], random.Random(7), K.Counter(), K.Counter(), {x["id"]: x for x in B.каталог_останнього_пакета()}
for n in range(N):
    ід = [rnd.choice(к[с])["id"] for с in ("верх", "низ", "сукня", "верхній_шар", "взуття", "сумка", "шарф", "пояс", "сережки")
          if к.get(с) and с not in (("верх", "низ") if n % 2 else ("сукня",)) and rnd.random() < 0.7]
    зн, вм = ПВ.знахідки(вх, ід); зз, кд = [z for z in зн if z.get("правило") in ПР], dict(zip(вм["вердикт"]["образи"][0]["речі"], (x["id"] for x in вм["речі"])))
    С.update(z["правило"] + ":" + str(z.get("сила")) for z in зз)
    Сир.update(cs.hex_з_lab(зі0[і]["lab"]) for z in зз if z["правило"] == "K-COL-05" and z.get("сила") == "default" for і in map(кд.get, z.get("речі") or ()) if зі0.get(і, {}).get("lab"))
N and print("(1) суд %d образів: %s" % (N, " · ".join("%s %d" % кв for кв in sorted(С.items()))))
N and print("    речі сиріт K-COL-05 default (колір: разів):", ", ".join("%s: %d" % кв for кв in Сир.most_common(14)))
Т = {cs.hex_з_lab(x["lab"]): (с, КР.акцент_меж(x), x.get("назва", "")[:34]) for с, xs in к.items() for x in map(зі0.get, (y["id"] for y in xs))
     if hasattr(КР, "акцент_меж") and x and x.get("lab") and КР.не_вимір(x) is None and cs.lch(x["lab"])[0] < 26 and not КО.нейтраль(tuple(x["lab"]))}
вх0, бачені, П = json.load(open("стенд_вх.json", encoding="utf-8")), set(), K.Counter()
for назва in ("офіс·18°C", "дощ·ресторан·вечір", "весілля·гість", "спека·парк"):
    кк = json.loads(B.виклик("запити", json.dumps(dict(вх0, сценарій=dict(СЗ.СЦЕНАРІЇ[назва]), випадок=назва), ensure_ascii=False)))["кандидати"]
    зі = {x["id"]: x for x in B.каталог_останнього_пакета()}
    рр = [(с, зі[x["id"]]) for с, xs in кк.items() for x in xs if зі.get(x["id"]) and зі[x["id"]].get("lab") and КР.не_вимір(зі[x["id"]]) is None]
    for i, (с1, x) in enumerate(рр):
        for с2, y in рр[i + 1:]:
            if с1 == с2 or (x["id"], y["id"]) in бачені: continue
            бачені |= {(x["id"], y["id"]), (y["id"], x["id"])}
            a, b = sorted((x, y), key=lambda t: cs.lch(t["lab"])[1])
            if not (4 <= cs.lch(a["lab"])[1] <= 8 <= 20 <= cs.lch(b["lab"])[1]): continue
            ра, рб, б = КР.запис_кольору(a), КР.запис_кольору(b), КВ.ВІКНА_ΔH
            КВ.ВІКНА_ΔH = {}; коло = КВ.вердикт(КВ.сила(ра, рб, "same_hue", False)); КВ.ВІКНА_ΔH = б
            коло != "так" and П.update(["пар", "same_hue " + КВ.вердикт(КВ.сила(ра, рб, "same_hue")), "tonal " + КР.відношення(a, b, "tonal")])
for h, (с, в, нм) in sorted(Т.items(), key=lambda t: cs.lch(cs.hx(t[0]))[0]): print("(2) %s L*%4.1f C*%4.1f h%5.1f %-11s акцент %-8s %s" % ((h,) + tuple(cs.lch(cs.hx(h))) + (с, в, нм)))
print("(3) пари C* 4–8 × C* ≥ 20, сектор кола — не «так»: %d; same_hue «так» %d (%.1f %%), tonal «так» %d" % (П["пар"], П["same_hue так"], 100 * П["same_hue так"] / max(1, П["пар"]), П["tonal так"]))
