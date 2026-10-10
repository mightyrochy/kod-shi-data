# -*- coding: utf-8 -*-
"""КОЛІР-ПРАКТИКИ (рядок 3421; K-COL-11…13): ближні відношення тону — сектор кола (Р2а) ∪ вікно ΔH* практиків (`колір_відношення.ВІКНА_ΔH`).
Пул руки 1 (4 сцени стенда), пари акцентів різних слотів, обидва — вимір, C* ≥ 12. ДО — `ВІКНА_ΔH = {}` (лише коло), ПІСЛЯ — як є.
(а) «same_hue» ДО → ПІСЛЯ за ділянкою пари; (б) бежеві й бурі (обидва тони CIELAB 50–75°); (в) протилежний підтон: обидва C* < 25,
один ≤5YR (h < 57, рожевий), другий ≥10YR (h > 72, жовтий) — не мають злитись у відлуння; (г) кемел ↔ темно-синій: комплемент і
тепле ↔ холодне; (д) кадри однієї речі (`каталог_кадри`): p90 розкиду тону між фото — на колі проти ±15° і в ΔH* проти ±3.
Запуск із джерела/: python3 проби/колір_практики.py"""
import json, gzip, math, itertools, sys, collections as K; sys.path.insert(0, ".")
import bridge as B, colorspace as cs, стенд_знімок as СЗ, колір_річ as КР, колір_відношення as КВ
вх0, Л, П, Д = json.load(open("стенд_вх.json", encoding="utf-8")), K.Counter(), {}, K.defaultdict(K.Counter)
def до(f):
    б, КВ.ВІКНА_ΔH = КВ.ВІКНА_ΔH, {}
    try: return f()
    finally: КВ.ВІКНА_ΔH = б
def ділянка(L, C):  return "насичені C≥40" if C >= 40 else "темні L<35" if L < 35 else "світлі L≥75" if L >= 75 else "майже нейтр. C<20" if C < 20 else "приглушені 20–40"
for назва in ("офіс·18°C", "дощ·ресторан·вечір", "весілля·гість", "спека·парк"):
    к = json.loads(B.виклик("запити", json.dumps(dict(вх0, сценарій=dict(СЗ.СЦЕНАРІЇ[назва]), випадок=назва), ensure_ascii=False)))["кандидати"]
    зі = {r["id"]: r for r in B.каталог_останнього_пакета()}
    ак = [(с, зі[r["id"]], cs.lch(зі[r["id"]]["lab"])) for с, xs in к.items() for r in xs if зі.get(r["id"]) and зі[r["id"]].get("lab") and not КР.не_вимір(зі[r["id"]])]
    ак = [t for t in ак if t[2][1] >= 12]
    for (с1, a, ла), (с2, b, лб) in itertools.combinations(ак, 2):
        if с1 == с2: continue
        v0, v1 = (КВ.вердикт(f()) for f in (lambda: до(lambda: КВ.сила(a, b, "same_hue")), lambda: КВ.сила(a, b, "same_hue")))
        дл = " × ".join(sorted((ділянка(ла[0], ла[1]), ділянка(лб[0], лб[1])))); Д[дл].update(("пар", "ДО так" * (v0 == "так"), "ПІСЛЯ так" * (v1 == "так"), "так→ні" * (v0 == "так" != v1)))
        if 50 <= ла[2] <= 75 and 50 <= лб[2] <= 75: Л["(б) беж/бурі: ДО %s → %s" % (v0, v1)] += 1; П.setdefault(v0 + v1, (a, b))
        if max(ла[1], лб[1]) < 25 and min(ла[2], лб[2]) < 57 and max(ла[2], лб[2]) > 72: Л["(в) протилежний підтон: ДО %s → %s" % (v0, v1)] += 1
        кн = sorted((ла, лб), key=lambda t: t[2])
        if 55 <= кн[0][2] <= 85 and 18 <= кн[0][1] <= 45 and 45 <= кн[0][0] <= 80 and 250 <= кн[1][2] <= 300 and кн[1][0] < 35:
            for кл in ("complementary", "warm_cool"): Л["(г) кемел×т.-синій %-13s ДО %s → %s" % (кл, КВ.вердикт(до(lambda: КВ.сила(a, b, кл))), КВ.вердикт(КВ.сила(a, b, кл)))] += 1
for дл, ц in sorted(Д.items()): print("  (а) %-38s пар %5d · same_hue «так» ДО %5d → ПІСЛЯ %5d · так→ні %d" % (дл, ц["пар"], ц["ДО так"], ц["ПІСЛЯ так"], ц["так→ні"]))
for к_, v in sorted(Л.items()): print("  %-66s %6d" % (к_, v))
for k_, (a, b) in П.items(): print("  приклад ДО/ПІСЛЯ %s: %s × %s same_hue %.2f → %.2f" % (k_, cs.hex_з_lab(a["lab"]), cs.hex_з_lab(b["lab"]), до(lambda: КВ.сила(a, b, "same_hue"))[0], КВ.сила(a, b, "same_hue")[0]))
Р = K.defaultdict(list)
for кк in json.load(gzip.open("каталог_кадри.json.gz"))["записи"].values():
    кк = [k for k in кк if k.get("lab") and k.get("слово")]; w = кк and K.Counter(k["слово"] for k in кк).most_common(1)[0][0]
    for p, q in itertools.combinations([k for k in кк if k["слово"] == w], 2):
        (La, Ca, ha), (Lb, Cb, hb) = cs.lch(p["lab"]), cs.lch(q["lab"])
        if abs(La - Lb) <= 10: Р[next(x for x in (4, 8, 12, 16, 20, 30, 40, 999) if min(Ca, Cb) < x)].append((КР.кут_на_колі(ha, hb), 2 * math.sqrt(Ca * Cb) * math.sin(math.radians(abs((ha - hb + 180) % 360 - 180)) / 2)))
p90 = lambda vv: sorted(vv)[int(0.9 * (len(vv) - 1))]
for x, vv in sorted(Р.items()): print("  (д) кадри C*<%3d n=%4d: p90 Δколо %5.1f (вікно ±15) · p90 ΔH* %4.2f (вікно ±3)" % (x, len(vv), p90([v[0] for v in vv]), p90([v[1] for v in vv])))
