"""Передумова прогону: сирі результати CLI й приймання зображення без API-ключа."""
import base64
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "вимір_транспорту"
EVIDENCE.mkdir(exist_ok=True)
AGY = shutil.which("agy")


def run(name, arguments, payload=None, cwd=None):
    start = time.time()
    result = subprocess.run(
        [AGY, *arguments], input=payload, capture_output=True,
        encoding="utf-8", errors="replace", cwd=cwd, timeout=900,
    )
    (EVIDENCE / (name + ".stdout.txt")).write_text(result.stdout, encoding="utf-8")
    (EVIDENCE / (name + ".stderr.txt")).write_text(result.stderr, encoding="utf-8")
    summary = {
        "команда": ["agy", *arguments], "код": result.returncode,
        "початок_utc": datetime.datetime.fromtimestamp(start, datetime.timezone.utc).isoformat(),
        "секунд": round(time.time() - start, 3),
    }
    (EVIDENCE / (name + ".json")).write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    if name != "фото":
        print(result.stdout, flush=True)
    return result


if __name__ == "__main__":
    run("версія", ["--version"])
    run("моделі", ["models"])
    run("квота_до", ["-p", "/usage"])
    image_path = ROOT.parent / "живий-як-людина-1" / "с4_побачення_19_30" / "знімки" / "001.jpg"
    prompt = (
        "Це перевірка передавання зображення до моделі перед живим прогоном. "
        "Не викликай інструментів, не читай файлів. Подивися лише на прикріплений знімок. "
        "Відповідай українською одним JSON-об'єктом: "
        '{"бачу_зображення": true або false, "видимий_напис": "дослівний великий напис зі знімка", '
        '"опис": "що видно на знімку"}. Якщо зображення не отримала, чесно постав false.'
    )
    message = {"event": "user", "message": {"content": [
        {"type": "text", "text": prompt},
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
         "data": base64.b64encode(image_path.read_bytes()).decode("ascii")}},
    ]}}
    payload = json.dumps(message, ensure_ascii=False) + "\n"
    (EVIDENCE / "фото.stdin.jsonl").write_text(payload, encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="agy-фото-", dir=os.environ["TEMP"]) as neutral:
        result = run("фото", ["--model", "gemini-3.8-flash-high", "--input-format", "stream-json",
                              "--output-format", "stream-json", "--disable-slash-commands"], payload, neutral)
    print(result.stdout[-10000:], flush=True)
    print(result.stderr[-2000:], flush=True)
    run("квота_після", ["-p", "/usage"])
    raise SystemExit(result.returncode)
