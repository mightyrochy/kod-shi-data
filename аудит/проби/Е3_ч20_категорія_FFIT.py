# -*- coding: utf-8 -*-
"""Е3 ч20: каталог тіл ДО → ПІСЛЯ за категорією FFIT (`body_shape.визначення`).

ДО — `body_shape` з `main` до ч20 (файл за аргументом `--до`, `git show origin/main:джерела/body_shape.py`);
ПІСЛЯ — поточний: похибка з точки ч13 (`силует_пропорції.похибка_виміру_тіла`, запису ще нема → None), далі
гіпотетична похибка 1 і 2 см на кожен вимір (лише показ: джерела числа нема). Тіла — сітка обхватів, см."""
import importlib.util, itertools, os, sys
from collections import Counter

корінь = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела")
sys.path.insert(0, корінь)


def модуль(шлях):
    с = importlib.util.spec_from_file_location("до", шлях)
    м = importlib.util.module_from_spec(с)
    с.loader.exec_module(м)
    return м


до_шлях = sys.argv[sys.argv.index("--до") + 1]
ДО, ПІСЛЯ = модуль(до_шлях), __import__("body_shape")
from силует_пропорції import похибка_виміру_тіла
тіла = list(itertools.product(range(80, 124, 4), range(60, 112, 4), range(86, 130, 4)))
рахунок = {к: Counter() for к in ("ДО", "ПІСЛЯ (запис)", "ПІСЛЯ ±1 см", "ПІСЛЯ ±2 см")}
for г, т, с in тіла:
    для = lambda в: похибка_виміру_тіла({}, в)
    for ключ, вих in (("ДО", ДО.визначення(г, т, с)),
                      ("ПІСЛЯ (запис)", ПІСЛЯ.визначення(г, т, с, похибка=для)),
                      ("ПІСЛЯ ±1 см", ПІСЛЯ.визначення(г, т, с, похибка=lambda в: 1)),
                      ("ПІСЛЯ ±2 см", ПІСЛЯ.визначення(г, т, с, похибка=lambda в: 2))):
        рахунок[ключ][вих["категорія"] or "невідомо"] += 1
print("тіл:", len(тіла))
for к, р in рахунок.items():
    print("%-14s" % к, ", ".join("%s %d" % (н, ч) for н, ч in sorted(р.items(), key=lambda x: -x[1])))
