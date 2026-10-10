# -*- coding: utf-8 -*-
"""Рядок 4282: що бачить опис (ОПИС_V1) ДО/ПІСЛЯ на записаних входах ЖИВІ-19 №11, №13 і ЖИВІ-18 №12.
ДО — записаний промпт; ПІСЛЯ — той самий образ, зібраний назад в обʼєкт коду й пропущений через
`pipeline.промпт_опису`. Друкує речі (n·kind), кольори кожної речі, вільний текст моделі поза складом
(idea, your_day_sentence) і річ способів носіння. Запуск із теки `джерела` (потрібні гілки
`origin/claude/zhyvi-19`, `zhyvi-18`): `python3 проби/опис_склад_4282.py`."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import pipeline as PL, внутрішня_мова as ВМ
Т = ВМ.ТАБЛИЦЯ
ЗАПИСИ = [("Ж19 №11 р1", "zhyvi-19", "живі_19/А/11_ж2_новорічна_мороз", 24), ("Ж19 №11 р2", "zhyvi-19", "живі_19/А/11_ж2_новорічна_мороз", 23),
          ("Ж19 №13 р1", "zhyvi-19", "живі_19/А/13_ж2_спорт_коментар", 21), ("Ж19 №13 р2", "zhyvi-19", "живі_19/А/13_ж2_спорт_коментар", 22),
          ("Ж18 №12 р1", "zhyvi-18", "живі_18/А/12_ж2_корпоратив_виділитися", 24), ("Ж18 №12 р2", "zhyvi-18", "живі_18/А/12_ж2_корпоратив_виділитися", 25)]
def записаний(гілка, тека, с):
    т = subprocess.run(["git", "show", "origin/claude/%s:../аудит/%s/VIDPOVIDI/seed3_%d_ОПИС_V1_ОПИС_ВІДПОВІДЬ_V1.txt" % (гілка, тека, с)],
                       capture_output=True, text=True, check=True).stdout.split("── ВІДПОВІДЬ")[0]
    return json.JSONDecoder().raw_decode(т[т.index('{"version"'):])[0]
def назад(д):   # записаний дріт → обʼєкт коду (лише поля, яких стосується рядок 4282)
    рч = д["outfit"]["items"]
    речі = [dict(н=x["n"], назва=x["name"], слот=Т["slot"].get(x.get("kind")), тип=Т["item_type"].get(x.get("type")),
                 магазин=x.get("shop"), колір=x.get("shop_color") or Т["color_name"].get(x.get("color")), hex=x.get("hex"),
                 кадр_колір=Т["color_name"].get(x.get("photo_colour")), фото_номери=x.get("photos")) for x in рч]
    повна = lambda w: next((x["name"] for x in рч if x["name"].startswith(w)), w)   # дріт обрізав назву до 60
    к3 = {"опції": [dict(річ=повна(w.get("item") or ""), клас="шарф", допустимі_місця=["neck"]) for w in д.get("ways_to_wear") or []]}
    return PL.опис_обʼєкт(речі, образ=д["outfit"]["id"], задум=д.get("idea"), свідомі=д.get("your_declared"),
                          день_образу=д.get("your_day_sentence"), канал_3=к3)
def кадр(д):
    рч = д["outfit"]["items"]
    кольори = {x["n"]: [x[к] for к in ("color", "photo_colour") if x.get(к)] for x in рч}
    return ("речі " + " ".join("%s·%s" % (x["n"], x.get("kind")) for x in рч),
            "кольорів на річ ≤ %d; %s" % (max(map(len, кольори.values())), "; ".join("%s %s" % (н, "/".join(к)) for н, к in кольори.items() if len(к) > 1) or "розладу нема"),
            "текст моделі поза складом: idea=%r day=%r" % ((д.get("idea") or "—")[:44], (д.get("your_day_sentence") or "—")[:60]),
            "способи носіння: %s" % ([w.get("item", "образ") for w in д.get("ways_to_wear") or []] or "—"))
for ім, гілка, тека, с in ЗАПИСИ:
    до = записаний(гілка, тека, с); після = PL.промпт_опису(назад(до))
    print("── %s (seed3_%d)" % (ім, с))
    for а, б in zip(кадр(до), кадр(після)):
        print("   ДО    %s\n   ПІСЛЯ %s" % (а, б) if а != б else "   ═     %s" % а)
