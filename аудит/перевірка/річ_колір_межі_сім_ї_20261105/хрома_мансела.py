# -*- coding: utf-8 -*-
"""C*ab межі хроми Мансела (/1.5 ISCC–NBS «-ish gray», /4 — кінець Nearly Neutrals) за тоном і світлотою.

Вимір до рядка дошки 13445 і рішення менеджера 06.11 («межа хроми — за тоном і світлотою, як /1.5 ISCC–NBS і /0–/4
Nearly Neutrals у хромі Мансела»): одна хрома Мансела дає в CIELAB різний C* за тоном і V. Renotation через
Colour (`munsell_colour_to_xyY`), освітлювач C → D65 Bradford, як у генераторі решітки.
Запуск із кореня (бібліотеки — `джерела/лабораторія/колір_сім_ї_контури.requirements.txt`):
python3 -W ignore аудит/перевірка/річ_колір_межі_сім_ї_20261105/хрома_мансела.py [хрома ...]  (типово 1.5)
Вимір 05.11 для /1.5, V 3–8, 11 тонів: C* 4.2–12.5, медіана 8.1 (5PB і 5P за V 7–8 — 4.2–5.0, 5Y і 5GY — 11.4–12.5)."""
import sys
import warnings; warnings.filterwarnings("ignore")
import numpy as np, colour, statistics
C_D65 = colour.CCS_ILLUMINANTS["CIE 1931 2 Degree Standard Observer"]


def lab(позначка):
    """Lab D65 точки Мансела «H V/C»."""
    XYZ = colour.xyY_to_XYZ(colour.munsell_colour_to_xyY(позначка))
    XYZ = colour.adaptation.chromatic_adaptation_VonKries(XYZ, colour.xy_to_XYZ(C_D65["C"]),
                                                          colour.xy_to_XYZ(C_D65["D65"]), transform="Bradford")
    return colour.XYZ_to_Lab(XYZ, C_D65["D65"])


for хрома in (sys.argv[1:] or ["1.5"]):
    усі = []
    print(f"/{хрома}: C*ab за V 3–8")
    for h in ["5R", "5YR", "10YR", "5Y", "5GY", "5G", "5BG", "5B", "5PB", "5P", "5RP"]:
        значення = []
        for V in [3, 4, 5, 6, 7, 8]:
            try:
                L, a, b = lab(f"{h} {V}/{хрома}")
                значення.append(round(float(np.hypot(a, b)), 1))
            except Exception:
                значення.append(None)
        усі += [в for в in значення if в]
        print(" ", h, значення)
    print(f"  медіана {statistics.median(усі)}, мін {min(усі)}, макс {max(усі)}")
