# -*- coding: utf-8 -*-
"""Запускає батарею КОД.md та офлайн-проби сім'ї жнив одним проходом до кінця."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Зберігає команду, код завершення й повний журнал кожної перевірки."""
    корінь = Path(__file__).resolve().parents[3]
    оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    оточення["NODE_PATH"] = str(Path.home() / "kod-shi-test-node/node_modules")
    оточення["LYUSTERKO_PYC_PYTHON"] = str(Path.home() / "tools/python-3.12.1/python.exe")
    команди = [[sys.executable, "стенд_знімок.py", "--дим"],
               [sys.executable, "тест_живого_шляху.py"],
               [sys.executable, "тест_протоколу.py"],
               [sys.executable, "прилади/розділи_гейтів.py"],
               [sys.executable, "audit_contracts.py"],
               ["node", "тест_показу.js"],
               [sys.executable, "проби/поділ_жнива_ast.py"],
               [sys.executable, "проби/поділ_жнива_офлайн.py"],
               [sys.executable, "проби/zhnyva_нові_магазини.py"],
               [sys.executable, "прилади/згорнути_дошку.py", "--лише-перевірити"]]
    результати = []
    with Path(__file__).with_name("батарея.log").open("w", encoding="utf-8", newline="\n") as лог:
        for команда in команди:
            початок = time.monotonic()
            print("Перевірка:", " ".join(команда[1:]), flush=True)
            прогін = subprocess.run(команда, cwd=корінь / "джерела", env=оточення,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=900)
            текст = прогін.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
            текст = "\n".join(рядок.rstrip() for рядок in текст.splitlines()) + "\n"
            лог.write("\n$ " + " ".join(команда) + "\n" + текст)
            лог.flush()
            результати.append(dict(команда=команда, код=прогін.returncode, секунд=round(time.monotonic() - початок, 2)))
            print("Код:", прогін.returncode, "секунд:", результати[-1]["секунд"], flush=True)
            if прогін.returncode:
                print(текст[-2500:], flush=True)
    Path(__file__).with_name("батарея.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(int(any(р["код"] for р in результати)))


if __name__ == "__main__":
    головна()
