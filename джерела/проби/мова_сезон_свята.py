# -*- coding: utf-8 -*-
"""ДОЩ-1 (рядок 1471): «Новорічний корпоратив у ресторані» — сезон і пора, які несе сама нагода.
1) Промпт ходу розмови: чи просить він `weather_feel` і `part_of_day` з події (новорічна вечірка —
   cold, evening) і чи тримає градуси лише названими. 2) Шлях коду без моделі: та сама відповідь
   шару (як ж7 живого прогону ДО, і з полями, яких просить промпт ПІСЛЯ) → паспорт → `day` стилістки.
Запуск: python3 проби/мова_сезон_свята.py"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М, сценарій as СЦ
слова = "Новорічний корпоратив у ресторані"
сц = {"нагода": "свято", "година": 11, "темп_c": 18, "типові_поля": ["година", "темп_c", "місце"]}
пр = json.loads(М.промпт_розмови({"розмова": {"нове": слова, "історія": []}, "сценарій": сц}))
текст = json.dumps(пр, ensure_ascii=False)
for що, рядок in (("weather_feel: новорічна вечірка — cold", "a New Year or a Christmas party — cold"),
                  ("part_of_day: новорічна вечірка — evening", "an opera or a New Year party — evening"),
                  ("temperature_c: лише названі градуси", "only when she names the degrees"),
                  ("сезон і пора події — не «інше поле»", "carries are her words, not another field")):
    print("промпт · %-42s %s" % (що, "так" if рядок in текст else "ні"))

def день(додано):
    upd = {"occasion": {"quote": "корпоратив", "value": "celebration"},
           "place": {"quote": "ресторані", "value": "restaurant_casual"}, "formality": {"from": 6, "to": 7}}
    р = М.прийняти_розмову(json.dumps({"update": dict(upd, **додано), "need": "none", "text": "Записала."},
                                      ensure_ascii=False))
    п = М.паспорт_з_шару(р["внутрішня"], сц, слова_ходу=[слова], частини=р["частини"])["паспорт"]
    return СЦ.день_кодами(СЦ.з_показу(сц, п)[0])

for підпис, додано in (("відповідь без сезону й пори (ж7 ДО)", {}),
                       ("weather_feel cold «Новорічний» + evening",
                        {"weather_feel": {"quote": "Новорічний", "value": "cold"}, "part_of_day": "evening"}),
                       ("weather_feel cold без опори в її словах", {"weather_feel": {"quote": "грудень",
                                                                                   "value": "cold"}})):
    д = день(додано)
    print("день · %-42s unknown %s · temperature_c %s · start_hour %s · part_of_day %s"
          % (підпис, д.get("unknown"), д.get("temperature_c"), д.get("start_hour"), д.get("part_of_day")))
