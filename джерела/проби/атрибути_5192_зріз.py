# -*- coding: utf-8 -*-
"""Рядок 5192, сім'я фід_атрибути: зріз полів ознак каталогу (id → значення) у json-файл;
два зрізи (ДО/ПІСЛЯ) порівнює `--різниця`. Прогін: python3 проби/атрибути_5192_зріз.py <вихід.json>
або python3 проби/атрибути_5192_зріз.py --різниця ДО.json ПІСЛЯ.json"""
import io, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
ПОЛЯ = ("матеріал", "еластан_%", "довжина_виробу_см", "деталі_крою", "талія", "крій", "крій_джерело",
        "довжина_рівень", "довжина_джерело", "розміщення_мотиву", "формат", "ремінь_см", "ланцюг_см",
        "місце", "місце_джерело", "den", "метал", "метали_варіантів", "слова_з_param", "волокно")
if sys.argv[1] == "--різниця":
    а, б = [json.load(io.open(ф, encoding="utf-8")) for ф in sys.argv[2:4]]
    for п in ПОЛЯ:
        змін = [і for і in а if а[і].get(п) != б.get(і, {}).get(п)]
        стало_невідомо = sum(1 for і in змін if а[і].get(п) is not None and б[і].get(п) is None)
        print("%-20s було_значення=%-5d змінилось=%-5d стало_невідомо=%-5d з_невідомо_у_значення=%d" % (
            п, sum(1 for і in а if а[і].get(п) is not None), len(змін), стало_невідомо,
            sum(1 for і in змін if а[і].get(п) is None and б[і].get(п) is not None)))
    sys.exit()
import feed
from фід_каталог import _прочитати_каталог
к = _прочитати_каталог(feed.каталог_на_диску(), 0, "кеш_кольорів.json", feed.читати_збагачення())["каталог"]
вих = {r["id"]: {п: r.get(п) for п in ПОЛЯ} for r in к}
json.dump(вих, io.open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False, default=str)
print("речей:", len(вих))
