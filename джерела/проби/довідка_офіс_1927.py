# -*- coding: utf-8 -*-
"""Рядок 1927: довідка помічниці називає смугу офісу з формальність.СМУГА_ОФІСУ_EN."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import формальність as Ф
h = (pathlib.Path(__file__).resolve().parent.parent / "показ.html").read_text()
print("ДО: «5 office or theatre by day» =", "5 office or theatre by day" in h, "; ПІСЛЯ: «%s» =" % Ф.СМУГА_ОФІСУ_EN, Ф.СМУГА_ОФІСУ_EN + "," in h)
assert "5 office or theatre by day" not in h and Ф.СМУГА_ОФІСУ_EN + "," in h
