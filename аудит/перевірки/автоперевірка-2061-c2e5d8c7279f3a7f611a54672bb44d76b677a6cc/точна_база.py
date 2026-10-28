"""Повторити порівняння на точній базі PR, окремій від новішого main робочої гілки."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def головна():
    """Перевірити SHA бази, підготувати каталог і зберегти точні команди та журнали."""
    база, голова = map(lambda п: Path(п).resolve(), sys.argv[1:3])
    тека = Path(__file__).resolve().parent
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=база, text=True).strip()
    assert sha == "fbd139f2a013e24d61aed42bfce4cba5747b1d5a"
    старий = тека / "база-каталог.json"
    if старий.exists() and not (тека / "початкове-main-каталог.json").exists():
        shutil.copy2(старий, тека / "початкове-main-каталог.json")
    команди = [
        ("база-PR-підготовка.txt", ["-c", "import чистка_каталогу as ч, feed as Ф; "
         "print('фід:', ч.забезпечити_чистим('каталог_повний.xml')['шлях']); "
         "print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"]),
        ("база-PR-каталог.txt", [голова / "аудит/перевірки/доробка-1927/відтворити.py", база, "каталог", старий]),
        ("метал-пул-ДО.txt", [тека / "метал_пулу.py", база, старий]),
    ]
    результати = []
    for журнал, арг in команди:
        команда = [sys.executable, "-X", "utf8", *map(str, арг)]
        with (тека / журнал).open("wb") as ф:
            р = subprocess.run(команда, cwd=база / "джерела", stdout=ф, stderr=subprocess.STDOUT)
        результати.append(dict(команда=команда, дерево=str(база), SHA=sha, код=р.returncode, журнал=журнал))
        (тека / "база-PR-результати.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
        print(журнал, р.returncode, flush=True)
        assert р.returncode == 0


if __name__ == "__main__":
    головна()
