"""Мірило 16345 на записаних прогонах: чи картка руки показує фото речей. Колонка вердикту `фото_речей` — скільки речей
картки мають фото (`показ/журнал.js`: `(к.речі||[]).filter(r=>r.фото).length`). Друкує за рукою: карток без жодного фото
речей і з фото. Руки 3–4 без закріплених речей мусять бути без фото — тоді рядка «опис без фото» там нема за умовою картки.
Її річ із фото (рука 1) у цю колонку не входить: її фото підставляє малювання з `фото_ід`.
Запуск з кореня: python3 аудит/проби/Е2-опора-пояснення-кадри-від-початку/фото_на_картках.py"""
import collections, hashlib, json, os

лік = collections.defaultdict(lambda: [0, 0]); бачено = set()


def записи(o):
    if isinstance(o, dict):
        if "фото_речей" in o and "рука" in o:
            yield o
        for v in o.values():
            yield from записи(v)
    elif isinstance(o, list):
        for v in o:
            yield from записи(v)


for д, _, фф in os.walk("аудит/проби"):
    for ф in фф:
        if not (ф == "вердикти.txt" or ф.endswith(".json")):
            continue
        try:
            дані = json.load(open(os.path.join(д, ф), encoding="utf8"))
        except Exception:
            continue
        for з in записи(дані):
            ключ = hashlib.sha1(json.dumps(з, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
            if ключ in бачено:
                continue
            бачено.add(ключ)
            лік[str(з.get("рука"))][1 if (з.get("фото_речей") or 0) else 0] += 1
for рука in sorted(лік):
    print(f"рука {рука}: карток без жодного фото речей {лік[рука][0]} · з фото {лік[рука][1]}")
