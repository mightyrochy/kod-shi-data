#!/usr/bin/env python3
"""Перелік проходу (наряд `Запис-речі-прохід-сцен`, п.1): речі, що потрапили в пули запитів складання сцен приймання
зі звіту `аудит/звіти/стилістка-вибір-з-пулу/рядки.csv.gz` і мають однозначний ід каталогу. Першими — ті, чий колір у пулі
невідомий (`н_hex`=1 хоч в одному запиті), далі решта. Вихід: `дані/перелік.json`. Запуск з кореня: python3 -I <цей файл>"""
import csv, gzip, json
from collections import defaultdict
from pathlib import Path
К = Path(__file__).resolve().parents[4]
ряд = list(csv.DictReader(gzip.open(К / "аудит/звіти/стилістка-вибір-з-пулу/рядки.csv.gz", "rt", encoding="utf-8")))
запити, невід, без_ід = defaultdict(set), set(), defaultdict(int)
for р in ряд:
    if not р["ід"]: без_ід[р["запит"].split("/")[0]] += 1; continue
    ід = р["ід"].split("@")[0]; запити[ід].add(р["запит"].split("/")[0])
    if р["н_hex"] == "1": невід.add(ід)
пор = sorted(запити, key=lambda і: (і not in невід, і))
вих = {"речей": len(пор), "з_невідомим_кольором_у_пулі": len(невід),
       "ситуації_з_ід": sorted({с for в in запити.values() for с in в}),
       "рядків_без_ід_за_ситуацією": dict(без_ід), "речі": [{"ід": і, "невідомий": і in невід, "ситуації": sorted(запити[і])} for і in пор]}
(К / "аудит/проби/запис-речі-прохід-сцен/дані/перелік.json").write_text(json.dumps(вих, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print({к: в for к, в in вих.items() if к != "речі"})
