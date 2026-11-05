"""Зберегти виміри до/після та виконати батарею до кінця без моделі й платних API."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[3]
КОД = КОРІНЬ / "джерела"
ДО = КОРІНЬ.parent / "tmp" / "складені-до"
ДО.mkdir(parents=True, exist_ok=True)
БАЗА = "aef9e6cbba"
for ім in ("мовний_шар.py", "картка_запиту.py", "паспорт_поля.py"):
    (ДО / ім).write_bytes(subprocess.check_output(["git", "show", БАЗА + ":джерела/" + ім], cwd=КОРІНЬ))
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1", PYTHONPATH=str(КОД), NODE_PATH=str(КОД / "node_modules"))
ПЕРЕВІРКИ = []
for версія, код in (("до", ДО), ("після", КОД)):
    запуск = ("import sys,runpy;sys.path[:0]=" + repr([str(код), str(КОД)]) +
              ";import мовний_шар,картка_запиту;runpy.run_path(" +
              repr(str(КОД / "проби/картка_складені.py")) + ",run_name='__main__')")
    ПЕРЕВІРКИ += [("складені-" + версія, [sys.executable, "-c", запуск], КОРІНЬ),
                   ("повтор-" + версія, [sys.executable, "джерела/прилади/replay_картки.py",
                    "джерела/проби/дані/картка_запиту.json", "--код", str(код),
                    "--запис", str(ТЕКА / ("повтор-" + версія + ".json"))], КОРІНЬ)]
ПЕРЕВІРКИ += [
    ("каталог", [sys.executable, "-c", "import чистка_каталогу as ч,feed as ф;"
     "print('фід:',ч.забезпечити_чистим('каталог_повний.xml'));print('фікстура:',ф.каталог_на_диску('каталог_brief.xml'))"], КОД),
    ("дим", [sys.executable, "стенд_знімок.py", "--дим"], КОД),
    ("живий-шлях", [sys.executable, "тест_живого_шляху.py"], КОД),
    ("протокол", [sys.executable, "тест_протоколу.py"], КОД),
    ("гейти", [sys.executable, "прилади/розділи_гейтів.py"], КОД),
    ("контракти", [sys.executable, "audit_contracts.py"], КОД),
    ("показ", ["node", "тест_показу.js"], КОД),
]
for ім in ("картка_події", "картка_replay", "картка_заперечення", "е2_підвиди_місця", "е2_дріт_вид", "е2_вид_факту"):
    ПЕРЕВІРКИ.append((ім, [sys.executable, "проби/" + ім + ".py"], КОД))
ПЕРЕВІРКИ += [("межі-після", [sys.executable, "джерела/прилади/корінь_е2_межі.py"], КОРІНЬ),
               ("промпти-після", [sys.executable, "-W", "ignore", "джерела/прилади/корінь_е2_промпти.py",
                "--база", "аудит/корені/Е2-промпти-довжини.json", "--деталі"], КОРІНЬ)]
підсумок = []
for назва, команда, тека in ПЕРЕВІРКИ:
    print("ПОЧАТО", назва, flush=True)
    початок = time.monotonic()
    with (ТЕКА / (назва + ".txt")).open("w", encoding="utf-8", newline="\n") as журнал:
        р = subprocess.run(команда, cwd=тека, stdout=журнал, stderr=subprocess.STDOUT)
    підсумок.append(dict(назва=назва, команда=команда, код=р.returncode,
                         секунд=round(time.monotonic() - початок, 2)))
    (ТЕКА / "підсумок.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("ЗАВЕРШЕНО", назва, р.returncode, flush=True)
sys.exit(int(any(п["код"] for п in підсумок if п["назва"] != "складені-до")))
