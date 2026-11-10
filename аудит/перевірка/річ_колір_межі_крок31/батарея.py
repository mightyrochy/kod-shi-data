"""Батарея кроку 31: кожна команда до кінця; повний вивід — окремим файлом."""
import os
import subprocess
import sys
from pathlib import Path


def головна():
    """Виконати обов'язкову батарею й проби сім'ї та зберегти коди виходу."""
    корінь = Path(__file__).resolve().parents[3]
    джерела = корінь / "джерела"
    звіт = Path(__file__).resolve().parent
    os.environ["PYTHONUTF8"] = "1"
    os.environ["NODE_PATH"] = str(джерела / "node_modules")
    команди = [
        [sys.executable, "стенд_знімок.py", "--дим"],
        [sys.executable, "тест_живого_шляху.py"],
        [sys.executable, "тест_протоколу.py"],
        [sys.executable, "прилади/розділи_гейтів.py"],
        [sys.executable, "audit_contracts.py"],
        ["node", "тест_показу.js"],
    ]
    проби = sorted((джерела / "проби").glob("поділ_*_ast.py"))
    проби += sorted(п for п in (джерела / "проби").glob("pal_*.py")
                    if п.name not in ("pal_вердикт.py", "pal_вимір.py"))
    проби += sorted((джерела / "проби").glob("колір_тип_213_*.py"))
    проби += [джерела / "проби/прикраси_обруч_6877.py"]
    команди += [[sys.executable, str(п.relative_to(джерела))] for п in проби]
    рядки = []
    for команда in команди:
        мітка = Path(команда[1]).stem
        with (звіт / (мітка + ".txt")).open("w", encoding="utf-8") as файл:
            вихід = subprocess.run(команда, cwd=джерела, stdout=файл, stderr=subprocess.STDOUT)
        рядок = " ".join(команда[1:]) + f": код {вихід.returncode}"
        рядки.append(рядок)
        print(рядок, flush=True)
        (звіт / "батарея.txt").write_text("\n".join(рядки) + "\n", encoding="utf-8")
    sys.exit(any(not р.endswith(": код 0") for р in рядки))


if __name__ == "__main__":
    головна()
