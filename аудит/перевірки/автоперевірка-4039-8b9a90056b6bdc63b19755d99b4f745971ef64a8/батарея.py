"""Запуск батареї та сусідніх проб до кінця; журнали пише в задану теку."""
import json
import os
from pathlib import Path
import subprocess
import sys

дерево, вихід = map(Path, sys.argv[1:3])
вихід.mkdir(parents=True, exist_ok=True)
env = dict(os.environ, PYTHONIOENCODING="utf-8", NODE_PATH="C:/Users/gemini/kod-shi-test-node/node_modules")
команди = [
    [sys.executable, "стенд_знімок.py", "--дим"],
    [sys.executable, "тест_живого_шляху.py"],
    [sys.executable, "тест_протоколу.py"],
    [sys.executable, "прилади/розділи_гейтів.py"],
    [sys.executable, "audit_contracts.py"],
    ["node", "тест_показу.js"],
]
команди += [[sys.executable, "проби/" + назва + ".py"] for назва in (
    "паспорт_факт", "паспорт_межі", "паспорт_один_опис_8740", "мова_к7_одна_цитата", "wea_верхній_шар")]
for номер, команда in enumerate(команди, 1):
    знімок = вихід / (str(номер).zfill(2) + ".txt")
    with знімок.open("w", encoding="utf-8") as лог:
        лог.write("КОМАНДА: " + " ".join(команда[1:]) + "\n")
        лог.flush()
        код = subprocess.run(команда, cwd=дерево / "джерела", env=env,
                             stdout=лог, stderr=subprocess.STDOUT).returncode
    print(json.dumps(dict(команда=команда[1:], код=код, журнал=знімок.name), ensure_ascii=False), flush=True)
