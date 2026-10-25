"""Рядки 9401–9402, 9552, 9581: переграний без моделі хід #1586.
Друкує шлях `update.*` у паспорт: схему, годину і частину дня; годину — за кодом моделі `named` (3.2-Е).
"""
import json
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import мовний_шар as М


відповідь = json.dumps({"update": {
    "palette": {"quote": "схема палітри — тріада", "value": "triad"},
    "hour": {"quote": "о 19:00", "value": 19, "named": "clock_time"},
    "part_of_day": "evening"}, "need": "none",
    "text": [{"about": ["palette", "hour"], "says": "Записала."}]}, ensure_ascii=False)
хід = М.прийняти_розмову(відповідь)
п = М.паспорт_з_шару(хід["внутрішня"], {}, слова_ходу=["схема палітри — тріада. Вистава о 19:00"])["паспорт"]
print("update.* без шляху:", [к for к in ("palette", "hour", "part_of_day")
      if к not in хід["внутрішня"] and not any(р.startswith("update.%s->" % к) for р in хід["перенесено"])])
print("вибір:", {"схема": п.get("схема"), "година": п.get("година"), "пора": п.get("пора")})


Н = "clock_time"
випадки = (
    ("о 19:00", 19, "evening", Н), ("о 7 вечора", 19, "evening", Н), ("о 16:00", 16, None, Н),
    ("о 8 вечора", 20, "evening", Н), ("о сьомій", 19, "evening", Н), ("на восьму", 20, None, Н),
    ("на шосту вечора", 18, None, Н), ("20 жовтня ввечері", 19, "evening", None),
    ("через 2 години ввечері", 19, "evening", None), ("5-го ввечері", 19, "evening", None),
    ("19 жовтня ввечері", 19, "evening", None), ("7-го ввечері", 19, "evening", None),
    ("субота ввечері", 19, None, None), ("о 19:00", 19, "evening", None),
)
for уривок, година, пора, названа in випадки:
    оновлення = {"hour": dict({"quote": уривок, "value": година}, **({"named": названа} if названа else {}))}
    if пора:
        оновлення["part_of_day"] = пора
    після, перенесено = М._година_при_порі(оновлення)
    print("година:", уривок, "named" if названа else "—", "→", "hour" if "hour" in після else після.get("part_of_day"),
          перенесено)
