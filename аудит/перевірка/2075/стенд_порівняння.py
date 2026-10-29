"""Дочеканий повтор стенда на фіксованих id ДО та ПІСЛЯ."""
import json
import os
from pathlib import Path
import subprocess
import sys

тут = Path(__file__).resolve().parent
корінь = тут.parents[2]
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
результати = []
for назва, дерево in (("ДО", Path(sys.argv[1]).resolve()), ("ПІСЛЯ", корінь)):
    команда = [sys.executable, "-X", "utf8", str(дерево / "аудит/проби/тип_кольору_213_стенд.py"),
               str(тут / (назва + "-стенд.json"))]
    if назва == "ПІСЛЯ":
        команда.append(str(тут / "ДО-стенд.json"))
    with (тут / (назва + "-стенд.txt")).open("wb") as ф:
        код = subprocess.run(команда, cwd=дерево / "джерела", stdout=ф, stderr=subprocess.STDOUT).returncode
    результати.append(dict(режим=назва, команда=команда, код=код))
    (тут / "стенд-команди.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf-8")
    print(назва, код, flush=True)
    if код:
        raise SystemExit(код)
