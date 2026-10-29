"""ДО/ПІСЛЯ історичних проб на записаних входах, без виклику моделей."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Повторити проби, яким потрібні історичні відповіді та JSON кадру."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    результати = []
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(корінь / "джерела/node_modules"),
                      GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="core.quotepath", GIT_CONFIG_VALUE_0="false")
    for режим, дерево in (("ДО", Path(sys.argv[1]).resolve()), ("ПІСЛЯ", корінь)):
        код = дерево / "джерела"
        вхід = дерево / "аудит/тести/власник_2026-10-14/verdykty-0phxvk-2026-10-14-1551.json"
        теки = sorted({str(п.parent) for п in (дерево / "аудит").rglob("*проза_рука_3_4.txt")})
        команди = [(ім, [str(вхід)]) for ім in ("колір_кадр_слово_5222", "колір_кадр_слово_5223")]
        команди += [(ім, теки) for ім in ("колір_названо", "колір_прози_шар")]
        команди += [("колір_ярлик_hex", ["HEAD:аудит"]), ("колір_hex_вікна", ["02f2fb9f", str(корінь)]),
                    ("колір_майже_нейтраль", ["02f2fb9f", str(корінь)])]
        for ім, аргументи in команди:
            команда = [sys.executable, "-X", "utf8", str(код / "проби" / (ім + ".py")), *аргументи]
            початок = time.monotonic()
            with (тека / (режим + "-" + ім + "-з-входом.txt")).open("wb") as журнал:
                р = subprocess.run(команда, cwd=дерево if ім == "колір_ярлик_hex" else код,
                                   stdout=журнал, stderr=subprocess.STDOUT)
            запис = dict(режим=режим, назва=ім, команда=команда, код=р.returncode,
                          секунд=round(time.monotonic() - початок, 2))
            результати.append(запис)
            print(json.dumps({к: в for к, в in запис.items() if к != "команда"}, ensure_ascii=False), flush=True)
            (тека / "додаткові-результати.json").write_bytes(
                json.dumps(результати, ensure_ascii=False, indent=2).encode("utf-8"))
    return int(any(р["код"] for р in результати if р["назва"] not in {"колір_прози_шар", "колір_ярлик_hex"}))


if __name__ == "__main__":
    raise SystemExit(головна())
