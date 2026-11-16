"""Аркуші огляду приймання 15.11: кадр, латка його hex, код `main` і ціль (назва запису каталогу).

З кореня, після `вибірка.py <тека> --фото`:
    python3 -I аудит/проби/річ_колір_приймання_1511/аркуші.py <тека>
Пише `контекст.tsv` (ціль, адреса, колір крамниці кожної речі вибірки) і `аркуш-NN.jpg`. Вердиктів не обчислює:
вони — ручний вхід `оцінки.tsv`.
"""
import csv, gzip, json, subprocess, sys, textwrap
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[2]
ДАНІ = "c7b37862c5195f823e0ef211cd8ecd718b498f95"
ШРИФТ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
Ш, В, ЛАТКА, ТЕКСТ, СТОВПЦІВ = 300, 380, 46, 84, 4


def плитка(фото, hex_, рядки):
    п = Image.new("RGB", (Ш, В + ЛАТКА + ТЕКСТ), "white")
    з = Image.open(фото).convert("RGB"); з.thumbnail((Ш, В))
    п.paste(з, ((Ш - з.width) // 2, (В - з.height) // 2))
    м = ImageDraw.Draw(п)
    м.rectangle([0, В, Ш, В + ЛАТКА], fill=hex_)
    ш = ImageFont.truetype(ШРИФТ, 14)
    for і, р in enumerate(рядки):
        м.text((5, В + ЛАТКА + 3 + і * 17), р, fill="black", font=ш)
    return п


def main():
    тека = Path(sys.argv[1]) / "фото" / "аудит/проби/річ_колір_перезбір_0411"
    кадри = list(csv.DictReader(open(ТУТ / "вибірка.tsv", encoding="utf-8"), delimiter="\t"))
    ід = {р["id"].split("@")[0] for р in кадри}
    каталог = {}
    сирі = subprocess.check_output(["git", "-C", str(КОРІНЬ), "show", ДАНІ + ":каталог_записи_v1.jsonl.gz"])
    for рядок in gzip.decompress(сирі).decode("utf-8").splitlines():
        р = json.loads(рядок)
        if р.get("ід") in ід:
            каталог[р["ід"]] = р
    контекст, плитки, бачені = [], [], set()
    for р in кадри:
        з = каталог.get(р["id"].split("@")[0], {})
        if р["номер"] not in бачені:
            бачені.add(р["номер"])
            пар = {x[0]: x[1] for x in з.get("параметри") or [] if isinstance(x, list) and len(x) > 1}
            контекст.append(dict(номер=р["номер"], id=р["id"], назва=з.get("назва", ""), адреса=з.get("адреса", ""),
                                 колір_крамниці=пар.get("Колір") or "—", колір_джерело=пар.get("колір_джерело") or "—"))
        назва = textwrap.shorten(з.get("назва", "?"), 40, placeholder="…")
        плитки.append(плитка(тека / р["фото"], р["hex"], ["№%s.%s %s %s" % (р["номер"], р["кадр"], р["hex"], р["клас"]),
                                                           "код main: %s" % р["код_main"], назва,
                                                           "C %s U %s ×%s" % (р["C"], р["U"], р["поправка"])]))
    with open(ТУТ / "контекст.tsv", "w", encoding="utf-8", newline="") as ф:
        п = csv.DictWriter(ф, fieldnames=list(контекст[0]), delimiter="\t", lineterminator="\n")
        п.writeheader(); п.writerows(контекст)
    for н in range(0, len(плитки), 8):
        шматок = плитки[н:н + 8]
        рядів = (len(шматок) + СТОВПЦІВ - 1) // СТОВПЦІВ
        а = Image.new("RGB", (СТОВПЦІВ * Ш, рядів * (В + ЛАТКА + ТЕКСТ)), "#dddddd")
        for і, п in enumerate(шматок):
            а.paste(п, ((і % СТОВПЦІВ) * Ш, (і // СТОВПЦІВ) * (В + ЛАТКА + ТЕКСТ)))
        ім = ТУТ / ("аркуш-%02d.jpg" % (н // 8 + 1))
        for якість in (80, 70, 60):
            а.save(ім, quality=якість, optimize=True)
            if ім.stat().st_size < 300_000:
                break
        assert ім.stat().st_size < 300_000, ім
    print("кадрів %d, речей %d, аркушів %d, назв знайдено %d" % (len(кадри), len(контекст), (len(плитки) + 7) // 8,
                                                                 sum(bool(к["назва"]) for к in контекст)))


if __name__ == "__main__":
    main()
