"""Повторити виправлений історичний вимір на одному корпусі для обох дерев."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Дочекатися двох вимірів та зберегти їхні повні команди й коди."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    назва = sys.argv[2] if len(sys.argv) > 2 else "колір_hex_вікна"
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")

    def виконати(режим, дерево):
        """Звірити код і каталог, читаючи однакові записи VIDPOVIDI."""
        команда = [sys.executable, "-X", "utf8", str(дерево / ("джерела/проби/" + назва + ".py")),
                   "02f2fb9f", str(корінь)]
        початок = time.monotonic()
        with (тека / (режим + "-" + назва + "-спільний-корпус.txt")).open("wb") as журнал:
            р = subprocess.run(команда, cwd=дерево / "джерела", stdout=журнал, stderr=subprocess.STDOUT)
        вих = dict(режим=режим, назва=назва, команда=команда,
                   код=р.returncode, секунд=round(time.monotonic() - початок, 2), корпус=str(корінь))
        print(json.dumps(вих, ensure_ascii=False), flush=True)
        return вих

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as пул:
        виклики = [пул.submit(виконати, р, д) for р, д in (("ДО", Path(sys.argv[1]).resolve()), ("ПІСЛЯ", корінь))]
        вих = [в.result() for в in виклики]
    файл = "hex-спільний-результати.json" if назва == "колір_hex_вікна" else "нейтраль-спільний-результати.json"
    (тека / файл).write_text(json.dumps(вих, ensure_ascii=False, indent=2), encoding="utf-8")
    return int(any(в["код"] for в in вих))


if __name__ == "__main__":
    raise SystemExit(головна())
