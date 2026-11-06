# -*- coding: utf-8 -*-
"""Звіряє два виходи `вимір.py` (ДО і ПІСЛЯ): за кожною функцією — входів, розбіжностей і перші приклади.
Запуск: python3 звірка.py <до.json.gz> <після.json.gz>"""
import gzip, hashlib, json, sys

до, після = (json.load(gzip.open(ш, "rt", encoding="utf-8")) for ш in sys.argv[1:3])
for к in sorted(set(до) | set(після)):
    а, б = до.get(к), після.get(к)
    if not isinstance(а, list) or к == "звірити_відношення":
        а, б = [а], [б]
    різні = [i for i in range(max(len(а), len(б))) if i >= len(а) or i >= len(б) or а[i] != б[i]]
    х = hashlib.sha256(json.dumps(б, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:12]
    print("%-22s входів %7d · розбіжностей %6d · sha256 ПІСЛЯ %s" % (к, len(а), len(різні), х))
    for i in різні[:3]:
        print("    #%d ДО %s\n        ПІСЛЯ %s" % (i, json.dumps(а[i], ensure_ascii=False)[:300], json.dumps(б[i], ensure_ascii=False)[:300]))
