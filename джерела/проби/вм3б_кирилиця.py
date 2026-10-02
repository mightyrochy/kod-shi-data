# -*- coding: utf-8 -*-
"""ВМ-3б (рядки 540–542): кирилиця в промптах оцінки, опису й повтору мови з теки стенда
(`VIDPOVIDI=<тека>`), розкладена за шляхами JSON. Назви речей, крамниць і її слова — окремо:
це дані (п.12), а не фрази коду. Запуск: python3 джерела/проби/вм3б_кирилиця.py <тека>"""
import json, os, re, sys
from collections import Counter
КИР = re.compile(r"[а-яіїєґА-ЯІЇЄҐ]")
# назва речі (і крамниці), колір словом крамниці, її питання, її подія й речення про день, збіги з тексту
# моделі й сам текст моделі, що повертається на перепис (рядок після «Текст:»)
ДАНІ = re.compile(r"(^|\.)(name|question|shop|color|item|items|збіги|matches|event|text|how_to_wear|wrong_photos|your_day_sentence)(\.free_text)?$")
ВИДИ = ("ОЦІНКА_відповідь", "ОПИС_V1", "повтор_мови")


def обхід(в, шлях, лік):
    if isinstance(в, dict):
        for к, v in в.items():
            лік[шлях + "{}"] += len(КИР.findall(к))
            обхід(v, (шлях + "." if шлях else "") + к, лік)
    elif isinstance(в, list):
        for v in в:
            обхід(v, шлях + "[]", лік)
    elif isinstance(в, str):
        лік[re.sub(r"\[\]", "", шлях)] += len(КИР.findall(в))


тека = sys.argv[1]
for вид in ВИДИ:
    дані, код = Counter(), Counter()
    for ф in sorted(os.listdir(тека)):
        if вид not in ф:
            continue
        т = open(os.path.join(тека, ф), encoding="utf-8").read().split("── ВІДПОВІДЬ")[0]
        лік = Counter()
        for р in т.splitlines():
            if р.startswith("{"):
                обхід(json.loads(р), "", лік)
        for ш, n in лік.items():
            (дані if ДАНІ.search(ш) else код)[ш] += n
    print("%s: код %d · дані (назви, крамниці, її слова) %d" % (вид, sum(код.values()), sum(дані.values())))
    for ш, n in код.most_common(8):
        if n:
            print("   %5d  %s" % (n, ш))
