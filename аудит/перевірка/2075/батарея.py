"""Дочекана батарея голови злиття та сусідніх сімей; усі коди збережено."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time

тут = Path(__file__).resolve().parent
корінь = тут.parents[2]
дж = корінь / "джерела"
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(дж / "node_modules"))
команди = [[sys.executable, "-X", "utf8", *а] for а in (
    ["стенд_знімок.py", "--дим"], ["тест_живого_шляху.py"], ["тест_протоколу.py"],
    ["прилади/розділи_гейтів.py"], ["audit_contracts.py"], ["досяжність.py"],
    [str(дж / "прилади/згорнути_дошку.py"), "--лише-перевірити"])]
команди.append(["node", "тест_показу.js"])
for маска in ("колір_*.py", "pal_*.py", "поділ_*_ast.py", "поверхня*.py"):
    for п in sorted((дж / "проби").glob(маска)):
        if п.name not in {"pal_вердикт.py", "pal_вимір.py", "колір_спільне.py"}:
            команди.append([sys.executable, "-X", "utf8", str(п)])


def виконати(команда):
    """Окремий журнал, без скорочення перевірок після першого провалу."""
    ім = Path(команда[3] if команда[0] == sys.executable else команда[1]).stem
    старт = time.monotonic()
    with (тут / ("батарея-" + ім + ".txt")).open("wb") as ф:
        код = subprocess.run(команда, cwd=дж, stdout=ф, stderr=subprocess.STDOUT).returncode
    р = dict(назва=ім, команда=команда, код=код, секунд=round(time.monotonic() - старт, 2))
    print(json.dumps(р, ensure_ascii=False), flush=True)
    return р


with concurrent.futures.ThreadPoolExecutor(max_workers=8) as пул:
    результати = list(пул.map(виконати, команди))
(тут / "батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf-8")
print("Завершено:", len(результати), "ненульових:", sum(bool(р["код"]) for р in результати))
