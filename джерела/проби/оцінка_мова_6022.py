# -*- coding: utf-8 -*-
"""Рядок 6022: частка відповідей ОЦІНКИ з кирилицею в "answer"/"text" при `"language": "English"` у запиті."""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import протокол as П


def тексти(об):
    """Рядки "answer" і кожного "text" відповіді."""
    вих = [об.get("answer")] if isinstance(об.get("answer"), str) else []
    for поле in ("works", "change", "unknown"):
        вих += [п["text"] for п in об.get(поле) or [] if isinstance(п, dict) and isinstance(п.get("text"), str)]
    return вих


def заміряти(тека):
    """Друкує по запису: сцена, файл, скільки текстів із кирилицею; разом — частка записів."""
    всього = з_кирилицею = 0
    for ф in sorted(Path(тека).rglob("*_ОЦІНКА_відповідь.txt")):
        запит, _, відповідь = ф.read_text(encoding="utf-8").partition("── ВІДПОВІДЬ")
        if '"language": "English"' not in запит:
            continue
        тіло = відповідь.split("\n", 1)[-1]
        об, _ = П.розбір(тіло)
        усі = тексти(об) if isinstance(об, dict) else re.findall(r'"(?:answer|text)": "((?:[^"\\]|\\.)*)"', тіло)
        кир = [т for т in усі if re.search("[А-Яа-яІіЇїЄєҐґ]", т)]
        всього, з_кирилицею = всього + 1, з_кирилицею + bool(кир)
        print(f"{ф.parent.parent.name[:2]} {ф.name}: {len(кир)}/{len(усі)}")
    print(f"Разом: кирилиця в текстах {з_кирилицею}/{всього} записів")


if __name__ == "__main__":
    заміряти(sys.argv[1])
