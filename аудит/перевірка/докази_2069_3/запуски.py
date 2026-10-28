"""Команди перевірки з дослівним виводом і кодами; кожен процес очікується до кінця."""
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
ДЖЕРЕЛА = КОРІНЬ / "джерела"
СЕРЕДОВИЩЕ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                   NODE_PATH=str(ДЖЕРЕЛА / "node_modules"))


def команда(аргументи, файл, cwd=КОРІНЬ):
    with (ТЕКА / файл).open("a", encoding="utf-8", newline="\n") as лог:
        лог.write("КОМАНДА: " + subprocess.list2cmdline(list(map(str, аргументи))) + "\n")
        лог.flush()
        результат = subprocess.run(list(map(str, аргументи)), cwd=cwd, env=СЕРЕДОВИЩЕ,
                                    stdout=лог, stderr=subprocess.STDOUT, timeout=1800)
        лог.write(f"\nКОД: {результат.returncode}\n\n")
    print(f"{Path(аргументи[1]).name}: код {результат.returncode}", flush=True)
    return результат.returncode


def main():
    режим = sys.argv[1]
    коди = []
    if режим == "власні":
        with tempfile.TemporaryDirectory(prefix="review-2069-before-") as тека:
            архів = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=КОРІНЬ)
            with tarfile.open(fileobj=io.BytesIO(архів)) as файл:
                файл.extractall(тека, filter="data")
            for дерево, назва in ((тека, "ДО.txt"), (КОРІНЬ, "ПІСЛЯ.txt")):
                коди.append(команда([sys.executable, ТЕКА / "незалежна.py", дерево], назва))
        коди.append(команда([sys.executable, ТЕКА / "повтор_2053.py", КОРІНЬ], "повтор_2053.txt"))
    elif режим == "батарея":
        for арг in (["стенд_знімок.py", "--дим"], ["тест_живого_шляху.py"], ["тест_протоколу.py"],
                    ["прилади/розділи_гейтів.py"], ["audit_contracts.py"]):
            коди.append(команда([sys.executable, *арг], "батарея.txt", ДЖЕРЕЛА))
        коди.append(команда(["node", "тест_показу.js"], "батарея.txt", ДЖЕРЕЛА))
    elif режим == "сім’я":
        проби = sorted((ДЖЕРЕЛА / "проби").glob("каталог_зависла_крамниця*.py"))
        проби += [ДЖЕРЕЛА / "проби" / н for н in ("каталог_проблеми_г_стеля.py", "каталог_проблеми_г_крамниці.py",
                     "журнал_стани_5659.py", "журнал_перелік_7130.py")]
        for файл in проби:
            коди.append(команда([sys.executable, файл], "сім’я.txt", ДЖЕРЕЛА))
        коди.append(команда([sys.executable, ДЖЕРЕЛА / "проби/журнал_відновлення_5659.py",
                              КОРІНЬ / "zhnyvarka/фікстури/bella_6975_20261017_raw.html"], "сім’я.txt", ДЖЕРЕЛА))
        with tempfile.TemporaryDirectory(prefix="review-2069-state-") as журнал:
            коди.append(команда([sys.executable, ДЖЕРЕЛА / "проби/каталог_обхід_стан.py", журнал], "сім’я.txt", ДЖЕРЕЛА))
        коди.append(команда([sys.executable, "аудит/перевірки/доробка-53Б-журнал/відтворення.py", str(КОРІНЬ)], "сім’я.txt"))
        коди.append(команда([sys.executable, "аудит/перевірки/доробка-53Б-журнал/автоперевірка_доказ.py", str(КОРІНЬ)], "сім’я.txt"))
    elif режим == "контроль":
        коди.append(команда([sys.executable, "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], "дошка.txt"))
        коди.append(команда([sys.executable, "досяжність.py"], "досяжність.txt", ДЖЕРЕЛА))
        коди.append(команда(["node", ТЕКА / "знімок.cjs"], "знімок.txt"))
        коди.append(команда(["git", "diff", "--check"], "диф.txt"))
    print(f"Запусків {len(коди)}; кодів 0: {коди.count(0)}; коди: {коди}", flush=True)
    return int(any(коди))


if __name__ == "__main__":
    raise SystemExit(main())
