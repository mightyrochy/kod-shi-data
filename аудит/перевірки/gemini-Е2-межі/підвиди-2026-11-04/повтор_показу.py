"""Завершити батарею показу після викладення потрібного архіву sparse-checkout."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
КОД = ТЕКА.parents[3] / "джерела"
os.environ.update(NODE_PATH=str(КОД / "node_modules"), PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
початок = time.monotonic()
with (ТЕКА / "показ-повтор.txt").open("w", encoding="utf-8", newline="\n") as журнал:
    р = subprocess.run(["node", "тест_показу.js"], cwd=КОД, stdout=журнал, stderr=subprocess.STDOUT)
підсумок = dict(команда=["node", "тест_показу.js"], код=р.returncode, секунд=round(time.monotonic()-початок, 2))
(ТЕКА / "показ-повтор.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
print(json.dumps(підсумок, ensure_ascii=False), flush=True)
sys.exit(р.returncode)
