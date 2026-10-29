# -*- coding: utf-8 -*-
"""Аркуш очима наряду 2.14 «коло тону»: пари з `джерела/проби/коло_тону_пари_214.py <пари.json>`.
40 пар, що змінили same_hue (сід 214), і 10 межових незмінних «ні» з найменшою Δ на колі — на аркушах по 10:
свотч виміру кожної речі (великий), фото речі (коли крамниця відповідає за 8 с), підпис: hex, Δ коло, ДО → ПІСЛЯ.
Запуск із кореня: python3 аудит/проби/коло_тону_214/аркуш.py <пари.json> <тека>"""
import ast, io, json, random, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont
пари, тека = json.load(open(sys.argv[1], encoding="utf-8")), sys.argv[2]
змінені = [п for п in пари if п["до"] != п["піс"]]
межові = sorted((п for п in пари if п["до"] == п["піс"] == "ні"), key=lambda п: п["дк"])
вибір = random.Random(214).sample(змінені, min(40, len(змінені))) + межові[:10]
шрифт = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
def фото(поле):
    try:
        url = (ast.literal_eval(поле) if поле and поле.startswith("[") else [поле])[0]
        з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        return Image.open(io.BytesIO(urllib.request.urlopen(з, timeout=8).read())).convert("RGB")
    except Exception:
        return None
опис = []
for л in range(0, len(вибір), 10):
    ар = Image.new("RGB", (1500, 10 * 230), "white"); д = ImageDraw.Draw(ар)
    for i, п in enumerate(вибір[л:л + 10]):
        y, н = i * 230, л + i + 1
        for j, р in enumerate((п["a"], п["b"])):
            x = 10 + j * 560
            д.rectangle((x, y + 10, x + 260, y + 200), fill=р[2])
            ф = фото(р[3])
            if ф: ф.thumbnail((260, 190)); ар.paste(ф, (x + 270, y + 10))
            д.text((x, y + 205), "%s %s" % (р[2], (р[1] or "")[:40]), fill="black", font=шрифт)
        д.text((1130, y + 80), "#%d  Δколо %.1f\n%s → %s" % (н, п["дк"], п["до"], п["піс"]), fill="black", font=шрифт)
        д.line((0, y + 228, 1500, y + 228), fill="#999")
        опис.append(dict(п, н=н))
    ар.save("%s/аркуш_%d.png" % (тека, л // 10 + 1))
json.dump(опис, open("%s/аркуш.json" % тека, "w", encoding="utf-8"), ensure_ascii=False, indent=0)
print("пар на аркушах:", len(опис), "· змінених усього:", len(змінені), "· межових ні:", len(межові))
