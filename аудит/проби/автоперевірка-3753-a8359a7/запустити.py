"""Один послідовний пакет, загальна межа 540 с з наряду (команда до 10 хв). <дерево> <журнали> <скрипти...>."""
import json
from pathlib import Path
import subprocess
import sys
import time

дерево = Path(sys.argv[1]).resolve()
журнали = Path(sys.argv[2]).resolve()
журнали.mkdir(parents=True, exist_ok=True)
кінець = time.monotonic() + 540
for назва in sys.argv[3:]:
    команда = [sys.executable, "-X", "utf8", *назва.split("::")]
    залишок = кінець - time.monotonic()
    if залишок <= 0:
        print("Пакет досяг межі; решта не виміряна:", назва, flush=True)
        break
    початок = time.monotonic()
    try:
        р = subprocess.run(команда, cwd=дерево / "джерела", capture_output=True,
                           encoding="utf-8", errors="replace", timeout=залишок)
        код, вивід = р.returncode, р.stdout + р.stderr
    except subprocess.TimeoutExpired as е:
        код = "не виміряно до межі 540 с"
        вивід = (е.stdout or b"") + (е.stderr or b"")
        if isinstance(вивід, bytes):
            вивід = вивід.decode("utf-8", errors="replace")
    запис = "КОМАНДА: " + json.dumps(команда, ensure_ascii=False) + "\nКОД: " + str(код) + "\n" + вивід
    файл = журнали / (Path(назва.split("::")[0]).stem + ".txt")
    файл.write_text(запис, encoding="utf-8")
    print(назва, "→", код, "за %.1f с" % (time.monotonic() - початок), flush=True)
