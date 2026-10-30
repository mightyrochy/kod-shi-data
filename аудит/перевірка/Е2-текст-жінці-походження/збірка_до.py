"""Збирає справжній шар ДО читачем Python, не змінюючи робочих файлів і перевірок збирача."""
import builtins
import io
import os
from pathlib import Path
import runpy
import subprocess
import sys


if __name__ == "__main__":
    корінь = Path.cwd()
    модуль = "джерела/показ/мовний_шар.js"
    ціль = os.path.normcase(str((корінь / модуль).resolve()))
    старий = subprocess.check_output(["git", "show", "1641412fe533cadb57943b26b12316e008fd35b2:" + модуль])
    читати = builtins.open

    def відкрити(файл, режим="r", *аргументи, **іменовані):
        """Підставляє тільки визначений файл у читачі збирача."""
        if isinstance(файл, (str, bytes, os.PathLike)) and "r" in режим:
            if os.path.normcase(str(Path(файл).resolve())) == ціль:
                return io.BytesIO(старий) if "b" in режим else io.StringIO(старий.decode("utf-8"))
        return читати(файл, режим, *аргументи, **іменовані)

    вихід = Path(os.environ["TEMP"]) / "е2-показ-до/index.html"
    sys.path.insert(0, str(корінь / "джерела"))
    sys.argv = ["build_артефакт.py", "джерела", str(вихід), "показ-повний"]
    builtins.open = відкрити
    try:
        runpy.run_path(str(корінь / "джерела/build_артефакт.py"), run_name="__main__")
    finally:
        builtins.open = читати
    html = вихід.read_text(encoding="utf-8")
    assert "ДЖЕРЕЛЬНІ_СЛОВА_ШАРУ_П" not in html
    assert "назвиКаталогуКарткиП" not in html
    print("ДО: засвідчень нового шару 0, нових читачів каталогу 0", flush=True)
