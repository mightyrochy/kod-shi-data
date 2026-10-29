"""Чи знаходить траурний_регістр.основний_колір основний елемент речі з двома кольорами.

Запуск: python -I -X utf8 основний.py <дерево> <знімок каталогу JSON>.
Лічить речі регістру з ≥2 colors, у яких жоден елемент не визнано основним, — їх K-OCC-01 пропускає.
"""
import json
import os
from pathlib import Path
import sys

дерево = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(дерево / "джерела"))
os.chdir(дерево / "джерела")
import outfit as О
import композитор_річ as КП
import колір_річ as КР
import траурний_регістр as ТР

каталог = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))["каталог"]
два = без = 0
приклади = []
типи = {}
for р in каталог:
    if len(р.get("colors") or []) < 2 or р.get("слот") == "верхній_шар":
        continue
    річ = КП.у_річ(р, р["слот"], {})
    if not ТР.регістрова_річ(річ):
        continue
    два += 1
    осн = max(річ["colors"], key=lambda c: float(c.get("coverage") or 0.0))
    т = КР.тип_кольору(осн) if hasattr(КР, "тип_кольору") else ("інтервал" if осн.get("не_вимір") else "вимір")
    типи[т] = типи.get(т, 0) + 1
    if not any(ТР.основний_колір(річ, е) for е in О.елементи([річ])):
        без += 1
        if len(приклади) < 5:
            приклади.append((р["id"], т, р.get("колір_назва")))
print("Речей регістру з ≥2 colors:", два, "тип основного сегмента:", типи)
print("Без основного елемента (K-OCC-01 пропускає):", без, "приклади:", приклади)
