"""Виконати перевірки послідовно й зберегти завершені результати."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main():
    """Виконати вимір лише під час запуску скрипту."""
    ТЕКА = Path(__file__).resolve().parent
    КОРІНЬ = ТЕКА.parents[3]
    КОД = КОРІНЬ / "джерела"
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(КОД / "node_modules"))
    ПЕРЕВІРКИ = [
        ("вимір-до", [sys.executable, str(ТЕКА / "вимір.py"), "до"], КОРІНЬ),
        ("вимір-після", [sys.executable, str(ТЕКА / "вимір.py"), "після"], КОРІНЬ),
        ("промпти-після", [sys.executable, "джерела/прилади/корінь_е2_промпти.py",
                           "--база", "аудит/корені/Е2-промпти-довжини.json"], КОРІНЬ),
        ("межі-після", [sys.executable, "джерела/прилади/корінь_е2_межі.py"], КОРІНЬ),
        ("каталоги", [sys.executable, "-c", "import чистка_каталогу as ч, feed as Ф; "
                      "print(ч.забезпечити_чистим('каталог_повний.xml')); "
                      "print(Ф.каталог_на_диску('каталог_brief.xml'))"], КОД),
        ("дим", [sys.executable, "стенд_знімок.py", "--дим"], КОД),
        ("живий-шлях", [sys.executable, "тест_живого_шляху.py"], КОД),
        ("протокол", [sys.executable, "тест_протоколу.py"], КОД),
        ("гейти", [sys.executable, "прилади/розділи_гейтів.py"], КОД),
        ("контракти", [sys.executable, "audit_contracts.py"], КОД),
        ("показ", ["node", "тест_показу.js"], КОД),
    ]
    for файл in sorted((КОД / "проби").glob("е2_*.py")):
        ПЕРЕВІРКИ.append((файл.stem, [sys.executable, str(файл)], КОД))
    підсумок = []
    for назва, команда, тека in ПЕРЕВІРКИ:
        print("ПОЧАТО", назва, flush=True)
        початок = time.monotonic()
        with (ТЕКА / (назва + ".txt")).open("wb") as журнал:
            р = subprocess.run(команда, cwd=тека, stdout=журнал, stderr=subprocess.STDOUT)
        підсумок.append(dict(назва=назва, команда=команда, тека=str(тека), код=р.returncode,
                             секунд=round(time.monotonic() - початок, 2)))
        (ТЕКА / "підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("ЗАВЕРШЕНО", назва, р.returncode, flush=True)
    sys.exit(int(any(п["код"] for п in підсумок)))


if __name__ == "__main__":
    main()
