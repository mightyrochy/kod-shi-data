"""Крок 21, п.1: чи годиться місцю кругового середнього тону (`колір_простір_риси.кут_розсіяння`) усереднення в OKLab.
Для 9 жінок стенда (`аудит/проби/жінки/ж*.json`) рахує розсіяння тону рис ансамблю `регіони` (CIELAB-тон, вага —
площа): чинне (одиничні вектори) і через середнє OKLab (R = |Σw·ab_ok| / Σw·C_ok). Друкує обидва й «темп_напругу»."""
import sys, os, json, math, glob
sys.path.insert(0, "джерела")
import колір_простір_риси as Р
from колір_простір_перетворення import to_oklab, lch, hx

ОРИГІНАЛ = Р.кут_розсіяння
записи = []
def ловець(hs, ваги=None):
    записи.append((list(hs), list(ваги or [1.0] * len(hs))))
    return ОРИГІНАЛ(hs, ваги)
Р.кут_розсіяння = ловець

def sig(x, c=22., w=12.):
    return round(1 / (1 + math.exp(-(x - c) / w)), 2)

розх = 0
for ф in sorted(glob.glob("аудит/проби/жінки/ж*.json")):
    сирі = json.load(open(ф, encoding="utf8"))
    F = {}
    for анг, укр in (("skin", "шкіра"), ("hair", "волосся"), ("eyes", "очі")):
        hh = сирі[анг] if isinstance(сирі[анг], list) else [сирі[анг]]
        лаби = [hx(h) for h in hh]
        L, a, b = (sum(x[i] for x in лаби) / len(лаби) for i in range(3))
        F[укр] = dict(L=L, a=a, b=b, rel_C=0.3)
    записи.clear()
    р = Р.регіони(F)
    if not записи:
        print(os.path.basename(ф), "ансамблю нема"); continue
    hs, ваги = записи[-1]
    од = ОРИГІНАЛ(hs, ваги)
    # OKLab: потрібні самі точки — беремо центри рис з ансамблю (через ті самі тони й хроми CIELAB рис)
    точки = [(F[н]["L"], F[н]["a"], F[н]["b"]) for н in ("шкіра", "волосся", "очі")]
    ok = [to_oklab(t) for t in точки]
    S = sum(ваги)
    A = sum(w * o[1] for o, w in zip(ok, ваги)) / S
    B = sum(w * o[2] for o, w in zip(ok, ваги)) / S
    Cm = sum(w * math.hypot(o[1], o[2]) for o, w in zip(ok, ваги)) / S
    R = math.hypot(A, B) / Cm if Cm else 0.0
    окл = round(math.degrees((-2 * math.log(max(R, 1e-9))) ** 0.5), 1)
    розх += sig(од) != sig(окл)
    print(os.path.basename(ф), "тони", [round(h) for h in hs], "ваги", [round(w, 2) for w in ваги],
          "| одиничні σ", од, "→ напруга", sig(од), "| OKLab σ", окл, "→ напруга", sig(окл))
print("жінок, де напруга розходиться:", розх)
