# -*- coding: utf-8 -*-
"""4381: фрази в `бракує` пунктів чеклістів на сценаріях стенда — рядок із ≥2 кириличними словами (≥3 літер)
поза іменами полів (`fields`, `source_fields`, `input`) і id. Лічить входження, як мірило рядка дошки."""
import os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import стенд_знімок as С
СЛОВО = re.compile(r"[а-яіїєґ]{3,}", re.I)
ЛИШЕ_ПОЛЯ = ("fields", "source_fields", "input", "items", "sources")


def фрази(x, в_бракує=False, k=None):
    if k in ЛИШЕ_ПОЛЯ:
        return []
    if isinstance(x, dict):
        return [f for кл, v in x.items() for f in фрази(v, в_бракує or кл == "бракує", кл)]
    if isinstance(x, (list, tuple)):
        return [f for v in x for f in фрази(v, в_бракує, k)]
    return [x] if в_бракує and isinstance(x, str) and len(set(СЛОВО.findall(x))) >= 2 else []


всього, ф, бракує_записів = 0, [], 0
for н, с in С.СЦЕНАРІЇ.items():
    р = С.образ_і_суд(н, с)
    if р.get("чеклісти"):
        ф += фрази(р["чеклісти"])
print("сценаріїв=%d · фраз_у_бракує=%d · форм=%d" % (len(С.СЦЕНАРІЇ), len(ф), len(set(ф))))
for х in sorted(set(ф))[:8]: print("  ", х[:150])
