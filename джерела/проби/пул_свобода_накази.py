# -*- coding: utf-8 -*-
"""ПУЛ-СВОБОДА (рядок 5512): що в промптах стилістки звучить як наказ — на ЗАПИСАНИХ промптах файлу вердиктів (рука 1,
кроки складання, ремонту й вибору). По кожному розділу (`rules`, `input`, `statement_codes`, полюси)
друкує, скільки речень має наказові маркери (do not / never / must / only / exactly / keep / take / reject / stop…),
і перші 4 речення-накази смаку (без технічних — формат JSON, «n» речі). Запуск: python3 джерела/проби/пул_свобода_накази.py ФАЙЛ"""
import json, re, sys
НАКАЗ = re.compile(r"\b(do not|don't|never|must|only|exactly|keep|take|reject|rejects|stops?|choose|always|no more|at least|at most)\b|ONE\b", re.I)
ТЕХНІКА = re.compile(r"answer|JSON|«n»|\"n\"|brace|schema|```|\bn\b alone|«id»|outfits_wanted|«pole»|written|write", re.I)
д = json.load(open(sys.argv[1], encoding="utf-8"))
в = next(в for п in д["прогони"] for в in п["вердикти"] if str(в.get("рука")) == "1")
for к in (в["етапи"]["виклики"]):
    з = (к.get("запит") or {}).get("текст")
    if к.get("крок") not in ("assembly", "repair", "choice") or not з: continue
    п = json.loads(з); т = п.get("task") or {}
    розділи = {"rules": т.get("rules") or [], "input": т.get("input") or [], "statement_codes": ["%s: %s" % кв for кв in (т.get("statement_codes") or {}).items()],
               "poles": ["%s: %s" % (x.get("id"), x.get("idea")) for x in п.get("poles") or []]}
    print("\n== %s · промпт %d симв., з них пул %d" % (к["крок"], len(з), len(json.dumps(п.get("pool") or п.get("verdict") or "", ensure_ascii=False))))
    for ім, рр in розділи.items():
        if not рр: continue
        накази = [р for р in рр if НАКАЗ.search(р)]; смак = [р for р in накази if not ТЕХНІКА.search(р)]
        print("  %-15s речень %3d · з наказом %3d · з них не технічних %3d" % (ім, len(рр), len(накази), len(смак)))
        for р in смак[:4]: print("     · " + р[:150])
