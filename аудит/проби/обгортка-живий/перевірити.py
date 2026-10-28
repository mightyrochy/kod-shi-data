"""Збирає новий SHA й виконує батарею та споріднені проби одним запуском."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]


def головна():
    """Зберігає окремий журнал кожної команди та їхні справжні коди виходу."""
    вихід = ТЕКА / "спроба-3"
    уточнені = "--уточнені-проби" in sys.argv
    if уточнені:
        вихід /= "уточнені-проби"
    вихід.mkdir(parents=True, exist_ok=True)
    конф = json.loads((ТЕКА / "середовище.json").read_text(encoding="utf-8-sig"))
    Path(конф["stand_root"]).mkdir(parents=True, exist_ok=True)
    node = конф["node_path"]
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_USE_SYSTEM_CA="1",
               LYUSTERKO_PYC_PYTHON=конф["компілятор"], LYUSTERKO_CATALOG="повний", NODE_PATH=конф["NODE_PATH"],
               CHROMIUM=конф["chromium_path"], PYTHONUNBUFFERED="1")
    env["PATH"] = str(Path(node).parent) + os.pathsep + env["PATH"]
    команди = [
        ("збірка", [sys.executable, "-X", "utf8", "build_артефакт.py", ".",
                     str(Path(конф["stand_root"]) / "index.html"), "показ-повний"]),
        ("дим", [sys.executable, "-X", "utf8", "стенд_знімок.py", "--дим"]),
        ("живий-шлях", [sys.executable, "-X", "utf8", "тест_живого_шляху.py"]),
        ("протокол", [sys.executable, "-X", "utf8", "тест_протоколу.py"]),
        ("розділи", [sys.executable, "-X", "utf8", "прилади/розділи_гейтів.py"]),
        ("контракти", [sys.executable, "-X", "utf8", "audit_contracts.py"]),
        ("показ", [node, "тест_показу.js"]),
        ("тест-проксі", [node, str(КОРІНЬ / "аудит/ноутбук_стенд_2/тест_проксі.js")]),
    ]
    проби = set()
    for маска in ("шлях_шар_*.py", "промпти3_*.py", "карт1_*.py", "мова_шару_*.py",
                  "м5_*.py", "шар845_*.py", "протокол_лапка_*.py", "поділ_pipeline_ast.py", "поділ_bridge_ast.py"):
        проби.update((КОРІНЬ / "джерела/проби").glob(маска))
    for п in sorted(проби):
        if п.stem == "промпти3_база":
            continue
        команда = [sys.executable, "-X", "utf8", str(п)]
        if п.stem == "карт1_картка":
            команда += [конф["stand_root"], str(Path.home() / "pyodide")]
        if п.stem == "промпти3_допит_6215":
            команда += ["68429c13bd29d3960d5b72caebcd9ed0cdaa23f6", "аудит/живі_1016_1"]
        команди.append((п.stem, команда))
    if уточнені:
        команди = [(н, к) for н, к in команди if н in (
            "карт1_картка", "промпти3_вибір_ід", "промпти3_допит_6215")]
    підсумок = []
    for назва, команда in команди:
        почато = time.monotonic()
        with (вихід / (назва + ".txt")).open("wb") as лог:
            р = subprocess.run(команда, cwd=КОРІНЬ / "джерела", env=env, stdout=лог, stderr=subprocess.STDOUT)
        рядок = dict(назва=назва, команда=команда, rc=р.returncode, секунд=round(time.monotonic() - почато, 1))
        підсумок.append(рядок)
        (вихід / "перевірки.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"{назва}: rc={р.returncode}, {рядок['секунд']} с", flush=True)
        if назва == "збірка" and р.returncode:
            return р.returncode
    return int(any(р["rc"] for р in підсумок))


if __name__ == "__main__":
    sys.exit(головна())
