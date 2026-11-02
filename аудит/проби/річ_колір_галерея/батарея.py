"""Один повний прогін батареї й сім'ї кадрів; кожен результат зберігається окремо."""
import json
import os
from pathlib import Path
import subprocess
import sys

КОРІНЬ = Path(__file__).resolve().parents[3]
ВИХІД = Path(__file__).resolve().parent


def головна():
    """Виконати всі призначені команди до кінця, зокрема після невдалої."""
    os.chdir(КОРІНЬ / "джерела")
    оточення = dict(os.environ, PYTHONUTF8="1", NODE_PATH="node_modules")
    команди = [[sys.executable, "-W", "ignore", ф, *арг] for ф, арг in (
        ("стенд_знімок.py", ["--дим"]), ("тест_живого_шляху.py", []),
        ("тест_протоколу.py", []), ("прилади/розділи_гейтів.py", []), ("audit_contracts.py", []),
        ("проби/кадри_поверхня_читач.py", []), ("проби/кадри_поверхня_запис.py", []),
        ("проби/кадри_групи_5697.py", []), ("проби/поділ_жнива_ast.py", []),
        ("проби/поділ_feed_ast.py", []))]
    команди.append(["node", "тест_показу.js"])
    результат = []
    for к in команди:
        назва = Path(к[3] if к[0] == sys.executable else к[1]).stem
        with (ВИХІД / (назва + ".txt")).open("wb") as ф:
            запуск = subprocess.run(к, env=оточення, stdout=ф, stderr=subprocess.STDOUT)
        результат.append(dict(команда=к[1:], код=запуск.returncode))
        print(назва, "код", запуск.returncode, flush=True)
    (ВИХІД / "батарея.json").write_text(json.dumps(результат, ensure_ascii=False, indent=2), encoding="utf-8")
    return int(any(р["код"] for р in результат))


if __name__ == "__main__":
    raise SystemExit(головна())
