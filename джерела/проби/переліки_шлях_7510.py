"""§126 бере той самий експорт із cwd кореня й джерел; хибний source не приймає."""
import ast
import json
import os
import sys
import tempfile
from pathlib import Path

ДЖЕРЕЛА = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ДЖЕРЕЛА))
import build_артефакт as Б

дерево = ast.parse((ДЖЕРЕЛА / "прилади/розділи_гейтів.py").read_text(encoding="utf-8"))
вузли = {n.targets[0].id: n for n in ast.walk(дерево)
         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
звідки = os.getcwd()
try:
    експорти = []
    for cwd in (ДЖЕРЕЛА.parent, ДЖЕРЕЛА):
        os.chdir(cwd)
        ns = {"_os": os, "_тут": str(ДЖЕРЕЛА), "_Б126": Б, "_json": json}
        for ім in ("_шлях", "_переліки126"):
            exec(compile(ast.Module(body=[вузли[ім]], type_ignores=[]), "§126", "exec"), ns)
        експорти.append(ns["_переліки126"])
    assert експорти[0] == експорти[1]
    with tempfile.TemporaryDirectory() as тека:
        for хибне in ("", тека, str(Path(тека) / "нема")):
            try:
                Б._переліки_показу(хибне)
            except (OSError, SystemExit):
                continue
            raise AssertionError("Хибне джерело прийнято: %r" % хибне)
finally:
    os.chdir(звідки)
print("§126: cwd кореня/джерел дають тотожний JSON; 3 хибні джерела відхилено")
