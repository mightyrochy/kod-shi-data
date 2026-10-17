# -*- coding: utf-8 -*-
"""Скретч: аркуш із фото — річ, її колір, центр ролі на світлоті речі, ДО→ПІСЛЯ. Вхід: [(ід, lab, центр_h, підпис, до, пс)]."""
import sys, os, io, pickle, hashlib, urllib.request
SP = "/tmp/claude-0/-home-user-kod-shi-data/776a4a9a-fd05-599a-a082-7a6de8527981/scratchpad/"
sys.path.insert(0, SP); sys.path.insert(0, "/home/user/kod-shi-data/джерела")
import colour_hex, колір_простір_риси as КП, colorspace as cs
from PIL import Image, ImageDraw, ImageFont
КЕШ = SP + "фото/"; os.makedirs(КЕШ, exist_ok=True)
шр = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)

def фото(url):
    if not url: return None
    f = КЕШ + hashlib.md5(url.encode()).hexdigest() + ".jpg"
    if not os.path.exists(f):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=20).read()
            Image.open(io.BytesIO(data)).convert("RGB").save(f)
        except Exception as e:
            return None
    return Image.open(f)

def аркуш(рядки, вих, по=8):
    """рядки: dict(ід, фото, lab, центр_м (тон Манселла центру), підпис, до, пс)."""
    for с in range(0, len(рядки), по):
        шм = рядки[с:с + по]
        im = Image.new("RGB", (4 * 300, 2 * 330), "white"); d = ImageDraw.Draw(im)
        for i, р in enumerate(шм):
            к, в = (i % 4) * 300, (i // 4) * 330
            ф = фото(р["фото"])
            if ф:
                ф.thumbnail((290, 220)); im.paste(ф, (к + 5, в + 5))
            L, C, h = cs.lch(р["lab"])
            d.rectangle([к + 5, в + 230, к + 100, в + 280], fill=colour_hex.з_lab(р["lab"]))
            d.rectangle([к + 100, в + 230, к + 195, в + 280], fill=colour_hex.з_lab(colour_hex.lab(L, C, р["центр_h"])))
            d.text((к + 200, в + 232), "#%d" % (с + i + 1), fill="black", font=шр)
            d.text((к + 200, в + 250), "%s→%s" % (р["до"], р["пс"]), fill="black", font=шр)
            d.text((к + 5, в + 284), р["підпис"][:38], fill="black", font=шр)
            d.text((к + 5, в + 302), "річ | центр ролі", fill="gray", font=шр)
        im.save(вих % (с // по + 1))
