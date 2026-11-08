"""Аркуш 40 кадрів приймання для повторного огляду: кадр, колір і код до → після, вердикт (червона рамка — хибна).

Запуск із кореня: python3 -I аудит/проби/річ_колір_приймання_0811/аркуш.py <тека_фото з вибірка.py>
"""
import csv
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТУТ = Path(__file__).resolve().parent
ШРИФТ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
Ш, В, ФОТО = 240, 390, 290


def головна():
    тека = Path(sys.argv[1])
    рядки = list(csv.DictReader((ТУТ / "приймання.tsv").open(encoding="utf-8"), delimiter="\t"))
    ф = ImageFont.truetype(ШРИФТ, 13)
    аркуш = Image.new("RGB", (8 * Ш, 5 * В), "white")
    олівець = ImageDraw.Draw(аркуш)
    for і, р in enumerate(рядки):
        x, y = (і % 8) * Ш, (і // 8) * В
        фото = ImageOps.contain(Image.open(тека / ("%02d.jpg" % int(р["номер"]))).convert("RGB"), (Ш - 10, ФОТО))
        аркуш.paste(фото, (x + (Ш - фото.width) // 2, y + 4))
        хибна = р["вердикт"] == "хибна"
        олівець.rectangle((x + 1, y + 1, x + Ш - 2, y + В - 2), outline="#d00000" if хибна else "#bbbbbb",
                          width=4 if хибна else 1)
        номер, крамниця = р["річ"].split("@", 1)
        олівець.text((x + 6, y + ФОТО + 6), "%s. %s %s" % (р["номер"], номер, "✗" if хибна else "✓"),
                     fill="#d00000" if хибна else "black", font=ф)
        олівець.text((x + 6, y + ФОТО + 22), крамниця[:32], fill="black", font=ф)
        до, після = (с.strip() for с in р["колір_до→після"].split("→"))
        код_до, код_після = (с.strip() for с in р["код_до→після"].split("→"))
        for зсув, hex_, код in ((0, до, код_до), (118, після, код_після)):
            олівець.rectangle((x + 6 + зсув, y + ФОТО + 40, x + 36 + зсув, y + ФОТО + 70), fill=hex_, outline="black")
            олівець.text((x + 40 + зсув, y + ФОТО + 42), код, fill="black", font=ф)
            олівець.text((x + 40 + зсув, y + ФОТО + 56), hex_, fill="black", font=ф)
        олівець.text((x + 6, y + ФОТО + 76), (р["причина"].split(":")[0] if хибна else "")[:30],
                     fill="#d00000", font=ф)
    аркуш.save(ТУТ / "аркуш.jpg", quality=85)


if __name__ == "__main__":
    головна()
