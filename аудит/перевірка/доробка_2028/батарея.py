"""Виконує батарею наряду й сім'ю палітри послідовно, з повними журналами."""
import gzip
import json
import os
import pathlib
import subprocess
import sys
import time


def головна():
    """Записує команду, код виходу й час кожної перевірки без зупинки на відомій ваді."""
    тека = pathlib.Path(__file__).resolve().parent
    корінь = тека.parents[2]
    джерела = корінь / "джерела"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONHASHSEED="0",
               NODE_PATH=str(джерела / "node_modules"))
    команди = [[sys.executable, *арг] for арг in (
        ["стенд_знімок.py", "--дим"], ["тест_живого_шляху.py"], ["тест_протоколу.py"],
        ["прилади/розділи_гейтів.py"], ["audit_contracts.py"])]
    команди.append(["node", "тест_показу.js"])
    команди += [[sys.executable, "проби/поділ_" + ім + "_ast.py"] for ім in ("palette", "bridge", "pipeline")]
    команди += [[sys.executable, str(п.relative_to(джерела))] for п in sorted((джерела / "проби").glob("pal_*.py"))
                if п.name not in ("pal_вердикт.py", "pal_вимір.py")]
    команди.append([sys.executable, "прилади/згорнути_дошку.py", "--лише-перевірити"])
    результати = []
    for і, команда in enumerate(команди, 1):
        print(f"{і}/{len(команди)}: {' '.join(команда[1:])}", flush=True)
        початок = time.monotonic()
        вихід = subprocess.run(команда, cwd=джерела, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        назва = f"батарея-{і:02}.txt.gz"
        (тека / назва).write_bytes(gzip.compress(вихід.stdout, mtime=0))
        запис = dict(команда=команда[1:], код=вихід.returncode, секунд=round(time.monotonic() - початок, 1), журнал=назва)
        результати.append(запис)
        (тека / "батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"  код={запис['код']}, {запис['секунд']} с", flush=True)
    return int(any(з["код"] for з in результати))


if __name__ == "__main__":
    sys.exit(головна())
