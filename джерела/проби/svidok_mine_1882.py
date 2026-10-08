# -*- coding: utf-8 -*-
"""Рядок 1882: що закріплюється «твоєю річчю» з кадру, коли модель зору каже «mine» без її слів.
Сира відповідь П-1 живого С6 ПІСЛЯ (ж1, «образ на роботу з моєю блузою з фото», гілка claude/zhyvyi-0810,
`аудит/живий_0810/ПІСЛЯ/С6/вердикти.txt`): у промпті лише фото (шар не дав `own_items`), модель
назвала «mine» сорочку, штани й туфлі. Друкує закріплення без її речей словами і з блузою словами.
Запуск: cd джерела && python3 проби/svidok_mine_1882.py"""
import inspect, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import річ_з_фото as Р
В = json.dumps({"items": [
    {"photo": "ф1", "name": "yellow shirt", "slot": "top", "color": "yellow", "cut": "relaxed", "pattern": "solid",
     "formality": 5, "owner": "mine", "frame": {"left": 0, "top": 160, "right": 698, "bottom": 643}},
    {"photo": "ф1", "name": "yellow pants", "slot": "bottom", "color": "yellow", "cut": "wide", "length": "maxi",
     "pattern": "solid", "formality": 5, "owner": "mine", "frame": {"left": 328, "top": 537, "right": 640, "bottom": 950}},
    {"photo": "ф1", "name": "black shoes", "slot": "shoes", "color": "black", "formality": 5, "owner": "mine",
     "frame": {"left": 304, "top": 928, "right": 591, "bottom": 969}}]})
ФОТО = [{"ід": "ф1", "ширина": 600, "висота": 900}]
БЛУЗА = [{"name": {"free_text": "блуза з фото", "lang": "uk"}, "slot": "top", "status": "has", "quote": "з моєю блузою з фото"}]
нове = "власні" in inspect.signature(Р.речі_з_відповіді_фото).parameters
for підпис, власні in (("у промпті лише фото (як у живому С6)", []), ("у промпті блуза словами", БЛУЗА)):
    речі = (Р.речі_з_відповіді_фото(В, ФОТО, власні=власні) if нове else Р.речі_з_відповіді_фото(В, ФОТО))["речі_з_фото"]
    print("%s → закріплено «твоєю річчю» %d: %s" % (підпис, sum(1 for р in речі if р["закріплена"] and р["чия"] == "моя"),
          "; ".join("%s %s чия=%s закр=%s%s" % (р["ід"], р["назва"], р["чия"], р["закріплена"],
                    " (%s)" % р["чому_не_закріплена"] if р.get("чому_не_закріплена") else "") for р in речі)))
