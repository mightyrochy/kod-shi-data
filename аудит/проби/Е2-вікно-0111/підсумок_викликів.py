"""Підсумок живого запису б1 з обміну рушія: вхід (usage.input_tokens), стеля (max_tokens), статуси, скорочення.
Запуск: python -X utf8 підсумок_викликів.py <тека запису> <вікно>"""
import json, re, sys
from pathlib import Path
д, вікно = Path(sys.argv[1]), int(sys.argv[2])
лог = (д / "лог.txt").read_text(encoding="utf-8", errors="replace")
типи = {int(м[1]): (м[2], int(м[3])) for м in re.finditer(r"↔ модель #(\d+) (.+?) \((\d+) симв\.", лог)}
ремонт1 = re.search(r"рука 1 · repair ← .*?запит (\d+) символів", лог)
ремонт1 = int(ремонт1[1]) if ремонт1 else None
рядки, макс, р400 = [], 0, 0
for н in sorted(типи):
    дан = json.loads((д / f"VIDPOVIDI/обмін/{н:05d}.json").read_text(encoding="utf-8", errors="replace"))
    відп = дан["відповідь"]; ст = відп["status"]; стеля = дан["запит"].get("max_tokens", 0)
    вх = json.loads(відп["body"]).get("usage", {}).get("input_tokens") if ст == 200 else None
    р400 += ст == 400
    if вх and дан["запит"]["model"].startswith("qwen"):
        макс = max(макс, вх + стеля)
    ру2 = "ВЕРДИКТ_V1→ОБРАЗИ_V1" in типи[н][0] and типи[н][1] != ремонт1  # інший ремонт (його запит у «рука 2» — до скорочення)
    рядки.append((н, типи[н][0], типи[н][1], ст, вх, стеля, ру2))
print(f"{д.name}: викликів {len(рядки)}, HTTP 400: {р400}, найбільший вхід+стеля стилістки: {макс} (вікно {вікно}, {'у межах' if макс <= вікно else 'ПЕРЕВИЩЕНО'})")
for м in re.finditer(r"prompt shrunk to fit window[^']*", лог):
    print("  скорочення:", м[0])
for н, т, с, ст, вх, ст_, ру2 in рядки:
    if "ОБРАЗИ_V1" in т:
        print(f"  #{н} {т} запит {с} симв. HTTP {ст} вхід {вх} + стеля {ст_} = {(вх or 0) + ст_}{'  ← ремонт руки 2' if ру2 else ''}")
