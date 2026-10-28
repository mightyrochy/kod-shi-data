"""Виконує команди перевірки послідовно та зберігає їхні повні виводи."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

ДЕРЕВО = Path(sys.argv[1]).resolve()
ДОКАЗИ = Path(__file__).resolve().parent
РЕЖИМ = sys.argv[2]
СЕРЕДОВИЩЕ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                   NODE_PATH=str(ДОКАЗИ.parents[2] / "джерела/node_modules"))


def виконати(аргументи, назва, тека=ДЕРЕВО):
    """Очікує завершення однієї команди, зберігаючи команду, SHA й код поруч із виводом."""
    with (ДОКАЗИ / (назва + ".txt")).open("w", encoding="utf-8") as лог:
        лог.write("КОМАНДА: " + subprocess.list2cmdline(list(map(str, аргументи))) + "\n")
        лог.write("ТЕКА: " + str(тека) + "\n")
        лог.write("SHA: " + subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ДЕРЕВО).decode().strip() + "\n")
        лог.flush()
        р = subprocess.run(list(map(str, аргументи)), cwd=тека, env=СЕРЕДОВИЩЕ,
                           stdout=лог, stderr=subprocess.STDOUT, timeout=1800)
        лог.write(f"\nКОД: {р.returncode}\n")
    print(f"{назва}: код {р.returncode}", flush=True)
    return dict(назва=назва, код=р.returncode)


def main():
    """Обирає батарею чи сімейство; усі запуски виконуються до кінця."""
    коди = []
    if РЕЖИМ == "батарея":
        for н, арг in enumerate((["стенд_знімок.py", "--дим"], ["тест_живого_шляху.py"],
                                ["тест_протоколу.py"], ["прилади/розділи_гейтів.py"], ["audit_contracts.py"]), 1):
            коди.append(виконати([sys.executable, *арг], f"батарея-{н}", ДЕРЕВО / "джерела"))
        коди.append(виконати(["node", "тест_показу.js"], "батарея-6", ДЕРЕВО / "джерела"))
    elif РЕЖИМ == "сімейство":
        файли = sorted((ДЕРЕВО / "джерела/проби").glob("каталог_зависла_крамниця*.py"))
        файли += [ДЕРЕВО / "джерела/проби" / н for н in
                  ("каталог_проблеми_г_стеля.py", "каталог_проблеми_г_крамниці.py", "журнал_стани_5659.py", "журнал_перелік_7130.py")]
        for н, файл in enumerate(файли, 1):
            коди.append(виконати([sys.executable, файл], f"сімейство-{н:02}", ДЕРЕВО / "джерела"))
        коди.append(виконати([sys.executable, ДЕРЕВО / "джерела/проби/журнал_відновлення_5659.py",
                              ДЕРЕВО / "zhnyvarka/фікстури/bella_6975_20261017_raw.html"], "відновлення", ДЕРЕВО / "джерела"))
    elif РЕЖИМ == "основні":
        база = ДЕРЕВО / "аудит/перевірка/докази_2069_3"
        for файл, назва in (("незалежна.py", "ПІСЛЯ"), ("повтор_2053.py", "повтор-2053"), ("послідовні.py", "послідовні")):
            коди.append(виконати([sys.executable, база / файл, ДЕРЕВО], назва))
        коди.append(виконати([sys.executable, ДЕРЕВО / "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], "дошка"))
    elif РЕЖИМ == "власні":
        коди.append(виконати([sys.executable, ДОКАЗИ / "власні.py", ДЕРЕВО], "власні"))
    elif РЕЖИМ == "знімок":
        коди.append(виконати(["node", ДОКАЗИ / "знімок.cjs"], "знімок"))
    elif РЕЖИМ == "контроль":
        коди.append(виконати(["git", "diff", "--exit-code", "3f1ad74a48e26e4b200637a851b5943c5ff62383", "--",
                              "zhnyvarka", "джерела", ".github", "аудит/адаптери/gemini"], "незмінність"))
        коди.append(виконати(["git", "diff", "--name-only", "7561309d7644bff3600a3cc1b07704661a85150f...HEAD", "--",
                              ".github", "аудит/адаптери/gemini"], "захищені-теки"))
        коди.append(виконати(["git", "rev-parse", "HEAD"], "голова"))
        коди.append(виконати(["git", "branch", "--show-current"], "гілка", ДОКАЗИ.parents[2]))
    elif РЕЖИМ == "до":
        with tempfile.TemporaryDirectory(prefix="review-2105-before-") as тека:
            дані = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=ДЕРЕВО)
            with tarfile.open(fileobj=io.BytesIO(дані)) as архів:
                архів.extractall(тека, filter="data")
            коди.append(виконати([sys.executable, ДЕРЕВО / "аудит/перевірка/докази_2069_3/незалежна.py", тека], "ДО"))
    else:
        raise ValueError(РЕЖИМ)
    (ДОКАЗИ / (РЕЖИМ + ".json")).write_text(json.dumps(коди, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Запусків {len(коди)}, кодів 0: {sum(з['код'] == 0 for з in коди)}", flush=True)


if __name__ == "__main__":
    main()
