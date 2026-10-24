"""Рядки 9401–9402: переграний без моделі хід #1586.
Друкує шлях `update.*` у паспорт: схему, годину і частину дня.
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import мовний_шар as М


відповідь = json.dumps({"update": {
    "palette": {"quote": "схема палітри — тріада", "value": "triad"},
    "hour": {"quote": "Вистава о 19:00", "value": 19},
    "part_of_day": "evening"}, "need": "none",
    "text": [{"about": ["palette", "hour"], "says": "Записала."}]}, ensure_ascii=False)
хід = М.прийняти_розмову(відповідь)
п = М.паспорт_з_шару(хід["внутрішня"], {}, слова_ходу=["схема палітри — тріада. Вистава о 19:00"])["паспорт"]
print("update.* без шляху:", [к for к in ("palette", "hour", "part_of_day")
      if к not in хід["внутрішня"] and not any(р.startswith("update.%s->" % к) for р in хід["перенесено"])])
print("вибір:", {"схема": п.get("схема"), "година": п.get("година"), "пора": п.get("пора")})


випадки = (
    ("о 19:00", 19, "evening"),
    ("о 7 вечора", 19, "evening"),
    ("20 жовтня ввечері", 19, "evening"),
    ("через 2 години ввечері", 19, "evening"),
    ("5-го ввечері", 19, "evening"),
    ("субота ввечері", 19, None),
)
for уривок, година, пора in випадки:
    оновлення = {"hour": {"quote": уривок, "value": година}}
    if пора:
        оновлення["part_of_day"] = пора
    після, перенесено = М._година_при_порі(оновлення)
    print("година:", уривок, "→", "hour" if "hour" in після else після.get("part_of_day"), перенесено)
