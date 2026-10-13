# -*- coding: utf-8 -*-
"""НГ-3 (рядок 243): чисел шкали ошатності 1–10 у пакетах моделі-стилістки — складання, ремонт, вибір —
на 4 сценаріях (смуга — числа заглушки стенда `СТЕНД_ОШАТНІСТЬ_НАГОДИ`). Число шкали — значення поля
ошатності (`formality`/`fo`, `band`, `up_to`, `formality_from_photo`, від/до в них) і число в тексті поруч
зі шкалою («1 to 10», «5–7 office», «9 gala»). Друкує факт. Запуск із `джерела`: [PRYKLAD=1] python3 проби/нг3_числа_в_дроті.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, feed as F
ПОЛЯ = {"formality", "fo", "up_to", "formality_from_photo", "event_level", "fabric_level", "cut_level", "target",
        "register_band", "occasion_band", "spread", "steps", "steps_over"}
ЗАЯВА_ОШ = re.compile(r"formality|occasion|dress_code_band|shoes_in_band|event_level|outfit_level")  # чий `band` — ошатність
ТЕКСТ = re.compile(r"\b(?:1 to 10|1[–-]10)\b|\b\d+[–-]\d+ office\b|\b\d+ (?:home|caf[eé]|gala|ceremony|theatre|evening out)\b")
def числа(в, у_полі=False, заява=""):
    if isinstance(в, dict):
        return sum(числа(v, у_полі or к in ПОЛЯ or (к in ("band", "item") and bool(ЗАЯВА_ОШ.search(заява))),
                         к if ЗАЯВА_ОШ.search(к) else заява) for к, v in в.items())
    if isinstance(в, list):
        return sum(числа(x, у_полі, заява) for x in в)
    if isinstance(в, str):
        return len(ТЕКСТ.findall(в))
    return int(у_полі and isinstance(в, (int, float)) and not isinstance(в, bool))
вх = dict(json.load(open("стенд_вх.json")), каталог=F.каталог_на_диску("каталог_повний.xml"), пакети=1)
СЦЕНИ = {"театр": dict(нагода="театр", місце="театр", година=19, темп_c=12, ошатність=[4, 6]),
         "офіс": dict(нагода="робота", місце="офіс", година=9, темп_c=18, ошатність=[5, 7]),
         "побачення": dict(нагода="побачення", місце="ресторан", година=20, темп_c=15, ошатність=[4, 5]),
         "весілля-гостя": dict(нагода="весілля_гість", година=16, темп_c=22, ошатність=[7, 9], зарезервований_колір="білий")}
for ім, сц in СЦЕНИ.items():
    д = dict(вх, сценарій=сц)
    з = json.loads(B.виклик("запити", json.dumps(д, ensure_ascii=False)))
    пул = (з["пакети"]["1"] or {}).get("пул") or {}
    ряд = [р["н"] for с in ("сукня", "верх", "низ", "взуття", "сумка", "верхній_шар") for р in (пул.get(с) or [])[:2]]
    відп = dict(версія="1", образи=[dict(ід="о1", підпис="a", речі=ряд[0::2]), dict(ід="о2", підпис="b", речі=ряд[1::2])])
    в = json.loads(B.виклик("від_моделі", json.dumps(dict(д, текст_моделі=json.dumps(відп, ensure_ascii=False)), ensure_ascii=False)))
    пп = {"складання": з["руки"]["1"], "ремонт": в.get("промпт_ремонту"), "вибір": в.get("промпт_лише_вибору")}
    н = {к: (числа(json.loads(т)) if т else "нема") for к, т in пп.items()}
    print("%-14s чисел шкали ошатності: %s · пул %s речей, %s симв."
          % (ім, " · ".join("%s %s" % кв for кв in н.items()), з.get("пул_речей"), len(пп["складання"])))
    if os.environ.get("PRYKLAD"):  # приклад рядка пакета: день і перша річ пулу
        с = json.loads(пп["складання"]); print("   day:", json.dumps(с.get("day"), ensure_ascii=False), "\n   річ:", json.dumps(с["pool"][0], ensure_ascii=False)[:400])
