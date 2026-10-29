"""ДО/ПІСЛЯ справжнього моста або заміни зі штатним судом образу.

Другий аргумент необов'язковий: колір_тип_213_заміна_суд.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def головна():
    """Виконати ту саму пробу в двох деревах і зберегти журнали."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    до = Path(sys.argv[1]).resolve()
    ім = sys.argv[2] if len(sys.argv) > 2 else "колір_тип_213_основа"
    підсумок = {"колір_тип_213_основа": "основа-результати.json",
                "колір_тип_213_заміна_суд": "заміна-суд-результати.json"}[ім]
    shutil.copy2(корінь / "джерела/проби" / (ім + ".py"), до / "джерела/проби" / (ім + ".py"))
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    результати = []
    for режим, дерево in (("ДО", до), ("ПІСЛЯ", корінь)):
        команда = [sys.executable, "-X", "utf8", "проби/" + ім + ".py"]
        початок = time.monotonic()
        with (тека / (режим + "-" + ім + ".txt")).open("wb") as журнал:
            р = subprocess.run(команда, cwd=дерево / "джерела", stdout=журнал, stderr=subprocess.STDOUT)
        запис = dict(режим=режим, назва=ім, команда=команда, код=р.returncode,
                      секунд=round(time.monotonic() - початок, 2))
        результати.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
        (тека / підсумок).write_bytes(
            json.dumps(результати, ensure_ascii=False, indent=2).encode("utf-8"))
    return результати[-1]["код"]


if __name__ == "__main__":
    raise SystemExit(головна())
