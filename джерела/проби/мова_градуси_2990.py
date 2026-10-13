# -*- coding: utf-8 -*-
"""Проба (рядок 2990, живі 11 К7): що бачить мовна модель у словнику кодів ходу розмови про градуси.
На «мінус п'ятнадцять і сніг» MamayLM двічі писала лише `weather_feel: frost` — опис `frost` мав межу в градусах
(«about -10 °C and colder»), і −15 ішло у відчуття. Друкує рядки `temperature_c` і `weather_feel` з `_коди_розмови()`
(те, що йде в промпт ходу) і три факти: чи є градуси в описі відчуття, чи несе опис числа пару-шаблон у формі
відповіді «мінус N → -N», чи каже опис відчуття, що «мінус N» — не його. Моделей не кличе.
Запуск: cd джерела && python3 проби/мова_градуси_2990.py"""
import os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import мовний_шар as МШ  # noqa: E402
коди = МШ._коди_розмови()
рядки = list(коди)
т = next(р for р in рядки if р.startswith("- temperature_c"))
в = next(р for р in рядки if р.startswith("- weather_feel"))
print(т, "\n", в, sep="")
print("градуси в описі weather_feel (°C чи -число):", bool(re.search(r"°C|-\d", в)))
print("пара-шаблон у формі відповіді в temperature_c («мінус N» → value -N):",
      '"value": -N' in т and "мінус N" in т)
print("weather_feel відсилає «мінус N» до temperature_c:", "мінус N" in в and "temperature_c" in в)
