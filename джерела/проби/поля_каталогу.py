# -*- coding: utf-8 -*-
# Рядки 183, 184, 187 (Л-17). ФАКТ трьома числами: (187) назв показу, що кінчаються ЯРЛИКОМ
# ПОЛЯ «артикул» без числа; (183) `param категорія_магазину` з кодом моделі крамниці, яку
# такою судить #426, — у СИРОМУ архіві й у ЧИСТОМУ каталозі (крамницю видно лише до чистки);
# (184) ЦІЛИХ наборів (верх+низ) у слоті-аксесуарі. Числа «до» — у тілі PR.
import os, sys, gzip, shutil, collections, re
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed, назва_речі as НР, чистка_каталогу as ЧК, фід_слот as ФС
чистий = sys.argv[1] if len(sys.argv) > 1 else feed.каталог_на_диску()
архів = sys.argv[2] if len(sys.argv) > 2 else os.path.join(
    os.path.dirname(чистий), os.pardir, "каталог_повний.xml.gz")
оферти = feed.читати_yml(чистий)[0]
ярлик = collections.Counter(ЧК._крамниця(o) for o in оферти
                            if re.search(r"артикул\s*$", НР.почистити(str(o.get("назва") or "")), re.I))
print("РЯДОК 187 — ярлик поля «артикул» у кінці назви ПОКАЗУ: %d %s"
      % (sum(ярлик.values()), dict(ярлик) or "—"))
сирий = os.path.join(os.path.dirname(os.path.abspath(чистий)), "_л17_сирий.xml")
with gzip.open(архів, "rb") as вх, open(сирий, "wb") as вих:
    shutil.copyfileobj(вх, вих)
сирі = feed.читати_yml(сирий)[0]
os.remove(сирий)
коди = ЧК.коди_крамниць(сирі)   # рішення про крамницю видно лише до чистки
def з_кодом(набір):
    c = collections.Counter()
    for o in набір:
        к = set(коди.get(ЧК._крамниця(o)) or ())
        т = str((o.get("параметри") or {}).get(ЧК.ПАРАМ_РОЗДІЛУ) or "")
        if к and {м.group(0) for м in НР._токени_коду(т)} & к:
            c[ЧК._крамниця(o)] += 1
    return c
сир, чист = з_кодом(сирі), з_кодом(оферти)
print("РЯДОК 183 — код моделі в `param %s` (крамниці з кодами: %s): у СИРОМУ архіві %d %s, "
      "у ЧИСТОМУ каталозі %d %s"
      % (ЧК.ПАРАМ_РОЗДІЛУ, [к for к, v in коди.items() if v],
         sum(сир.values()), dict(сир) or "—", sum(чист.values()), dict(чист) or "—"))
набори = [(feed.слот(o), ФС.набір_цілий(o)) for o in оферти if ФС.набір_цілий(o) is not None]
чужі = [с for с, н in набори if н is True and с is not None and с not in ФС.СЛОТИ_РОЗМІРУ_ОДЯГУ]
print("РЯДОК 184 — ЦІЛИЙ набір у слоті-аксесуарі: %d %s; НЕцілих наборів в аксесуарах "
      "(законні, лишаються): %d" % (len(чужі), чужі or "—",
      sum(1 for с, н in набори if н is False and с is not None and с not in ФС.СЛОТИ_РОЗМІРУ_ОДЯГУ)))
