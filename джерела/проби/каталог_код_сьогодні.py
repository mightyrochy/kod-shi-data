# -*- coding: utf-8 -*-
"""Проба: ЩО ЗАРАЗ ВИРІШУЮТЬ СЛОВНИКИ КОДУ на всьому каталозі — покриття кожного поля розбору
(це «ДО» для заміру мовної моделі; модель не кличеться). Друкує також типи, яких внутрішня мова
не має, і збої коду. Запуск: python3 джерела/проби/каталог_код_сьогодні.py [скільки речей]"""
import collections, os, sys                                                   # noqa: E401
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import каталог_розбір as КР, фід_каталог as ФК, фід_розбір as ФР               # noqa: E401,E402
скільки = int(sys.argv[1]) if len(sys.argv) > 1 else 0
офери = ФР.читати_yml(ФК.каталог_на_диску(), показ=False)[0]
офери = офери[:скільки] if скільки else офери
є, поза, збої = collections.Counter(), collections.Counter(), collections.Counter()
for o in офери:
    поля, з = КР.що_каже_код(o)
    for ш, в in поля.items():
        if в:
            є[ш] += 1
    for ш, текст in з.items():
        (поза if текст.startswith("поза") else збої)[
            текст.split(": ", 1)[1] if текст.startswith("поза") else "%s · %s" % (ш, текст)] += 1
n = len(офери) or 1
print("речей %d · словники коду вирішують:" % n)
for ш, _, _ in КР.ПОЛЯ:
    к = ш.split("[")[0]
    print("  %-18s %5d  %3d %%  ← %s" % (ш, є[к], round(100 * є[к] / n),
                                         КР.ЗВІДКИ.get(к.split(".")[0], "")))
print("типи коду поза переліком внутрішньої мови: %d речей · %s"
      % (sum(поза.values()), ", ".join("%s×%d" % (т, ч) for т, ч in поза.most_common(8)) or "нема"))
print("збої коду: %s" % (", ".join("%s×%d" % (т, ч) for т, ч in збої.most_common(6)) or "нема"))
