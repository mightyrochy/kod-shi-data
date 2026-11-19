"""Відтворює заморожений повтор відбору: python -X utf8 збір.py <тека фото сцен>.

Фото лишаються поза репозиторієм. Кадри без sha256 не були одержані під час відбору й не входять у вимір.
"""
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.request


def головна():
    """Дістає лише описані байти, звіряє sha256 і завершується з помилкою при невідтворюваному файлі."""
    набір = json.loads(Path(__file__).with_name("повтор-відбору.json").read_text("utf-8"))
    тека = Path(sys.argv[1]) / "портрети"
    тека.mkdir(parents=True, exist_ok=True)
    одержано = 0
    for ф in набір["кадри"]:
        if "sha256" not in ф:
            continue
        шлях = тека / (ф["id"] + ".jpg")
        if not шлях.exists() or hashlib.sha256(шлях.read_bytes()).hexdigest() != ф["sha256"]:
            time.sleep(1.5)
            запит = urllib.request.Request(ф["url"], headers={"User-Agent": "PortraitProbe/0.1 (research script)"})
            with urllib.request.urlopen(запит, timeout=60) as відповідь:
                байти = відповідь.read()
            if hashlib.sha256(байти).hexdigest() != ф["sha256"]:
                raise ValueError("Інші байти за адресою: " + ф["id"])
            шлях.write_bytes(байти)
        одержано += 1
    print("Звірено кадрів:", одержано)


if __name__ == "__main__":
    головна()
