"""Завершений прогін спільної батареї та сім'ї ознак для доробки опису person."""
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """Виконує наявні перевірки, зберігаючи код виходу й повний журнал кожної."""
    тут = Path(__file__).resolve().parent
    код = тут.parents[2] / "джерела"
    оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                    NODE_PATH=str(код / "node_modules"))
    команди = [
        [sys.executable, "стенд_знімок.py", "--дим"],
        [sys.executable, "тест_живого_шляху.py"],
        [sys.executable, "тест_протоколу.py"],
        [sys.executable, "прилади/розділи_гейтів.py"],
        [sys.executable, "audit_contracts.py"],
        ["node", "тест_показу.js"],
    ]
    команди.extend([sys.executable, str(п.relative_to(код))]
                   for п in sorted((код / "проби").glob("ознаки_*.py"))
                   if п.name != "ознаки_межа_5192.py")
    результати = []
    for команда in команди:
        ім = Path(команда[1]).stem
        початок = time.monotonic()
        журнал = тут / (ім + ".log")
        with журнал.open("wb") as ф:
            р = subprocess.run(команда, cwd=код, env=оточення, stdout=ф, stderr=subprocess.STDOUT)
        стислий = журнал.with_suffix(".log.gz")
        with gzip.open(стислий, "wb") as ф:
            ф.write(журнал.read_bytes())
        журнал.unlink()
        результати.append(dict(команда=команда[1:], код=р.returncode,
                              секунд=round(time.monotonic() - початок, 2), журнал=стислий.name))
        (тут / "батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf-8")
        print(ім, "код", р.returncode, "секунд", результати[-1]["секунд"], flush=True)
    return int(any(р["код"] for р in результати))


if __name__ == "__main__":
    sys.exit(main())
