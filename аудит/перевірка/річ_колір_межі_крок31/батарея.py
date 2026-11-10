"""Батарея кроку 31: кожна команда до кінця; повний вивід — окремим файлом."""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def головна():
    """Виконати обов'язкову батарею й проби сім'ї та зберегти коди виходу."""
    корінь = Path(__file__).resolve().parents[3]
    джерела = корінь / "джерела"
    звіт = Path(__file__).resolve().parent
    os.environ["PYTHONUTF8"] = "1"
    os.environ["NODE_PATH"] = str(джерела / "node_modules")
    команди = [
        [sys.executable, "стенд_знімок.py", "--дим"],
        [sys.executable, "тест_живого_шляху.py"],
        [sys.executable, "тест_протоколу.py"],
        [sys.executable, "прилади/розділи_гейтів.py"],
        [sys.executable, "audit_contracts.py"],
        ["node", "тест_показу.js"],
    ]
    проби = sorted((джерела / "проби").glob("поділ_*_ast.py"))
    проби += sorted(п for п in (джерела / "проби").glob("pal_*.py")
                    if п.name not in ("pal_вердикт.py", "pal_вимір.py"))
    проби += sorted((джерела / "проби").glob("колір_тип_213_*.py"))
    проби += [джерела / "проби/прикраси_обруч_6877.py"]
    команди += [[sys.executable, str(п.relative_to(джерела))] for п in проби]
    ключ = lambda команда: " ".join(команда[1:]).replace("\\", "/")
    коди = {}
    if "--продовжити" in sys.argv and (звіт / "батарея.txt").exists():
        for рядок in (звіт / "батарея.txt").read_text(encoding="utf-8").splitlines():
            назва, _, код = рядок.rpartition(": код ")
            if назва and код == "0": коди[назва.replace("\\", "/")] = 0

    def виконати(команда):
        """Дочекатися одного процесу й зберегти його повний журнал."""
        мітка = Path(команда[1]).stem
        with (звіт / (мітка + ".txt")).open("w", encoding="utf-8") as файл:
            вихід = subprocess.run(команда, cwd=джерела, stdout=файл, stderr=subprocess.STDOUT)
        return команда, вихід.returncode

    def записати(результат):
        """Оновити спільний журнал лише після завершення команди."""
        команда, код = результат
        коди[ключ(команда)] = код
        рядок = ключ(команда) + f": код {код}"
        print(рядок, flush=True)
        рядки = [ключ(к) + f": код {коди[ключ(к)]}" for к in команди if ключ(к) in коди]
        (звіт / "батарея.txt").write_text("\n".join(рядки) + "\n", encoding="utf-8")

    for команда in команди[:6]:
        if коди.get(ключ(команда)) != 0: записати(виконати(команда))
    # Проби читають джерела й офлайн-каталог; кожна має окремий процес і журнал.
    # Вимір середовища: 32 логічні процесори, 4 979 520 KiB вільної пам'яті.
    with ThreadPoolExecutor(max_workers=3) as пул:
        роботи = [пул.submit(виконати, команда) for команда in команди[6:] if коди.get(ключ(команда)) != 0]
        for робота in as_completed(роботи): записати(робота.result())
    sys.exit(any(коди.get(ключ(к)) != 0 for к in команди))


if __name__ == "__main__":
    головна()
