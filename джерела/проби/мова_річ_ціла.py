# -*- coding: utf-8 -*-
"""Річ у внутрішній мові — одне ціле (вимір MamayLM-12B 25.09, рядок 156 «Можна яскравий верх —
куртку чи жакет, не темного кольору»): перекладач написав межу {slot: top, color_name: dark}, а
`dark` — не назва кольору. Друкує, що з кожної відповіді стає межею ядра (`вето_тверде`): річ із
нечитаною ознакою не береться — а не звужується до «жодного верху»; «невідомо» в ознаці — не збій;
її власна річ тримається назвою.
Запуск: cd джерела && python3 проби/мова_річ_ціла.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import мовний_шар as М
ВІДПОВІДІ = [
    ("рядок 156, MamayLM-12B", {"wants": [{"slot": "top", "item_type": "jacket", "color_class": "bright"}],
                                "vetoes": [{"slot": "top", "color_name": "dark"}]}),
    ("та сама межа, ключ з одруком", {"vetoes": [{"slot": "top", "colour": "dark"}]}),
    ("межа прочитана", {"vetoes": [{"color_class": "dark"}]}),
    ("колір «невідомо»", {"vetoes": [{"slot": "top", "color_name": "null"}]}),
    ("її річ із чужою ознакою (Т-12, 12B)", {"own_items": [{"name": "спідницю", "status": "has", "slot": "bottom",
                                                            "zone": "belly"}]}),
]
for де, відп in ВІДПОВІДІ:
    р = М.прийняти_вхід("scenario", json.dumps(відп, ensure_ascii=False))
    п = М.паспорт_з_шару(р["внутрішня"], {})["паспорт"]
    межі = {к: v for к, v in (п.get("вето_тверде") or {}).items() if v and к != "без_читача"}
    print("── %s\n   ВІДПОВІДЬ: %s\n   ВНУТРІШНЯ: %s\n   незнайомі: %s\n   МЕЖІ ЯДРА: %s\n   БАЖАННЯ: %s" % (
        де, json.dumps(відп, ensure_ascii=False), json.dumps(р["внутрішня"], ensure_ascii=False),
        р["незнайомі"] or "—", json.dumps(межі, ensure_ascii=False) if межі else "—",
        json.dumps(п.get("бажання") or [], ensure_ascii=False)))
