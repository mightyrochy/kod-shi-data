"""Запускає єдину призначену сцену на передньому плані та зберігає команду й код виходу."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

тека = Path(__file__).resolve().parent
корінь = тека.parents[2]
середовище = json.loads((тека / "середовище.json").read_text(encoding="utf-8"))
assert середовище["rc"] == 0
env = dict(os.environ, NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules",
           PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
assert env.get("NODE_OPTIONS") == середовище["змінні"]["NODE_OPTIONS"]
assert env.get("PYTHONPATH") == середовище["змінні"]["PYTHONPATH"]
команда = [sys.executable, str(корінь / "аудит/проби/записати_сцену.py"),
           str(корінь.parent / "tmp/збірка"), "C:/Users/gemini/pyodide",
           str(тека / "б1_концерт_стримано"), "--сцена", "б1_концерт_стримано"]
запис = {"початок_utc": datetime.now(timezone.utc).isoformat(), "команда": команда,
         "cwd": str(корінь), "змінні": {к: env[к] for к in ["NODE_PATH", "NODE_OPTIONS", "PYTHONPATH", "PYTHONUTF8", "PYTHONIOENCODING"]}}
(тека / "команди.json").write_text(json.dumps(запис, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
with (тека / "запуск.txt").open("w", encoding="utf-8") as лог:
    р = subprocess.run(команда, cwd=корінь, env=env, stdout=лог, stderr=subprocess.STDOUT)
запис.update(rc=р.returncode, кінець_utc=datetime.now(timezone.utc).isoformat())
(тека / "команди.json").write_text(json.dumps(запис, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print((тека / "запуск.txt").read_text(encoding="utf-8"))
raise SystemExit(р.returncode)
