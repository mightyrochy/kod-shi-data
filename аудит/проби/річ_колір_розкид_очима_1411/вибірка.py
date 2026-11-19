"""Відтворювана вибірка й аркуші для ручного огляду; даних продукту не змінює.

З кореня: python -I аудит/проби/річ_колір_розкид_очима_1411/вибірка.py <тимчасова тека>
Потрібні git-об'єкти гілки даних; її зафіксовану голову наведено нижче.
"""
import csv
import hashlib
import io
import random
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ДЖЕРЕЛО = "c7b37862c5195f823e0ef211cd8ecd718b498f95"
ЗЕРНО = 20261114
ТУТ = Path(__file__).resolve().parent
СУКУПНІСТЬ = "аудит/проби/річ_колір_розкид_0811/зберегли_код.tsv"
ФОТО = "аудит/проби/річ_колір_перезбір_0411/"


def обʼєкт(шлях):
    return subprocess.check_output(["git", "show", f"{ДЖЕРЕЛО}:{шлях}"])


def головна():
    тимчасова = Path(sys.argv[1])
    тимчасова.mkdir(parents=True, exist_ok=True)
    байти = обʼєкт(СУКУПНІСТЬ)
    усі = list(csv.DictReader(io.StringIO(байти.decode("utf-8")), delimiter="\t"))
    ідентифікатори = sorted({р["id"] for р in усі})
    assert (len(усі), len(ідентифікатори)) == (292, 154)
    вибрані = random.Random(ЗЕРНО).sample(ідентифікатори, 40)
    рядки = []
    for номер, ід in enumerate(вибрані, 1):
        кадри = [р for р in усі if р["id"] == ід]
        for кадр, р in enumerate(кадри, 1):
            знімок = обʼєкт(ФОТО + р["фото"])
            назва = f"{номер:02d}-{кадр:02d}.jpg"
            (тимчасова / назва).write_bytes(знімок)
            рядки.append(dict(номер=номер, кадр=кадр, **р,
                              sha256=hashlib.sha256(знімок).hexdigest(), локально=назва))
    with (ТУТ / "вибірка.tsv").open("w", encoding="utf-8", newline="") as ф:
        п = csv.DictWriter(ф, fieldnames=list(рядки[0]), delimiter="\t", lineterminator="\n")
        п.writeheader()
        п.writerows(рядки)
    шрифт = Path("C:/Windows/Fonts/arial.ttf")
    if not шрифт.exists():
        шрифт = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ш = ImageFont.truetype(str(шрифт), 18)
    # 8 кадрів на аркуші: кожен досить великий для порівняння кольору з латкою.
    for початок in range(0, len(рядки), 8):
        аркуш = Image.new("RGB", (1280, 1080), "white")
        олівець = ImageDraw.Draw(аркуш)
        for і, р in enumerate(рядки[початок:початок + 8]):
            x, y = (і % 4) * 320, (і // 4) * 540
            фото = ImageOps.contain(Image.open(тимчасова / р["локально"]).convert("RGB"), (308, 412))
            аркуш.paste(фото, (x + (320 - фото.width) // 2, y + 3))
            олівець.text((x + 8, y + 419), f'{р["номер"]}.{р["кадр"]} {р["id"].split("@")[0]}', font=ш, fill="black")
            олівець.text((x + 8, y + 443), р["id"].split("@")[1][:29], font=ш, fill="black")
            олівець.rectangle((x + 8, y + 470, x + 78, y + 523), fill=р["hex"], outline="black")
            олівець.text((x + 88, y + 472), р["код"], font=ш, fill="black")
            олівець.text((x + 88, y + 498), р["hex"], font=ш, fill="black")
            олівець.rectangle((x, y, x + 319, y + 539), outline="#bbbbbb")
        назва = ТУТ / f"аркуш-{початок // 8 + 1:02d}.jpg"
        for якість in (88, 82, 75, 65, 55):
            аркуш.save(назва, quality=якість, optimize=True)
            if назва.stat().st_size <= 300_000:
                break
        assert назва.stat().st_size <= 300_000
    print(f"Сукупність: {len(усі)} кадри / {len(ідентифікатори)} речі; вибірка: {len(рядки)} кадрів / 40 речей")
    print(f"SHA256 сукупності: {hashlib.sha256(байти).hexdigest()}")
    for н, ід in enumerate(вибрані, 1):
        print(н, ід, sum(р["id"] == ід for р in рядки))


if __name__ == "__main__":
    головна()
