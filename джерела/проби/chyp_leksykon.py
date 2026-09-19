# -*- coding: utf-8 -*-
"""Рядок 43 БЕКЛОГ: чи лягає hex кожного чипа ґратки (`bridge._ґратка_основ`)
у вікно ТОГО САМОГО слова лексикону (`verify.ЛЕКСИКОН`), яким його підписано
(`palettes._назва`)? Окремо — три смуги хроми «червоної» сім'ї.
Запуск із теки `джерела`: `python3 проби/chyp_leksykon.py`."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bridge as B, verify as V, colorspace as cs


def вікна(lab):
    """Усі імена ЛЕКСИКОНУ, чиє вікно містить точку (не лише перше, як `_назва`)."""
    L, C, h = cs.lch(lab)
    ім = []
    for н, (Llo, Lhi, Clo, Chi, д) in V.ЛЕКСИКОН.items():
        if not (Llo <= L <= Lhi and Clo <= C <= Chi):
            continue
        if д is None:
            ім.append(н); continue
        a, b = д
        if (a <= h <= b) if a <= b else (h >= a or h <= b):
            ім.append(н)
    return ім


осн, порядок = B._ґратка_основ()
бреше_підпис, у_вікні, разом = 0, 0, 0
чуже = {}
for ключ in порядок:
    hex_, ім = осн[ключ]
    разом += 1
    свої = вікна(cs.hx(hex_))
    if ім in свої:
        у_вікні += 1
    else:
        бреше_підпис += 1
        чуже[ім] = чуже.get(ім, 0) + 1

print("Усього чипів: %d · у вікні власного слова: %d · поза (найближче): %d"
      % (разом, у_вікні, бреше_підпис))
print("Слова-підписи, що НЕ в своєму вікні (топ-5):",
      sorted(чуже.items(), key=lambda kv: -kv[1])[:5])

print("\nЧервона сім'я (тепла, L≈50) за трьома смугами хроми:")
for ключ in порядок:
    ч = ключ.split("·")
    if ч[0] != "червоний" or ч[1] != "тепла":
        continue
    hex_, ім = осн[ключ]
    L, C, h = cs.lch(cs.hx(hex_))
    свої = вікна(cs.hx(hex_))
    print("  %-10s L%s C*%.0f h%.0f  %s  вікна: %s" % (ч[3], ч[2], C, h, hex_, свої))
