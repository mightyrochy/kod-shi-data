"""Рядок 2090: стеля хроми поверхні при L* < 15 не вища за вузол L* 15 (монотонність на краю сітки)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import colorspace as cs
пор = 0
for h in range(0, 360, 10):
    c15 = cs.c_max_поверхня(15, h)[0]
    for L in (5, 10, 12, 14):
        c = cs.c_max_поверхня(L, h)[0]
        if c > c15 + 1e-9:
            пор += 1
print("порушень (стеля при L*<15 вища за вузол L*15), 36 відтінків × 4 світлоти:", пор)
for h in (100, 115):
    print("h", h, [(L, round(cs.c_max_поверхня(L, h)[0], 1)) for L in (10, 15, 20)])
