"""Виконує всю обов'язкову батарею й проби сім'ї, зберігаючи кожний результат."""
import json
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
ДЖЕРЕЛА = ТЕКА.parents[2] / "джерела"


def main():
    """Ганяє всі команди до кінця, включно з командами після падіння."""
    команди = [
        [sys.executable, "стенд_знімок.py", "--дим"],
        [sys.executable, "тест_живого_шляху.py"],
        [sys.executable, "тест_протоколу.py"],
        [sys.executable, "прилади/розділи_гейтів.py"],
        [sys.executable, "audit_contracts.py"],
        ["node", "тест_показу.js"],
        [sys.executable, "проби/жнива_вставка.py"],
        [sys.executable, "проби/поділ_жнива_ast.py"],
        [sys.executable, "проби/поділ_жнива_офлайн.py"],
    ]
    результати = []
    for номер, команда in enumerate(команди, 1):
        шлях = ТЕКА / ("батарея_%02d.txt" % номер)
        with шлях.open("w", encoding="utf-8") as лог:
            р = subprocess.run(команда, cwd=ДЖЕРЕЛА, stdout=лог, stderr=subprocess.STDOUT)
        результати.append({"команда": команда, "код": р.returncode, "лог": шлях.name})
        print(номер, "код", р.returncode, " ".join(команда[1:]), flush=True)
    (ТЕКА / "батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    raise SystemExit(int(any(р["код"] for р in результати)))


if __name__ == "__main__":
    main()
