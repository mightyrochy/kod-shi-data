# -*- coding: utf-8 -*-
"""КОЛО ТОНУ (наряд 2.14): похибка тону одного виміру — звідки `колір_відношення.ПОХИБКА_ТОНУ`. (а) Кадри однієї речі
(`каталог_кадри.json.gz`): пари кадрів того самого слова, |ΔL*| ≤ 10, обидва C* ≥ 12 — p90 ΔH* за світлотою й хромою;
p90 одного виміру — p90 пари / √2. (б) Каст крамниці: медіана a*, b* вимірів зі словом нейтралі (чорний, сірий, білий,
графіт), крамниці з ≥ 8 такими, — σ між крамницями (те, що додала б пара речей різних крамниць). (в) Що дає похибка на
колі художника: допуск пари двох вимірів однієї хроми за ділянками кола (`колір_відношення._допуск`).
Запуск із джерела/: python3 проби/коло_тону_похибка_214.py"""
import json, gzip, math, itertools, sys, statistics as S, collections as K; sys.path.insert(0, ".")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ
q = lambda vv, p: sorted(vv)[int(p * (len(vv) - 1))]
П = K.defaultdict(list)
for кк in json.load(gzip.open("каталог_кадри.json.gz"))["записи"].values():
    кк = [k for k in кк if k.get("lab") and k.get("слово")]
    w = кк and K.Counter(k["слово"] for k in кк).most_common(1)[0][0]
    for p, r in itertools.combinations([k for k in кк if k["слово"] == w], 2):
        (La, Ca, ha), (Lb, Cb, hb) = cs.lch(p["lab"]), cs.lch(r["lab"])
        if abs(La - Lb) > 10 or min(Ca, Cb) < 12: continue
        dH = 2 * math.sqrt(Ca * Cb) * math.sin(math.radians(abs((ha - hb + 180) % 360 - 180)) / 2)
        L = (La + Lb) / 2
        for к in ("усі", "L*<35" if L < 35 else "L* 35–65" if L < 65 else "L*≥65", "C*<30" if min(Ca, Cb) < 30 else "C*≥30"): П[к].append(dH)
for к, vv in П.items(): print("(а) %-8s пар %4d · ΔH* пари p50 %.2f p90 %.2f · одного виміру p90 %.2f" % (к, len(vv), q(vv, .5), q(vv, .9), q(vv, .9) / math.sqrt(2)))
print("    ПОХИБКА_ТОНУ =", КВ.ПОХИБКА_ТОНУ)
B.виклик("запити", open("стенд_вх.json", encoding="utf-8").read())
м = K.defaultdict(list)
for r in B.каталог_останнього_пакета():
    if КР.не_вимір(r) is None and r.get("lab") and (r.get("колір_назва_крамниці") or r.get("колір_назва")) in ("чорний", "сірий", "білий", "графіт"): м[r["магазин"]].append(r["lab"])
к = [(S.median(t[1] for t in тт), S.median(t[2] for t in тт)) for тт in м.values() if len(тт) >= 8]
print("(б) крамниць %d · каст між крамницями σ a* %.2f b* %.2f · |каст − середній| p90 %.2f" % (len(к), S.pstdev(a for a, _ in к), S.pstdev(b for _, b in к),
      q([math.hypot(a - S.mean(x for x, _ in к), b - S.mean(y for _, y in к)) for a, b in к], .9)))
for Cc in (20, 40, 70):
    рр = [КР.запис_кольору(dict(lab=(55, Cc * math.cos(math.radians(h)), Cc * math.sin(math.radians(h))))) for h in range(0, 360, 15)]
    print("(в) C* %d: допуск пари на колі, ° (тон CIELAB 0, 15, …):" % Cc, " ".join("%.0f" % КВ._допуск(р, р)[1] for р in рр), "· ΔH* %.2f" % КВ._допуск(рр[0], рр[0])[0])
