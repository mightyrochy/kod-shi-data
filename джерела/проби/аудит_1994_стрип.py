# -*- coding: utf-8 -*-
"""Рядок 1994: стрип зберігає абзаци багаторядкового промпту."""
import os
import sys

корінь = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, корінь)
import build_артефакт as Б
import мовний_шар as М

простір = {}
exec(Б._стрип(os.path.join(корінь, "мовний_шар.py")), простір)
print("розривів абзаців у джерелі:", М.ПРОМПТ_ВИХОДУ.count("\n\n"), "у збірці:", простір["ПРОМПТ_ВИХОДУ"].count("\n\n"))
