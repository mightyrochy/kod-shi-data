"""Послідовний тестовий прогін наряду; кожна сцена зберігається окремим комітом."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
SHA = "6530d4324c6aee95d5e0d4a55cfd154c4c2a8e9a"
ЗБІРКА = КОРІНЬ.parent / "tmp/збірка"
КЕШ = Path("C:/Users/gemini/pyodide")
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                  NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules")

def команда(args):
    return subprocess.run(args, cwd=КОРІНЬ, text=True, encoding="utf-8", capture_output=True)

def час():
    return datetime.now(timezone.utc).isoformat()

def main():
    текст = (ТЕКА / "НАРЯД.md").read_text(encoding="utf-8")
    план = json.loads(текст.split("ПЛАН ЖИВОГО — ДАНІ (JSON):\n", 1)[1].splitlines()[0])
    if not (ТЕКА / "середовище.json").exists():
        with urllib.request.urlopen("http://127.0.0.1:1234/api/v1/models", timeout=20) as r:
            моделі = json.load(r)
        предок = команда(["git", "merge-base", "--is-ancestor", SHA, "origin/main"])
        if предок.returncode:
            raise RuntimeError("Призначена збірка не предок origin/main")
        дані = {"час_utc": час(), "збірка": SHA, "штамп": (ЗБІРКА / "build.txt").read_text().strip(),
                "голова_перед_прогоном": команда(["git", "rev-parse", "HEAD"]).stdout.strip(),
                "origin_main": команда(["git", "rev-parse", "origin/main"]).stdout.strip(),
                "перевірка_предка_rc": предок.returncode, "моделі": моделі,
                "gpu": команда(["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv"]).stdout,
                "python": sys.version, "node": команда(["node", "--version"]).stdout.strip(),
                "NODE_OPTIONS": os.environ.get("NODE_OPTIONS"), "PYTHONPATH": os.environ.get("PYTHONPATH"),
                "кеш_pyodide": str(КЕШ), "збірка_тека": str(ЗБІРКА),
                "контекст_проксі": {"qwen/qwen3.5-9b": 57344, "mamaylm-gemma-3-12b-it-v2.0": 16384},
                "parallel": 1, "канал": "Останній рядок відповіді читає обгортка"}
        (ТЕКА / "середовище.json").write_text(json.dumps(дані, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    обрані = sys.argv[1:] or list(план["scenes"])
    for сцена in обрані:
        if сцена not in план["scenes"]:
            raise ValueError(сцена)
        вихід = ТЕКА / сцена
        if вихід.exists():
            raise RuntimeError("Запис уже існує: " + сцена)
        args = [sys.executable, "аудит/проби/записати_сцену.py", str(ЗБІРКА), str(КЕШ), str(вихід), "--сцена", сцена]
        print(час() + " ПОЧАТОК " + сцена, flush=True)
        with (ТЕКА / "команди.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps({"час": час(), "команда": args}, ensure_ascii=False) + "\n")
        р = команда(args)
        with (ТЕКА / "запускач.txt").open("a", encoding="utf-8") as f:
            f.write(час() + " " + сцена + " rc=" + str(р.returncode) + "\n" + р.stdout + р.stderr + "\n")
        with (ТЕКА / "done.txt").open("a", encoding="utf-8") as f:
            f.write(час() + " " + сцена + " rc=" + str(р.returncode) + "\n")
        print(час() + " КІНЕЦЬ " + сцена + " rc=" + str(р.returncode), flush=True)
        додано = команда(["git", "add", "--", str(ТЕКА.relative_to(КОРІНЬ))])
        if додано.returncode:
            raise RuntimeError(додано.stderr)
        коміт = команда(["git", "commit", "-m", "Автоживий: записати сцену " + сцена + " (rc=" + str(р.returncode) + ")"])
        print(коміт.stdout, flush=True)
        if коміт.returncode:
            raise RuntimeError(коміт.stderr)
        if р.returncode >= 2 or р.returncode < 0:
            print(р.stderr, flush=True)
            return р.returncode
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
