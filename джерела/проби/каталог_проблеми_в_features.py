# -*- coding: utf-8 -*-
# Реєстр проблем бази одягу, напрям В, клас «рядок features». ФАКТ на трьох прогонах MamayLM
# еталону 60 речей (`аудит/розбір_каталогу/404_а*/розбір.json`): (1) скільки рядків «unknown»;
# (2) слів у рядку і скільки впирається в стелю `каталог_розбір.СТЕЛЯ_СЛІВ` (обрізані на
# півслові — без крапки й коми в кінці при ≥ стеля−4 слів); (3) рядки з порадою носіння чи
# маркетингом замість нюансу речі, з кодом товару чи числами; (4) чи однаковий рядок тієї
# самої речі в трьох прогонах. Слова тут читає ПРОБА, не код продукту (п.12).
import os, re, sys, json, collections as C
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ)
import каталог_розбір as КР
тека = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ТУТ, os.pardir, "аудит", "розбір_каталогу")
прогони = {}
for п in sorted(os.listdir(тека)):
    ф = os.path.join(тека, п, "розбір.json")
    if os.path.exists(ф):
        прогони[п] = {k: (v or {}).get("features") for k, v in json.load(open(ф, encoding="utf-8")).items()
                      if isinstance(v, dict)}
ПОРАДА = re.compile(r"\b(versatile|basic|comfortable|perfect|ideal|can be worn|wear(ing)?|"
                    r"tucked|stylish|elegant look|for (any|every|different)|outfit|look[s]?)\b", re.I)
for п, ф in прогони.items():
    є = [x for x in ф.values() if x and x.strip().lower() != КР.UNKNOWN]
    сл = [len(x.split()) for x in є]
    print("%s: речей %d · unknown %d · слів сер. %.1f, макс %d (стеля %d) · обрізано біля стелі %d · "
          "порада/маркетинг %d · з кодом чи числом %d · кирилиця %d"
          % (п, len(ф), len(ф) - len(є), sum(сл) / max(1, len(сл)), max(сл or [0]), КР.СТЕЛЯ_СЛІВ,
             sum(1 for x in є if len(x.split()) >= КР.СТЕЛЯ_СЛІВ - 4 and not re.search(r"[.,;)]$", x.strip())),
             sum(1 for x in є if ПОРАДА.search(x)), sum(1 for x in є if re.search(r"\d", x)),
             sum(1 for x in є if re.search("[а-яіїє]", x, re.I))))
спільні = set.intersection(*(set(ф) for ф in прогони.values())) if прогони else set()
однакові = sum(1 for k in спільні if len({(ф[k] or "").strip().lower() for ф in прогони.values()}) == 1)
відомі_всі = sum(1 for k in спільні if all(ф[k] and ф[k].strip().lower() != КР.UNKNOWN for ф in прогони.values()))
print("речей у всіх прогонах %d · рядок однаковий у всіх %d · відомий у всіх %d" % (len(спільні), однакові, відомі_всі))
print("приклади поради:", [x for x in прогони[next(iter(прогони))].values() if x and ПОРАДА.search(x)][:3])
