"""Послідовний запуск призначених сцен; кожний завершений запис комітиться."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ЗБІРКА = КОРІНЬ.parent / "tmp" / "збірка"
ПЛАН = json.loads(ТЕКА.joinpath("НАРЯД.md").read_text(encoding="utf-8").split("ПЛАН ЖИВОГО — ДАНІ (JSON):\n")[1])
ОТОЧЕННЯ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
    NODE_PATH=r"C:\Users\gemini\kod-shi-test-node\node_modules")

for сцена in ПЛАН["scenes"]:
    вихід = ТЕКА / сцена
    if вихід.joinpath("результат.json").exists():
        print("Уже записано: " + сцена, flush=True)
        continue
    команда = [sys.executable, str(ЗБІРКА / "аудит/проби/записати_сцену.py"),
        str(ЗБІРКА), r"C:\Users\gemini\pyodide", str(вихід), "--сцена", сцена]
    час = datetime.now(timezone.utc).isoformat()
    with ТЕКА.joinpath("команди.jsonl").open("a", encoding="utf-8") as файл:
        файл.write(json.dumps({"час": час, "команда": команда}, ensure_ascii=False) + "\n")
    результат = subprocess.run(команда, cwd=КОРІНЬ, env=ОТОЧЕННЯ)
    with ТЕКА.joinpath("done.txt").open("a", encoding="utf-8") as файл:
        файл.write(f"{datetime.now(timezone.utc).isoformat()} {сцена} rc={результат.returncode}\n")
    subprocess.run(["git", "add", "--", str(ТЕКА.relative_to(КОРІНЬ))], cwd=КОРІНЬ, check=True)
    subprocess.run(["git", "commit", "-m", "Записати тестову сцену " + сцена], cwd=КОРІНЬ, check=True)
    print(f"Збережено {сцена}: rc={результат.returncode}", flush=True)
    if результат.returncode >= 2:
        print("Потрібен розбір збою середовища перед наступною сценою", flush=True)
        sys.exit(результат.returncode)

print("ПЛАН ЗАПИСАНО", flush=True)
