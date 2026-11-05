"""Повторити три відмови §117 тим самим способом на базі та голові."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / "джерела"
ДО = КОРІНЬ.parent / "tmp" / "імпорт117-до"
ЧУЖА = КОРІНЬ.parent / "tmp" / "імпорт117-порожня"
ДО.mkdir(parents=True, exist_ok=True)
ЧУЖА.mkdir(parents=True, exist_ok=True)
for ім in ("мовний_шар.py", "паспорт_нагоди.py", "паспорт_поля.py"):
    (ДО / ім).write_bytes(subprocess.check_output(["git", "show", "7a66c78e9:джерела/" + ім], cwd=КОРІНЬ))
звіт = []
for версія, шляхи in (("до", [ДО, КОД]), ("після", [КОД])):
    for модуль in ("траса_петлі", "гейти_нові", "measure_person_axis"):
        середа = dict(os.environ, PYTHONPATH=os.pathsep.join(map(str, шляхи)))
        команда = [sys.executable, "-c", "import " + модуль]
        початок = time.time()
        try:
            р = subprocess.run(команда, cwd=ЧУЖА, env=середа, capture_output=True, text=True, timeout=10)
            дані = dict(версія=версія, модуль=модуль, код=р.returncode, секунд=round(time.time()-початок, 2),
                        stderr=р.stderr[-200:], stdout=р.stdout)
        except subprocess.TimeoutExpired:
            дані = dict(версія=версія, модуль=модуль, код=None, секунд=10, таймаут=True)
        звіт.append(дані)
        print(json.dumps(дані, ensure_ascii=False), flush=True)
(ТЕКА / "імпорт117.json").write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
