# -*- coding: utf-8 -*-
"""Рядок 1926: чи доходить фігура до опису в руці 2 без K-BOD-02. Друкує поле `тіло` опису
(рука 1 і рука 2) і чи несе промпт опису поле `body` з інструкцією «що образ робить для фігури».
Запуск із теки `джерела`: python3 проби/фігура3_опис_рука2_1926.py"""
import os, sys, json
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import fit as ПС, hypergraph as ГГ, розбір_відповідей as РВ

т = ПС.тіло(154, dict(плечі=90, груди=84, талія=64, стегна=88))
for рука, вимк in (("рука 1", ()), ("рука 2 без K-BOD-02", ("K-BOD-02",))):
    тіло = ГГ.тіло_для_опису(т, вимкнені=вимк)
    об = РВ.опис_обʼєкт([dict(id="1", назва="x", слот="верх")], тіло=тіло)
    пр = json.dumps(РВ.промпт_опису(об), ensure_ascii=False)
    print("%-20s тіло=%s · поле body у промпті: %s"
          % (рука, sorted(тіло) if тіло else тіло, "так" if "what this outfit does for her figure" in пр
             or '"body"' in пр else "ні"))
