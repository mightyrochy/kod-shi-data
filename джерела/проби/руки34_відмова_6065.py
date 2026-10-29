# -*- coding: utf-8 -*-
"""Рядок 6065 · записані пари рук 3–4 (проза OUTFIT_TEXT + її перелік ITEM_LIST, `VIDPOVIDI`) → `bridge.виклик("від_моделі")`,
як кличе показ: код переліку «опис — образ» (`опис_образ`: True / False / None) і скільки речей дав міст. Показ ставить
картку лише на True; інше — повтор руки раз, далі порожнє місце з причиною у звіті. ЖИВІ-14 №27 рука 4 (відмова qwen,
перелік — проза з прикладом JSON): ДО — 3 речі прикладу під відмовою; ПІСЛЯ — None → картки нема. Записи до рядка
6065 коду не несуть (поля в схемі не було) — для них None очікуваний; міра — свіжі записи живого ПІСЛЯ.
Запуск: cd джерела && python3 проби/руки34_відмова_6065.py <тека зі сценами, де є VIDPOVIDI>"""
import collections, glob, json, os, sys
sys.path.insert(0, "проби"); sys.path.insert(0, ".")
import pal_вердикт as ПВ
def частини(ф):
    т = open(ф, encoding="utf-8").read()
    пр, _, в = т.partition("\n── ВІДПОВІДЬ")
    return пр.partition("──\n")[2].strip(), в.partition("──\n")[2].strip()
вх = ПВ.стенд(гілка=0)[0]
лік, рядки = collections.Counter(), []
for ф2 in sorted(glob.glob(sys.argv[1] + "/**/VIDPOVIDI/*перелік_речей_руки_3_4*.txt", recursive=True)):
    пр2, перелік = частини(ф2)
    try:
        проза = json.loads(пр2).get("description")
    except ValueError:
        continue
    в = json.loads(ПВ.B.виклик("від_моделі", json.dumps(dict(вх, текст_моделі=проза, перелік_речей=перелік), ensure_ascii=False)))
    в = в.get("вердикт", в)
    код = в.get("опис_образ")
    лік[str(код)] += 1
    if код is not True:
        рядки.append("  %s · опис_образ=%s · речей від мосту %d · картка: нема (повтор, далі порожнє місце)"
                     % (os.path.relpath(ф2, sys.argv[1])[:90], код, len(в.get("речі") or [])))
print("переліків: %d · опис_образ: %s" % (sum(лік.values()), dict(лік)))
print("\n".join(рядки))
