"""Послідовне виконання призначених живих сцен без зміни реалізації стенда."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT.parent / "tmp/збірка"
CACHE = Path("C:/Users/gemini/pyodide")
SHA = "dc451033e51070d44ea809c9123755f3933b752b"


def main():
    order = (OUT / "НАРЯД.md").read_text(encoding="utf-8")
    plan = json.loads(order.split("ПЛАН ЖИВОГО — ДАНІ (JSON):\n")[1].splitlines()[0])
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules")
    # Файл входу наявної сцени, дослівно з того самого призначеного коміту.
    conversation = subprocess.check_output(["git", "show", SHA + ":аудит/перевірки/rozbir_0210/R_chervone.json"], cwd=ROOT)
    (BUILD / "R_chervone.json").write_bytes(conversation)
    (OUT / "R_chervone.json").write_bytes(conversation)
    journal = OUT / "done.txt"
    for scene in plan["scenes"]:
        if (OUT / scene / "результат.json").exists():
            print("Уже записано: " + scene, flush=True)
            continue
        scene_env = dict(env)
        if scene == "ж1_робота":
            scene_env["MODEL_VYBIR"] = "assess"
        if scene == "ж4_робота_стримано":
            scene_env["ZAMINA_RUK"] = "1,2"
        command = [sys.executable, str(BUILD / "аудит/проби/записати_сцену.py"),
                   str(BUILD), str(CACHE), str(OUT / scene), "--сцена", scene]
        start = datetime.now(timezone.utc).isoformat()
        print(start + " ПОЧАТОК " + scene, flush=True)
        with (OUT / "команди.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"utc": start, "cwd": str(BUILD), "command": command,
                                "додаткові_змінні": {k: scene_env[k] for k in ("MODEL_VYBIR", "ZAMINA_RUK") if k in scene_env}}, ensure_ascii=False) + "\n")
        result = subprocess.run(command, cwd=BUILD, env=scene_env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (OUT / (scene + "_запускач.txt")).write_bytes(result.stdout)
        line = datetime.now(timezone.utc).isoformat() + " " + scene + " rc=" + str(result.returncode)
        with journal.open("a", encoding="utf-8") as f:
            f.write(line + "\n")
        print(result.stdout.decode("utf-8", errors="replace"), flush=True)
        print(line, flush=True)
        subprocess.run(["git", "add", "--", str(OUT)], cwd=ROOT, check=True)
        subprocess.run(["git", "commit", "-m", "Записати живу сцену " + scene + " на призначеній збірці"], cwd=ROOT, check=True)
        if result.returncode >= 2 or result.returncode < 0:
            print("Потрібен розбір збою середовища перед продовженням", flush=True)
            return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
