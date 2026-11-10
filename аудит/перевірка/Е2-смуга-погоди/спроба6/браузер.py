"""Збирає тимчасовий показ і виконує стандартний браузерний стенд без живих моделей."""
import functools
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
from urllib.request import urlretrieve

КОРІНЬ = Path(__file__).resolve().parents[4]
ЖУРНАЛИ = Path(__file__).resolve().parent
ТИМЧАСОВЕ = КОРІНЬ.parent / "tmp"


def команда(назва, аргументи, середовище):
    """Чекає команду до кінця й лишає її повний журнал."""
    with (ЖУРНАЛИ / (назва + ".txt")).open("w", encoding="utf-8") as вихід:
        код = subprocess.run(аргументи, cwd=КОРІНЬ / "джерела", env=середовище,
                             stdout=вихід, stderr=subprocess.STDOUT).returncode
    print(назва, "код:", код, flush=True)
    return код


if __name__ == "__main__":
    середовище = {к: в for к, в in os.environ.items() if not к.startswith(("MODEL", "ZHYVA", "ROZMOVA"))}
    середовище.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONWARNINGS="ignore",
                       NODE_PATH=str(КОРІНЬ / "джерела" / "node_modules"), LYUSTERKO_CATALOG="повний")
    кеш = ТИМЧАСОВЕ / "pyodide"
    сторінка = ТИМЧАСОВЕ / "стенд"
    кеш.mkdir(exist_ok=True)
    сторінка.mkdir(exist_ok=True)
    for назва in ("pyodide.js", "pyodide.asm.js", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"):
        файл = кеш / назва
        if not файл.exists():
            urlretrieve("https://cdn.jsdelivr.net/pyodide/v0.26.4/full/" + назва, файл)
        print("кеш", назва, файл.stat().st_size, flush=True)
    код = команда("збірка", [sys.executable, "-X", "utf8", "build_артефакт.py", ".",
                            str(сторінка / "index.html"), "показ-повний"], середовище)
    if код:
        sys.exit(код)
    обробник = functools.partial(SimpleHTTPRequestHandler, directory=str(сторінка))
    сервер = ThreadingHTTPServer(("127.0.0.1", 0), обробник)
    потік = threading.Thread(target=сервер.serve_forever)
    потік.start()
    try:
        код = команда("браузер", ["node", str(КОРІНЬ / "аудит/проби/рв6_стенд.js"),
                                f"http://127.0.0.1:{сервер.server_port}", str(сторінка), str(кеш), "3"], середовище)
    finally:
        сервер.shutdown()
        сервер.server_close()
        потік.join()
    sys.exit(код)
