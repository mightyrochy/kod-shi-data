# -*- coding: utf-8 -*-
"""Рядок 49 БЕКЛОГ: чипи з роллю «нейтраль» (`bridge._основи`, поле `нейтралі`,
той самий Cstar<12 поділ, що й `bases.за_родом`) — чи є вони нейтраллю за
власним означенням коду (`колір_образу.нейтраль`, K-COL-06: ахромат або
тепла/холодна нейтральна сім'я)? Запуск із теки `джерела`:
`python3 проби/nejtral_chypy.py`."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bridge as B, colorspace as cs, колір_образу as КО

d = json.load(open("стенд_вх.json", encoding="utf-8"))
F, T, зріст, kw = B._збірка(d)
осн = B._основи(F)

поза = []
print("Чипи з роллю «нейтраль» (рекомендовані): %d" % len(осн["нейтралі"]))
for x in осн["нейтралі"]:
    lab = cs.hx(x["hex"])
    L, C, h = cs.lch(lab)
    вердикт = КО.нейтраль(lab)
    статус = вердикт if вердикт else "ПОЗА ОЗНАЧЕННЯМ"
    if not вердикт:
        поза.append(x)
    print("  %-40s L%.0f C*%.1f h%.0f  %s  %s" % (x["ключ"], L, C, h, x["hex"], статус))

print("\nнейтралей поза означенням: %d" % len(поза))
