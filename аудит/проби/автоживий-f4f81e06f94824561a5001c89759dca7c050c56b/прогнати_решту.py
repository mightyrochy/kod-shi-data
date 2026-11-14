"""Послідовний запис трьох решти сцен призначеної збірки, без повторів."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ЗБІРКА = КОРІНЬ.parent / "збірка-cff64796"
КЕШ = Path("C:/Users/gemini/pyodide")
ОТОЧЕННЯ = dict(os.environ, NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules",
                PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
ПЕРША = json.loads((ТЕКА / "б1_концерт_стримано/результат.json").read_text(encoding="utf-8"))
if ПЕРША.get("rc") not in (0, 1):
    raise SystemExit("Першу сцену не завершено: решту не почато")

команди = []
for сцена in ("ж4_робота", "ж1_свято_тріада", "ж2_побачення_вечір"):
    команда = [sys.executable, str(ЗБІРКА / "аудит/проби/записати_сцену.py"),
               str(ЗБІРКА), str(КЕШ), str(ТЕКА / сцена), "--сцена", сцена]
    запис = {"сцена": сцена, "команда": команда,
             "початок": datetime.now(timezone.utc).isoformat()}
    print(json.dumps(запис, ensure_ascii=False), flush=True)
    результат = subprocess.run(команда, cwd=КОРІНЬ, env=ОТОЧЕННЯ)
    запис.update(rc=результат.returncode, кінець=datetime.now(timezone.utc).isoformat())
    команди.append(запис)
    (ТЕКА / "команди-решти.json").write_text(json.dumps(команди, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("ЗАВЕРШЕНО " + сцена + ": rc=" + str(результат.returncode), flush=True)
    if результат.returncode not in (0, 1):
        raise SystemExit(результат.returncode)
    subprocess.run(["git", "add", "--", str(ТЕКА)], cwd=КОРІНЬ, check=True)
    subprocess.run(["git", "commit", "-m", "Зберегти завершений запис сцени " + сцена], cwd=КОРІНЬ, check=True)

raise SystemExit(0)
