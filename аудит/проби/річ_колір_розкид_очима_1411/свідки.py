"""Свідки #3717 із зафіксованого злиття: три фото, записи й аркуш без мережі."""
import hashlib
import io
import json
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТУТ = Path(__file__).resolve().parent
ДЖЕРЕЛО = "d7ac67c9692ecdea2f1aa7005a1fddab6a548bf7"
ПРЕФІКС = "аудит/проби/Прогін1-пояснення-проти-фото/"


def обʼєкт(назва):
    return subprocess.check_output(["git", "show", f"{ДЖЕРЕЛО}:{ПРЕФІКС}{назва}"])


def головна():
    дані = json.loads(обʼєкт("джерела.json"))
    маніфест = json.loads(обʼєкт("кадри/походження.json"))
    шрифт = Path("C:/Windows/Fonts/arial.ttf")
    if not шрифт.exists():
        шрифт = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ш = ImageFont.truetype(str(шрифт), 18)
    аркуш = Image.new("RGB", (1200, 650), "white")
    олівець = ImageDraw.Draw(аркуш)
    записи = []
    for і, (ключ, hex_, код) in enumerate([("2-16-6", "#584c4d", "black"),
                                          ("3-16-7", "#4a2b2c", "brown"),
                                          ("3-16-8", "#4a2b2c", "brown")]):
        р = маніфест["кадри"][ключ]
        байти = обʼєкт("кадри/" + р["файл"])
        assert hashlib.sha256(байти).hexdigest() == р["sha256"]
        im = ImageOps.contain(Image.open(io.BytesIO(байти)).convert("RGB"), (390, 505))
        аркуш.paste(im, (і * 400 + (400 - im.width) // 2, 0))
        олівець.text((і * 400 + 8, 515), ключ, font=ш, fill="black")
        олівець.rectangle((і * 400 + 8, 550, і * 400 + 88, 630), fill=hex_, outline="black")
        олівець.text((і * 400 + 100, 560), hex_, font=ш, fill="black")
        олівець.text((і * 400 + 100, 590), код, font=ш, fill="black")
        записи.append(dict(кадр=ключ, **р, запис=дані["каталог"][ключ]))
    аркуш.save(ТУТ / "свідки-3717.jpg", quality=82, optimize=True)
    assert (ТУТ / "свідки-3717.jpg").stat().st_size <= 300_000
    (ТУТ / "свідки-3717.json").write_text(json.dumps(dict(
        джерело=ДЖЕРЕЛО, архівовано_utc=маніфест["архівовано_utc"], межа=маніфест["походження"],
        кадри=записи, речі=[р for о in дані["образи"][:2] for р in о["вхід"]["outfit"]["items"]
                          if р["n"] in ("#395·16", "#390·07")]), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Свідки #3717: три фото, хеші звірено; дві речі поза випадковою вибіркою")


if __name__ == "__main__":
    головна()
