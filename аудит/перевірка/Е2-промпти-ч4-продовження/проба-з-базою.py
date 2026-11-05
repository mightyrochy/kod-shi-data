"""Повторює архівну пробу з обома зміненими Python-модулями бази замість голови."""
from pathlib import Path
import os
import runpy
import subprocess
import sys
import types

КОРІНЬ = Path(__file__).resolve().parents[3]
база, проба = sys.argv[1:]
sys.path.insert(0, str(КОРІНЬ / "джерела"))
os.chdir(КОРІНЬ / "джерела")
for назва in ("спільні_вимоги", "жнива_збагачення"):
    шлях = "джерела/" + назва + ".py"
    текст = subprocess.check_output(["git", "show", база + ":" + шлях], cwd=КОРІНЬ)
    модуль = types.ModuleType(назва)
    модуль.__file__ = str(КОРІНЬ / шлях)
    sys.modules[назва] = модуль
    exec(compile(текст, модуль.__file__, "exec"), модуль.__dict__)
sys.argv = [str(КОРІНЬ / проба)]
runpy.run_path(sys.argv[0], run_name="__main__")
