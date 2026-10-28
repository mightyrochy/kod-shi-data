"""Відтворення перевірки #2075 без викликів моделей; кожна команда дочекана."""
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import subprocess
import sys

дерево = Path(sys.argv[1]).resolve()
тека = Path(__file__).resolve().parent
код = дерево / "джерела"
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
               NODE_PATH=str(тека.parents[2] / "джерела/node_modules"))
завдання = [("дим", ["стенд_знімок.py", "--дим"]),
            ("живий_шлях", ["тест_живого_шляху.py"]),
            ("протокол", ["тест_протоколу.py"]),
            ("розділи", ["прилади/розділи_гейтів.py"]),
            ("контракти", ["audit_contracts.py"]),
            ("показ", ["node", "тест_показу.js"])]
пропуск = {"колір_спільне.py", "pal_вердикт.py", "pal_вимір.py"}
for шаблон in ("колір_*.py", "pal_*.py", "поділ_*_ast.py"):
    завдання.extend((п.stem, [str(дерево / "аудит/проби/тип_кольору_213_нейтраль.py")]
                    if п.name == "колір_нейтраль.py" else [str(п)])
                    for п in sorted((код / "проби").glob(шаблон))
                    if п.name not in пропуск)
завдання.extend([
    ("власні_попередньої_перевірки", [str(дерево / "аудит/перевірка/власні_проби_1927_3.py")]),
    ("дошка", [str(код / "прилади/згорнути_дошку.py"), "--лише-перевірити"]),
    ("досяжність", ["досяжність.py"]),
])
результати = (json.loads((тека / "результати.json").read_text(encoding="utf-8"))
              if (тека / "результати.json").exists() else [])
готові = {р["назва"] for р in результати}
def виконати(назва, аргументи):
    команда = (["node", *аргументи[1:]] if аргументи[0] == "node" else
               [sys.executable, "-X", "utf8", *аргументи])
    вихід = subprocess.run(команда, cwd=код, env=оточення, stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT, encoding="utf-8", errors="replace")
    (тека / (назва + ".txt")).write_text(вихід.stdout, encoding="utf-8")
    print(назва, "код", вихід.returncode, flush=True)
    return dict(назва=назва, команда=команда, код=вихід.returncode)

with ThreadPoolExecutor(max_workers=4) as пул:
    запущені = [пул.submit(виконати, н, а) for н, а in завдання if н not in готові]
    for завершене in as_completed(запущені):
        результати.append(завершене.result())
        (тека / "результати.json").write_text(
            json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
