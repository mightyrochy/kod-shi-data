# -*- coding: utf-8 -*-
"""Рядок 6208: replay записаних відповідей вибору (ВЕРДИКТ_V1 → ВИБІР_V1) живих прогонів пачки 15 — звідки ід кожного
«accept[].finding»: із «remarks_by_code» обраного образу, з чужого образу, нізвідки (вигаданий); скільки образів
вердикта несуть «findings», на які правило ДО посилало; і чи правило ПІСЛЯ (`повнота_образу.ВИБІР`) ще посилає.
Запуск із `джерела`: python3 проби/промпти3_вибір_ід.py"""
import collections, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); sys.path.insert(1, os.getcwd())
import промпти3_база as Б, протокол as П, повнота_образу as ПО

лік = collections.Counter()
for ш, промпт, відп in Б.записи(r"ВЕРДИКТ_V1_ВИБІР_V1\.txt$"):
    try:
        д = json.loads(промпт)
    except ValueError:
        лік["промпт не JSON"] += 1
        continue
    ф = "правило з «findings» · " if "or the outfit's «findings»" in промпт else "старіша форма · "
    лік[ф + "записів"] += 1
    лік[ф + "образів"] += len(д.get("verdict") or [])
    лік[ф + "образів з «findings»"] += sum(bool(о.get("findings")) for о in д.get("verdict") or [])
    ід = {П.ід_з_дроту(з.get("id")): П.ід_з_дроту(з.get("outfit")) for зз in (д.get("remarks_by_code") or {}).values()
          for з in зз}
    при = {П.ід_з_дроту(з.get("id")) for о in д.get("verdict") or [] for з in о.get("findings") or []}
    об, _, _ = П.розбір_за_схемою(відп, "ВИБІР_V1")
    for пр in ((об or {}).get("прийнято") or []):
        з = str(пр.get("знахідка") or "")
        лік[ф + "accept"] += 1
        лік[ф + ("  ід із remarks_by_code обраного" if ід.get(з) == (об or {}).get("обрано")
                 else "  ід із remarks_by_code чужого образу" if з in ід
                 else "  ід із «findings» образу" if з in при else "  ід нізвідки (вигаданий)")] += 1
for к, v in sorted(лік.items()):
    print("%-66s %d" % (к, v))
print("правило ПІСЛЯ посилає на «findings» образу:", any("or the outfit's «findings»" in р for р in ПО.ВИБІР.правила))
