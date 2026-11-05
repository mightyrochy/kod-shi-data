"""Таблиця п'яти запитів з записів прогону: rc, 400, рука 2, токени рушія (usage.input_tokens у обміні), скорочення."""
import glob, json, re, sys
from pathlib import Path
Т = Path(__file__).resolve().parent
ІД = ["б1_концерт_сміливо", "б1_сніг_вихідні_стримано", "б1_зима_звично", "б1_дощ_зустріч_стримано", "б1_дощ_зустріч_звично"]
for id_ in ІД:
    д = Т / id_
    if not д.exists():
        print(id_, "не виміряно: нема запису"); continue
    лог = (д / "лог.txt").read_text(encoding="utf-8", errors="replace")
    rc = (д / "rc.txt").read_text().strip().removeprefix("rc=") if (д / "rc.txt").exists() else "?"
    виклики = {}
    for м in re.finditer(r"↔ модель #(\d+) (.+?) \((\d+) симв\., разом \d+\) → [\d.]+ с · HTTP (\d+)", лог):
        виклики[int(м[1])] = (м[2], int(м[3]), м[4])
    р400 = len(re.findall(r"HTTP 400", лог + (д / "проксі.txt").read_text(encoding="utf-8", errors="replace")))
    вікно = len(re.findall(r"(?i)exceed|перевищ", лог)) 
    скор = len(re.findall(r"prompt shrunk|промпт скорочено до вікна", лог + (д / "запуск.txt").read_text(encoding="utf-8", errors="replace") if (д / "запуск.txt").exists() else ""))
    print(f"\n{id_}: rc={rc} HTTP400={р400} рядків_про_вікно={вікно} скорочено={'є ' + str(скор) if скор else 'нема'}")
    for м in re.finditer(r"рука 2 · (\S+) ← (\S+) .*?запит (\d+) символів · відповідь (\d+) · образів кроку (\d+)", лог):
        п = [n for n, (_, s, _) in виклики.items() if s == int(м[3])]
        ток = "?"
        if п:
            ф = д / "VIDPOVIDI/обмін" / f"{п[0]:05d}.json"
            дан = json.loads(ф.read_text(encoding="utf-8", errors="replace")); ключі = list(дан)
            ток = json.loads(дан[ключі[2]]["body"])["usage"]["input_tokens"]
        відп = glob.glob(str(д / f"VIDPOVIDI/seed3_{п[0]:02d}_*.txt")) if п else []
        print(f"  рука 2 {м[1]}: виклик #{п} HTTP {виклики[п[0]][2] if п else '?'} prompt_tokens={ток} відповідь={м[4]} симв. образів={м[5]} {Path(відп[0]).relative_to(Т.parents[3]) if відп else ''}")
