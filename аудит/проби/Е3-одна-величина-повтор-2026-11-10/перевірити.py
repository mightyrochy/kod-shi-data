"""Повторює чинне мірило доробки #3089 після злиття main без нових гейтів."""
import datetime
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Запускає чинні перевірки й зберігає їхні журнали та коди завершення."""
    звіти = Path(__file__).resolve().parent
    корінь = звіти.parents[2]
    джерела = корінь / "джерела"
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                       NODE_PATH=str(джерела / "node_modules"))
    середовище.pop("MODEL", None)
    команди = [
        ("прилад", корінь, [sys.executable, "джерела/прилади/корінь_е3_одна_величина.py", "--тихо"]),
        ("дим", джерела, [sys.executable, "стенд_знімок.py", "--дим"]),
        ("живий-шлях", джерела, [sys.executable, "тест_живого_шляху.py"]),
        ("протокол", джерела, [sys.executable, "тест_протоколу.py"]),
        ("гейти", джерела, [sys.executable, "прилади/розділи_гейтів.py"]),
        ("контракти", джерела, [sys.executable, "audit_contracts.py"]),
        ("показ", джерела, ["node", "тест_показу.js"]),
        ("питання-картки", корінь, ["node", "аудит/проби/Е3_питання_картки.js"]),
        ("спільні-питання", джерела, ["node", "проби/шар_спільні_питання.js"]),
        ("запис", джерела, [sys.executable, "проби/запис_одна_величина.py"]),
        ("запис-каталог", корінь, [sys.executable, "аудит/проби/Е3_запис_каталог.py"]),
    ]
    лише_проби = "--лише-проби" in sys.argv
    if лише_проби:
        команди = [к for к in команди if к[0] in {"питання-картки", "спільні-питання", "запис"}]
    файл_результату = "результат-проб.json" if лише_проби else "результат.json"
    результат = {
        "час_UTC": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "голова": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь, text=True).strip(),
        "python": sys.version,
        "перевірки": [],
    }
    for назва, тека, команда in команди:
        початок = time.monotonic()
        прогін = subprocess.run(команда, cwd=тека, env=середовище,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        with gzip.open(звіти / (назва + ".log.gz"), "wb") as журнал:
            журнал.write(прогін.stdout)
        рядок = dict(назва=назва, команда=команда, код=прогін.returncode,
                     секунд=round(time.monotonic() - початок, 2))
        результат["перевірки"].append(рядок)
        (звіти / файл_результату).write_text(
            json.dumps(результат, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{назва}: код {прогін.returncode}; {рядок['секунд']} с", flush=True)
        if прогін.returncode:
            print(прогін.stdout.decode("utf-8", errors="replace")[-4000:], flush=True)
    return int(any(п["код"] for п in результат["перевірки"]))


if __name__ == "__main__":
    sys.exit(головна())
