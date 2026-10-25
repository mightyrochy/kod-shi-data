# -*- coding: utf-8 -*-
"""каталог_сусіди_колір_звірка.py — МІРИЛО 3 НАРЯДУ 5.4-С: колір нового шляху ↔ `color_main` повного розбору.

Без моделі. Читає кеш кольорових викликів `<тека>/колір/*.txt` (його пише `каталог_розбір_прогін.py --колір-проба
ТЕКА --модель … --сусіди РЕЖИМ`) і порівнює `color_main.value` короткого виклику з `color_main.value` повного
розбору тієї самої речі у файлі кодів частини 1 (`каталог_розбір_коди.json.gz`). Друкує таблицю: збіглося /
розійшлося / не було в кеші, і `--очима N` випадкових розбіжностей (колір картки, цитата й код обох шляхів).
Запуск: python3 джерела/проби/каталог_сусіди_колір_звірка.py ТЕКА --режим значення [--очима 20] [--сід 1]"""
import argparse
import gzip
import json
import os
import random
import sys
import warnings

warnings.filterwarnings("ignore")
ТУТ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ТУТ, ".."))
import фід_каталог as ФК                      # noqa: E402
import фід_розбір as ФР                       # noqa: E402
import каталог_розбір as КР                   # noqa: E402
import каталог_розбір_сусіди as С             # noqa: E402
import протокол as ПР                         # noqa: E402


def відповідь_кешу(тека, o, режим):
    шлях = os.path.join(тека, "колір", С.колір_ключ(o, режим) + ".txt")
    if not os.path.exists(шлях):
        return None
    текст = open(шлях, encoding="utf-8").read().partition("\n\n── ВІДПОВІДЬ\n")[2]
    об = ПР.розібрати_json(текст.replace(КР.ВСТАВКА, ""))
    return об if isinstance(об, dict) else None


if __name__ == "__main__":
    р = argparse.ArgumentParser()
    р.add_argument("тека")
    р.add_argument("--режим", choices=С.РЕЖИМИ, required=True)
    р.add_argument("--коди", default=os.path.join(ТУТ, "..", "каталог_розбір_коди.json.gz"))
    р.add_argument("--очима", type=int, default=20)
    р.add_argument("--сід", type=int, default=1)
    а = р.parse_args()
    коди = json.load(gzip.open(а.коди))
    офери, _ = ФР.читати_yml(ФК.каталог_на_диску(), показ=False)
    збіг, розбіг, нема = [], [], 0
    for o in офери:
        if o["id"] not in коди or not С.розбити(o)[1]:
            continue
        к = відповідь_кешу(а.тека, o, а.режим)
        if к is None:
            нема += 1
            continue
        нове = (к.get("color_main") or {}).get("value")
        старе = коди[o["id"]].get("color_main")
        (збіг if нове == старе else розбіг).append((o, нове, старе, к))
    разом = len(збіг) + len(розбіг)
    print("режим %s · речей з повним розбором і кольором %d, у кеші %d, без кешу %d" % (а.режим, разом + нема, разом, нема))
    if разом:
        print("color_main збігся %d (%.1f%%) · розійшовся %d (%.1f%%)"
              % (len(збіг), 100 * len(збіг) / разом, len(розбіг), 100 * len(розбіг) / разом))
        unk = sum(1 for _, н, с, _ in розбіг if "unknown" in (н, с))
        print("з розбіжностей: одна зі сторін unknown — %d, код↔код — %d" % (unk, len(розбіг) - unk))
    for o, нове, старе, к in random.Random(а.сід).sample(розбіг, min(а.очима, len(розбіг))):
        print("\n%s · колір картки %s\n   повний: %s · новий: %s · цитата нового: %r · extra нового: %s"
              % (o["id"], С.розбити(o)[1], старе, нове, (к.get("color_main") or {}).get("quote"),
                 [e.get("value") for e in к.get("color_extra") or []]))
