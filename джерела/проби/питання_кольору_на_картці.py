# -*- coding: utf-8 -*-
"""Рядок 2894: питання кольору про речі ЦЬОГО образу (K-COL-06 «два різні білі», «дві нейтралі», K-COL-01
структура світлоти) — на картці за кнопкою (`на_розгортання`: шар пише лише тоді, коли жінка
розгорне), а «площі не виміряно» — межа системи, у `для_всіх` один раз. 6 сценаріїв стенда × 10 випадкових
образів (сід 11): частка образів із кожним кодом на картці / лише у звіті; час `від_моделі` (заглушка).
Запуск із `джерела`: python3 проби/питання_кольору_на_картці.py   (~2 хв)"""
import sys, os, json, random, time, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import feed; feed.каталог_на_диску("каталог_повний.xml")
import bridge as B, стенд_знімок as СЗ
КОДИ = ("cannot_tell_two_different_whites", "cannot_tell_lightness_structure", "cannot_tell_two_neutrals_distinct",
        "which_white_suits_unknown", "which_white_answer_no_side", "areas_not_measured")
вх0, R, ч = json.load(open("стенд_вх.json")), random.Random(11), collections.Counter()
образів, сек = 0, 0.0
for назва, сц in СЗ.СЦЕНАРІЇ.items():
    вх = dict(вх0, сценарій=сц, випадок=назва)
    к = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False))).get("кандидати") or {}
    for _ in range(10):
        ід = [R.choice(к[с])["id"] for с in ("верх", "низ", "верхній_шар", "взуття", "сумка", "шарф") if к.get(с)]
        т0 = time.time()
        п = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False))).get("питання") or []
        сек += time.time() - т0; образів += 1
        for код in КОДИ:
            з = [q for q in п if код in json.dumps(q.get("повідомлення"))]
            ч[код, "картка"] += any(not q.get("для_всіх") for q in з)
            ч[код, "лише_звіт"] += any(q.get("для_всіх") for q in з)
            ч[код, "розгорнути"] += any(q.get("на_розгортання") for q in з)
            ч[код, "у_для_всіх_разів"] += sum(1 for q in з if q.get("для_всіх"))
        ч["шар_одразу"] += sum(1 for q in п if q.get("повідомлення") and not q.get("для_всіх") and not q.get("на_розгортання"))
for код in КОДИ:
    print("%-36s картка %2d/%d · лише звіт %2d · за кнопкою (на_розгортання) %2d · разів у для_всіх %d" % (
        код, ч[код, "картка"], образів, ч[код, "лише_звіт"], ч[код, "розгорнути"], ч[код, "у_для_всіх_разів"]))
print("питань, які шар пише під час збирання: %.1f на образ · від_моделі (заглушка) %.2f с на образ" % (ч["шар_одразу"] / образів, сек / образів))
