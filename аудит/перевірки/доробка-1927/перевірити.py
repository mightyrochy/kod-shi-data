"""Повтор каталогу, батареї та доступних проб сім'ї без моделей і мережевих фото."""
import concurrent.futures
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def головна():
    """Виконати всі команди до завершення й зберегти окремий журнал кожної."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    код = корінь / "джерела"
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8", NODE_PATH=str(код / "node_modules"))
    результати = []

    def виконати(назва, команда):
        """Запустити команду з успадкованим середовищем і дочекатися її кінця."""
        початок = time.monotonic()
        with (тека / (назва + ".txt")).open("wb") as журнал:
            код_виходу = subprocess.run(команда, cwd=код, stdout=журнал, stderr=subprocess.STDOUT).returncode
        р = dict(назва=назва, команда=команда, код=код_виходу, секунд=round(time.monotonic() - початок, 2))
        print(json.dumps(р, ensure_ascii=False), flush=True)
        return р

    probe = str(тека / "відтворити.py")
    for режим in ("каталог", "два", "невідомо", "полюс"):
        команда = [sys.executable, probe, str(корінь), режим]
        if режим in ("каталог", "два"):
            команда.append(str(тека / "каталог-ПІСЛЯ.json"))
        результати.append(виконати("ПІСЛЯ-" + режим, команда))
    батарея = [("дим", ["стенд_знімок.py", "--дим"]), ("живий_шлях", ["тест_живого_шляху.py"]),
               ("протокол", ["тест_протоколу.py"]), ("розділи", ["прилади/розділи_гейтів.py"]),
               ("контракти", ["audit_contracts.py"])]
    for назва, аргументи in батарея:
        результати.append(виконати(назва, [sys.executable, *аргументи]))
    результати.append(виконати("показ", ["node", "тест_показу.js"]))
    окремі_входи = {"колір_весь_кадр_5286.py", "колір_кадр_слово_5222.py", "колір_кадр_слово_5223.py"}
    спільні = {"колір_спільне.py", "pal_вердикт.py", "pal_вимір.py"}
    історичні = {"колір_hex_вікна.py", "колір_майже_нейтраль.py"}
    проби = sorted(set(код.glob("проби/колір_*.py")) | set(код.glob("проби/pal_*.py")) |
                   set(код.glob("проби/поділ_*_ast.py")))
    доступні = [п for п in проби if п.name not in окремі_входи | спільні | історичні]
    def команда_проби(п):
        """Для 300 образів зберегти штатний суд і звірене індексування діагностики (9704)."""
        if п.name == "колір_нейтраль.py":
            return [sys.executable, str(корінь / "аудит/проби/тип_кольору_213_нейтраль.py")]
        return [sys.executable, str(п)]
    # Це незалежні процеси команд, без спільних Python-модулів чи підміни каталогу.
    # Кожна команда дочекана; скрипти зі змінами worktree виконуються послідовно нижче.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as пул:
        завдання = [пул.submit(виконати, п.stem, команда_проби(п)) for п in доступні]
        for завдання_ in concurrent.futures.as_completed(завдання):
            результати.append(завдання_.result())
            (тека / "результати.json").write_bytes(json.dumps(результати, ensure_ascii=False, indent=2).encode())
    for назва in sorted(історичні):
        результати.append(виконати(Path(назва).stem, [sys.executable, str(код / "проби" / назва)]))
    підсумок = dict(команди=результати, окремі_входи=sorted(окремі_входи), спільні_модулі=sorted(спільні))
    (тека / "результати.json").write_bytes(json.dumps(підсумок, ensure_ascii=False, indent=2).encode())
    return int(any(р["код"] for р in результати))


if __name__ == "__main__":
    raise SystemExit(головна())
