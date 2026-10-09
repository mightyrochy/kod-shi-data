# -*- coding: utf-8 -*-
"""Спільне для проб: пул пакета моделі (`pool`) — ПЛАСКИЙ список {n, type, …} (п.12);
проби, що міряють слот, перегруповують його тут за `внутрішня_мова.СЛОТ_ТИПУ`.
Запуск (друкує факт): python3 проби/пул_слотами.py — скільки речей у кожному слоті руки 1."""
import sys, os, json
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import внутрішня_мова as ВМ

СЛОТ_УКР = {"dress": "сукня", "top": "верх", "bottom": "низ", "shoes": "взуття", "bag": "сумка",
            "ring": "каблучка", "outerwear": "верхній_шар", "scarf": "шарф", "jewelry": "прикраси"}


def пул_слотами(пакет):
    """{слот українською: [річ з полем «н» = n]} з пакета (dict чи його JSON)."""
    пак = json.loads(пакет) if isinstance(пакет, str) else пакет
    о = {}
    for x in пак["pool"]:
        с = ВМ.СЛОТ_ТИПУ.get(x.get("type"))
        о.setdefault(СЛОТ_УКР.get(с, с), []).append(dict(x, н=x["n"]))
    return о


if __name__ == "__main__":
    import tempfile, bridge as B, feed as Ф
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    вх = json.load(open("стенд_вх.json", encoding="utf-8"))
    d0 = dict(вх, каталог=Ф.каталог_на_диску("каталог_brief.xml"), варіантів=10,
              кеш_кольорів=os.path.join(tempfile.gettempdir(), "кеш_пул_слотами.json"))
    п = пул_слотами(json.loads(B.виклик("запити", json.dumps(d0, ensure_ascii=False)))["руки"]["1"])
    print("речей у пулі руки 1: %d · слотів: %s" % (sum(map(len, п.values())), {с: len(v) for с, v in п.items()}))
