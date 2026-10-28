"""Повторює перевірки, зачеплені останніми виправленнями; кожна команда до кінця."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def main():
    """Повний повтор гейтів, часткове фото, інвентар, дошка й усі історичні AST."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / "джерела"
    голова = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=корінь).decode().strip()
    команди = [("розділи", ["прилади/розділи_гейтів.py"], джерела),
               ("поверхня_1993_невизначеність", ["проби/поверхня_1993_невизначеність.py"], джерела),
               ("колір_центр_вікна_хрома", ["проби/колір_центр_вікна_хрома.py"], джерела),
               ("поділ_жнива_офлайн", ["проби/поділ_жнива_офлайн.py"], джерела),
               ("колір_тип_213_межа", ["проби/колір_тип_213_межа.py"], джерела),
               ("межа-продукту", [str(тека / "межа_продукту.py")], корінь),
               ("інвентар", [str(тека / "межа_інвентар.py")], корінь),
               ("дошка", ["прилади/згорнути_дошку.py", "--лише-перевірити"], джерела)]
    команди += [(п.stem, [str(п)], джерела) for п in sorted((джерела / "проби").glob("поділ_*_ast.py"))]
    результати = []
    for ім, аргументи, де in команди:
        команда = [sys.executable, "-X", "utf8", *аргументи]
        початок = time.monotonic()
        with (тека / ("ГОЛОВА-" + ім + ".txt")).open("w", encoding="utf-8") as журнал:
            процес = subprocess.run(команда, cwd=де, env=dict(os.environ, PYTHONUTF8="1",
                PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1"), stdout=журнал, stderr=subprocess.STDOUT)
        факт = dict(назва=ім, команда=команда, тека=str(де), код=процес.returncode,
                    голова=голова, секунд=round(time.monotonic() - початок, 1))
        факт["очікуваний_код"] = 1 if ім == "поділ_жнива_офлайн" else 0
        if ім == "поділ_жнива_офлайн":
            текст = (тека / ("ГОЛОВА-" + ім + ".txt")).read_text("utf-8")
            факт["саме_10681"] = "AttributeError" in текст and "_у_дузі" in текст
        результати.append(факт)
        (тека / "ГОЛОВА-команди.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), "utf-8")
        print(json.dumps(факт, ensure_ascii=False), flush=True)
    return int(any(ф["код"] != ф["очікуваний_код"] or ф.get("саме_10681") is False for ф in результати))


if __name__ == "__main__":
    raise SystemExit(main())
