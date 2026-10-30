"""ДО/ПІСЛЯ стенда 2.13 на тих самих id речей, без викликів моделей."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Зберегти повні знімки з окремим охопленням без входу кольору."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    результати = []
    for режим, дерево in (("ДО", Path(sys.argv[1]).resolve()), ("ПІСЛЯ", корінь)):
        команда = [sys.executable, "-X", "utf8", str(дерево / "аудит/проби/тип_кольору_213_стенд.py"),
                   str(тека / (режим + "-стенд.json"))]
        if режим == "ПІСЛЯ":
            команда.append(str(тека / "ДО-стенд.json"))
        початок = time.monotonic()
        with (тека / (режим + "-стенд.txt")).open("wb") as журнал:
            р = subprocess.run(команда, cwd=дерево / "джерела", stdout=журнал, stderr=subprocess.STDOUT)
        запис = dict(режим=режим, назва="стенд-2.13", команда=команда, код=р.returncode,
                      секунд=round(time.monotonic() - початок, 2))
        результати.append(запис)
        print(json.dumps(запис, ensure_ascii=False), flush=True)
        (тека / "стенд-результати.json").write_bytes(
            json.dumps(результати, ensure_ascii=False, indent=2).encode("utf-8"))
        if р.returncode:
            return р.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(головна())
