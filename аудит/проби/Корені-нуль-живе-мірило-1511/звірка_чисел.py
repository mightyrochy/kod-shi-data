#!/usr/bin/env python3
"""Проба наряду (не прилад кореня): градуси й години в записі кожної сцени — паспорт (`вердикти.txt` чи рядок паспорта
логу), запити до стилістки (промпти VIDPOVIDI руки 1–2, крім мовного шару й рук 3–4) і текст для неї (відповіді стилістки й мовного шару).
Запуск: python3 звірка_чисел.py <тека сцени>…  Друкує зразки з контекстом; рішення «так/ні» — у ЗВІТ.md."""
import json, re, sys
from pathlib import Path
ГРАДУСИ = re.compile(r"[-−+]?\d+\s*°|\bмінус\s+\w+|\bплюс\s+\d+|\"(?:temp|temperature|t_c|degrees)\w*\"\s*:\s*-?\d|−\d+|\bminus\s+\w+", re.I)
ГОДИНИ = re.compile(r"\b\d{1,2}:\d{2}\b|\bо\s+(?:десятій|сьомій|дев'ятій|восьмій|\d{1,2})\b|\bat\s+\d{1,2}(?::\d{2})?\s*(?:am|pm)?\b|\b\d{1,2}\s*(?:am|pm)\b", re.I)
def зразки(т, рв, n=3):
    return [т[max(0, м.start()-50):м.end()+30].replace("\n", " ") for м in list(рв.finditer(т))[:n]], len(рв.findall(т))
for д in map(Path, sys.argv[1:]):
    print(f"## {д.name}")
    паспорт = ""
    в = д / "вердикти.txt"
    if в.exists():
        м = re.search(r'"паспорт":\s*(\{.*?\})\s*,\n', в.read_text(encoding="utf-8"), re.S); паспорт = м[1] if м else ""
    if not паспорт:
        л = (д / "лог.txt").read_text(encoding="utf-8", errors="replace")
        паспорт = "\n".join(р for р in л.splitlines() if "паспорт" in р.lower() and "{" in р)
    джерела = {"паспорт": паспорт, "запити_стилістці": "", "текст_для_неї": ""}
    for ф in sorted((д / "VIDPOVIDI").glob("*.txt")):
        т = ф.read_text(encoding="utf-8", errors="replace"); п, _, в_ = т.partition("── ВІДПОВІДЬ")
        if "руки_3_4" in ф.name or "рука_3_4" in ф.name: continue   # руки 3–4 — модель без коду, не продукт (живі_порядок.md)
        if "мовний_шар" not in ф.name: джерела["запити_стилістці"] += f"\n[{ф.name}] " + п
        джерела["текст_для_неї"] += f"\n[{ф.name}] " + в_
    for назва, т in джерела.items():
        for мітка, рв in (("градуси", ГРАДУСИ), ("години", ГОДИНИ)):
            з, n = зразки(т, рв)
            if n: print(f"- {назва} · {мітка}: {n} — " + " | ".join(з))
    print()
