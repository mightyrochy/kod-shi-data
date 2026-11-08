# -*- coding: utf-8 -*-
"""Аркуш для двох оглядачів ПІСЛЯ: кадр · латка ПІСЛЯ · код (як `річ_колір_приймання_0811/аркуш.py`).

Кадр — з рамками ділянки, яку назвала модель і в якій міряв код (блакитні); під кадром — латка точки коду
(hex), її код і слово, стан («певний» / «не певний» з межами виміру) і родина від моделі. ДО-огляду, вердиктів
приймання й причин тут нема. `аркуш_1.jpg` — речі 1–20, `аркуш_2.jpg` — 21–40; `аркуш.tsv` — ті самі
дані текстом з порожніми колонками вердиктів.

Запуск із кореня (після `git fetch origin claude/Річ-колір-вимір`):
`python3 -I аудит/проби/річ_колір_модель_бачить/аркуш.py`.
"""
import csv
import io
import json
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ТУТ = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ = os.path.abspath(os.path.join(ТУТ, "..", "..", ".."))
sys.path.insert(0, os.path.join(КОРІНЬ, "джерела"))
import словник_кольору as СК  # noqa: E402

ДАНІ = "43dd34adee5bf462c70cbdc9f01719da7250719e"
ТЕКА_ДАНИХ = "аудит/проби/річ_колір_перезбір_0411/"
ШРИФТ = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
КОЛОНОК, РЯДІВ, Ш, В, ФОТО = 5, 4, 380, 630, 470


def кадр(шлях):
    байти = subprocess.run(["git", "-C", КОРІНЬ, "show", ДАНІ + ":" + ТЕКА_ДАНИХ + шлях],
                           check=True, capture_output=True).stdout
    return Image.open(io.BytesIO(байти)).convert("RGB")


def межі_текстом(м):
    L0, L1, C0, C1, дуга = json.loads(м)
    return "L* %.0f–%.0f · C* %.0f–%.0f · %s" % (L0, L1, C0, C1, "тон %d–%d°" % tuple(дуга) if дуга else "тон будь-який")


def клітинка(олівець, аркуш, x, y, м, в, ф, фж):
    фото = кадр(м["кадр"])
    W, H = фото.size
    мал = ImageDraw.Draw(фото)
    товщина = max(3, round(max(W, H) / 250))
    for x0, y0, x1, y1 in json.loads(м["ділянка"]):
        мал.rectangle((x0, y0, x1, y1), outline="#00b7ff", width=товщина)
    фото = ImageOps.contain(фото, (Ш - 10, ФОТО))
    аркуш.paste(фото, (x + (Ш - фото.width) // 2, y + 4))
    олівець.rectangle((x + 1, y + 1, x + Ш - 2, y + В - 2), outline="#bbbbbb", width=1)
    номер, крамниця = м["річ"].split("@", 1)
    т = y + ФОТО + 8
    олівець.text((x + 8, т), "%s. %s · %s" % (м["номер"], номер, крамниця[:26]), fill="black", font=фж)
    олівець.rectangle((x + 8, т + 22, x + 58, т + 72), fill=в["hex"], outline="black")
    олівець.text((x + 66, т + 22), "%s (%s)" % (в["код_точки"], СК.СЛОВО[в["код_точки"]]), fill="black", font=фж)
    олівець.text((x + 66, т + 42), "%s · %s" % (в["hex"], в["родина_точки"]), fill="black", font=ф)
    не_певний = в["стан"] != "певний"
    олівець.text((x + 66, т + 58), в["стан"], fill="#c05000" if не_певний else "#006000", font=фж)
    олівець.text((x + 8, т + 80), "модель: %s · %s" % (м["код"], м["родина"]), fill="black", font=ф)
    олівець.text((x + 8, т + 97), "принт %s · тло %s" % (м["принт"], м["тло"]), fill="black", font=ф)
    if не_певний:
        олівець.text((x + 8, т + 114), межі_текстом(в["межі"]), fill="#c05000", font=ф)


def головна():
    with open(os.path.join(ТУТ, "модель.tsv"), encoding="utf-8") as ф:
        модель = list(csv.DictReader(ф, delimiter="\t"))
    with open(os.path.join(ТУТ, "вимір.tsv"), encoding="utf-8") as ф:
        вимір = {р["номер"]: р for р in csv.DictReader(ф, delimiter="\t")}
    ф, фж = ImageFont.truetype(ШРИФТ, 13), ImageFont.truetype(ШРИФТ.replace("Sans.", "Sans-Bold."), 15)
    на_аркуш = КОЛОНОК * РЯДІВ
    for а in range(0, len(модель), на_аркуш):
        аркуш = Image.new("RGB", (КОЛОНОК * Ш, РЯДІВ * В), "white")
        олівець = ImageDraw.Draw(аркуш)
        for і, м in enumerate(модель[а:а + на_аркуш]):
            клітинка(олівець, аркуш, (і % КОЛОНОК) * Ш, (і // КОЛОНОК) * В, м, вимір[м["номер"]], ф, фж)
        аркуш.save(os.path.join(ТУТ, "аркуш_%d.jpg" % (а // на_аркуш + 1)), quality=85)
    поля = ("номер", "річ", "кадр", "ділянка_моделі", "hex_ПІСЛЯ", "код_ПІСЛЯ", "стан", "межі_виміру",
            "родина_моделі", "принт_моделі", "тло_моделі", "вердикт_оглядача", "причина_оглядача")
    with open(os.path.join(ТУТ, "аркуш.tsv"), "w", encoding="utf-8", newline="") as вих:
        п = csv.writer(вих, delimiter="\t", lineterminator="\n")
        п.writerow(поля)
        for м in модель:
            в = вимір[м["номер"]]
            п.writerow((м["номер"], м["річ"], м["кадр"], м["ділянка"], в["hex"],
                        "%s (%s)" % (в["код_точки"], СК.СЛОВО[в["код_точки"]]), в["стан"],
                        межі_текстом(в["межі"]) if в["стан"] != "певний" else "",
                        "%s · %s" % (м["код"], м["родина"]), м["принт"], м["тло"], "", ""))


if __name__ == "__main__":
    головна()
