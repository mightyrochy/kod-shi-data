# -*- coding: utf-8 -*-
"""Одна стеля для смуги хроми людини й кандидата палітри (рядок 1977).

Смуга людини — rel_C рис на Cmax(sRGB); кандидат нормувався на Cmax поверхні (Pointer).
Проба: на стендовому профілі ранг `сила` кольорових чипів зі змішаною стелею (ДО) проти
однієї sRGB (ПІСЛЯ, у коді) — скільки чипів змінили місце. Запуск із `джерела`."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import palettes as PAL, personal_palette as PP, colorspace as cs, bridge as B

вх = json.load(open(pathlib.Path(__file__).resolve().parent.parent / "стенд_вх.json", encoding="utf-8"))
F = B._features(вх)[0]
П_рис = PP.палітра(F, source="uncontrolled")
к = [c for c in PAL.кольори(PAL.осі(F, "uncontrolled", None), П_рис) if c["h"] is not None]
св, хр = П_рис["світлота"], П_рис["хрома"]
def сила(c, стеля):
    return round(PP.членство(св, c["L"]) * PP.членство(хр, c["C"] / max(1.0, стеля(c["L"], c["h"]))), 3)
до = lambda L, h: cs.c_max_поверхня(L, h)[0]
ранг = lambda f: [c["hex"] for c in sorted(к, key=lambda c: (-сила(c, f), c["hex"]))]
р_до, р_після = ранг(до), ранг(cs.c_max)
зміни = sum(1 for a, b in zip(р_до, р_після) if a != b)
print("смуга хроми людини (rel_C, sRGB): %s · кольорових чипів %d" % (хр["межі"], len(к)))
print("L40 h250: C/Cmax(sRGB)=%.2f проти C/Cmax(Pointer)=%.2f при C=20" % (20 / cs.c_max(40, 250), 20 / до(40, 250)))
змін_сили = sum(1 for c in к if сила(c, до) != сила(c, cs.c_max))
print("сила змінилась у %d чипів; перша п'ятірка ДО %s · ПІСЛЯ %s" % (змін_сили, р_до[:5], р_після[:5]))
print("чипів змінили місце в ранзі сили: %d з %d" % (зміни, len(к)))
у_коді = [c["сила"] for c in PAL.кольори(PAL.осі(F, "uncontrolled", None), П_рис) if c["h"] is not None]
assert sorted(у_коді) == sorted(сила(c, cs.c_max) for c in к), "код рахує силу не тією стелею, що смуга людини"
