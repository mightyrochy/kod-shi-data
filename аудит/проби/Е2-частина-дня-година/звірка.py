#!/usr/bin/env python3
"""Прилад проби (не код продукту): мірило наряду Е2-частина-дня-година на записах сцени.
Запуск: python3 звірка.py <тека прогону> — друкує на кожну сцену: подію паспорта (`event` мовного шару), частину дня,
скільки запитів до стилістки (не мовний шар) несуть її годину, скільки карток (тексти стилістки, `знімки/картки.txt`)
її несуть, і що в рядку картки «Твої слова». Година — її годинник у словах сцени: «19:30», «о сьомій», «о десятій»."""
import json, re, sys
from pathlib import Path

ГОДИНА = re.compile(r"\b(?:[01]?\d|2[0-3]):[0-5]\d\b|\bо (?:сьомій|десятій|восьмій|першій)\b|\bat \d{1,2}(?::\d\d)?\s?(?:p\.?m|a\.?m)",
                    re.IGNORECASE)
теки = sorted(п for п in Path(sys.argv[1]).iterdir() if (п / "VIDPOVIDI").is_dir())
for д in теки:
    події, пори, запитів, з_годиною = set(), set(), 0, []
    for ф in sorted((д / "VIDPOVIDI" / "обмін").glob("*.json")):
        о = json.loads(ф.read_text(encoding="utf-8"))
        промпт = json.dumps(о["запит"].get("messages"), ensure_ascii=False)
        тіло = json.loads(о["відповідь"].get("body") or "{}")
        текст = "".join(ч.get("text", "") for ч in тіло.get("content", []) if isinstance(ч, dict)) or \
            "".join((в.get("message") or {}).get("content") or "" for в in тіло.get("choices", []))
        try:
            відп = json.loads(текст)
        except ValueError:
            відп = None
        оновл = (відп or {}).get("update") if isinstance(відп, dict) else None
        if isinstance(оновл, dict):
            if оновл.get("event"):
                е = оновл["event"]
                події.add(е if isinstance(е, str) else json.dumps(е, ensure_ascii=False))
            if оновл.get("part_of_day"):
                пори.add(json.dumps(оновл["part_of_day"], ensure_ascii=False))
        if '"task":{"role":"You are the stylist' in промпт.replace("\\", "") or "ПАКЕТ_V1" in промпт or \
                ('"case"' in промпт.replace("\\", "") and "her_new_message" not in промпт):
            запитів += 1
            ц = промпт.replace("\\", "")
            м = ГОДИНА.search(ц)
            if м:
                з_годиною.append("%s «%s»" % (ф.name, ц[max(0, м.start() - 60):м.end() + 10]))
    картки = (д / "знімки" / "картки.txt")
    рядки_карток = [р for р in (картки.read_text(encoding="utf-8").splitlines() if картки.exists() else []) if р.strip()]
    картки_з_годиною = [р[:160] for р in рядки_карток if ГОДИНА.search(р)]
    екрани = (д / "знімки" / "текст_екранів.txt")
    слова = sorted(set(re.findall(r"Твої слова\n([^\n]{0,160})", екрани.read_text(encoding="utf-8")))) if екрани.exists() else []
    розм = (д / "знімки" / "ng4_rozmova_seed3.txt")
    випадок = json.JSONDecoder().raw_decode(розм.read_text(encoding="utf-8"))[0].get("випадок") if розм.exists() else None
    print("== %s" % д.name)
    print("   подія: %s · пора: %s · картка розмови: %s" % (sorted(події), sorted(пори), випадок))
    print("   запитів стилістці: %d · з її годиною: %d" % (запитів, len(з_годиною)))
    for з in з_годиною[:4]:
        print("     ", з)
    print("   рядків карток: %d · з її годиною: %d" % (len(рядки_карток), len(картки_з_годиною)))
    for к in картки_з_годиною[:4]:
        print("     ", к)
    print("   «Твої слова» на екрані: %s" % (слова or "—"))
    if розм.exists() and "Твої слова" not in розм.read_text(encoding="utf-8"):
        pass
