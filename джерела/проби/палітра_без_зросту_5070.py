# -*- coding: utf-8 -*-
"""5070: кольоровий endpoint без зросту, зі справжнім аудитом і незмінною вимогою збирання."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import bridge
import міст_вхід as В
import міст_основи as О
вхід = dict(шкіра=["#edc4ad"], волосся=["#66412f"], очі="#6f7858", зріст=None,
            обхвати={}, випадок="офіс", сценарій=dict(нагода="робота", місце="офіс"))
кольори = lambda п: {к: з for к, з in п.items() if к != "слід_правил"}
рахунок = lambda д: json.loads(bridge.виклик("палітри", д))
без = рахунок(вхід)
вибір = json.loads(bridge.виклик("вибір_палітри", вхід))
for об in ({}, dict(плечі=98), dict(плечі=98, груди=92, талія=74, стегна=99)):
    for зріст in (None, "", 148, 168, 188):
        д = dict(вхід, зріст=зріст, обхвати=об)
        assert кольори(рахунок(д)) == кольори(без)
        assert json.loads(bridge.виклик("вибір_палітри", д)) == вибір
        F, T, з, kw = В._збірка(д, лише_палітра=True)
        if зріст in (None, ""):
            assert T is None and з is None
            п = О._пакет(F, T, з, kw)
            assert п["особа"]["масштаб"] is None
            assert "зріст" in п["бракує_входів"]["онбординг"][0]
for виклик in (lambda: В._збірка(вхід), lambda: В._збірка(вхід, донорський=True, лише_палітра=True),
               lambda: bridge.виклик("запити", вхід)):
    try:
        виклик()
    except ValueError as помилка:
        assert "зріст" in str(помилка)
    else:
        raise AssertionError("збирання прийняло відсутній зріст")
assert any(с["правило"] == "K-IO-02" for с in без["слід_правил"])
print("5070: 15 станів мірок — однакові кольори й вибір; брак зросту й масштаб невідомі; 3 обов'язкові шляхи відхилено")
