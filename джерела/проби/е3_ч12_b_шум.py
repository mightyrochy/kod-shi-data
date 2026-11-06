# -*- coding: utf-8 -*-
"""Е3-одна-величина ч12 (рішення 06.11 «факт замість межі», п.3): похибка b* кольору речі з фото — з повтору.

Вхід — `каталог_кадри.json.gz`, пари кадрів одного кольорового варіанта (той самий корінь імені, що в
`н4_друге_фото_de.py`): |Δb*| між двома кадрами ОДНІЄЇ речі. Медіана — `Δb_шум_фото` (та сама статистика, що
`ΔE_шум_фото`); окремо — пари, де обидва кадри нейтралі (C* < `neutral_C`, гілка боку b* у `нейтраль`).
Запуск із теки `джерела`: `python3 проби/е3_ч12_b_шум.py`."""
import sys, pathlib, gzip, json, re, itertools, statistics
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import колір_річ as КР
from реєстр_правил import C
корінь_файлу = lambda ф: re.sub(r"[_-]?\d+$", "", re.sub(r"_[0-9a-f]{8}-[0-9a-f-]{20,}$", "",
                                                            ф.rsplit("/", 1)[-1].rsplit(".", 1)[0]))
все, нейтр = [], []
for кадри in json.load(gzip.open(pathlib.Path(__file__).resolve().parent.parent / "каталог_кадри.json.gz",
                                 "rt", encoding="utf-8"))["записи"].values():
    гр = {}
    for к in кадри:
        т = КР.точка_кольору(к)
        if т:
            гр.setdefault(корінь_файлу(к["файл"]), []).append(tuple(т))
    for g in гр.values():
        for a, b in itertools.combinations(g, 2):
            все.append(abs(a[2] - b[2]))
            if max(КР.lch(a)[1], КР.lch(b)[1]) < C["neutral_C"]:
                нейтр.append(abs(a[2] - b[2]))
for ім, с in (("усі пари", все), ("обидва кадри C* < neutral_C", нейтр)):
    с.sort()
    print("ФАКТ · |Δb*| між двома кадрами однієї речі, %s: пар %d, медіана %.1f, p90 %.1f, максимум %.1f"
          % (ім, len(с), statistics.median(с), с[int(0.9 * len(с))], с[-1]))
print("реєстр Δb_шум_фото:", C.get("Δb_шум_фото"))
