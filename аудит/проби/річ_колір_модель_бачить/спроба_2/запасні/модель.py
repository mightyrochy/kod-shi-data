# -*- coding: utf-8 -*-
"""`модель.jsonl` запасних → `модель.tsv` тим самим кодом, що зводить записи 40 (`../модель.py`), лише в цій теці.

Скрипт нічого не міряє. Запуск із кореня: `python3 -I аудит/проби/річ_колір_модель_бачить/спроба_2/запасні/модель.py`.
"""
import importlib.util
import os

ТУТ = os.path.dirname(os.path.abspath(__file__))
_с = importlib.util.spec_from_file_location("модель_спроби_2", os.path.join(ТУТ, "..", "модель.py"))
М = importlib.util.module_from_spec(_с)
_с.loader.exec_module(М)
М.ТУТ = ТУТ

if __name__ == "__main__":
    М.головна()
