"""Запустити незмінені прилади голови на заданому дереві та зберегти їхні числа."""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path


def main():
    """Виміряти два корені тими самими приладами та базою довжин."""
    дерево, назва = Path(sys.argv[1]), sys.argv[2]
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[3]
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    результати = []
    for ім, файл, аргументи in (
        ("межі", "корінь_е2_межі.py", []),
        ("промпти", "корінь_е2_промпти.py",
         ["--база", str(корінь / "аудит/корені/Е2-промпти-довжини.json")]),
    ):
        команда = [sys.executable, str(корінь / "джерела/прилади" / файл),
                   "--корінь", str(дерево), *аргументи]
        початок = time.monotonic()
        журнал = тека / (ім + "-" + назва + ".txt")
        print("ПОЧАТО", ім, назва, flush=True)
        with журнал.open("wb") as вихід:
            р = subprocess.run(команда, cwd=дерево, stdout=вихід, stderr=subprocess.STDOUT)
        текст = журнал.read_text(encoding="utf-8", errors="replace")
        числа = re.findall(r"^місць: (\d+)\s*$", текст, re.M)
        результати.append(dict(корінь=ім, дерево=str(дерево), команда=команда,
                               код=р.returncode, місць=int(числа[-1]) if числа else None,
                               секунд=round(time.monotonic() - початок, 2)))
        (тека / ("прилади-" + назва + ".json")).write_text(
            json.dumps(результати, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("ЗАВЕРШЕНО", ім, назва, результати[-1]["місць"], р.returncode, flush=True)
    return int(any(р["код"] or р["місць"] is None for р in результати))


if __name__ == "__main__":
    sys.exit(main())
