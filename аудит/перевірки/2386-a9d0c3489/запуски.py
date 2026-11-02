"""Виконує прицільні перевірки призначеної голови до кінця, зберігаючи виводи й коди."""
import json
import os
from pathlib import Path
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf8")
докази = Path(__file__).resolve().parent
корінь = Path(sys.argv[1]).resolve()
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                NODE_PATH=str(Path.home() / "kod-shi-test-node/node_modules"))
команди = [([sys.executable, str(докази / (імя + ".py"))], імя)
           for імя in ("новий_замір", "мірила", "фото", "черга", "чистка")]
команди += [([sys.executable, str(корінь / шлях)], назва) for шлях, назва in (
    ("аудит/жнива_5_3/читачі_повтор.py", "10682"),
    ("джерела/проби/каталог_рецепт_повтор.py", "рецепт"),
    ("джерела/проби/каталог_цикл_53.py", "цикл"),
    ("джерела/проби/картка_вузол_5_1.py", "вузол_5_1"))]
команди.append((["node", str(докази / "картка.cjs")], "знімок"))
підсумок = []
for команда, назва in команди:
    with (докази / (назва + ".txt")).open("w", encoding="utf8") as ф:
        ф.write("КОМАНДА: " + subprocess.list2cmdline(команда) + "\nТЕКА: " + str(корінь) + "\n")
        ф.flush()
        результат = subprocess.run(команда, cwd=корінь, env=оточення, stdout=ф, stderr=subprocess.STDOUT)
        ф.write("\nКОД: " + str(результат.returncode) + "\n")
    підсумок.append(dict(назва=назва, код=результат.returncode))
    print(назва, "код", результат.returncode, flush=True)
(докази / "підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
