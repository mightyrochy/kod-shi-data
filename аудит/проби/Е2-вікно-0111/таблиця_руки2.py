"""Рука 2 на всіх записаних запитах б1: пул (збирання) і ремонт — вхід рушія (usage.input_tokens з обміну; для HTTP 400 без usage —
оцінка за симв. того ж запису) і межа досяжності скорочення ремонту: пул + 2800 < ремонт + 4000. Запуск з кореня репозиторію."""
import json, re, sys
from pathlib import Path
К = Path("аудит/проби/б1")
ПУЛ, РЕМ = 2800, 4000
рядки = []
for ф in sorted(list(К.glob("ПІСЛЯ-Е3/*/лог.txt")) + list(К.glob("Е2-вікно-3110/*/лог.txt"))):
    д = ф.parent
    if not (д / "VIDPOVIDI/обмін").exists():
        continue
    лог = ф.read_text(encoding="utf-8", errors="replace")
    вик = {}
    for м in re.finditer(r"↔ модель #(\d+) (.+?) \((\d+) симв\., разом \d+[^)]*\) → [\d.]+ с · HTTP (\d+)", лог):
        вик.setdefault(int(м[3]), []).append((int(м[1]), м[4]))
    def ток(симв):
        for н, ст in вик.get(симв, []):
            if ст == "200":
                дан = json.loads((д / f"VIDPOVIDI/обмін/{н:05d}.json").read_text(encoding="utf-8", errors="replace"))
                return json.loads(дан[list(дан)[2]]["body"])["usage"]["input_tokens"], ст
        return None, (вик[симв][0][1] if симв in вик else "?")
    пул = next(((int(м[1])) for м in re.finditer(r"рука 2 · assembly ← .*?запит (\d+) символів", лог)), None)
    рем = next(((int(м[1]), м[2]) for м in re.finditer(r"рука 2 · (repair|not_delivered) ← .*?запит (\d+) символів", лог) for м in [(None, м[2], м[1])]), None)
    м = re.search(r"рука 2 · (repair|not_delivered) ← .*?запит (\d+) символів", лог)
    рем = int(м[2]) if м else None
    пт, _ = ток(пул) if пул else (None, "?")
    рт, рст = ток(рем) if рем else (None, "?")
    коеф = пт / пул if пт and пул else None
    рт_оц = рт if рт else (round(рем * коеф) if рем and коеф else None)
    ід = (д.parent.name + "/" if д.parent.name.startswith("Е2") else "") + д.name
    рядки.append((ід, пул, пт, рем, рт_оц, "виміряно" if рт else f"оцінка (HTTP {рст})"))
print("| запис | пул, симв. | пул, т. | ремонт, симв. | ремонт, т. | пул+2800 | ремонт+4000 | скорочення ремонту досяжне |")
print("|---|---|---|---|---|---|---|---|")
for ід, пул, пт, рем, рт, як in рядки:
    if not (пт and рт):
        print(f"| {ід} | {пул} | {пт} | {рем} | — | — | — | рука 2 без ремонту |"); continue
    дос = "так" if пт + ПУЛ < рт + РЕМ else "ні"
    print(f"| {ід} | {пул} | {пт} | {рем} | {рт} ({як}) | {пт+ПУЛ} | {рт+РЕМ} | {дос} (вікно {пт+ПУЛ}…{рт+РЕМ}) |" if дос == "так" else f"| {ід} | {пул} | {пт} | {рем} | {рт} ({як}) | {пт+ПУЛ} | {рт+РЕМ} | ні |")
