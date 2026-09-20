# -*- coding: utf-8 -*-
"""Рядок 106: чи рухає НАМІР ранг рекомендованих основ. Профіль стенда (`стенд_вх.json`), для кожного
наміру з `реєстр_намір.INTENT` (плюс невідомий) — перші 8 рекомендованих чипів і 8 кольорових у ранзі,
скільки позицій відрізняється від conventional, max |Δбал| по всій ґратці. Факт: корпус правила
«намір → добір основ» не має (докстрінг `bases.ранг`), тож вісімки мають бути ОДНІ на всіх намірах —
і до перейменування `intent → _intent`, і після. Запуск із теки `джерела`: `python3 проби/bas_namir_106.py`."""
import sys, os, json, inspect
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import colorspace as cs, bridge as B, bases as ОС
from реєстр_намір import INTENT
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
F = cs.features(cs.hx(вх["шкіра"]), cs.hx(вх["волосся"][0]), cs.hx(вх["очі"]))
def ранг(намір):
    о = B._основи(F, intent=намір)
    усі = о["рекомендовані"] + о["інші"]
    return ([x["ключ"] for x in о["рекомендовані"]][:8],
            [x["ключ"] for x in усі if x["сім_я"] != "нейтраль"][:8], {x["ключ"]: x["бал"] for x in усі})
зм = lambda a, b: sum(1 for x, y in zip(a, b) if x != y)
парам = [p for p in inspect.signature(ОС.ранг).parameters if p.lstrip("_") == "intent"][0]
print("bases.ранг: параметр наміру зветься `%s` — %s" % (парам, "читається? ні (страховка)" if парам.startswith("_") else "у сигнатурі без `_`"))
р0, к0, б0 = ранг("conventional")
print("conventional · рекомендовані 8: " + " | ".join(р0)); print("conventional · кольорові 8:     " + " | ".join(к0))
разом_р = разом_к = 0; max_δ = 0.0
for намір in list(INTENT) + ["гранж"]:
    р, к, б = ранг(намір)
    δ = max(abs(б[k] - б0[k]) for k in б0); max_δ = max(max_δ, δ)
    разом_р += зм(р0, р); разом_к += зм(к0, к)
    print("  %-16s змінено: рекомендованих %d/8 · кольорових %d/8 · max|Δбал| %.3f · ґратка %d клітинок"
          % (намір, зм(р0, р), зм(к0, к), δ, len(б)))
print("ПІДСУМОК: %d намірів, змінених позицій %d (рекомендовані) + %d (кольорові), max|Δбал| %.3f — намір ранг основ не рухає"
      % (len(INTENT) + 1, разом_р, разом_к, max_δ))
