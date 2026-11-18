# -*- coding: utf-8 -*-
"""Е2-текст-жінці-неперевірене-пари (дошка 15391): знахідки різних правил про той самий брак тієї самої речі — один
пункт картки; число на розкривачі = число пунктів. Друкує `місць: <N>` — скільки пар «річ і чого бракує» стоїть на
картці більш ніж одним пунктом (ПІСЛЯ — 0). Запуск із джерела/: python3 -W ignore проби/неперевірене_пари_е2.py"""
import json, os, sys, collections
sys.path.insert(0, os.getcwd())
import внутрішня_мова as ВМ, міст_відповіді as МВ


def пит(правило, код, ід, **з):
    р = {"item_id": ід, "kind": "scarf"}
    заява = ВМ.заява(код, item=р, item_id=ід, **з)
    return dict(правило=правило, суть="x", речі=[ід], повідомлення=ВМ.повідомлення("card_unchecked", заява))


входи = [
    [пит("K-ACC-07", "scarf_near_face_way_unknown", "s1", ways=[ВМ.код_або_невідомо("wear_place", "шия")], source="catalogue"),
     пит("K-ACC-03", "wear_way_not_chosen", "s1"), пит("K-ACC-03", "wear_way_not_chosen", "s2")],
    [пит("K-COL-06-T", "wear_way_not_chosen", "s1"), пит("K-ACC-07", "scarf_near_face_way_unknown", "s1",
        ways=[ВМ.код_або_невідомо("wear_place", "шия")], source="catalogue")],
]
# клас «чого бракує» — свій у проби, не з коду, який перевіряє (прилад не береться з виправлення)
БРАК = {"wear_way_not_chosen": "спосіб", "scarf_near_face_way_unknown": "спосіб"}
місць = 0
for в in входи:
    пар = collections.Counter()
    пп = МВ._пункти_картки(в)
    for п in [п for п in пп if not п.get("для_всіх")]:
        for з in (п.get("повідомлення") or {}).get("statements") or []:
            пар[(БРАК.get(з["code"], з["code"]), з["values"]["item_id"])] += 1
    print([(п["правило"], [з["code"] for з in (п.get("повідомлення") or {}).get("statements") or []], bool(п.get("для_всіх"))) for п in пп])
    місць += sum(1 for ч in пар.values() if ч > 1)
print("місць:", місць)
