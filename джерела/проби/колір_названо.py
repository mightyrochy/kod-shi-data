# -*- coding: utf-8 -*-
"""Рядок 4104: hex біля її назви кольору — ДО (код завжди) і ПІСЛЯ (без коду, коли назву вже написано).

Читає записані відповіді рук 3–4 (`*проза_рука_3_4.txt` стенда, ЖИВІ-17 `аудит/живі_17/А/*/VIDPOVIDI`) і для кожного
hex у тексті друкує, що піде в мовний шар. Запуск: `python3 проби/колір_названо.py <теки VIDPOVIDI…>`."""
import glob, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import мовний_шар as М

підряд = lambda т: М._HEX_У_ТЕКСТІ.sub(lambda м: "[colour: код]", т)       # ДО: код на кожен hex
всього = названо = 0
for тека in sys.argv[1:]:
    for ф in sorted(glob.glob(os.path.join(тека, "*проза_рука_3_4.txt"))):
        т = open(ф, encoding="utf-8").read()
        т = т[т.index("── ВІДПОВІДЬ"):] if "── ВІДПОВІДЬ" in т else т
        for м in М._HEX_У_ТЕКСТІ.finditer(т):
            if re.search(r"skin_hex|hair_hex|eye_hex", т[max(0, м.start() - 40):м.start()]):
                continue
            всього += 1
            н = М._колір_названо(т, м.start(), м.end())
            названо += н
            print("%-8s %s" % ("ЛИШЕ СЛОВО" if н else "КОД", т[max(0, м.start() - 30):м.end() + 30].replace("\n", " ")))
print("hex у відповідях: %d · її назва поряд (другої назви не буде): %d · кодом: %d" % (всього, названо, всього - названо))
