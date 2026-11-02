"""Виконує батарею й мірило до кінця, зберігаючи вивід кожної команди.

Запуск із кореня репозиторію; залежності Node задає середовище NODE_PATH.
"""
import os
from pathlib import Path
import subprocess
import sys


if __name__ == "__main__":
    корінь = Path.cwd()
    звіти = Path(__file__).resolve().parent
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    команди = [
        ("дим", [sys.executable, "стенд_знімок.py", "--дим"]),
        ("живий-шлях", [sys.executable, "тест_живого_шляху.py"]),
        ("протокол", [sys.executable, "тест_протоколу.py"]),
        ("розділи-гейтів", [sys.executable, "прилади/розділи_гейтів.py"]),
        ("контракти", [sys.executable, "audit_contracts.py"]),
        ("показ-після", ["node", "тест_показу.js"]),
        ("обходи", [sys.executable, "проби/текст_жінці_обходи.py"]),
        ("записи", [sys.executable, "проби/текст_жінці_записи.py"]),
        ("записи-самотест", [sys.executable, "проби/текст_жінці_записи_самотест.py"]),
        ("прилад-після", [sys.executable, "прилади/корінь_е2_текст_жінці.py", "."]),
    ]
    хиб = 0
    for назва, команда in команди:
        with (звіти / (назва + ".txt")).open("wb") as журнал:
            результат = subprocess.run(команда, cwd=корінь / "джерела", env=середовище,
                                       stdout=журнал, stderr=subprocess.STDOUT)
        хиб += результат.returncode != 0
        print(f"{назва}: код {результат.returncode}", flush=True)
    print(f"Команд: {len(команди)}, ненульових кодів: {хиб}", flush=True)
    sys.exit(bool(хиб))
