"""Повторити локальні докази на незмінній голові PR та зберегти власні журнали."""
import concurrent.futures
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def головна():
    """Дочекатися всіх команд; моделі та зовнішні платні сервіси не викликати."""
    тека = Path(__file__).resolve().parent
    після, до = map(lambda п: Path(п).resolve(), sys.argv[1:3])
    os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8",
                      NODE_PATH=str(після / "джерела/node_modules"))
    for дерево in (після, до):
        subprocess.run([sys.executable, "-X", "utf8", "-c",
            "import чистка_каталогу as ч, feed as Ф; "
            "print('фід:', ч.забезпечити_чистим('каталог_повний.xml')['шлях']); "
            "print('фікстура:', Ф.каталог_на_диску('каталог_brief.xml'))"],
            cwd=дерево / "джерела", check=True)
    for п in (після / "джерела/проби").glob("колір_тип_213_*.py"):
        shutil.copy2(п, до / "джерела/проби" / п.name)
    завдання = []
    батарея = [("дим", ["стенд_знімок.py", "--дим"]),
               ("живий_шлях", ["тест_живого_шляху.py"]),
               ("протокол", ["тест_протоколу.py"]),
               ("розділи", ["прилади/розділи_гейтів.py"]),
               ("контракти", ["audit_contracts.py"]),
               ("показ", ["node", "тест_показу.js"])]
    завдання.extend(("ПІСЛЯ", після, ім, арг) for ім, арг in батарея)
    пропуск = {"колір_спільне", "pal_вердикт", "pal_вимір", "колір_нейтраль",
               "колір_весь_кадр_5286", "колір_кадр_слово_5222", "колір_кадр_слово_5223",
               "колір_hex_вікна", "колір_майже_нейтраль", "колір_прози_шар", "колір_ярлик_hex"}
    for п in sorted((після / "джерела/проби").glob("*.py")):
        if not п.stem.startswith(("колір_", "pal_", "поділ_")) or п.stem in пропуск:
            continue
        if п.stem.startswith("поділ_") and not п.stem.endswith("_ast"):
            continue
        завдання.append(("ПІСЛЯ", після, п.stem, [п]))
        if п.stem.startswith("колір_тип_213_") or п.stem == "pal_K-PAL-16":
            завдання.append(("ДО", до, п.stem, [до / "джерела/проби" / п.name]))
    відтворити = після / "аудит/перевірки/доробка-1927/відтворити.py"
    for режим, дерево in (("ДО", до), ("ПІСЛЯ", після)):
        завдання.append((режим, дерево, "каталог", [відтворити, дерево, "каталог", тека / (режим + "-каталог.json")]))

    def виконати(режим, дерево, ім, арг):
        """Записати точну команду, код та повний вивід одного завершеного процесу."""
        команда = (["node", *map(str, арг[1:])] if арг[0] == "node" else
                   [sys.executable, "-X", "utf8", *map(str, арг)])
        час = time.monotonic()
        with (тека / (режим + "-" + ім + ".txt")).open("wb") as журнал:
            код = subprocess.run(команда, cwd=дерево / "джерела", stdout=журнал,
                                 stderr=subprocess.STDOUT).returncode
        return dict(режим=режим, назва=ім, команда=команда, дерево=str(дерево),
                    код=код, секунд=round(time.monotonic() - час, 2))

    результати = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as пул:
        виклики = [пул.submit(виконати, *з) for з in завдання]
        for в in concurrent.futures.as_completed(виклики):
            р = в.result()
            результати.append(р)
            print(р["режим"], р["назва"], р["код"], р["секунд"], flush=True)
            (тека / "результати.json").write_text(json.dumps(результати, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Завершено команд:", len(результати), flush=True)


if __name__ == "__main__":
    головна()
