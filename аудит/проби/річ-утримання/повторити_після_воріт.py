"""Повтор зачеплених перевірок після виправлення джерела воріт пакета."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
команди = [
    ("шлях-остаточний", [str(Д / "шлях.py"), str(Д / "шлях-після.json.gz")]),
    ("сцени-остаточні", [str(Д / "сцени.py"), "після"]),
    ("живий-шлях-остаточний", [str(К / "джерела/тест_живого_шляху.py")]),
    ("поділ-colorspace-остаточний", [str(К / "джерела/проби/поділ_colorspace_ast.py")]),
    ("ознаки-джерело-пакета", [str(К / "джерела/проби/ознаки_джерело_пакета.py")]),
]
результати = []
for назва, арг in команди:
    t = time.monotonic()
    with (Д / (назва + ".log")).open("wb") as ф:
        р = subprocess.run([sys.executable] + арг, cwd=К / "джерела", env=env, stdout=ф, stderr=subprocess.STDOUT)
    результати.append(dict(назва=назва, код=р.returncode, секунд=round(time.monotonic() - t, 2)))
    print(назва, результати[-1], flush=True)
(Д / "повтор-ворота.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf8")
sys.exit(any(р["код"] for р in результати))
