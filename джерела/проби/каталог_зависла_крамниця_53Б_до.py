"""Відтворює А–В тими самими командами на точному коді бази 2167dcb8."""
import os, subprocess, sys, tempfile
from pathlib import Path


def main():
    """Вивантажує історичні джерела поза git без зміни робочої гілки."""
    корінь = Path(__file__).resolve().parents[2]
    база = "2167dcb8492e267a3ae65886065994f1a6f7cd06"
    with tempfile.TemporaryDirectory(prefix="обхід-53Б-до-") as ж:
        тека = Path(ж)
        (тека / "zhnyvarka").mkdir()
        for файл in (корінь / "zhnyvarka").iterdir():
            if файл.suffix not in (".py", ".tsv"): continue
            код = subprocess.check_output(["git", "show", f"{база}:zhnyvarka/{файл.name}"], cwd=корінь)
            (тека / "zhnyvarka" / файл.name).write_bytes(код)
        проби = тека / "джерела/проби"; проби.mkdir(parents=True)
        for назва in ("json_проба", "sqlite_проба", "обрив_json", "обрив_стан", "обрив_тіло"):
            ім = f"каталог_зависла_крамниця_{назва}.py"
            (проби / ім).write_bytes(Path(__file__).with_name(ім).read_bytes())
        for назва, доказ in (("json", "добре=False"), ("стан", "атомарно=False"), ("тіло", "добре=False")):
            п = subprocess.run([sys.executable, str(проби / f"каталог_зависла_крамниця_обрив_{назва}.py")],
                               capture_output=True, text=True, encoding="utf-8", timeout=30,
                               env=dict(os.environ, PYTHONIOENCODING="utf-8"))
            print(п.stdout, end="")
            assert п.returncode == 1 and доказ in п.stdout, п.stderr
        скрипт = корінь / "аудит/перевірки/доробка-53Б-обрив/відтворення.py"
        тека_git = subprocess.check_output(["git", "rev-parse", "--absolute-git-dir"], cwd=корінь, text=True).strip()
        п = subprocess.run([sys.executable, str(скрипт), ж], capture_output=True, text=True, encoding="utf-8",
                           timeout=30, env=dict(os.environ, PYTHONIOENCODING="utf-8", GIT_DIR=тека_git))
        print(п.stdout, end="")
        assert п.returncode == 0, п.stderr
    print("5.3-Б ДО 2167dcb8: А–В відтворено; та сама команда ПІСЛЯ має код 0")


if __name__ == "__main__":
    main()
