# -*- coding: utf-8 -*-
"""Проба 5.1: поле картки — лише з вузла свого товару. Друкує факти по трьох збережених сторінках; `python3 -I … [жниварка.py]`
(другий аргумент — інший варіант модуля для «ДО»)."""
import gzip, importlib.util, os, re, sys

КОРІНЬ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
шлях = sys.argv[1] if len(sys.argv) > 1 else os.path.join(КОРІНЬ, "zhnyvarka", "жниварка.py")
сп = importlib.util.spec_from_file_location("ж", шлях); ж = importlib.util.module_from_spec(сп); сп.loader.exec_module(ж)
Ф = os.path.join(КОРІНЬ, "zhnyvarka", "фікстури")
ЧУЖЕ = re.compile(r"Швидкий перегляд|З цим товаром|Останні відгуки|Дивіться також|Вечірня гіпюрова|Жіноча шапка|Правила|дякую за", re.I)
СТОРІНКИ = (("ricamare", gzip.open(os.path.join(Ф, "ricamare_3448.html.gz"), "rt", encoding="utf8").read(), "https://ricamare.com.ua/svitshot/3448/", "ricamare.com.ua"),
            ("bella", open(os.path.join(Ф, "bella_6975_20261017_raw.html"), encoding="utf8").read(), "https://bella-bicchi.com/catalog/palto-122344/", "bella-bicchi.com"),
            ("синтетична", open(os.path.join(Ф, "картка_чуже_5_1.html"), encoding="utf8").read(), "https://t.example/product/suknia-1/", "t.example"))
всього = {}
for ім, т, url, дом in СТОРІНКИ:
    факти = ж.факти_з_картки(т, url, ж.рецепт_селекторів(дом))
    з = ж.канонічний_запис(факти, {"домен": дом, "платформа": "x"}, "картка")
    текст = " ".join([з.get("опис") or "", з.get("склад") or ""] + [str(x) for p in з["характеристики_сирі"] for x in p] + [str(x[0]) for x in з["свотчі_всі"]]
                     + [str(x) for x in (з.get("розміри") or [])])
    дубль = bool(re.search(r"(\d+)% (\w{4})\w*[;, ]+\1% \2", з.get("склад") or ""))
    числа = [x for x in з["розміри"] if re.fullmatch(r"\d+", x) and not 30 <= int(x) <= 60]
    пол = {"чужі_фрагменти": len(ЧУЖЕ.findall(текст)), "свотчів": len(факти["свотчі"]), "мірки_в_розмірах": len(числа),
           "склад_дубль": int(дубль), "склад_з_опису": int(з.get("склад_джерело") == "опис"),
           "полів_із_джерелом": sum(1 for v in (з.get("джерела_полів") or {}).values() if v), "сирий_запис": int(bool(з.get("сирий")))}
    print(ім, пол)
    for к, в in пол.items():
        всього[к] = всього.get(к, 0) + в
з = ж.канонічний_запис({"url": "https://h.example/p/1", "назва": "Шапка Джойс", "опис": "Склад: 100% котон Колір: сіра *Будь ласка", "ціна": 1.0}, {"домен": "h.example", "платформа": "x"}, "shopify")
print("опис без поля складу (6858): склад =", з.get("склад"), "| джерело", з.get("склад_джерело"))
print("РАЗОМ", всього)
