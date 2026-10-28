"""Каталог ДО з точної бази PR, незалежно від свіжішої бази гілки звіту."""
import json
import os
from pathlib import Path
import subprocess
import sys

до, голова, знімок_до, знімок_голови = map(Path, sys.argv[1:5])
тека = Path(__file__).resolve().parent
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=до, encoding="utf-8").strip()
assert sha == "dd06478133f0aa34e1e3d2523a9c24f045e46efb", sha
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
завдання = [
    ["-c", "import чистка_каталогу as ч; ч.забезпечити_чистим('каталог_повний.xml'); print('Каталог підготовлено')"],
    [str(голова / "аудит/перевірки/доробка-1927/відтворити.py"), str(до), "каталог", str(знімок_до)],
    [str(тека / "каталог_порівняти.py"), str(голова), str(знімок_до), str(знімок_голови)],
]
результати = []
for аргументи in завдання:
    команда = [sys.executable, "-X", "utf8", *аргументи]
    р = subprocess.run(команда, cwd=до / "джерела", env=оточення, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, encoding="utf-8")
    результати.append(dict(дерево=str(до), sha=sha, команда=команда, код=р.returncode, вивід=р.stdout))
    (тека / "точна-база-результати.json").write_text(
        json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    print(р.stdout, flush=True)
    assert р.returncode == 0, команда
