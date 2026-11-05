"""Продовжити справжній перезбір до 60 галерей і зберегти точний журнал."""
import gzip
import json
from pathlib import Path
import subprocess
import sys
import time

ТЕКА = Path(__file__).resolve().parent


def головна():
    """Дочекатися штатного записувача й зберегти його stdout та stderr без перекодування."""
    команда = [sys.executable, "-X", "utf8", "-u", str(ТЕКА / "перезібрати.py"), "--ліміт", "60"]
    початок = time.monotonic()
    рядки = []
    знімок = dict(команда=команда, почато_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with gzip.open(ТЕКА / "сирий_0511.log.gz", "wb") as журнал:
        with subprocess.Popen(команда, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as прогін:
            for рядок in прогін.stdout:
                журнал.write(рядок)
                текст = рядок.decode("utf-8", errors="replace").rstrip("\r\n") + "\n"
                if текст.startswith(("ЧЕРГА:", "[", "ПІДСУМОК:", "Traceback", "RuntimeError")):
                    рядки.append(текст)
                    print(текст, end="", flush=True)
            код = прогін.wait()
    (ТЕКА / "прогін_0511.log").write_text("".join(рядки), encoding="utf-8", newline="\n")
    знімок.update(код=код, час_секунд=round(time.monotonic() - початок, 1),
                  завершено_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    (ТЕКА / "команда_0511.json").write_text(
        json.dumps(знімок, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return код


if __name__ == "__main__":
    sys.exit(головна())
