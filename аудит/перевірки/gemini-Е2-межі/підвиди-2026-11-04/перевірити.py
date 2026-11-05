"""Виконати батарею до кінця; повні виводи й коди завершення лишаються поруч."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / "джерела"
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(КОД / "node_modules"))
ПЕРЕВІРКИ = [
    ("дим", [sys.executable, "стенд_знімок.py", "--дим"], КОД),
    ("живий-шлях", [sys.executable, "тест_живого_шляху.py"], КОД),
    ("протокол", [sys.executable, "тест_протоколу.py"], КОД),
    ("гейти", [sys.executable, "прилади/розділи_гейтів.py"], КОД),
    ("контракти", [sys.executable, "audit_contracts.py"], КОД),
    ("показ", ["node", "тест_показу.js"], КОД),
    ("підвиди", [sys.executable, "проби/е2_підвиди_місця.py"], КОД),
    ("вид-факту", [sys.executable, "проби/е2_вид_факту.py"], КОД),
    ("вид-дроту", [sys.executable, "проби/е2_дріт_вид.py"], КОД),
    ("повтор-до", [sys.executable, str(ТЕКА / "повтор.py"), "до"], КОРІНЬ),
    ("повтор-після", [sys.executable, str(ТЕКА / "повтор.py"), "після"], КОРІНЬ),
    ("межі-після", [sys.executable, "джерела/прилади/корінь_е2_межі.py"], КОРІНЬ),
]
підсумок = []
for назва, команда, тека in ПЕРЕВІРКИ:
    print("ПОЧАТО", назва, flush=True)
    початок = time.monotonic()
    with (ТЕКА / (назва + ".txt")).open("w", encoding="utf-8", newline="\n") as журнал:
        р = subprocess.run(команда, cwd=тека, stdout=журнал, stderr=subprocess.STDOUT)
    підсумок.append(dict(назва=назва, команда=команда, тека=str(тека), код=р.returncode,
                         секунд=round(time.monotonic() - початок, 2)))
    (ТЕКА / "підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("ЗАВЕРШЕНО", назва, р.returncode, flush=True)
sys.exit(int(any(п["код"] for п in підсумок)))
