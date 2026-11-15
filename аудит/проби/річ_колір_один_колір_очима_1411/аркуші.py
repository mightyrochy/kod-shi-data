"""Аркуші огляду: кадр, латка його hex і слово — для частини 1 (код кроку) і частини 2 (слово крамниці).

З кореня репозиторію (фото — гілка даних, лише потрібні файли):
    git fetch --depth 1 origin claude/Річ-колір-вимір
    git archive c7b37862c5195f823e0ef211cd8ecd718b498f95 <шляхи фото з вибірка.tsv першого огляду> | tar -x -C <тека>
    python3 -I аудит/проби/річ_колір_один_колір_очима_1411/аркуші.py <тека>
Вердиктів не обчислює: вони — ручний вхід `огляд_крок.tsv` і `чотирнадцять.tsv`.
"""
import csv, subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[2]
КРОК = "96673cd6cb5afd744eb141e2c192c2ecd2fad1a1"
ШРИФТ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
Ш, В, ЛАТКА, ТЕКСТ, СТОВПЦІВ = 300, 380, 46, 64, 4


def tsv(текст):
    return list(csv.DictReader(текст.splitlines(), delimiter="\t"))


def плитка(фото, hex_, рядки):
    п = Image.new("RGB", (Ш, В + ЛАТКА + ТЕКСТ), "white")
    з = Image.open(фото).convert("RGB"); з.thumbnail((Ш, В))
    п.paste(з, ((Ш - з.width) // 2, (В - з.height) // 2))
    м = ImageDraw.Draw(п)
    м.rectangle([0, В, Ш, В + ЛАТКА], fill=hex_)
    ш = ImageFont.truetype(ШРИФТ, 15)
    for і, р in enumerate(рядки):
        м.text((6, В + ЛАТКА + 4 + і * 19), р, fill="black", font=ш)
    return п


def аркуші(плитки, префікс):
    імена = []
    for н in range(0, len(плитки), 8):
        шматок = плитки[н:н + 8]
        рядів = (len(шматок) + СТОВПЦІВ - 1) // СТОВПЦІВ
        а = Image.new("RGB", (СТОВПЦІВ * Ш, рядів * (В + ЛАТКА + ТЕКСТ)), "#dddddd")
        for і, п in enumerate(шматок):
            а.paste(п, ((і % СТОВПЦІВ) * Ш, (і // СТОВПЦІВ) * (В + ЛАТКА + ТЕКСТ)))
        ім = "%s-%02d.jpg" % (префікс, н // 8 + 1)
        а.save(ТУТ / ім, quality=80, optimize=True)
        assert (ТУТ / ім).stat().st_size < 300_000, ім
        імена.append(ім)
    return імена


def main():
    тека = Path(sys.argv[1])
    кадри = tsv(subprocess.check_output(["git", "-C", str(КОРІНЬ), "show",
                                         "HEAD:аудит/проби/річ_колір_розкид_очима_1411/вибірка.tsv"], text=True))
    фото = {(р["номер"], р["кадр"]): тека / "аудит/проби/річ_колір_перезбір_0411" / р["фото"] for р in кадри}
    крок = tsv(subprocess.check_output(["git", "-C", str(КОРІНЬ), "show",
                                        КРОК + ":аудит/проби/річ_колір_один_колір_1411/вибірка_40.tsv"], text=True))
    п1 = [плитка(фото[(р["номер"], р["кадр"])], р["hex"], ["№%s.%s  %s" % (р["номер"], р["кадр"], р["hex"]),
                                                          "код крок: %s" % р["код_крок"]])
          for р in крок if р["код_крок"] != "невідомо"]
    чотирнадцять = {р["номер"]: р for р in csv.DictReader(open(ТУТ / "чотирнадцять.tsv", encoding="utf-8"), delimiter="\t")}
    п2 = [плитка(фото[(р["номер"], р["кадр"])], р["hex"], ["№%s.%s  %s  код: невідомо" % (р["номер"], р["кадр"], р["hex"]),
                                                          "крамниця: %s" % (чотирнадцять[р["номер"]]["слово_крамниці"] or "—")])
          for р in крок if р["номер"] in чотирнадцять]
    print("частина 1:", len(п1), "кадрів →", аркуші(п1, "аркуш-крок"))
    print("частина 2:", len(п2), "кадрів →", аркуші(п2, "аркуш-14"))


if __name__ == "__main__":
    main()
