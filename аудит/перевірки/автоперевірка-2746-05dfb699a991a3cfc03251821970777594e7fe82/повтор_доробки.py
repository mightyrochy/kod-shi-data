"""Звірити доробку PR 2746 за сирими відповідями без викликів моделей."""
import json
import pathlib
import re
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
evidence = root / "аудит/проби/Е2-вікно-0111"
for folder in sorted(evidence.glob("б1_п2_*")):
    window = int(folder.name.rsplit("_", 1)[1])
    log = (folder / "лог.txt").read_text(encoding="utf-8")
    statuses = re.findall(r"↔ модель #\d+ .*? HTTP (\d+)", log)
    print(f"{folder.name}: викликів={len(statuses)}, HTTP400={statuses.count('400')}, скорочень={log.count('warning: model · prompt shrunk to fit window')}")
    for response_file in sorted((folder / "обмін").glob("*.json")):
        data = json.loads(response_file.read_text(encoding="utf-8"))
        request, response = data["запит"], data["відповідь"]
        usage = json.loads(response["body"])["usage"]
        tokens, ceiling = usage["input_tokens"], request["max_tokens"]
        print(f"  #{int(response_file.stem)}: HTTP{response['status']}, вхід={tokens}, стеля={ceiling}, сума={tokens+ceiling}, перевищення={max(0, tokens+ceiling-window)}")
    for line_no, line in enumerate(log.splitlines(), 1):
        if line.lstrip().startswith("рука 2 {"):
            hand = json.loads(line[line.index('{'):])
            print(f"  рядок {line_no}: рука2, речей={hand['речей']}, фото={hand['фото']}, збій={hand['збій']}")
        if "warning: model · prompt shrunk" in line:
            print(f"  рядок {line_no}: {line.strip()}")

generated = subprocess.run([sys.executable, "-X", "utf8", str(evidence / "таблиця_руки2.py")], cwd=root, capture_output=True, check=True, encoding="utf-8").stdout
original = (evidence / "таблиця_руки2.md").read_text(encoding="utf-8")
rows = generated.splitlines()[2:]
print("таблиця: тотожна=%s, усіх записів=%d, без ремонту=%d, з ремонтом=%d, досяжно=%d" % (
    generated.splitlines() == original.splitlines(), len(rows),
    sum("без ремонту" in row for row in rows), sum("без ремонту" not in row for row in rows),
    sum("| так " in row for row in rows)))
