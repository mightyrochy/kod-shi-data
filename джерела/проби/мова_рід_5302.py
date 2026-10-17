# -*- coding: utf-8 -*-
"""Рядки 5302, 5983, 6619: стилістка про себе в чоловічому роді («я підготував», «я б додав», «я радий») і форми
«ви» в тому, що жінка читає: `знімки/картки.txt`, `знімки/текст_екранів.txt`, бульбашка `ng4_rozmova_*.txt`
(«стилістка») і сирий хід розмови (`*_хід_розмови.txt`: `text[].says`, `invite`, `ask`). Слова читає ПРОБА
(мірило очима), не код (п.12). Запуск: cd джерела && python3 проби/мова_рід_5302.py <тека живого прогону>"""
import json, re, sys
from pathlib import Path
sys.path.insert(0, ".")
from проби.мова_ти_5983 import ФОРМИ, НЕ_ФОРМИ

_Л = "а-яіїєґ'’ʼ"
РІД = re.compile(r"(?<![%s])я(?:\s+(?:б|би|вже|ще|теж|також|навмисно|свідомо|спеціально|тут|тобі|для тебе))*\s+"
                 r"([%s]{2,}(?:ав|ив|ів|ув|їв|яв|ов|аў|ився|ався|увся)|радий|впевнений|готовий|згоден|рад)"
                 r"(?![%s])" % (_Л, _Л, _Л), re.I)

def тексти(ф):
    т = ф.read_text(encoding="utf-8")
    if ф.name.startswith("ng4_rozmova_"):
        return [json.JSONDecoder().raw_decode(т.lstrip())[0].get("стилістка") or ""]
    if ф.name.endswith("_хід_розмови.txt"):
        в = re.split(r"── ВІДПОВІДЬ[^\n]*\n", т, maxsplit=1)[-1]
        в = в[в.find("{"):] if "{" in в else ""
        try:
            о = json.JSONDecoder().raw_decode(в)[0]
        except ValueError:
            return []
        return [ч.get("says") or "" for ч in о.get("text") or [] if isinstance(ч, dict)] + [о.get("invite") or "", о.get("ask") or ""]
    return [т]

тека, рід, ви, файлів = Path(sys.argv[1]), 0, 0, 0
for ф in sorted(тека.rglob("*.txt")):
    if not (ф.name in ("картки.txt", "текст_екранів.txt") or ф.name.startswith("ng4_rozmova_") or ф.name.endswith("_хід_розмови.txt")):
        continue
    файлів += 1
    for т in тексти(ф):
        р = [м.group(0) for м in РІД.finditer(т)]
        в = [м.group(1) for м in ФОРМИ.finditer(т) if м.group(1).lower() not in НЕ_ФОРМИ]
        рід, ви = рід + len(р), ви + len(в)
        if р or в:
            print("  %s: рід %s · «ви» %s" % (ф.relative_to(тека), р, в))
print("файлів %d · стилістка в чоловічому роді %d · форм «ви» %d" % (файлів, рід, ви))
