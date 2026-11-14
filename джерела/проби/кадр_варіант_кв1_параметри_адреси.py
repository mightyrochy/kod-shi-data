"""Частина кв1: параметри адреси одноколірного запису — мітки переходу й ідентичність сторінки не відхиляють доказ,
параметр вибору варіанта (`variant`, `attribute_…`, невідомий) — відхиляє. Запуск: python3 -W ignore джерела/проби/кадр_варіант_кв1_параметри_адреси.py"""
import json, sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[1])]
import фід_власник_кадру as в

def доказ(адреса):
    к = "https://s.ua/a.jpg"
    вл = dict(джерело="картка:один_колір", товар="7", адреса=адреса, варіанти=["7"], зв_язки={к: ["7"]})
    о = dict(id="1", url=адреса, фото=[к], параметри=dict(id_магазину="7", власник_кадру=json.dumps(вл)))
    return в.доказ_варіанта(о, к) is not None

випадки = {"https://s.ua/p/": True, "https://s.ua/p/?sc_content=1_r2v3": True, "https://s.ua/p/?utm_source=x&gclid=1": True,
           "https://s.ua/index.php?route=product/product&product_id=7": True, "https://s.ua/p/?variant=5": False,
           "https://s.ua/p/?attribute_pa_color=red": False, "https://s.ua/p/?color=red": False,
           "https://s.ua/p/?sc_content=1&variant=5": False}
for а, чекаю in випадки.items():
    assert доказ(а) == чекаю, а
print("кадр_варіант_кв1_параметри_адреси: ОК")
