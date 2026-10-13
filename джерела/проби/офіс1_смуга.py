# -*- coding: utf-8 -*-
"""ОФІС-1 (рядки 474/1211/1436): перший хід розмови на офісних фразах і на плитці «Робота» без слів — `update.formality`
і `update.place` з живої моделі, N разів на фразу (типово 4). Друкує смуги й місця, як їх дала модель, і скільки разів
смуга вийшла 5–7. ДО/ПІСЛЯ — та сама проба на двох деревах. Запуск: cd джерела && ZHYVA=sonnet [N=4] python3 проби/офіс1_смуга.py"""
import json, os, re, sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import мова_спільне as С
if not С.МОДЕЛЬ:
    sys.exit("без моделі вимірювати нічого: ZHYVA=sonnet")
М, ПН, N = С.М, С.ПН, int(os.environ.get("N") or 4)
ПЛИТКА = {"нагода": "робота", "місце": ПН.МІСЦЕ_ПЛИТКИ_НАГОДИ["робота"], "типові_поля": ["місце"]}
ФРАЗИ = [("робочий день в офісі", {}), ("на вулиці мінус десять і сніг, йду на роботу пішки 20 хвилин", {}),
         ("йду в офіс, у нас корпоративний суворий дрес-код", {}), ("робочий день у креативній агенції", {}),
         ("", ПЛИТКА)]
def хід(фраза, сц):
    т = С.модель(М.промпт_розмови({"розмова": {"нове": фраза, "історія": []}, "сценарій": сц, "паспорт": {}}))[0] or ""
    м = re.search(r"\{.*\}", т, re.S)
    try:
        у = json.loads(м.group(0)).get("update") or {} if м else {}
    except ValueError:
        return "збій", "—"
    ф, п = у.get("formality") or {}, у.get("place") or {}
    смуга = "%s–%s" % (ф.get("from"), ф.get("to")) if isinstance(ф, dict) and ф.get("from") is not None else "—"
    return смуга, (п.get("value") if isinstance(п, dict) else п) or "—"
завдання = [(ф, сц) for ф, сц in ФРАЗИ for _ in range(N)]
with ThreadPoolExecutor(int(os.environ.get("PAR") or 8)) as пул:
    відп = list(пул.map(lambda а: хід(*а), завдання))
всі = Counter()
for і, (ф, сц) in enumerate(ФРАЗИ):
    р = відп[і * N:(і + 1) * N]
    смуги = Counter(с for с, _ in р); всі.update(смуги)
    print("%-62s смуги %s · місце %s" % ((ф or "плитка «Робота» без слів, місце %s" % сц["місце"])[:62],
          dict(смуги), dict(Counter(п for _, п in р))))
print("модель %s · N=%d · викликів %d · смуг 5–7 %d · 6–8 %d · 4–6 %d" % (С.МОДЕЛЬ, N, len(відп), всі["5–7"], всі["6–8"], всі["4–6"]))
