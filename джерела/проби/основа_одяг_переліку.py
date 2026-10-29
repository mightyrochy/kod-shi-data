# -*- coding: utf-8 -*-
"""Рядок 5229: стилістка бачить, скільки одягу нагоди лежить у вікні кожної кольорової основи.

Промпт `вибір_палітри` (крок 1) для двох жінок — стенд_вх (офіс) і профіль файла 1551 (побачення,
ресторан): у кожної кольорової основи поле `clothing` (і `clothing_maybe`), у нейтральної — нема.
Друкує, скільки основ мають 0 одягу у вікні, і число для «м'ятний·86» (основа файла 1551).
Запуск із теки `джерела`: `python3 проби/основа_одяг_переліку.py`."""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import bridge as B

стенд = json.load(open("стенд_вх.json", encoding="utf-8"))
for k in ("гілка", "схема", "вибір_кольору"):
    стенд.pop(k, None)
ж1551 = dict(стенд, зріст=167, обхвати={"плечі": 108, "груди": 104, "талія": 78, "стегна": 106},
             шкіра="#d9a88f", волосся=["#d2b37c", "#69513d"], очі="#597d81", очі_кільце="#30474c",
             сценарій={"нагода": "побачення", "місце": "ресторан_районний", "дрес_код": "smart_casual",
                       "година": 11, "темп_c": 18, "опади": "дощ", "мета": "лестити"},
             випадок="побачення, ресторан, дощ")
for ім, вх in (("стенд_вх", стенд), ("1551", ж1551)):
    r = json.loads(B.виклик("вибір_палітри", json.dumps(вх, ensure_ascii=False)))
    осн = json.loads(r["промпт"])
    осн = next(v for v in (осн.get("data") or осн).values() if isinstance(v, list)
               and v and isinstance(v[0], dict) and "fit" in v[0]) if "bases" not in осн else осн["bases"]
    кол = [о for о in осн if о.get("family") != "neutral"]
    нуль = [о["colour"] + "·%s" % о["lightness"] for о in кол if о.get("clothing") == 0]
    мʼята = [(о["lightness"], о["saturation"], о.get("clothing"), о.get("clothing_maybe")) for о in кол
             if о["colour"] == "mint"]
    print("ФАКТ · %s · основ %d, кольорових %d, з полем clothing %d · 0 одягу у вікні: %d %s · м'ятні "
          "(L*, гама, clothing, maybe): %s" % (ім, len(осн), len(кол), sum("clothing" in о for о in кол),
                                              len(нуль), нуль[:6], мʼята))
    assert кол and all("clothing" in о for о in кол), кол[:2]
    assert not any("clothing" in о for о in осн if о.get("family") == "neutral")
