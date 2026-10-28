"""Історичні проби сім'ї з їхніми наявними записаними входами, без моделей."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Повторити проби, яким замало запуску без аргументів."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    код = корінь / "джерела"
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(код / "node_modules"),
                      GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")
    вхід = корінь / "аудит/тести/власник_2026-10-14/verdykty-0phxvk-2026-10-14-1551.json"
    теки = sorted({str(п.parent) for п in (корінь / "аудит").rglob("*проза_рука_3_4.txt")})
    команди = [(ім, [str(вхід)]) for ім in ("колір_кадр_слово_5222", "колір_кадр_слово_5223")]
    команди += [(ім, теки) for ім in ("колір_названо", "колір_прози_шар")]
    команди.append(("колір_ярлик_hex", ["HEAD:аудит"]))
    результати = []
    for ім, аргументи in команди:
        команда = [sys.executable, str(код / "проби" / (ім + ".py")), *аргументи]
        початок = time.monotonic()
        with (тека / (ім + "-з-входом.txt")).open("wb") as журнал:
            р = subprocess.run(команда, cwd=корінь if ім == "колір_ярлик_hex" else код,
                               stdout=журнал, stderr=subprocess.STDOUT)
        результати.append(dict(назва=ім, команда=команда, код=р.returncode, секунд=round(time.monotonic() - початок, 2)))
        print(json.dumps({к: в for к, в in результати[-1].items() if к != "команда"}, ensure_ascii=False), flush=True)
        (тека / "додаткові-результати.json").write_bytes(json.dumps(результати, ensure_ascii=False, indent=2).encode())
    return int(any(р["код"] for р in результати))


if __name__ == "__main__":
    raise SystemExit(головна())
