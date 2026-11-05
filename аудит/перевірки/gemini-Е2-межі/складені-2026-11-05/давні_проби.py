"""Звірити дві відмови годинних проб на незмінених модулях бази гілки."""
import json
import os
import subprocess
import sys
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
КОД = ТЕКА.parents[3] / "джерела"
ДО = КОД.parent.parent / "tmp/складені-до"
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
звіт = []
for ім in ("картка_події", "картка_replay"):
    код = ("import sys,runpy;sys.path[:0]=" + repr([str(ДО), str(КОД)]) +
           ";import мовний_шар,картка_запиту,паспорт_поля;runpy.run_path(" +
           repr(str(КОД / ("проби/" + ім + ".py"))) + ",run_name='__main__')")
    з = subprocess.run([sys.executable, "-c", код], cwd=КОД, capture_output=True, text=True, encoding="utf-8")
    (ТЕКА / (ім + "-база.txt")).write_text(з.stdout + з.stderr, encoding="utf-8")
    після = (ТЕКА / (ім + ".txt")).read_text(encoding="utf-8")
    до = з.stdout + з.stderr
    однаково = до.strip().splitlines()[-1] == після.strip().splitlines()[-1]
    звіт.append(dict(проба=ім, код_бази=з.returncode, останній_рядок_збігся=однаково))
(ТЕКА / "давні-проби.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps(звіт, ensure_ascii=False))
sys.exit(int(not all(з["код_бази"] == 1 and з["останній_рядок_збігся"] for з in звіт)))
