#!/usr/bin/env python3
"""Прилад проби: градуси її слів у картці й запитах до стилістки на теці сцен (повтор чи живий запис).
Запуск: python3 лічба.py <тека сцен> [сцена…]. Друкує на сцену: смугу дня запитів, градусів цитатою поля (field_quotes,
sources.quote погоди), градусів у тексті запитів поза сталим правилом рук 3–4 і градусів у картці (рядок КАРТКА логу,
шапка й випадок вердиктів)."""
import json, re, sys
from pathlib import Path
ГРАДУСИ = re.compile(r"[+−-]?\d+\s*°\s*C|\bмінус\s+\w+|\bплюс\s+\w+|градус\w*", re.I)
ПРАВИЛО = "at +20 °C and warmer there is none"   # сталий рядок промпту рук 3–4 (не її слова; окрема знахідка)
ТЕКА = Path(sys.argv[1])
for д in sorted(Path(ТЕКА / с) for с in (sys.argv[2:] or [п.name for п in ТЕКА.iterdir() if п.is_dir()])):
    цитат, текст, смуги = 0, [], set()
    for ф in sorted((д / "VIDPOVIDI").glob("*.txt")):
        if "мовний_шар" in ф.name:
            continue
        промпт = ф.read_text(encoding="utf-8", errors="replace").split("── ВІДПОВІДЬ")[0].replace(ПРАВИЛО, "")
        цитат += len(re.findall(r'"weather_band"\s*:\s*"(?!(?:deep_frost|frost|cold|cool|mild|warm|hot)")[^"]*"', промпт))
        цитат += len(re.findall(r'"weather_band"\s*:\s*\{[^{}]*"quote"', промпт))
        смуги |= set(re.findall(r'"weather_band"\s*:\s*"(deep_frost|frost|cold|cool|mild|warm|hot)"', промпт))
        текст += ["%s: %s" % (ф.name[:22], м.group(0)) for м in ГРАДУСИ.finditer(промпт)]
    лог = (д / "лог.txt").read_text(encoding="utf-8", errors="replace") if (д / "лог.txt").exists() else ""
    картки = [р.split("КАРТКА:", 1)[1].strip() for р in лог.splitlines() if "КАРТКА:" in р]
    вердикти = (д / "вердикти.txt").read_text(encoding="utf-8", errors="replace") if (д / "вердикти.txt").exists() else ""
    шапка = re.findall(r'"смуга_погоди"\s*:\s*\{\s*"текст"\s*:\s*"([^"]*)"', вердикти.replace('\\"', '"'))
    у_картці = [м.group(0) for к in картки + шапка for м in ГРАДУСИ.finditer(к)]
    print(json.dumps({"сцена": д.name, "смуга_дня": sorted(смуги), "цитат_поля_погоди": цитат,
                      "градусів_у_тексті_запитів": len(текст), "картка": картки[-1:] , "градусів_у_картці": len(у_картці),
                      "приклади": (текст + у_картці)[:3]}, ensure_ascii=False))
