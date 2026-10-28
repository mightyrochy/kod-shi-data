"""Послідовні запуски з новими логами; історичні докази зберігаються побайтово."""
import io
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile

ТЕКА = Path(__file__).resolve().parent
КОРІНЬ = ТЕКА.parents[2]
СТАРІ = ТЕКА.with_name("докази_2069_3")
СЕРЕДОВИЩЕ = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1",
                   NODE_PATH=str(КОРІНЬ / "джерела/node_modules"))


def команда(арг, лог, cwd=КОРІНЬ):
    with (ТЕКА / лог).open("w", encoding="utf-8", newline="\n") as ф:
        ф.write("КОМАНДА: " + subprocess.list2cmdline(list(map(str, арг))) + "\n")
        ф.flush()
        р = subprocess.run(list(map(str, арг)), cwd=cwd, env=СЕРЕДОВИЩЕ, stdout=ф,
                           stderr=subprocess.STDOUT, timeout=1800)
        ф.write(f"\nКОД: {р.returncode}\n")
    print(f"{лог}: код {р.returncode}", flush=True)
    return р.returncode


def архів(дім, sha):
    сирий = subprocess.check_output(["git", "archive", sha, "zhnyvarka"], cwd=КОРІНЬ)
    with tarfile.open(fileobj=io.BytesIO(сирий)) as ф:
        ф.extractall(дім, filter="data")


def штатні(режими):
    коди = []
    for режим in режими:
        збережені = {ф: ф.read_bytes() for ф in СТАРІ.glob("*.txt")}
        try:
            коди.append(команда([sys.executable, СТАРІ / "запуски.py", режим], f"запуск-{режим}.txt"))
            for ф, байти in збережені.items():
                нові = ф.read_bytes()
                if нові != байти:
                    assert нові.startswith(байти), str(ф)
                    (ТЕКА / f"{режим}-{ф.name}").write_bytes(нові[len(байти):])
        finally:
            for ф, байти in збережені.items():
                ф.write_bytes(байти)
    return int(any(коди))


def main():
    режим = sys.argv[1]
    if режим == "власні":
        with tempfile.TemporaryDirectory(prefix="review-2069-4-before-") as дім:
            архів(дім, "7a3173e767b403ffcee0030dea4a721cb4dd156b")
            до = команда([sys.executable, ТЕКА / "незалежна.py", дім], "ДО.txt")
        після = команда([sys.executable, ТЕКА / "незалежна.py", КОРІНЬ], "ПІСЛЯ.txt")
        return int(до != 1 or після != 0)
    if режим == "штатні":
        return штатні(("власні", "сім’я", "послідовні", "батарея"))
    if режим == "чутливість":
        with tempfile.TemporaryDirectory(prefix="review-2069-4-broken-") as дім:
            дім = Path(дім)
            архів(дім, "HEAD")
            докази = дім / "аудит/перевірка/докази_2069_3"
            shutil.copytree(СТАРІ, докази, ignore=shutil.ignore_patterns("*.txt", "*.png", "__pycache__"))
            shutil.copytree(КОРІНЬ / "джерела/проби", дім / "джерела/проби", ignore=shutil.ignore_patterns("__pycache__"))
            subprocess.run(["git", "init", "-q", str(дім)], check=True)
            архів_до = subprocess.check_output(["git", "archive", "a136a841db8fed6703c17866166514729f2875eb", "zhnyvarka"], cwd=КОРІНЬ)
            subprocess.run(["git", "-C", str(дім), "fetch", "-q", str(КОРІНЬ), "a136a841db8fed6703c17866166514729f2875eb"], check=True)
            # Справжній злам коду ПІСЛЯ: кожне читання JSONL падає. Прилад не змінюється.
            (дім / "zhnyvarka/журнал_карток.py").write_text(
                'def прочитати(*args):\n    raise RuntimeError("ПРОБА_10678_ЗЛАМАНО_ПІСЛЯ")\n', encoding="utf-8")
            код = команда([sys.executable, докази / "запуски.py", "власні"], "чутливість.txt", дім)
            for ф in докази.glob("*.txt"):
                shutil.copyfile(ф, ТЕКА / ("чутливість-" + ф.name))
            return int(код != 1 or "отримано 1" not in (ТЕКА / "чутливість.txt").read_text(encoding="utf-8"))
    raise ValueError(режим)


if __name__ == "__main__":
    raise SystemExit(main())
