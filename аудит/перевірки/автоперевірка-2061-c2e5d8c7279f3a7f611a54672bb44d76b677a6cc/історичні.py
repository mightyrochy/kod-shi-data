"""Повторити історичні проби на наявних записаних входах обох дерев."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Зберегти команди й ненульові результати старих приладів без порожньої вибірки."""
    тека = Path(__file__).resolve().parent
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", GIT_CONFIG_COUNT="1",
        GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")
    результати = []
    for режим, дерево in zip(("ДО", "ПІСЛЯ"), map(Path, sys.argv[1:3])):
        дерево = дерево.resolve()
        код = дерево / "джерела"
        вхід = дерево / "аудит/тести/власник_2026-10-14/verdykty-0phxvk-2026-10-14-1551.json"
        теки = sorted({str(п.parent) for п in (дерево / "аудит").rglob("*проза_рука_3_4.txt")})
        assert вхід.exists() and теки
        команди = [(ім, [str(вхід)]) for ім in ("колір_кадр_слово_5222", "колір_кадр_слово_5223")]
        команди += [(ім, теки) for ім in ("колір_названо", "колір_прози_шар")]
        команди += [("колір_ярлик_hex", ["HEAD:аудит"]), ("колір_hex_вікна", ["02f2fb9f"]),
                    ("колір_майже_нейтраль", ["02f2fb9f"])]
        for ім, арг in команди:
            команда = [sys.executable, "-X", "utf8", str(код / "проби" / (ім + ".py")), *арг]
            час = time.monotonic()
            with (тека / ("історичні-" + режим + "-" + ім + ".txt")).open("wb") as журнал:
                р = subprocess.run(команда, cwd=дерево if ім == "колір_ярлик_hex" else код,
                    stdout=журнал, stderr=subprocess.STDOUT)
            запис = dict(режим=режим, назва=ім, команда=команда, код=р.returncode,
                секунд=round(time.monotonic() - час, 2))
            результати.append(запис)
            print(режим, ім, р.returncode, flush=True)
            (тека / "історичні-результати.json").write_text(
                json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    головна()
