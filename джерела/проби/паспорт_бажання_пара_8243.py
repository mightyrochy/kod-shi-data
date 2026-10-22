# -*- coding: utf-8 -*-
"""Рядки 8243, 8660 (ЖИВІ-29 С06 «хочу щось червоне», `claude/zhyvi-29:…/06_ж1_побачення_день_червоне/VIDPOVIDI/seed3_03`):
replay відповіді ходу, де річ `wants` записано парою {quote, value}. Друкує `незнайомі` розбору, `бажання` паспорта й
`not_taken` речення. Запуск: cd джерела && python3 проби/паспорт_бажання_пара_8243.py"""
import os, sys, json
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import мовний_шар as М
відповідь = json.dumps({"update": {"wants": [{"quote": "червоне", "value": "red"}]}, "need": "none",
                        "text": [{"about": ["wants"], "says": "Записала: ти хочеш червоний колір."}]}, ensure_ascii=False)
р = М.прийняти_розмову(відповідь)
п = М.паспорт_з_шару(р["внутрішня"], {"нагода": "побачення"}, слова_ходу=["хочу щось червоне"])["паспорт"]
print("незнайомі:", len(р["незнайомі"]), р["незнайомі"])
print("внутрішня.wants:", json.dumps(р["внутрішня"].get("wants"), ensure_ascii=False))
print("паспорт.бажання:", json.dumps(п.get("бажання"), ensure_ascii=False))
print("not_taken речення:", [ч.get("not_taken") for ч in р["частини"].get("text_parts") or [] if ч.get("not_taken")])
