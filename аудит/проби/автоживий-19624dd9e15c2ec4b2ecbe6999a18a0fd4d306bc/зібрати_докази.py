"""Зберігає джерела й фактичну відмову записувача для призначеного плану."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys

ТЕКА = Path(__file__).resolve().parent
РЕПО = ТЕКА.parents[2]
ЗБІРКА = РЕПО.parent / "tmp" / "збірка"
SHA = "b857ec997017ac110abf4fc9cdb15cd9dcf20bd3"
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


def команда(назва, аргументи):
    початок = datetime.now(timezone.utc).isoformat()
    р = subprocess.run(аргументи, cwd=РЕПО, capture_output=True,
                       text=True, encoding="utf-8", errors="replace", check=False)
    (ТЕКА / (назва + ".txt")).write_text(р.stdout + р.stderr, encoding="utf-8")
    return {"назва": назва, "команда": аргументи, "початок_utc": початок,
            "кінець_utc": datetime.now(timezone.utc).isoformat(), "rc": р.returncode}


запуски = [
    команда("предок", ["git", "merge-base", "--is-ancestor", SHA, "origin/main"]),
    команда("голови", ["git", "rev-parse", "HEAD", "origin/main"]),
    команда("тимчасове_дерево", ["git", "-C", str(ЗБІРКА), "rev-parse", "HEAD"]),
    команда("реєстр_призначеної_збірки", ["git", "show", SHA + ":аудит/проби/живі_сцени.txt"]),
    команда("PR_2417", ["gh", "pr", "view", "2417", "--json", "number,url,state,body,mergedAt,mergeCommit"]),
    команда("PR_2423", ["gh", "pr", "view", "2423", "--json", "number,url,state,isDraft,mergedAt,mergeCommit,headRefOid"]),
    команда("зміни_записувача", ["git", "diff", SHA, "HEAD", "--",
                                "аудит/проби/записати_сцену.py", "аудит/проби/живі_сцени.txt"]),
    команда("спроба_сцени", [sys.executable, "аудит/проби/записати_сцену.py",
                             str(ЗБІРКА), str(РЕПО.parent / "tmp" / "pyodide"),
                             str(ТЕКА / "обгортка"), "--сцена", "обгортка"]),
]
реєстр = (ТЕКА / "реєстр_призначеної_збірки.txt").read_text(encoding="utf-8")
факти = {
    "час_utc": datetime.now(timezone.utc).isoformat(),
    "призначений_sha": SHA,
    "сцена_в_реєстрі": any(р.startswith("обгортка|") for р in реєстр.splitlines()),
    "build.txt": (ЗБІРКА / "build.txt").read_text(encoding="utf-8").strip(),
    "моделі_не_запускались": True,
    "запуски": запуски,
}
(ТЕКА / "докази.json").write_text(json.dumps(факти, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
for р in запуски:
    print(р["назва"] + ": rc=" + str(р["rc"]))
print("Сцена в реєстрі: " + str(факти["сцена_в_реєстрі"]))
