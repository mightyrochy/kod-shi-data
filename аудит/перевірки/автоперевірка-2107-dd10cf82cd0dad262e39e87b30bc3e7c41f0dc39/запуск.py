"""Зберегти команду, повний вивід та її завершений результат."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

дерево = Path(sys.argv[1]).resolve()
назва, команда = sys.argv[2], sys.argv[3:]
тут = Path(__file__).resolve().parent
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                  NODE_PATH=str(дерево / "джерела/node_modules"))
початок = time.monotonic()
р = subprocess.run(команда, cwd=дерево / "джерела", stdout=subprocess.PIPE,
                   stderr=subprocess.STDOUT)
(тут / (назва + ".txt")).write_bytes(р.stdout)
факт = dict(команда=команда, cwd=str(дерево / "джерела"), код=р.returncode,
            секунд=round(time.monotonic() - початок, 2))
(тут / (назва + ".json")).write_text(json.dumps(факт, ensure_ascii=False, indent=2), "utf-8")
print(json.dumps(факт, ensure_ascii=False))
print(р.stdout.decode("utf-8", errors="replace"))
raise SystemExit(р.returncode)
