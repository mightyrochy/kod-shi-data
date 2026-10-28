"""Незалежно запускає мірила PR #2085 на незмінній голові в окремому дереві."""
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import time


def main():
    """Зберігає команди, повний вивід і коди без перезаписування доказів виконавця."""
    дерево = Path(sys.argv[1]).resolve()
    режим = sys.argv[2]
    докази = Path(__file__).resolve().parent
    джерела = дерево / "джерела"
    пакунки = Path(__file__).resolve().parents[3] / "джерела/node_modules"
    середовище = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                      PYTHONUNBUFFERED="1", NODE_PATH=str(пакунки))
    команди = []
    with tempfile.TemporaryDirectory(prefix="review-2085-") as тимчасова:
        if режим == "мірила":
            архів = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=дерево)
            with tarfile.open(fileobj=io.BytesIO(архів)) as потік:
                потік.extractall(тимчасова, filter="data")
            проба = str(джерела / "проби/каталог_зависла_крамниця_жнива.py")
            команди = [("ДО", [sys.executable, проба, тимчасова], 1),
                       ("ПІСЛЯ", [sys.executable, проба, str(дерево)], 0)]
        elif режим == "сімя":
            файли = sorted((джерела / "проби").glob("каталог_зависла_крамниця*.py"))
            файли += [джерела / "проби" / ф for ф in (
                "каталог_проблеми_г_стеля.py", "каталог_проблеми_г_крамниці.py", "каталог_обхід_стан.py",
                "журнал_стани_5659.py")]
            команди = [(ф.name, [sys.executable, str(ф)] + ([тимчасова] if ф.name == "каталог_обхід_стан.py" else []), 0) for ф in файли]
        elif режим == "батарея":
            команди = [(ф, [sys.executable, ф, *арг], 0) for ф, арг in (
                ("стенд_знімок.py", ["--дим"]), ("тест_живого_шляху.py", []),
                ("тест_протоколу.py", []), ("прилади/розділи_гейтів.py", []), ("audit_contracts.py", []))]
            команди += [("тест_показу.js", ["node", "тест_показу.js"], 0)]
        else:
            raise ValueError(режим)
        результати = []
        with (докази / (режим + ".txt")).open("w", encoding="utf-8", newline="\n") as журнал:
            for назва, команда, очікуваний in команди:
                початок = time.monotonic()
                журнал.write("КОМАНДА: " + subprocess.list2cmdline(команда) + "\n")
                журнал.flush()
                try:
                    код = subprocess.run(команда, cwd=джерела, env=середовище,
                                         stdout=журнал, stderr=subprocess.STDOUT, timeout=1200).returncode
                except subprocess.TimeoutExpired:
                    код = 124
                секунди = round(time.monotonic() - початок, 2)
                журнал.write(f"\nКОД: {код}; очікуваний: {очікуваний}; секунд: {секунди}\n\n")
                журнал.flush()
                результати.append(dict(назва=назва, код=код, очікуваний=очікуваний, секунд=секунди))
                print(f"{назва}: код {код}, очікуваний {очікуваний}, {секунди} с", flush=True)
        (докази / (режим + ".json")).write_text(json.dumps(результати, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return int(any(р["код"] != р["очікуваний"] for р in результати))


if __name__ == "__main__":
    raise SystemExit(main())
