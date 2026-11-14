"""Відтворення незалежної перевірки #3753; код PR не змінює.

python -X utf8 <цей файл> <дерево 7067f645> <тека журналів> <проби|сусідні|батарея> [<назва>]
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

дерево, вихід, режим = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3]
вихід.mkdir(parents=True, exist_ok=True)
оточення = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
оточення.pop("MODEL", None)  # проба вибору працює із заглушкою, без API
проби = [
    "колір_відлуння_образи", "колір_тип_213_добір_металу", "повтор_стеля",
    "vzuttia_руки", "е2_дріт_вид", "вибір_стабільність", "слот_цілком_ранг", "сід3_солі",
]
сусідні = [
    "колір_опори_до_після", "колір_тип_213_великі", "колір_тип_213_композитор",
    "колір_тип_213_контраст", "колір_тип_213_межа", "колір_тип_213_метал",
    "колір_тип_213_опора", "колір_тип_213_основа", "колір_тип_213_читачі",
    "повтор_воронка", "повтор_голова", "повтор_каталог", "повтор_позиція",
    "повтор_руки", "повтор_сіди", "повтор_страти", "повтор_частки", "ш1_таблиця_каталогу", "збій_п5",
]
if режим in ("проби", "сусідні"):
    завдання = [(ім, [sys.executable, "-X", "utf8", "проби/" + ім + ".py"] +
                 (["assess"] if ім == "вибір_стабільність" else [])) for ім in (проби if режим == "проби" else сусідні)]
    if режим == "проби":
        завдання.insert(0, ("сторож", [sys.executable, "-I", "-X", "utf8", str(дерево / "аудит/проби/Проби-таблиця-збірки/тест_сторожа.py")]))
elif режим == "батарея":
    завдання = [(ім, [sys.executable, "-X", "utf8", ім + ".py"] + (["--дим"] if ім == "стенд_знімок" else []))
                for ім in ["стенд_знімок", "тест_живого_шляху", "тест_протоколу", "прилади/розділи_гейтів", "audit_contracts"]]
    завдання.append(("тест_показу", ["node", "тест_показу.js"]))
else:
    raise SystemExit("невідомий режим")
if len(sys.argv) > 4:
    завдання = [(ім, команда) for ім, команда in завдання if ім in sys.argv[4].split(",")]
результати = []
початок_пакета = time.monotonic()
for ім, команда in завдання:
    ліміт = 540 - (time.monotonic() - початок_пакета)
    if ліміт <= 0:
        print("Межа пакета 540 с; решту не запущено.", flush=True)
        break
    початок = time.monotonic()
    try:
        процес = subprocess.run(команда, cwd=дерево / "джерела", env=оточення, capture_output=True,
                                encoding="utf-8", errors="replace", timeout=ліміт)
        код, журнал = процес.returncode, процес.stdout + процес.stderr
    except subprocess.TimeoutExpired as е:
        код = "час %s с" % round(ліміт, 2)
        def текст(х):
            return х.decode("utf-8", "replace") if isinstance(х, bytes) else (х or "")
        журнал = текст(е.stdout) + текст(е.stderr)
    запис = dict(проба=ім, код=код, секунди=round(time.monotonic() - початок, 2), команда=команда)
    результати.append(запис)
    назва = ім.replace("/", "_")
    (вихід / (назва + ".txt")).write_text("КОМАНДА: " + json.dumps(команда, ensure_ascii=False) +
        "\nКОД: " + str(код) + "\n" + журнал, encoding="utf-8")
    (вихід / (режим + ".json")).write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(запис, ensure_ascii=False), flush=True)
