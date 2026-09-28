# -*- coding: utf-8 -*-
"""Контакт-аркуш 40 речей зі станом «свій_кадр» для очного огляду перевірки #409.
Запуск: python3 vidbir_svii_kadru_409.py вибір.json && python3 arkush_svii_kadru_409.py вибір.json <тека_виходу>"""
import json, os, sys, subprocess, hashlib, concurrent.futures as cf, textwrap
from PIL import Image, ImageDraw, ImageFont

д = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "vidbir_409.json", encoding="utf-8"))
SC = sys.argv[2] if len(sys.argv) > 2 else "."
кеш = "/tmp/foto_409"; os.makedirs(кеш, exist_ok=True)

def шлях(u):
    return os.path.join(кеш, hashlib.md5(u.encode()).hexdigest() + ".img")

def тягти(u):
    p = шлях(u)
    if not os.path.exists(p) or os.path.getsize(p) == 0:
        subprocess.run(["curl", "-sS", "-L", "-m", "25", "-o", p, u], capture_output=True)
    return p

with cf.ThreadPoolExecutor(12) as ex:
    list(ex.map(тягти, [x["кадр_url"] for x in д if x.get("кадр_url")]))

шр = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
шрж = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
Ш, ВФ, ВТ = 260, 320, 130
НА_АРКУШ = 8
аркуші = [д[i:i+НА_АРКУШ] for i in range(0, len(д), НА_АРКУШ)]
for н, гр in enumerate(аркуші, 1):
    рядків = (len(гр) + 3) // 4
    арк = Image.new("RGB", (Ш*4, (ВФ+ВТ)*рядків + 30), "white")
    дв = ImageDraw.Draw(арк)
    дв.text((8, 6), "перевірка #409 — свій_кадр, аркуш %d/%d" % (н, len(аркуші)), fill="black", font=шрж)
    for i, x in enumerate(гр):
        X, Y = (i % 4) * Ш, 30 + (i // 4) * (ВФ+ВТ)
        u = x.get("кадр_url")
        try:
            im = Image.open(шлях(u)).convert("RGB")
            im.thumbnail((Ш-10, ВФ-10))
            арк.paste(im, (X+5, Y+5))
        except Exception as e:
            дв.rectangle([X+5, Y+5, X+Ш-10, Y+ВФ-10], outline="red")
            дв.text((X+10, Y+10), "фото не завантажилось: %s" % e, fill="red", font=шр)
        рядки = [
            "%d) %s" % (i+1 + (н-1)*НА_АРКУШ, x["id"]),
            "назва: %s" % (x.get("назва") or "")[:38],
            "колір_назва: %s" % x.get("колір_назва"),
            "мульти: %s" % ("ТАК" if x["мульти"] else "ні"),
        ]
        if x["мульти"]:
            рядки.append("одногрупники: " + ", ".join("%s" % c for _, c in x["одногрупники"][:4]))
        ty = Y + ВФ
        for р in рядки:
            for рядок in textwrap.wrap(р, width=40):
                дв.text((X+5, ty), рядок, fill="black", font=шр)
                ty += 16
    арк.save(SC + "/arkush_409_%02d.png" % н)
print("аркушів:", len(аркуші))
