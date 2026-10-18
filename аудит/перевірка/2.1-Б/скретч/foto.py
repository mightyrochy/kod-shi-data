# -*- coding: utf-8 -*-
"""Скретч: аркуш із фото — річ | край дуги | центр дуги (на L*, C* речі), підпис, ДО→ПІСЛЯ. 8 клітинок на аркуш."""
import sys, os, io, hashlib, urllib.request
SP = os.path.dirname(os.path.abspath(__file__)) + "/"; sys.path.insert(0, SP)
import colour_hex
from PIL import Image, ImageDraw, ImageFont
КЕШ = SP + "фото/"; os.makedirs(КЕШ, exist_ok=True)
шр = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
def фото(url):
    if not url: return None
    f = КЕШ + hashlib.md5(url.encode()).hexdigest() + ".jpg"
    if not os.path.exists(f):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20).read()
            Image.open(io.BytesIO(data)).convert("RGB").save(f)
        except Exception:
            return None
    return Image.open(f)
def аркуш(рядки, вих, по=8):
    for с in range(0, len(рядки), по):
        im = Image.new("RGB", (4 * 300, 2 * 340), "white"); d = ImageDraw.Draw(im)
        for i, р in enumerate(рядки[с:с + по]):
            к, в = (i % 4) * 300, (i // 4) * 340
            ф = фото(р["фото"])
            if ф: ф.thumbnail((290, 215)); im.paste(ф, (к + 5, в + 5))
            for j, h in enumerate((None, р["край_h"], р["центр_h"])):
                if h is None and j: continue
                d.rectangle([к + 5 + 64 * j, в + 225, к + 69 + 64 * j, в + 280],
                            fill=colour_hex.з_lab(р["lab"] if j == 0 else р["очі_lab"] if р.get("очі_lab") else colour_hex.lab(р["L"], р["C"], h)))
            d.text((к + 200, в + 228), "#%d" % (с + i + 1), fill="black", font=шр)
            d.text((к + 200, в + 248), "%s→%s" % (р["до"], р["пс"]), fill="black", font=шр)
            d.text((к + 5, в + 284), р["підпис"][:40], fill="black", font=шр)
            d.text((к + 5, в + 302), "річ | край | центр", fill="gray", font=шр)
        im.save(вих % (с // по + 1))
