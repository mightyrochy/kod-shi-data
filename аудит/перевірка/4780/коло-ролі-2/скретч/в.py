# -*- coding: utf-8 -*-
"""Скретч: ДО (тверда дуга CIELAB ±пів+10, як суд на main) проти варіантів вікна; змінені вердикти каталогу."""
import sys, os, math, pickle, random, collections as K
SP = os.path.dirname(os.path.abspath(__file__)) + "/"
os.chdir("/home/user/kod-shi-data/джерела"); sys.path.insert(0, ".")
import colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС, колір_простір_риси as КП
кат = pickle.load(open(SP + "кат.pkl", "rb"))
def кут(a, b):
    d = abs(a - b) % 360; return min(d, 360 - d)
def ролі():
    ор = ПС._дуга; ПС._дуга = lambda h, п: ("R", round(h % 360, 1), п)
    out = {}
    for i in range(12):
        h0 = cs.з_кола_художника(30.0 * i)
        for сх, з in ПС.СХЕМИ.items():
            for роль, д in з["тон"](h0).items():
                if isinstance(д, tuple): out.setdefault((д[1], д[2]), (сх, роль))
    ПС._дуга = ор
    return out
РОЛІ = ролі()
ТП = КВ.ТЕПЛИЙ_ПОЛЮС
def тепло(h): return math.cos(math.radians(cs.у_коло_художника(h) - ТП))
def сила(L, C, h, ц, пів, в):
    """в: dict(шкала='lab'|'mun', σ, cref (ΔH* опора, 0 — без), обсяг='all'|'warm'|'earth', σΔ)."""
    if в["шкала"] == "mun":
        мц = КП.тон_манселла(ц); мп = (КП.тон_манселла((ц + пів) % 360) - КП.тон_манселла((ц - пів) % 360)) % 360 / 2
        d = кут(КП.тон_манселла(h), мц); п = мп
    else:
        d = кут(h, ц); п = пів
    σ = в["σ"]
    if в.get("край"):
        e = math.degrees(2 * math.asin(min(1.0, в["край"] / (2 * max(C, 1e-6)))))
        σ = max(5.0, min(10.0, e) / 1.6449)
    if в.get("шум"):
        τ = КВ.певність_тону(dict(L=(L, L), C=(C, C), дуга=(h, h)))[0] if в.get("τ") else 1.0
        σ = min(math.hypot(σ, math.degrees(в["шум"] / max(C * τ, 1e-6))), в.get("стеля", 99))
    с = КВ.у_вікні(d, (0, п, False), σ)
    if в.get("коридор"):
        if 45 <= h <= 115 and 45 <= ц <= 115 and C <= 34:
            W = 2 * в["коридор"] * math.sin(math.radians(п) / 2)
            с = max(с, КВ.у_вікні(2 * C * math.sin(math.radians(d) / 2), (0, W, False), в.get("σΔ", 1.0)))
    if в.get("буре"):
        б = lambda hh: КВ._буре(dict(L=(L, L), C=(C, C), дуга=(hh, hh), коло=(cs.у_коло_художника(hh),) * 2))[0] >= 0.5
        if б(h) and б(ц): с = 1.0
    if в.get("крайΔ"):
        e = max(0.0, кут(h, ц) - п); ок = True
        if в.get("обсяг") == "коридор": ок = 45 <= h <= 115 and 45 <= ц <= 115 and C <= 34
        if ок: return max(с, КВ.у_вікні(2 * C * math.sin(math.radians(e) / 2), (0, в["край"], False), в.get("σΔ", 1.0)))
        return с
    if not в["cref"]: return с
    ок = True
    if в["обсяг"] == "warm": ок = тепло(h) >= КВ.МЕЖА_ТЕПЛИХ and тепло(ц) >= КВ.МЕЖА_ТЕПЛИХ
    if в["обсяг"] == "earth": ок = в["земля"][0] <= h <= в["земля"][1] and в["земля"][0] <= ц <= в["земля"][1]
    if not ок: return с
    W = 2 * в["cref"] * math.sin(math.radians(п) / 2)
    dl = кут(h, ц)
    пр = КВ.у_вікні(2 * C * math.sin(math.radians(dl) / 2), (0, W, False), в.get("σΔ", КВ.СІГМА_ΔH)) * КВ.у_вікні(dl, (0, 90, False), 5)
    return max(с, пр)
def точки(x):
    м = КР.межі_кольору(x)
    if КР.не_вимір(x) is None:
        L, C, h = cs.lch(x["lab"]); return [(L, C, h)]
    if м[4] is None: return None
    hs = КР._тони_дуги((м[4][0] % 360, м[4][1] % 360), [])  or [м[4][0], м[4][1]]
    lo, hi = м[4][0] % 360, м[4][1] % 360; span = (hi - lo) % 360
    hs = [(lo + span * k / 8) % 360 for k in range(9)]
    return [((м[0] + м[1]) / 2, c, h) for h in hs for c in (м[2], м[3])]
def вердикт(тт, f):
    if тт is None: return "невідомо"
    вв = [f(*т) for т in тт]
    return "так" if all(вв) else "ні" if not any(вв) else "невідомо"
def зміни(в, поріг=КВ.КІНЕЦЬ_ЗГАСАННЯ):
    ЗМ = []
    for (ц, пів), (сх, роль) in РОЛІ.items():
        for x in кат:
            тт = точки(x)
            до = вердикт(тт, lambda L, C, h: кут(h, ц) <= пів + 10)
            пс = вердикт(тт, lambda L, C, h: сила(L, C, h, ц, пів, в) >= поріг)
            if до != пс:
                L, C, h = cs.lch(x["lab"]) if x.get("lab") else (0, 0, 0)
                ЗМ.append(dict(ід=x["id"], lab=tuple(x["lab"]) if x.get("lab") else None, фото=(x.get("фото") or [None])[0],
                               слово=КР.не_вимір(x) is not None, ц=ц, пів=пів, сх=сх, роль=роль, до=до, пс=пс, L=L, C=C, h=h))
    return ЗМ
def зведення(ЗМ):
    к = K.Counter()
    for з in ЗМ:
        т = "тепл" if тепло(з["h"]) >= КВ.МЕЖА_ТЕПЛИХ else "хол"
        к[(з["до"] + "→" + з["пс"], т, "C<15" if з["C"] < 15 else "C<34" if з["C"] < 34 else "C34+", "сл" if з["слово"] else "вим")] += 1
    return sorted(к.items(), key=lambda kv: -kv[1])
