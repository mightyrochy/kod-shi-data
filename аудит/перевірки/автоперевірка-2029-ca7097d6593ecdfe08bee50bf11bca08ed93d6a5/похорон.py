"""K-OCC-01 на похороні для речей регістру з двома кольорами й основним інтервалом.

Запуск: python -I -X utf8 похорон.py <дерево> <знімок каталогу JSON> <id> [<id> …].
Друкує знахідки K-OCC-01 штатного `формальність.нагода_палітра` для кожної речі окремо.
"""
import json
import os
from pathlib import Path
import sys

дерево = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(дерево / "джерела"))
os.chdir(дерево / "джерела")
import outfit as О
import композитор_річ as КП
import формальність as Ф

за_id = {р["id"]: р for р in json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["каталог"]}
for і in sys.argv[3:]:
    р = за_id[і]
    річ = КП.у_річ(р, р["слот"], {})
    E = О.елементи([річ])
    зн = Ф.нагода_палітра(E, нагода="похорон", місце="похорон", речі=[річ])
    зн = зн if isinstance(зн, list) else (зн or {}).get("знахідки", зн)
    k = [(з.get("сила") or з.get("рівень"), з.get("суть") or з.get("що")) for з in зн
         if isinstance(з, dict) and "K-OCC-01" in str(з.get("код") or з.get("id") or з.get("правило"))]
    print(і, р["слот"], р.get("колір_назва"), "елементів", len(E), "K-OCC-01:", len(k), k[:1])
