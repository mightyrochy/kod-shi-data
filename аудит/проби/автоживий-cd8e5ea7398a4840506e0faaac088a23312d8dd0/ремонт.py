"""Факти ремонту (#2130) із записаних відповідей: строгий JSON, стоп, токени, образи. Моделей не викликає."""
import json
from pathlib import Path
import re

root = Path(__file__).resolve().parent
out = {}
for folder in sorted(root.iterdir()):
    if not (folder / "done.txt").exists() or not (folder / "знімки/модель_виклики.json").exists():
        continue
    calls = json.loads((folder / "знімки/модель_виклики.json").read_text(encoding="utf-8"))["виклики"]
    log = (folder / "лог.txt").read_text(encoding="utf-8")
    hands = {int(m[2]): m[1] for m in re.finditer(r"рука (\d) · repair ← repair_prompt .*?запит (\d+) символів", log)}
    rows = []
    for i, call in enumerate(calls, 1):
        if call["тип"] != "ВЕРДИКТ_V1→ОБРАЗИ_V1":
            continue
        path = next((folder / "відповіді").glob(f"seed3_{i:02d}_*.txt"))
        text = path.read_text(encoding="utf-8")
        size = int(re.search(r"── ПРОМПТ \((\d+) симв", text)[1])
        answer = text.split("── ВІДПОВІДЬ", 1)[1].split("\n", 1)[1].strip()
        row = {"виклик": i, "рука": hands.get(size), "файл": path.name, "стоп": call["стоп"], "вихід_т": call["вихід"],
               "вхід_т": call["вхід"], "стеля": call["стеля"]}
        try:
            data = json.loads(answer)
            row["строгий_JSON"] = True
        except ValueError as error:
            row["строгий_JSON"] = False
            row["вада"] = f"{error.msg} на символі {error.pos}"
            data = None
        if isinstance(data, dict):
            outfits = data.get("outfits") or []
            row["образів"] = len(outfits)
            row["різних_складів"] = len({tuple(sorted(o.get("items") or [])) for o in outfits})
            row["з_why"] = sum(bool((o.get("why") or "").strip()) for o in outfits)
            row["речей"] = [len(o.get("items") or []) for o in outfits]
            row["needed"] = [o.get("needed") for o in outfits]
            row["з_caption"] = sum(bool((o.get("caption") or "").strip()) for o in outfits)
            row["з_day"] = sum(bool((o.get("day") or "").strip()) for o in outfits)
            row["з_deliberate"] = sum(bool(o.get("deliberate")) for o in outfits)
        rows.append(row)
    out[folder.name] = rows
(root / "ремонт.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
for scene, rows in out.items():
    for r in rows:
        print(scene, json.dumps(r, ensure_ascii=False))
