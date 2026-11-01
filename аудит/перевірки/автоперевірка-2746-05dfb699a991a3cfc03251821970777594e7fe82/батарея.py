"""Виконати всі команди батареї й сусідні проби без зупинки після першої помилки."""
import os
import pathlib
import subprocess
import sys

root = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(__file__).resolve().parent
env = dict(os.environ, PYTHONUTF8="1")
env["NODE_PATH"] = str(root / "джерела/node_modules")
commands = [
    [sys.executable, "стенд_знімок.py", "--дим"],
    [sys.executable, "тест_живого_шляху.py"],
    [sys.executable, "тест_протоколу.py"],
    [sys.executable, "прилади/розділи_гейтів.py"],
    [sys.executable, "audit_contracts.py"],
    ["node", "тест_показу.js"],
    [sys.executable, "проби/поділ_жнива_ast.py"],
    [sys.executable, "проби/каталог_розбір_цитати.py"],
    [sys.executable, "проби/каталог_розбір_особливості.py"],
    [sys.executable, "проби/каталог_розбір_нюанси.py"],
    [sys.executable, "прилади/корінь_е2_вікно.py"],
]
for index, command in enumerate(commands, 1):
    log = out / f"батарея_{index:02}.log"
    with log.open("w", encoding="utf-8") as stream:
        result = subprocess.run(command, cwd=root / "джерела", env=env, stdout=stream, stderr=subprocess.STDOUT)
    lines = log.read_text(encoding="utf-8").splitlines()
    print(f"{index:02}: {' '.join(command[1:] if command[0] == sys.executable else command)}: код={result.returncode}; {lines[-1] if lines else '(без виводу)'}", flush=True)
