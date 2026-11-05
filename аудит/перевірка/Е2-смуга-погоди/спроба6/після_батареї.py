"""Послідовно завершує виміри доробки після основної батареї."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time

КОРІНЬ = Path(__file__).resolve().parents[4]
ЖУРНАЛИ = Path(__file__).resolve().parent
ПІТОН_311 = КОРІНЬ.parent / "tmp/python/cpython-3.11.18-windows-x86_64-none/python.exe"


if __name__ == "__main__":
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore")
    for ключ in ("MODEL_URL", "MODEL_MOVA"):
        середовище.pop(ключ, None)
    команди = (
        ("прилад-після", [str(ПІТОН_311), "джерела/прилади/корінь_е2_смуга_погоди.py", "--тихо"], КОРІНЬ),
        ("каталог-верхнього", [sys.executable, str(ЖУРНАЛИ / "каталог_верхнього.py")], КОРІНЬ),
        ("живий-шлях-повтор", [sys.executable, "тест_живого_шляху.py"], КОРІНЬ / "джерела"),
        ("верхній-шар-повтор", [sys.executable, "джерела/проби/wea_верхній_шар.py"], КОРІНЬ),
        ("дошка", [sys.executable, "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], КОРІНЬ),
    )
    звіт = dict(UTC=datetime.now(timezone.utc).isoformat(),
                код_продукту=subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=КОРІНЬ, text=True).strip(),
                перевірки=[])
    for назва, аргументи, тека in команди:
        початок = time.monotonic()
        with (ЖУРНАЛИ / (назва + ".txt")).open("w", encoding="utf-8") as вихід:
            код = subprocess.run(аргументи, cwd=тека, env=середовище,
                                 stdout=вихід, stderr=subprocess.STDOUT).returncode
        рядок = dict(назва=назва, код=код, секунд=round(time.monotonic() - початок, 1), команда=аргументи)
        звіт["перевірки"].append(рядок)
        (ЖУРНАЛИ / "після-батареї.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(рядок, ensure_ascii=False), flush=True)
    sys.exit(any(р["код"] for р in звіт["перевірки"]))
