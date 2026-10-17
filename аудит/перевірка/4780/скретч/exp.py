# -*- coding: utf-8 -*-
"""Скретч: вердикт «річ у дузі ролі» ДО (CIELAB + запас 10) проти кандидатів вікна кола."""
import json, sys, os, math, pickle, random, collections as K
sys.path.insert(0, "/home/user/kod-shi-data/джерела"); os.chdir("/home/user/kod-shi-data/джерела")
import bridge as B, colorspace as cs, колір_річ as КР, колір_відношення as КВ, палітра_схеми as ПС
SP = "/tmp/claude-0/-home-user-kod-shi-data/9a5eb989-d513-548d-aefc-237879e686bd/scratchpad/"
if os.path.exists(SP + "кат.pkl"):
    кат = pickle.load(open(SP + "кат.pkl", "rb"))
else:
    вх = json.load(open("стенд_вх.json", encoding="utf-8"))
    B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    кат = [r for r in B.каталог_останнього_пакета() if КР.межі_кольору(r) and КР.не_вимір(r) is None and КР.нейтраль_меж(r) == "ні"]
    кат = [dict(id=r["id"], lab=tuple(r["lab"]), назва=r.get("назва"), фото=(r.get("фото") or [None])[0], слот=r.get("слот")) for r in кат]
    pickle.dump(кат, open(SP + "кат.pkl", "wb"))
MT = {tuple([k.split("|")[0], int(k.split("|")[1])]): v for k, v in json.load(open(SP + "munsell_h.json")).items()}
ГУЕ = sorted({k[0] for k in MT}, key=lambda H: MT[(H, 5)][1])

def h_ref(h, L):
    """Тон CIELAB при L*≈51 того самого тону Манселла (лінії сталого тону)."""
    V = min(max(L / 10.0, 1.0), 9.0); v0 = int(math.floor(V)); v1 = min(v0 + 1, 9); t = V - v0
    hv = [(MT[(H, v0)][1] + t * (((MT[(H, v1)][1] - MT[(H, v0)][1] + 180) % 360) - 180)) % 360 for H in ГУЕ]
    h5 = [MT[(H, 5)][1] for H in ГУЕ]
    n = len(ГУЕ)
    for i in range(n):
        a, b = hv[i], hv[(i + 1) % n]; span = (b - a) % 360; x = (h - a) % 360
        if x <= span:
            f = x / span if span else 0; a5, b5 = h5[i], h5[(i + 1) % n]
            return (a5 + f * ((b5 - a5) % 360)) % 360
    return h

def м_поз(h, L):
    """Положення тону Манселла 0..40 (крок 2.5) для тону CIELAB h на світлоті L."""
    V = min(max(L / 10.0, 1.0), 9.0); v0 = int(math.floor(V)); v1 = min(v0 + 1, 9); t = V - v0
    hv = [(MT[(H, v0)][1] + t * (((MT[(H, v1)][1] - MT[(H, v0)][1] + 180) % 360) - 180)) % 360 for H in ГУЕ]
    n = len(ГУЕ)
    for i in range(n):
        a, b = hv[i], hv[(i + 1) % n]; span = (b - a) % 360; x = (h - a) % 360
        if span < 90 and x <= span:
            return (i + (x / span if span else 0)) % n
    return 0.0

def м_h(поз, L):
    """Тон CIELAB положення Манселла `поз` на світлоті L (обернене до м_поз)."""
    V = min(max(L / 10.0, 1.0), 9.0); v0 = int(math.floor(V)); v1 = min(v0 + 1, 9); t = V - v0
    hv = lambda H: (MT[(H, v0)][1] + t * (((MT[(H, v1)][1] - MT[(H, v0)][1] + 180) % 360) - 180)) % 360
    i = int(поз) % len(ГУЕ); f = поз - int(поз); a, b = hv(ГУЕ[i]), hv(ГУЕ[(i + 1) % len(ГУЕ)])
    return (a + f * ((b - a) % 360)) % 360

def кут(a, b):
    d = abs(a - b) % 360; return min(d, 360 - d)

def сила(lab, ц_h, п_w, k, корекція):
    L, C, h = cs.lch(lab)
    if корекція == 16:
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h)); dL = кут(h, ц_h)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        теплі = тепло(h) >= math.cos(math.radians(75)) and тепло(ц_h) >= math.cos(math.radians(75))
        d = max(dL, dw) if (теплі and C >= 34.0) else dL
        sa = КВ.у_вікні(d, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        if not теплі: return sa
        W = 2 * 34.0 * math.sin(math.radians(п_w) / 2)
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dL) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5)
        return max(sa, sh)
    if корекція in (14, 15):
        import колір_простір_риси as КП
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
        dL = кут(h, ц_h); dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        d = max(dL, dM) if корекція == 14 else dL
        sa = КВ.у_вікні(d, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        м = math.cos(math.radians(75))
        if not (тепло(h) >= м and тепло(ц_h) >= м): return sa
        W = 2 * 34.0 * math.sin(math.radians(п_w) / 2)
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(d) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5)
        return max(sa, sh)
    if корекція in (12, 13):
        import колір_простір_риси as КП
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
        dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        sa = КВ.у_вікні(dM, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        м = math.cos(math.radians(75))
        ті, тц = тепло(h), тепло(ц_h)
        гейт = (ті >= м and тц >= м) if корекція == 12 else ((ті >= м and тц >= м) or (ті <= -м and тц <= -м))
        р = КР.запис_кольору(dict(lab=lab)); τ = max(КВ.певність_тону(р)[0], 1e-3)
        W = 2 * 34.0 * math.sin(math.radians(п_w) / 2) / τ
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dM) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5) * гейт
        return max(sa, sh)
    if корекція == 11:
        import колір_простір_риси as КП
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
        dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        sa = КВ.у_вікні(max(dw, dM), (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        тепла = тепло(h) >= math.cos(math.radians(75)) and тепло(ц_h) >= math.cos(math.radians(75))
        р = КР.запис_кольору(dict(lab=lab)); τ = max(КВ.певність_тону(р)[0], 1e-3)
        W = п_w * (0.6 if тепла else 0.2) / τ
        dH = 2 * C * math.sin(math.radians(dM) / 2)
        sh = КВ.у_вікні(dH, (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5)
        return max(sa, sh)
    if корекція in (9, 10):
        import колір_простір_риси as КП
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
        dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        sa = КВ.у_вікні(max(dw, dM), (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        ті, тц = тепло(h), тепло(ц_h)
        гейт = (ті > 0 and тц > 0) if корекція == 9 else (ті * тц > 0)
        dH = 2 * C * math.sin(math.radians(dM) / 2)
        sh = КВ.у_вікні(dH, (0, п_w * 0.6, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5) * гейт
        return max(sa, sh)
    if корекція in (7, 8):
        dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
        sa = КВ.у_вікні(dw, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        ті, тц = тепло(h), тепло(ц_h)
        гейт = (ті > 0 and тц > 0) if корекція == 8 else (ті * тц > 0)
        dH = 2 * C * math.sin(math.radians(кут(h, ц_h)) / 2)
        sh = КВ.у_вікні(dH, (0, п_w * 0.6, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dw, (0, 90, False), 5) * гейт
        return max(sa, sh)
    if корекція in (5, 6):
        import колір_простір_риси as КП
        dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        W = 2 * 34.0 * math.sin(math.radians(п_w) / 2)
        sa = КВ.у_вікні(dM, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        тепло = lambda hh: math.cos(math.radians(cs.у_коло_художника(hh) - 30.0))
        тт = (тепло(h), тепло(ц_h))
        гейт = min(0.5 + 0.5 * math.tanh(4 * т) for т in тт) if корекція == 5 else max(0.0, min(1.0, 0.5 + 0.5 * math.tanh(4 * тт[0] * (1 if тт[1] > 0 else -1))))
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dM) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dM, (0, 90, False), 5) * гейт
        return max(sa, sh)
    if корекція == 4:
        import колір_простір_риси as КП
        dM = кут(КП.тон_манселла(h), КП.тон_манселла(ц_h))
        W = 2 * 34.0 * math.sin(math.radians(п_w) / 2)
        sa = КВ.у_вікні(dM, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dM) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dM, (0, 90, False), 5)
        return max(sa, sh)
    if корекція == 3:
        import колір_простір_риси as КП
        from реєстр_правил import C as РС
        м = КП.тон_манселла(h); мц = КП.тон_манселла(ц_h)
        dM = кут(м, мц)
        sa = КВ.у_вікні(dM, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dM) / 2), (0, п_w * k, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dM, (0, 90, False), 5)
        буре = (L < 25 or L < 40) and C <= РС["warm_neutral"][2] and max(L - 3, 28) <= h <= РС["warm_neutral"][1]
        if буре and 28 <= ц_h <= 88:
            return 1.0
        return max(sa, sh)
    if корекція == 2:
        dM = кут(м_поз(h, L) * 9.0, м_поз(ц_h, 51.0) * 9.0)
        sa = КВ.у_вікні(dM, (0, п_w, False), КВ.СІГМА_МЕЖІ)
        sh = КВ.у_вікні(2 * C * math.sin(math.radians(dM) / 2), (0, п_w * k, False), КВ.СІГМА_ΔH) * КВ.у_вікні(dM, (0, 90, False), 5)
        return max(sa, sh)
    if корекція: h = h_ref(h, L)
    dw = кут(cs.у_коло_художника(h), cs.у_коло_художника(ц_h))
    sw = КВ.у_вікні(dw, (0, п_w, False), КВ.СІГМА_МЕЖІ)
    dH = 2 * C * math.sin(math.radians(кут(h, ц_h)) / 2)
    чв = КВ.у_вікні(dw, (0, КВ.МЕЖА_БЛИЗЬКИХ, False), КВ.СІГМА_МЕЖІ)
    sh = КВ.у_вікні(dH, (0, п_w * k, False), КВ.СІГМА_ΔH) * чв
    return max(sw, sh)

def ролі():
    """[(схема, роль, центр h, пів CIELAB)] — 12 якорів × схеми."""
    out = []
    for i in range(12):
        h0 = cs.з_кола_художника(30.0 * i)
        for сх, з in ПС.СХЕМИ.items():
            for роль, д in з["тон"](h0).items():
                if isinstance(д, tuple):
                    пів = ((д[1] - д[0]) % 360) / 2; ц = (д[0] + пів) % 360
                    out.append((сх, роль, round(ц, 1), round(пів, 1), i))
    return sorted(set(out))

if __name__ == "__main__":
    k = float(sys.argv[1]); корекція = int(sys.argv[2]); поріг = float(sys.argv[3]) if len(sys.argv) > 3 else КВ.КІНЕЦЬ_ЗГАСАННЯ
    РР = ролі(); Л = K.Counter(); ЗМ = []
    for (сх, роль, ц, пів, i) in РР:
        for x in кат:
            L, C, h = cs.lch(x["lab"])
            до = кут(h, ц) <= пів + 10
            пс = сила(x["lab"], ц, пів, k, корекція) >= поріг
            Л[(до, пс)] += 1
            if до != пс: ЗМ.append((сх, роль, ц, пів, x["id"], до, пс))
    print("k=%s корекція=%s поріг=%s:" % (k, корекція, поріг), {"%s→%s" % (a, b): n for (a, b), n in sorted(Л.items())})
    pickle.dump(ЗМ, open(SP + "зм_%s_%d.pkl" % (k, корекція), "wb"))
