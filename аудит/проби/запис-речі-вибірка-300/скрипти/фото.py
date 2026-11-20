#!/usr/bin/env python3
"""Фото 300 речей: до двох кадрів з каталогу (для моделей — 640 px, поза репозиторієм у /tmp/запис300/модель), один кадр 480 px для сторінки огляду
(`ohliad-zapysu/foto/<ід>.jpg`). Запуск з кореня репозиторію."""
import gzip, json, io, os, urllib.request
from concurrent.futures import ThreadPoolExecutor
from PIL import Image
ВИБ = json.load(open("аудит/проби/запис-речі-вибірка-300/дані/вибірка.json", encoding="utf-8"))
R = {}
for л in gzip.open("каталог_записи_v1.jsonl.gz", "rt", encoding="utf-8"):
    р = json.loads(л)
    if "ід" in р: R[р["ід"]] = р
ТЕКА_М = "/tmp/запис300/модель"; ТЕКА_С = "ohliad-zapysu/foto"
os.makedirs(ТЕКА_М, exist_ok=True); os.makedirs(ТЕКА_С, exist_ok=True)
def взяти(url):
    з = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(з, timeout=25) as в: б = в.read()
    І = Image.open(io.BytesIO(б)); І.load(); return І.convert("RGB")
def зменшити(І, п):
    І = І.copy(); І.thumbnail((п, п)); return І
def одна(в):
    ід = в["ід"]; кадри = [к for к in R[ід]["кадри"] if к.startswith("http")]; готово = []
    for к in кадри[:5]:
        if len(готово) == 2: break
        try:
            І = взяти(к)
            if І.width < 120 or І.height < 120: continue
            готово.append(І)
        except Exception: continue
    for н, І in enumerate(готово):
        зменшити(І, 640).save("%s/%s-%d.jpg" % (ТЕКА_М, ід, н + 1), quality=78)
    if готово: зменшити(готово[0], 480).save("%s/%s.jpg" % (ТЕКА_С, ід), quality=68)
    return ід, len(готово)
with ThreadPoolExecutor(10) as п: рез = list(п.map(одна, ВИБ))
print("без фото:", [і for і, н in рез if not н]); print("з одним:", sum(1 for _, н in рез if н == 1), "з двома:", sum(1 for _, н in рез if н == 2))
