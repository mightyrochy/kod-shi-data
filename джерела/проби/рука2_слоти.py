# -*- coding: utf-8 -*-
"""Р2-2г (рядок 434): які слоти пулу руки 2 різняться від руки 1 (`pool_diff_slots`) для правил, що діють у пулі.
Сценарії й сіди 1–30; друкує правило, pool_diff і слоти. Запуск: cd джерела && python3 проби/рука2_слоти.py"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B
вх0 = json.load(open("стенд_вх.json"))
СЦ = {"office": dict(нагода="робота", місце="офіс", година=9, темп_c=18, дрес_код="business_casual"),
      "date": dict(нагода="побачення", місце="ресторан", година=20, темп_c=5, опади="дощ", тривалість_год=4)}
for ім, сц in СЦ.items():
    for сід in range(1, 31):
        п = json.loads(B.виклик("запити", json.dumps(dict(вх0, каталог="каталог_повний.xml", сід=сід, сценарій=сц), ensure_ascii=False)))["поломка"]
        if п["пара"]["дія"] != "pool": continue
        м = re.search(r"pool_diff=(\S+) · pool_diff_slots=(\S+)", п["що_змінено"])
        print("%-6s сід %2d · %-10s · pool_diff=%s · слоти %s" % (ім, сід, п["правило"], *м.groups()))
