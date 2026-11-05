"""Один завершений прогін сім'ї ознак; --зі-спільними додає шість спільних перевірок."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
код = К / "джерела"
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(код / "node_modules"))
спільні = [
    [sys.executable, "стенд_знімок.py", "--дим"],
    [sys.executable, "тест_живого_шляху.py"],
    [sys.executable, "тест_протоколу.py"],
    [sys.executable, "прилади/розділи_гейтів.py"],
    [sys.executable, "audit_contracts.py"],
    ["node", "тест_показу.js"],
]
команди = спільні if "--зі-спільними" in sys.argv else []
проби = set()
for шаблон in ("ознаки_*.py", "поділ_palette_ast.py", "поділ_pipeline_ast.py", "поділ_bridge_ast.py", "поділ_colorspace_ast.py",
               "rang_нейтраль_якір.py", "pc_R-PC-10.py", "bas_ochi_foto_н1.py", "підтон_v03_009.py"):
    проби.update((код / "проби").glob(шаблон))
проби = sorted(п for п in проби if п.name != "ознаки_межа_5192.py")
команди.extend([sys.executable, str(п.relative_to(код))] for п in проби)
підсумок = []
for н, команда in enumerate(команди, 1):
    назва = Path(команда[1]).stem
    журнал = Д / (назва + ".log")
    t = time.monotonic()
    with журнал.open("wb") as ф:
        р = subprocess.run(команда, cwd=код, env=оточення, stdout=ф, stderr=subprocess.STDOUT)
    запис = dict(команда=команда[1:], код=р.returncode, секунд=round(time.monotonic() - t, 2), журнал=журнал.name)
    підсумок.append(запис)
    print(н, "/", len(команди), назва, "код", р.returncode, "секунд", запис["секунд"], flush=True)
(Д / "батарея.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), "utf8")
sys.exit(any(р["код"] for р in підсумок))
