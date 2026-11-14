"""Частина кв1: параметри адреси одноколірного запису — мітки переходу й ідентичність сторінки не відхиляють доказ,
параметр вибору варіанта (`variant`, `attribute_…`, невідомий) — відхиляє. Запуск: python3 -W ignore джерела/проби/кадр_варіант_кв1_параметри_адреси.py"""
import json, sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[1])]
import фід_власник_кадру as в

def доказ(адреса, товар="7"):
    к = "https://s.ua/a.jpg"
    вл = dict(джерело="картка:один_колір", товар=товар, адреса=адреса, варіанти=[товар], зв_язки={к: [товар]})
    о = dict(id="1", url=адреса, фото=[к], параметри=dict(id_магазину=товар, власник_кадру=json.dumps(вл)))
    return в.доказ_варіанта(о, к) is not None

випадки = {"https://s.ua/p/": True, "https://s.ua/p/?sc_content=1_r2v3": True, "https://s.ua/p/?utm_source=x&gclid=1": True,
           "https://s.ua/index.php?route=product/product&product_id=7": True, "https://s.ua/p/?variant=5": False,
           "https://s.ua/p/?attribute_pa_color=red": False, "https://s.ua/p/?color=red": False,
           "https://s.ua/p/?sc_content=1&variant=5": False}
for а, чекаю in випадки.items():
    assert доказ(а) == чекаю, а
# id з хвоста мітки переходу — не id товару (Twice, 15253): відхиляється; id із product_id OpenCart — приймається
assert not доказ("https://s.ua/p/?sc_content=37254_r2979v3594", "3594")
assert not доказ("https://s.ua/p/?sc_content=37254_r2979v3594", "37254")
assert доказ("https://s.ua/p/?sc_content=37254_r2979v3594", "555")
assert доказ("https://s.ua/index.php?route=product/product&product_id=2322", "2322")
print("кадр_варіант_кв1_параметри_адреси: ОК")
