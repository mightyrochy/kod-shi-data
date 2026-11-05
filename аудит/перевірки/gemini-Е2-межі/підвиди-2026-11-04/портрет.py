"""Повторити окремо єдиний червоний розділ показу на базі та голові."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ТЕКА=Path(__file__).resolve().parent
КОРІНЬ=ТЕКА.parents[3]
КОД=КОРІНЬ/"джерела"
ДО=КОРІНЬ.parent/"tmp"/"імпорт117-до"
звіт=[]
for версія in ("до","після"):
    середа=dict(os.environ,NODE_PATH=str(КОД/"node_modules"),PYTHONUTF8="1",PYTHONIOENCODING="utf-8")
    if версія=="до": середа["PIDVYDY_BASE"]=str(ДО)
    початок=time.monotonic()
    with (ТЕКА/("портрет-"+версія+".txt")).open("w",encoding="utf-8",newline="\n") as журнал:
        р=subprocess.run(["node",str(ТЕКА/"портрет.js")],cwd=КОРІНЬ,env=середа,stdout=журнал,stderr=subprocess.STDOUT)
    звіт.append(dict(версія=версія,код=р.returncode,секунд=round(time.monotonic()-початок,2)))
(ТЕКА/"портрет.json").write_text(json.dumps(звіт,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(json.dumps(звіт,ensure_ascii=False))
sys.exit(int(any(з["код"] for з in звіт)))
