"""Відтворює збережені обміни мосту на базі наряду або поточному коді без моделей."""
import asyncio
import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

К = Path(__file__).resolve().parents[3]
Д = Path(__file__).resolve().parent
режим = sys.argv[1]
sys.path.insert(0, str(К / "джерела/прилади"))
import знімок_мосту as З
З.підготувати(str(К / "джерела"))
if режим == "до":
    накладка = Path(tempfile.gettempdir()) / "код-до-утримання"
    накладка.mkdir(exist_ok=True)
    шляхи = subprocess.check_output(["git", "-c", "core.quotepath=off", "diff", "6be1a61a", "--name-only"], cwd=К, encoding="utf8").splitlines()
    for шлях in шляхи:
        if шлях.startswith("джерела/") and шлях.endswith(".py") and "/" not in шлях[len("джерела/"):]:
            вихід = subprocess.run(["git", "show", "6be1a61a:" + шлях], cwd=К, capture_output=True, check=True)
            (накладка / Path(шлях).name).write_bytes(вихід.stdout)
    sys.path.insert(0, str(накладка))
import feed
feed.каталог_на_диску("каталог_brief.xml")
кеш = Path(tempfile.gettempdir()) / ("кольори-утримання-" + режим + ".json")
кеш.write_text("{}", "utf8")
підсумок = []
for сцена in ("палітра_її", "плитка_робота"):
    запис = З.прочитати(str(К / "аудит/проби/знімок_входи" / (сцена + ".jsonl.gz")))
    рядки = [json.loads(р) for р in запис.splitlines() if р.strip()]
    for рядок in рядки:
        вхід = json.loads(рядок["вхід"])
        if "кеш_кольорів" in вхід: вхід["кеш_кольорів"] = str(кеш)
        рядок["вхід"] = json.dumps(вхід, ensure_ascii=False)
    запис = "\n".join(json.dumps(р, ensure_ascii=False) for р in рядки)
    знімок, час = asyncio.run(З.прогнати(запис))
    записи = [json.loads(р) for р in знімок.splitlines()][1:]
    (Д / (сцена + "-" + режим + ".jsonl.gz")).write_bytes(gzip.compress(знімок.encode("utf8"), mtime=0))
    помилки = [dict(н=з["н"], ім=з["ім"], помилка=з["помилка"]) for з in записи if "помилка" in з]
    підсумок.append(dict(сцена=сцена, викликів=len(записи), помилки=помилки, час=час))
    print(сцена, "викликів", len(записи), "винятків", len(помилки), flush=True)
(Д / ("сцени-" + режим + ".json")).write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), "utf8")
sys.exit(any(с["помилки"] for с in підсумок))
