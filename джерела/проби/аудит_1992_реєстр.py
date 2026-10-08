# -*- coding: utf-8 -*-
"""Рядок 1992: явна репліка сильніша за корпусну силу; суфіксне правило бере тір основи."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import реєстр_тіри as Т
import реєстр_політика as П

print("K-FIT-06/strong:", Т.регістр("K-FIT-06", "strong"), "(було гейт)")
print("тір K-COL-06-M:", Т._тір_правила("K-COL-06-M"), "= тір K-COL-06:", Т._тір_правила("K-COL-06"))
яв = [k for k, v in П.ПОЛІТИКА_РЕГІСТРУ.items() if v.get("регістр") == "репліка" and v.get("сила_корпусу") in ("hard", "strong")]
print("явна репліка з корпусною силою:", яв)
