#!/usr/bin/env python3
"""Мірила (в) і (г): що бачить модель палітри про очі й які основи вона має — з тек стенда `рв6_стенд.js`
(`DO=palitra`, `ZHYVA=sonnet`, `VIDPOVIDI=<тека>/відповіді`), ДО і ПІСЛЯ.

Читає файли викликів як є: відповідь моделі на портрет (`*_кольори_з_портрета.txt`: `eyes`, `eye_colour`), запит
вибору палітри (`*_вибір_палітри_*.txt`: `person.eyes`, `bases` з полем `eyes`, вибір моделі), відповіді мовного
шару (усі речення, де є «оч»). Кожен рядок — з файла, нічого не вгадано.
Запуск (з кореня): python3 аудит/проби/очі-називає-модель/стенд_розбір.py <тека ДО> <тека ПІСЛЯ> [<сцена>…]"""
import json, re, sys
from pathlib import Path


def _частини(файл):
    т = файл.read_text(encoding="utf-8")
    і = т.find("── ВІДПОВІДЬ")
    return т[:і], т[і:].split("\n", 1)[1] if і >= 0 else ""


def _json(т):
    к = т.find("{")
    try:
        return json.JSONDecoder().raw_decode(т[к:])[0]
    except Exception:
        return None


def сцена(тека):
    в = Path(тека) / "відповіді"
    р = {}
    пор = next(iter(sorted(в.glob("*_кольори_з_портрета.txt"))), None)
    if пор:
        о = _json(_частини(пор)[1]) or {}
        р["модель_очі"] = f"{о.get('eyes')} {о.get('eye_colour', '—')}"
    пал = next(iter(sorted(в.glob("*_вибір_палітри_*.txt"))), None)
    if пал:
        промпт, відповідь = _частини(пал)
        з = _json(промпт[промпт.find("{"):]) or {}
        оч = (з.get("person") or {}).get("eyes") or {}
        р["person.eyes"] = ", ".join(f"{к}={оч[к]}" for к in ("status", "family", "yellow_blue", "lightness",
                                                                "confidence") if к in оч)
        р["основи"] = "; ".join(f"{б.get('id')} {б.get('colour')} ({б.get('family')}, очі: {б.get('eyes') or '—'})"
                                for б in з.get("bases") or [])
        в_м = _json(відповідь) or {}
        р["вибір"] = f"{в_м.get('scheme')} / {в_м.get('base')}"
    про_очі = []
    for ф in sorted(в.glob("*_мовний_шар*.txt")):
        о = _json(_частини(ф)[1])
        тексти = о.values() if isinstance(о, dict) else []
        for т in тексти:
            if isinstance(т, str) and re.search(r"\bоч(і|ей|ам|има|ах)\b", т, re.I):
                про_очі.append(т)
    р["мовний_шар_про_очі"] = " | ".join(про_очі) or "мовчить"
    return р


if __name__ == "__main__":
    до, після, *сцени = sys.argv[1:]
    сцени = сцени or sorted(п.name for п in Path(після).iterdir() if п.is_dir())
    for с in сцени:
        print(f"### {с}\n\n| поле | ДО | ПІСЛЯ |\n|---|---|---|")
        а, б = сцена(Path(до) / с), сцена(Path(після) / с)
        for к in ("модель_очі", "person.eyes", "основи", "вибір", "мовний_шар_про_очі"):
            print(f"| {к} | {а.get(к, '—')} | {б.get(к, '—')} |")
        print()
