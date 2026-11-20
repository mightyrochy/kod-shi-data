"""Передній запуск плану й негайне звільнення GPU після його завершення."""
from pathlib import Path
from datetime import datetime, timezone
import json
import os
import subprocess
import sys

корінь = Path(__file__).resolve().parents[3]
вихід = Path(__file__).resolve().parent
os.chdir(корінь)
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=r"C:\Users\gemini\kod-shi-test-node\node_modules")
команда = [sys.executable, "аудит/проби/записати_план.py", str(вихід / "ПЛАН.json"),
           str(корінь.parent / "tmp/збірка-e45a0d9"), r"C:\Users\gemini\pyodide", str(вихід)]
запис = {"початок": datetime.now(timezone.utc).isoformat(), "команда": команда, "межа_секунд": 9600}
try:
    with (вихід / "план_вивід.txt").open("w", encoding="utf-8") as лог:
        р = subprocess.run(команда, stdout=лог, stderr=subprocess.STDOUT, timeout=9600)
        запис["rc"] = р.returncode
finally:
    with (вихід / "кінець_моделі.txt").open("w", encoding="utf-8") as лог:
        к = subprocess.run([sys.executable, "аудит/проби/кінець_моделі.py"], stdout=лог, stderr=subprocess.STDOUT)
    запис["кінець_моделі_rc"] = к.returncode
    запис["кінець"] = datetime.now(timezone.utc).isoformat()
    (вихід / "запуск.json").write_text(json.dumps(запис, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(запис, ensure_ascii=False), flush=True)
raise SystemExit(запис.get("rc", 2))
