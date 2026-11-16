"""Спроба 2: сирі входи й відповіді передавання фото файлом за підпискою."""
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parent
СПРОБА = os.environ.get("SPROBA", "спроба_2")
OUT = ROOT / "вимір_транспорту" / СПРОБА
PHOTOS = OUT / "файли"
WORK = Path(os.environ["TEMP"]) / ("agy-транспорт-" + СПРОБА)
AGY = shutil.which("agy")
MODEL = "gemini-3.8-flash-high"
QUESTION = (
    "Подивись на три фото речей у цьому запиті. Для кожного фото назви вид речі "
    "й основний колір. Якщо фото немає або ти не можеш його бачити, чесно скажи це; "
    "не вгадуй. Відповідай українською коротким JSON-масивом із полями файл, вид, колір. "
    "Дозволено лише читати прикладені фото в поточній робочій теці. "
    "Не запускай команд, не змінюй файлів, не звертайся до мережі, інших тек чи інших агентів."
)
CONTROL = (
    "Це перевірка читання трьох фото. Прочитай кожен із зазначених нижче файлів "
    "інструментом view_file рівно один раз. Якщо файл відсутній, для нього запиши "
    "немає фото; інших шляхів не перевіряй, повторних спроб не роби. Для отриманих "
    "фото назви вид речі та основний колір, які бачиш на фото, без здогадів. "
    "Після цих трьох читань одразу поверни лише короткий JSON-масив "
    "із полями файл, вид, колір. Дозволено лише читання цих трьох файлів "
    "у поточній теці; жодних інших інструментів, команд, записів, мережі чи агентів.\n\n"
    "@01.jpg\n@02.jpg\n@03.webp"
)


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def run(name, args, prompt=None, executable=None):
    started = time.time()
    command = [executable or AGY, *args]
    if prompt is not None:
        (OUT / (name + ".prompt.txt")).write_text(prompt, encoding="utf-8")
    stdout_path = OUT / (name + ".stdout.txt")
    stderr_path = OUT / (name + ".stderr.txt")
    with stdout_path.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, cwd=WORK,
                                    stdout=stdout, stderr=stderr, timeout=360)
            code = result.returncode
        except FileNotFoundError as error:
            stderr.write(str(error))
            code = 127
        except subprocess.TimeoutExpired as error:
            stderr.write(str(error))
            code = 124
    metadata = {"команда": [executable or "agy", *args], "cwd": str(WORK), "код": code,
                "початок_utc": datetime.datetime.fromtimestamp(started, datetime.timezone.utc).isoformat(),
                "секунд": round(time.time() - started, 3)}
    save(name + ".json", metadata)
    events = []
    for line in stdout_path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            events.append(json.loads(line))
        except ValueError:
            pass
    final = next((e["result"] for e in reversed(events) if e.get("event") == "result"), None)
    print(json.dumps({**metadata, "результат": final}, ensure_ascii=False), flush=True)
    return metadata


def prepare():
    OUT.mkdir(exist_ok=True, parents=True)
    WORK.mkdir(exist_ok=True)
    PHOTOS.mkdir(exist_ok=True)
    archive = ROOT.parent / "живий-як-людина-1/стенд/службове/с4_побачення_19_30/обміни.jsonl.gz"
    urls = []

    def walk(value):
        if isinstance(value, str) and value.startswith("{"):
            try:
                walk(json.loads(value))
            except ValueError:
                pass
        elif isinstance(value, list):
            for entry in value:
                walk(entry)
        elif isinstance(value, dict):
            if value.get("type") == "image":
                url = value.get("source", {}).get("url")
                if url and url not in urls:
                    urls.append(url)
            for entry in value.values():
                walk(entry)

    with gzip.open(archive, "rt", encoding="utf-8") as stream:
        for line in stream:
            walk(json.loads(line))
    records = []
    for number, index in enumerate((0, 2, 4), 1):
        url = urls[index]
        request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request, timeout=45) as response:
            data = response.read()
            record = {"url": url, "статус": response.status,
                      "тип": response.headers.get("Content-Type"), "байтів": len(data)}
        extension = ".webp" if data[8:12] == b"WEBP" else ".jpg"
        name = f"{number:02d}" + extension
        (WORK / name).write_bytes(data)
        (PHOTOS / name).write_bytes(data)
        records.append({**record, "файл": name, "sha256": hashlib.sha256(data).hexdigest(),
                        "джерело": str(archive.relative_to(ROOT.parent.parent.parent))})
    save("походження_фото.json", records)
    print(json.dumps(records, ensure_ascii=False), flush=True)


def ask(name, prompt):
    return run(name, ["--model", MODEL, "--output-format", "stream-json",
                      "--disable-slash-commands", "--print-timeout", "4m", "-p", prompt], prompt)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    mode = sys.argv[1]
    if mode == "підготувати":
        prepare()
        run("версія", ["--version"])
        run("довідка", ["--help"])
        run("моделі", ["models"])
        run("квота_до", ["-p", "/usage"])
    elif mode == "без_фото":
        ask("без_фото", QUESTION)
    elif mode == "посилання":
        photos = json.loads((OUT / "походження_фото.json").read_text(encoding="utf-8"))
        ask("посилання", QUESTION + "\n\n" + "\n".join("@" + p["файл"] for p in photos))
    elif mode == "інструмент":
        photos = json.loads((OUT / "походження_фото.json").read_text(encoding="utf-8"))
        ask("інструмент", QUESTION + "\n\nПрочитай фото інструментом view_file за абсолютними шляхами:\n" +
            "\n".join(str(WORK / p["файл"]) for p in photos))
    elif mode == "квота_після":
        run("квота_після", ["-p", "/usage"])
    elif mode == "вхід_claude":
        run("вхід_claude", ["auth", "status"], executable="claude")
    elif mode in {"контроль_без_фото", "контроль_фото"}:
        WORK = Path(os.environ["TEMP"]) / ("agy-транспорт-контроль-" + СПРОБА)
        WORK.mkdir(exist_ok=True)
        if mode == "контроль_без_фото":
            assert not any(WORK.iterdir()), "Контрольна тека має бути порожньою"
        else:
            for photo in PHOTOS.iterdir():
                shutil.copyfile(photo, WORK / photo.name)
        ask(mode, CONTROL)
