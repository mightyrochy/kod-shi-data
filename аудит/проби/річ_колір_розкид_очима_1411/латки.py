"""Прямокутники, вибрані при огляді: свідки, не вимір продукту і не поріг вердикту.

З кореня: python -X utf8 -I аудит/проби/річ_колір_розкид_очима_1411/латки.py <тека фото>
Координати частками кадру; медіана Lab ділянки без поправки за тлом.
"""
import csv
import statistics
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТУТ = Path(__file__).resolve().parent
sys.path.insert(0, str(ТУТ.parents[2] / "джерела"))
import colorspace as К
import surface as П

ЛАТКИ = {
    "03-01.jpg": (0.38, 0.43, 0.45, 0.49),
    "14-01.jpg": (0.17, 0.20, 0.30, 0.32),
    "22-01.jpg": (0.36, 0.55, 0.45, 0.63),
    "25-01.jpg": (0.43, 0.61, 0.50, 0.70),
    "27-01.jpg": (0.60, 0.63, 0.73, 0.72),
    "32-02.jpg": (0.54, 0.48, 0.62, 0.61),
    "37-02.jpg": (0.40, 0.31, 0.49, 0.42),
}


def головна():
    фото = Path(sys.argv[1])
    with (ТУТ / "вибірка.tsv").open(encoding="utf-8") as ф:
        за_назвою = {р["локально"]: р for р in csv.DictReader(ф, delimiter="\t")}
    шрифт = Path("C:/Windows/Fonts/arial.ttf")
    if not шрифт.exists():
        шрифт = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    ш = ImageFont.truetype(str(шрифт), 17)
    аркуш = Image.new("RGB", (1280, 1100), "white")
    олівець = ImageDraw.Draw(аркуш)
    вихід = []
    for і, (назва, межі) in enumerate(ЛАТКИ.items()):
        р = за_назвою[назва]
        im = Image.open(фото / назва).convert("RGB")
        пікселі = tuple(round(в * (im.width if н % 2 == 0 else im.height)) for н, в in enumerate(межі))
        шмат = im.crop(пікселі).resize((60, 60))
        дані = шмат.get_flattened_data() if hasattr(шмат, "get_flattened_data") else шмат.getdata()
        лаби = [К.to_lab(п) for п in дані]
        лаб = tuple(statistics.median(л[к] for л in лаби) for к in range(3))
        вимір = К.to_lab(tuple(int(р["hex"][н:н + 2], 16) for н in (1, 3, 5)))
        код, _ = П.слово_з_lab(лаб)
        вихід.append(dict(номер=р["номер"], кадр=р["кадр"], локально=назва,
                          межі=json_межі(межі), пікселі=json_межі(пікселі),
                          hex_латки=К.hex_з_lab(лаб), Lab_латки=json_межі(tuple(round(в, 2) for в in лаб)),
                          код_латки=код, hex_запису=р["hex"], код_запису=р["код"],
                          dE00=round(К.de00(лаб, вимір), 2)))
        ImageDraw.Draw(im).rectangle(пікселі, outline="#ff00ff", width=max(2, im.width // 300))
        im = ImageOps.contain(im, (310, 410))
        x, y = (і % 4) * 320, (і // 4) * 550
        аркуш.paste(im, (x + (320 - im.width) // 2, y))
        олівець.text((x + 8, y + 415), f'{р["номер"]}.{р["кадр"]}', font=ш, fill="black")
        for зсув, hex_, підпис in [(0, р["hex"], "запис"), (155, К.hex_з_lab(лаб), "ділянка")]:
            олівець.text((x + зсув + 8, y + 443), підпис, font=ш, fill="black")
            олівець.rectangle((x + зсув + 8, y + 468, x + зсув + 68, y + 525), fill=hex_, outline="black")
            олівець.text((x + зсув + 72, y + 483), hex_, font=ш, fill="black")
    with (ТУТ / "латки.tsv").open("w", encoding="utf-8", newline="") as ф:
        п = csv.DictWriter(ф, fieldnames=list(вихід[0]), delimiter="\t", lineterminator="\n")
        п.writeheader()
        п.writerows(вихід)
    аркуш.save(ТУТ / "свідки-латки.jpg", quality=82, optimize=True)
    assert (ТУТ / "свідки-латки.jpg").stat().st_size <= 300_000
    for р in вихід:
        print(р["номер"], р["hex_латки"], р["код_латки"], р["dE00"])


def json_межі(значення):
    return ",".join(str(в) for в in значення)


if __name__ == "__main__":
    головна()
