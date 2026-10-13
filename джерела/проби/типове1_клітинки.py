# -*- coding: utf-8 -*-
"""ТИПОВЕ-1: лічба живих прогонів стенда (теки з `відповіді.tar.gz`, `картки.txt`, `текст_екранів.txt`).
Друкує на теку: відкрите взуття (sandals, heeled_sandals, espadrilles) і тренчі/пальта в пулі першого
ПАКЕТ_V1 руки 1; `day_outing`/`evening_outing` і `start_hour` у ньому; `day.place`, `day.unknown`;
лофери/мокасини на картках рук 1–2; «Де» з першої картки сценарію.
Запуск: python3 проби/типове1_клітинки.py <тека> [<тека> …]"""
import sys, os, re, json, tarfile, collections
ВІДКРИТЕ, ШАР = ("sandals", "heeled_sandals", "espadrilles"), ("trench_coat", "coat")
for т in sys.argv[1:]:
    with tarfile.open(os.path.join(т, "відповіді.tar.gz")) as tf:
        пак = sorted((m for m in tf.getmembers() if "ПАКЕТ_V1_ОБРАЗИ" in m.name), key=lambda m: m.name)
        p = None
        for m in пак:
            t = tf.extractfile(m).read().decode("utf-8")
            мм = re.match(r"── ПРОМПТ \((\d+) симв\.\) ──\n(.*)\n\n── ВІДПОВІДЬ", t, re.S)
            p = json.loads(мм.group(2)) if мм else None
            if p and "pool" in p:
                break
    пул = collections.Counter(і.get("type") for і in (p or {}).get("pool") or [])
    пр = json.dumps((p or {}).get("style_rules"), ensure_ascii=False)
    д = (p or {}).get("day") or {}
    карт = open(os.path.join(т, "картки.txt"), encoding="utf-8").read().split("═══ картка ")[1:]
    рук12 = [к for к in карт if re.match(r"\d з \d · рука [12]", к)]
    лоф = sum(1 for к in рук12 if re.search(r"лофер|мокасин", к.split("\nРазом")[0], re.I))   # перелік речей
    екр = open(os.path.join(т, "текст_екранів.txt"), encoding="utf-8").read().splitlines()
    де = next((екр[і + 1] for і, р in enumerate(екр[:-1]) if р.strip() == "Де"), "—")
    print("%-34s відкрите %2d · тренч %d пальто %2d · day_outing %-5s evening_outing %-5s start_hour %s · "
          "place %s unknown %s · лофери %d/%d карток рук 1–2 · Де: %s"
          % (os.path.basename(т.rstrip("/")), sum(пул[x] for x in ВІДКРИТЕ), пул["trench_coat"], пул["coat"],
             "day_outing" in пр, "evening_outing" in пр, д.get("start_hour"), д.get("place"), д.get("unknown"),
             лоф, len(рук12), де))
