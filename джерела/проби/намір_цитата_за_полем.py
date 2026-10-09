# -*- coding: utf-8 -*-
"""Автоогляд Codex #706 (рядок 2620): код наміру на полі `goal` переноситься на `intent` РАЗОМ із записом верхнього
`quotes` — інакше сторож цитат скидає намір у conventional. Без моделі. Друкує для трьох форм відповіді (верхній
`quotes`; пари {quote, value}; обидва коди не на своїх полях) перенесене, внутрішню мову й те, що лишає сторож.
Запуск: cd джерела && python3 проби/намір_цитата_за_полем.py"""
import json, os, sys; ТУТ = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(ТУТ))
import мовний_шар as М
СЛОВА = "головне щоб без претензій"
ФОРМИ = {"quotes_goal": {"goal": "context_optimal", "quotes": {"goal": "без претензій"}},
         "пара": {"goal": {"quote": "без претензій", "value": "context_optimal"}},
         "міняються": {"goal": "statement", "intent": "conceal", "quotes": {"goal": "без претензій", "intent": "головне"}}}
for назва, відп in ФОРМИ.items():
    р = М.прийняти_вхід("scenario", json.dumps(відп, ensure_ascii=False))
    лишено, _ = М._тримається(р["внутрішня"], СЛОВА)
    print("%-12s перенесено %-22s внутрішня %s | після сторожа %s" % (назва, р["перенесено"],
          json.dumps(р["внутрішня"], ensure_ascii=False), json.dumps(лишено, ensure_ascii=False)))
