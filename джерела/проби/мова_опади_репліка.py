# -*- coding: utf-8 -*-
"""Рядок 1881: «увесь день дощ» → паспорт `опади` → `day.precipitation`. Шов без моделі: відповідь шару
з опорою в її словах / без неї / з «можливим дощем»; і що промпт каже моделі про опади.
Запуск: python3 проби/мова_опади_репліка.py"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import мовний_шар as М, сценарій as СЦ
слова = "Іду на роботу, увесь день дощ"
сц = {"нагода": "робота", "типові_поля": ["година", "темп_c", "місце"]}
пр = json.dumps(json.loads(М.промпт_розмови({"розмова": {"нове": слова, "історія": []}, "сценарій": сц})), ensure_ascii=False)
i = пр.find("- precipitation")
print("промпт · precipitation:", пр[i:i + 330])
for підпис, додано in (("дощ, опора «дощ»", {"precipitation": {"quote": "дощ", "value": "rain"}}),
                       ("дощ, опора «увесь день дощ»", {"precipitation": {"quote": "увесь день дощ", "value": "rain"}}),
                       ("дощ без опори", {"precipitation": "rain"}),
                       ("дощ, опора не з її слів", {"precipitation": {"quote": "злива", "value": "rain"}})):
    р = М.прийняти_розмову(json.dumps({"update": dict({"occasion": {"quote": "роботу", "value": "work"}}, **додано),
                                       "need": "none", "text": "Записала."}, ensure_ascii=False))
    п = М.паспорт_з_шару(р["внутрішня"], сц, слова_ходу=[слова], частини=р["частини"])["паспорт"]
    д = СЦ.день_кодами(СЦ.з_показу(сц, п)[0])
    print("%-32s опади=%s · day.precipitation=%s" % (підпис, п.get("опади"), д.get("precipitation")))
