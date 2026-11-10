# -*- coding: utf-8 -*-
"""Звіт запасних → `звіт.tsv` тим самим кодом, що звіт 40 (`../звіт.py`), лише в цій теці.

Запуск (після `git fetch origin claude/Річ-колір-вимір`) із кореня: `python3 -I аудит/проби/річ_колір_модель_бачить/спроба_2/запасні/звіт.py`.
"""
import importlib.util
import os

ТУТ = os.path.dirname(os.path.abspath(__file__))
_с = importlib.util.spec_from_file_location("звіт_спроби_2", os.path.join(ТУТ, "..", "звіт.py"))
М = importlib.util.module_from_spec(_с)
_с.loader.exec_module(М)
М.ТУТ = ТУТ

if __name__ == "__main__":
    М.головна()
