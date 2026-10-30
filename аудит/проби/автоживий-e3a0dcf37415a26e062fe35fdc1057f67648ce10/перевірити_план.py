"""Зберігає доказ можливості запуску призначеного плану без звернень до моделей."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
SHA = "fa0fd9b44ff79cec3604914dde4c816a109b40fc"
TREE = Path(os.environ["TEMP"]) / "assigned-build"
RESULT = {"час_utc": datetime.now(timezone.utc).isoformat(), "призначений_sha": SHA, "команди": []}


def run(args, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8",
                       errors="replace", env=dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8"))
    RESULT["команди"].append({"команда": [str(x) for x in args], "тека": str(cwd),
                              "rc": p.returncode, "stdout": p.stdout, "stderr": p.stderr})
    return p


assert run(["git", "merge-base", "--is-ancestor", SHA, "origin/main"]).returncode == 0
created = False
try:
    p = run(["git", "worktree", "add", "--detach", "--no-checkout", str(TREE), SHA])
    assert p.returncode == 0, p.stderr
    created = True
    p = run(["git", "sparse-checkout", "set", "--no-cone", "/index.html", "/build.txt",
             "/аудит/проби/живі_сцени.txt", "/аудит/проби/записати_сцену.py"], TREE)
    assert p.returncode == 0, p.stderr
    assert run(["git", "checkout", "--detach", SHA], TREE).returncode == 0
    RESULT["sha_тимчасового_дерева"] = run(["git", "rev-parse", "HEAD"], TREE).stdout.strip()
    registry = (TREE / "аудит/проби/живі_сцени.txt").read_text(encoding="utf-8")
    RESULT["рядків_сцени_обгортка"] = sum(line.startswith("обгортка|") for line in registry.splitlines())
    p = run(["python", str(TREE / "аудит/проби/записати_сцену.py"), str(TREE),
             str(Path(os.environ["TEMP"]) / "pyodide-cache"), str(OUT / "обгортка"), "--сцена", "обгортка"], TREE)
    RESULT["код_записувача"] = p.returncode
    RESULT["живий_прогін_почався"] = False
    RESULT["примітка"] = "Записувач відмовив до читання кешу, запуску браузера, проксі та звернень до моделей."
finally:
    if created:
        p = run(["git", "worktree", "remove", str(TREE)])
        RESULT["тимчасове_дерево_прибрано"] = p.returncode == 0
    (OUT / "докази.json").write_text(json.dumps(RESULT, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in RESULT.items() if k != "команди"}, ensure_ascii=False))
