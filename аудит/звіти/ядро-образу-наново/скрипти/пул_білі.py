"""Пул запиту стилістці (дошка 16933): скільки рядків, скільки речей кольору white/ivory/cream і за якими
категоріями, і чи несе запит `near_white_veto: true`.

Запуск з кореня: python3 -I аудит/звіти/ядро-образу-наново/скрипти/пул_білі.py \
  аудит/проби/Живий-через-міст/стенд/службове/с5_весілля_сестри/обміни.jsonl 6
(другий аргумент — номер рядка обміну від нуля; у с5 рядок 6 — запит складання). Рядок пулу — список, що
починається номером «#N·NN»: [номер, ціна, колір, hex, родина, категорія, …].
"""
import collections
import json
import re
import sys

рядок = open(sys.argv[1], encoding="utf-8").readlines()[int(sys.argv[2])]
пул, вето = {}, []


def обхід(x):
    if isinstance(x, str):
        s = x.strip()
        if s[:1] in "[{":
            try:
                обхід(json.loads(s))
            except ValueError:
                pass
    elif isinstance(x, dict):
        if "near_white_veto" in x:
            вето.append(x["near_white_veto"])
        for v in x.values():
            обхід(v)
    elif isinstance(x, list):
        if x and isinstance(x[0], str) and re.fullmatch(r"#\d+·\d+", x[0]) and len(x) > 6:
            пул[x[0]] = x
        else:
            for v in x:
                обхід(v)


обхід(json.loads(рядок))
білі = [r for r in пул.values() if r[2] in ("white", "ivory", "cream")]
print(f"рядків пулу {len(пул)}; white/ivory/cream {len(білі)}:",
      dict(collections.Counter(r[5] for r in білі).most_common()))
print("near_white_veto:", вето, "; near_white_reserved у запиті:", рядок.count("near_white_reserved"))
