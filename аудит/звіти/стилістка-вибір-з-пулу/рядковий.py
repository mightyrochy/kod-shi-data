#!/usr/bin/env python3
"""Перевірка стійкості: частка взятого серед усіх рядків пулу (а не лише речей, які бачили ≥5 разів) за відомим/невідомим кольором,
по сценах окремо. Вихід: рядковий.json. Запуск з кореня: python3 -I аудит/звіти/стилістка-вибір-з-пулу/рядковий.py"""
import csv, gzip, json
from collections import defaultdict
from pathlib import Path
ТЕКА = Path(__file__).resolve().parent
рядки = list(csv.DictReader(gzip.open(ТЕКА / "рядки.csv.gz", "rt", encoding="utf-8")))
ТЕ = defaultdict(lambda: [0, 0])
вихід = {}
for розріз, ключ in (("усі рядки", lambda r: "усі"), ("за сценою", lambda r: r["запит"].split("/")[0]),
                     ("за типом (≥200 рядків)", lambda r: r["тип"])):
    acc = defaultdict(lambda: [0, 0, 0, 0])  # відомий: взято, всього; невідомий: взято, всього
    for r in рядки:
        a = acc[ключ(r)]; j = 2 if r["н_hex"] == "1" else 0
        a[j] += int(r["взято"]); a[j + 1] += 1
    вихід[розріз] = {k: dict(відомий=f"{v[0]}/{v[1]}", частка_відомий=round(v[0] / v[1], 3) if v[1] else None,
                              невідомий=f"{v[2]}/{v[3]}", частка_невідомий=round(v[2] / v[3], 3) if v[3] else None)
                     for k, v in sorted(acc.items()) if розріз != "за типом (≥200 рядків)" or v[1] + v[3] >= 200}
(ТЕКА / "рядковий.json").write_text(json.dumps(вихід, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
for k, v in вихід.items():
    print(k)
    for g, x in v.items():
        print("  ", g, x["відомий"], x["частка_відомий"], "|", x["невідомий"], x["частка_невідомий"])
