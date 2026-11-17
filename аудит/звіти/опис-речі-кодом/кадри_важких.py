"""Тягне по три кадри кожної дібраної речі й складає аркуш «річ — один рядок кадрів» для опису з фото.

Кадри й аркуші — поза репозиторієм (тека в аргументі): у репозиторії лишаються адреси кадрів у `важкі_речі.tsv`.

    python аудит/звіти/опис-речі-кодом/кадри_важких.py /tmp/важкі
"""
import csv
import io
import subprocess
import sys
from pathlib import Path

from PIL import Image

ТЕКА = Path(__file__).resolve().parent
ВИСОТА = 760


def головне(куди):
    куди.mkdir(parents=True, exist_ok=True)
    with open(ТЕКА / "важкі_речі.tsv", encoding="utf-8") as ф:
        for р in csv.DictReader(ф, delimiter="\t"):
            кадри = []
            for адреса in р["кадри"].split()[:3]:
                дані = subprocess.run(["curl", "-sSL", "--max-time", "40", "-A", "Mozilla/5.0", адреса],
                                      capture_output=True).stdout
                try:
                    к = Image.open(io.BytesIO(дані)).convert("RGB")
                except Exception:
                    continue
                кадри.append(к.resize((round(к.width * ВИСОТА / к.height), ВИСОТА)))
            if not кадри:
                print(р["номер"], "кадрів нема")
                continue
            аркуш = Image.new("RGB", (sum(к.width for к in кадри) + 8 * (len(кадри) - 1), ВИСОТА), "white")
            x = 0
            for к in кадри:
                аркуш.paste(к, (x, 0))
                x += к.width + 8
            аркуш.save(куди / f"{int(р['номер']):02d}.jpg", quality=88)
            print(р["номер"], len(кадри), аркуш.size)


if __name__ == "__main__":
    головне(Path(sys.argv[1]))
