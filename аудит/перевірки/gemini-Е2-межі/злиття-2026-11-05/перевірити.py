"""Завершити батарею й проби меж після злиття main, зберігши всі результати."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    """Послідовно виконати всі перевірки, навіть після відмови окремої."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[3]
    код = корінь / "джерела"
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                      NODE_PATH=str(код / "node_modules"))
    команди = [
        ("каталог", [sys.executable, "-c", "import чистка_каталогу as ч, feed as ф; "
                    "print(ч.забезпечити_чистим('каталог_повний.xml')); "
                    "print(ф.каталог_на_диску('каталог_brief.xml'))"]),
        ("дим", [sys.executable, "стенд_знімок.py", "--дим"]),
        ("живий-шлях", [sys.executable, "тест_живого_шляху.py"]),
        ("протокол", [sys.executable, "тест_протоколу.py"]),
        ("гейти", [sys.executable, "прилади/розділи_гейтів.py"]),
        ("контракти", [sys.executable, "audit_contracts.py"]),
        ("показ", ["node", "тест_показу.js"]),
    ]
    команди += [(ф.stem, [sys.executable, str(ф)])
                for ф in sorted((код / "проби").glob("е2_*.py"))]
    команди.append(("промпти3_розмова_розмір",
                    [sys.executable, "проби/промпти3_розмова_розмір.py"]))
    підсумок = []
    for назва, команда in команди:
        print("ПОЧАТО", назва, flush=True)
        початок = time.monotonic()
        with (тека / (назва + ".txt")).open("wb") as журнал:
            результат = subprocess.run(команда, cwd=код, stdout=журнал,
                                       stderr=subprocess.STDOUT)
        підсумок.append(dict(назва=назва, команда=команда, код=результат.returncode,
                             секунд=round(time.monotonic() - початок, 2)))
        (тека / "підсумок.json").write_text(
            json.dumps(підсумок, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("ЗАВЕРШЕНО", назва, результат.returncode, flush=True)
    return int(any(п["код"] for п in підсумок))


if __name__ == "__main__":
    sys.exit(main())
