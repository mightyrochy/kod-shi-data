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
    if режим == "читачі":
        return команда([sys.executable, ТЕКА / "читачі.py"], "читачі.txt")
    if режим == "фінал":
        коди = []
        for арг, назва in (
            ([sys.executable, "джерела/прилади/згорнути_дошку.py", "--лише-перевірити"], "дошка.txt"),
            (["git", "diff", "--exit-code", "878370b0985c18988fdda88ef6ba7a8bffe5dc59", "HEAD", "--",
              "zhnyvarka", "джерела", ".github", "аудит/адаптери/gemini"], "код-після-злиття.txt"),
            (["git", "diff", "--exit-code", "39989dd42a49625c74c1593aaafc249f44fc54c0", "HEAD", "--",
              ".github", "аудит/адаптери/gemini"], "захищені-шляхи.txt"),
            (["git", "diff", "--exit-code", "--", "аудит/перевірка/докази_2069_3"], "старі-докази.txt"),
            (["git", "diff", "--cached", "--check", "--", ".", ":(exclude)аудит/перевірка/докази_2069_4/*.txt"], "диф.txt"),
        ):
            коди.append(команда(арг, назва))
        return int(any(коди))
    if режим == "чутливість":
        with tempfile.TemporaryDirectory(prefix="review-2069-4-broken-") as дім:
            дім = Path(дім)
            архів(дім, "HEAD")
            докази = дім / "аудит/перевірка/докази_2069_3"
            shutil.copytree(СТАРІ, докази, ignore=shutil.ignore_patterns("*.txt", "*.png", "__pycache__"))
            shutil.copytree(КОРІНЬ / "джерела/проби", дім / "джерела/проби", ignore=shutil.ignore_patterns("__pycache__"))
            subprocess.run(["git", "init", "-q", str(дім)], check=True)
            обєкти = subprocess.check_output(["git", "rev-parse", "--git-path", "objects"], cwd=КОРІНЬ).decode().strip()
            # Лише читання вже наявних об'єктів: повна копія історії тут не потрібна.
            (дім / ".git/objects/info/alternates").write_bytes(
                (КОРІНЬ / обєкти).resolve().as_posix().encode("utf-8") + b"\n")
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
