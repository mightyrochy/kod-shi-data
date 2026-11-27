#!/usr/bin/env python3
"""Мірило (а): 60 випадкових речей проходу (зерно 20261127), яких не було серед перших 60 (`запис-речі-колір-с5/дані/вибірка.json`,
`очима`), із відомим кольором у записі й кадрами. Аркуші всіх кадрів — /tmp/прохід-сцен/аркуш (поза репозиторієм); вихід — `дані/вибірка_а.json`
(ключ відповіді — окремо `дані/ключ_а.json`, оглядач його не бачить). Запуск з кореня: python3 -I <цей файл>"""
import glob, gzip, json, random
from PIL import Image
з = json.load(gzip.open("аудит/проби/запис-речі-прохід-сцен/дані/записи_речі.json.gz", "rt", encoding="utf-8"))
перші = {в["ід"].split("@")[0] for в in json.load(open("аудит/проби/запис-речі-колір-с5/дані/вибірка.json", encoding="utf-8"))["речі"] if в.get("очима")}
кандидати = sorted(к for к, в in з.items() if к.split("@")[0] not in перші and isinstance(в["мітки"].get("колір", {}).get("значення"), list)
                   and glob.glob(f"/tmp/прохід-сцен/кадри/{к.split('@')[0]}-1.jpg"))
вибір = sorted(random.Random(20261127).sample(кандидати, 60))
import os; os.makedirs("/tmp/прохід-сцен/аркуш", exist_ok=True)
ключ = {}
for н, к in enumerate(вибір, 1):
    б = к.split("@")[0]
    І = [Image.open(ф) for ф in sorted(glob.glob(f"/tmp/прохід-сцен/кадри/{б}-*.jpg"))]
    І = [i.resize((max(1, round(i.width * 400 / i.height)), 400)) for i in І]
    рядки, р, ш = [], [], 0
    for i in І:
        if р and ш + i.width > 1200: рядки.append(р); р, ш = [], 0
        р.append(i); ш += i.width
    рядки.append(р)
    А = Image.new("RGB", (max(sum(i.width for i in р) for р in рядки), 400 * len(рядки)), "white")
    for ір, р in enumerate(рядки):
        x = 0
        for i in р: А.paste(i, (x, ір * 400)); x += i.width
    А.thumbnail((1200, 1200)); А.save(f"/tmp/прохід-сцен/аркуш/{н:02d}.jpg", quality=82)
    ключ[f"{н:02d}"] = {"ід": к, "тип": з[к]["мітки"].get("тип", {}).get("значення"), "колір": з[к]["мітки"]["колір"]}
json.dump(ключ, open("аудит/проби/запис-речі-прохід-сцен/дані/ключ_а.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
json.dump({"речей": 60, "зерно": 20261127, "кандидатів": len(кандидати)}, open("аудит/проби/запис-речі-прохід-сцен/дані/вибірка_а.json", "w"), ensure_ascii=False)
print(len(кандидати), len(ключ))
