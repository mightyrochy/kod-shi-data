"""Зберігає нові виводи штатних команд, не переписуючи докази попередньої перевірки."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ПОПЕРЕДНІ = КОРІНЬ / "аудит/перевірка/докази_2069_3"
СЕРЕДОВИЩЕ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")


def команда(аргументи, назва):
    """Очікує завершення процесу й зберігає його обидва потоки та код."""
    with (ТЕКА / назва).open("w", encoding="utf-8", newline="\n") as лог:
        лог.write("КОМАНДА: " + subprocess.list2cmdline(list(map(str, аргументи))) + "\n")
        лог.flush()
        результат = subprocess.run(list(map(str, аргументи)), cwd=КОРІНЬ, env=СЕРЕДОВИЩЕ,
                                    stdout=лог, stderr=subprocess.STDOUT, timeout=7200)
        лог.write(f"\nКОД: {результат.returncode}\n")
    print(f"{назва}: код {результат.returncode}", flush=True)
    return результат.returncode


def main():
    """Виконує один режим, передаючи штатному приладу незмінні аргументи."""
    режим = sys.argv[1]
    if режим == "до":
        with tempfile.TemporaryDirectory(prefix="доробка-2069-2-до-") as тека:
            архів = subprocess.check_output(["git", "archive", "7a3173e767b403ffcee0030dea4a721cb4dd156b",
                                             "zhnyvarka", "джерела/проби"], cwd=КОРІНЬ)
            with tarfile.open(fileobj=io.BytesIO(архів)) as файл:
                файл.extractall(тека, filter="data")
            код = команда([sys.executable, ПОПЕРЕДНІ / "повтор_2053.py", тека], "ДО.txt")
        return int(код != 1)
    if режим == "стійкість":
        return команда([sys.executable, ТЕКА / "стійкість.py"], "стійкість.txt")
    назви = {"власні": ["ДО.txt", "ПІСЛЯ.txt", "повтор_2053.txt"], "сім’я": ["сім’я.txt"],
             "послідовні": ["послідовні.txt"], "батарея": ["батарея.txt"]}[режим]
    давні = {назва: (ПОПЕРЕДНІ / назва).read_bytes() for назва in назви}
    try:
        код = команда([sys.executable, ПОПЕРЕДНІ / "запуски.py", режим], f"запуск-{режим}.txt")
    finally:
        for назва, вміст in давні.items():
            файл = ПОПЕРЕДНІ / назва
            новий = файл.read_bytes()
            assert новий.startswith(вміст), назва
            (ТЕКА / ("власні-ДО.txt" if назва == "ДО.txt" else назва)).write_bytes(новий[len(вміст):])
            файл.write_bytes(вміст)
    return код


if __name__ == "__main__":
    raise SystemExit(main())
