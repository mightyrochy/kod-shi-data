# -*- coding: utf-8 -*-
"""Скретч: на викликах 300 образів — вердикт ролі ДО (код) і кандидат ПІСЛЯ (Манселл, k, поріг)."""
import sys, os, math, pickle, random, collections as K
SP = "/tmp/claude-0/-home-user-kod-shi-data/9a5eb989-d513-548d-aefc-237879e686bd/scratchpad/"
sys.path.insert(0, "/home/user/kod-shi-data/джерела"); os.chdir("/home/user/kod-shi-data/джерела")
import колір_простір_риси as КП, колір_відношення as КВ, колір_річ as КР, colorspace as cs

def кут(a, b):
    d = abs(a - b) % 360; return min(d, 360 - d)

import exp as E
def сила(lab, дуга, k, без_темн=False):
    L, C, h = cs.lch(lab)
    if k >= 5:
        пів = ((дуга[1] - дуга[0]) % 360) / 2; ц = (дуга[0] + пів) % 360
        return E.сила(lab, ц, round(пів), k, int(k))
    if k == 4:
        м0, м1 = КП.тон_манселла(дуга[0], 51.0), КП.тон_манселла(дуга[1], 51.0)
        пів = ((м1 - м0) % 360) / 2; ц = (м0 + пів) % 360
        d = кут(КП.тон_манселла(h, 51.0), ц); W = 2 * 34.0 * math.sin(math.radians(пів) / 2)
        return max(КВ.у_вікні(d, (0, пів, False), КВ.СІГМА_МЕЖІ),
                   КВ.у_вікні(2 * C * math.sin(math.radians(d) / 2), (0, W, False), КВ.СІГМА_ΔH) * КВ.у_вікні(d, (0, 90, False), КВ.СІГМА_МЕЖІ))
    м0, м1 = КП.тон_манселла(дуга[0], 51.0), КП.тон_манселла(дуга[1], 51.0)
    пів = ((м1 - м0) % 360) / 2; ц = (м0 + пів) % 360
    d = кут(КП.тон_манселла(h, 51.0 if без_темн else L), ц)
    sa = КВ.у_вікні(d, (0, пів, False), КВ.СІГМА_МЕЖІ)
    sh = КВ.у_вікні(2 * C * math.sin(math.radians(d) / 2), (0, пів * k, False), КВ.СІГМА_ΔH) * КВ.у_вікні(d, (0, 90, False), КВ.СІГМА_МЕЖІ)
    return max(sa, sh)

def вердикти(k, поріг, без_темн=False):
    О = pickle.load(open(SP + "о300.pkl", "rb")); out = []
    for n, о in enumerate(О):
        for (ід, lab, дуги, до, слово) in dict.fromkeys(о["виклики"]):
            if слово or до not in ("так", "ні"):
                continue
            x = dict(lab=lab)
            if КР.нейтраль_меж(x) == "так":
                continue
            пс = "так" if max(сила(lab, д, k, без_темн) for д in дуги) >= поріг else "ні"
            out.append((n, ід, lab, дуги, до, пс))
    return О, out

if __name__ == "__main__":
    k, поріг = float(sys.argv[1]), float(sys.argv[2]); бт = len(sys.argv) > 3
    О, В = вердикти(k, поріг, бт)
    Л = K.Counter((в[4], в[5]) for в in В)
    print("k=%s поріг=%s без_темн=%s образів %d вердиктів %d:" % (k, поріг, бт, len(О), len(В)), dict(Л))
    pickle.dump([в for в in В if в[4] != в[5]], open(SP + "кал_%s_%s%s.pkl" % (k, поріг, "_бт" if бт else ""), "wb"))
