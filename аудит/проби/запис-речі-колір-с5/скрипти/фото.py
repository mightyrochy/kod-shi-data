#!/usr/bin/env python3
"""Галерея кожної речі вибірки (`дані/вибірка.json`): усі кадри варіанта з каталогу (`каталог_записи_v1.jsonl.gz`,
до 8), 640 px — моделі запису; аркуш усіх кадрів речі в одному зображенні (до 1200 px) — оглядачеві очима. Обидва
поза репозиторієм: /tmp/колір-с5/{модель,аркуш}. Запуск з кореня: python3 аудит/проби/запис-речі-колір-с5/скрипти/фото.py"""
import gzip, io, json, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ВИБ = json.load(open("аудит/проби/запис-речі-колір-с5/дані/вибірка.json", encoding="utf-8"))["речі"]
ПОТРІБНІ = {в["ід"].split("@")[0] for в in ВИБ}
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if р.get("ід") in ПОТРІБНІ:
        R[р["ід"]] = р
ТЕКА_М, ТЕКА_А = "/tmp/колір-с5/модель", "/tmp/колір-с5/аркуш"
os.makedirs(ТЕКА_М, exist_ok=True); os.makedirs(ТЕКА_А, exist_ok=True)


def взяти(url):
    з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(з, timeout=25) as в:
        І = Image.open(io.BytesIO(в.read())); І.load()
    return І.convert("RGB")


def одна(в):
    ід = в["ід"].split("@")[0]
    if ід not in R:
        return ід, -1
    готово = []
    for к in [к for к in R[ід]["кадри"] if к.startswith("http")][:8]:
        try:
            І = взяти(к)
        except Exception:
            continue
        if min(І.size) >= 120:
            готово.append(І)
    for н, І in enumerate(готово):
        м = І.copy(); м.thumbnail((640, 640)); м.save(f"{ТЕКА_М}/{ід}-{н + 1}.jpg", quality=82)
    if готово:
        висота = 400
        малі = [І.resize((max(1, round(І.width * висота / І.height)), висота)) for І in готово]
        рядки, рядок, ширина = [], [], 0
        for м in малі:
            if рядок and ширина + м.width > 1200:
                рядки.append(рядок); рядок, ширина = [], 0
            рядок.append(м); ширина += м.width
        рядки.append(рядок)
        аркуш = Image.new("RGB", (max(sum(м.width for м in р) for р in рядки), висота * len(рядки)), "white")
        for і, р in enumerate(рядки):
            x = 0
            for м in р:
                аркуш.paste(м, (x, і * висота)); x += м.width
        аркуш.thumbnail((1200, 1200)); аркуш.save(f"{ТЕКА_А}/{ід}.jpg", quality=82)
    return ід, len(готово)


with ThreadPoolExecutor(10) as п:
    рез = list(п.map(одна, ВИБ))
json.dump(dict(рез), open("/tmp/колір-с5/кадрів.json", "w"), ensure_ascii=False)
print("нема в каталозі:", [і for і, н in рез if н < 0], "без фото:", [і for і, н in рез if н == 0],
      "кадрів:", sum(н for _, н in рез if н > 0), "речей з кадрами:", sum(1 for _, н in рез if н > 0))
