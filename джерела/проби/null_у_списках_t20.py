# -*- coding: utf-8 -*-
"""Т-19/Т-20 (ноутбук 25.09): null у списку від моделі — «невідомо», а не слово «None».
Друкує, що `паспорт_з_json` кладе в бажання, настрій, межі й питання з відповіді з null.
Запуск: cd джерела && python3 проби/null_у_списках_t20.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import паспорт_нагоди as ПН
відповідь = {"бажання": [None, "сукня"], "настрій": [None], "питання_людині": [None],
             "вето": {"типи": [None], "кольори": [None, "темні"], "зони": [None]}}
п = ПН.паспорт_з_json(json.dumps(відповідь), {}, "хочу сукню, не хочу темні")
поля = dict(бажання=п["бажання"], настрій=п["настрій"], питання=п["питання_людині"],
            вето={к: v for к, v in п["вето"].items() if v})
print(json.dumps(поля, ensure_ascii=False))
print("слово «None» у полях: %d" % json.dumps(поля).lower().count("none"))
