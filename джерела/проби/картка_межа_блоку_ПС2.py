# -*- coding: utf-8 -*-
"""ПС-2: поле картки — лише з блоку цього товару. ДО (`git show <основа>:zhnyvarka/жниварка.py`, перший аргумент — шлях до
нього) і ПІСЛЯ на збережених сторінках: що DOM-поле ДО брало, а ПІСЛЯ не бере (поза межею), і чи межа знайдена.
`python3 -I проби/картка_межа_блоку_ПС2.py /tmp/ж_до.py`"""
import gzip, importlib.util, os, sys, tempfile

КОРІНЬ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
Ж = os.path.join(КОРІНЬ, "zhnyvarka")
Ф = os.path.join(Ж, "фікстури")


def завант(шлях, ім):
    сп = importlib.util.spec_from_file_location(ім, шлях); м = importlib.util.module_from_spec(сп); сп.loader.exec_module(м)
    return м


після = завант(os.path.join(Ж, "жниварка.py"), "після")
до = завант(sys.argv[1], "до") if len(sys.argv) > 1 else None
ПОЛЯ = ("опис", "характеристики_сирі", "свотчі", "розміри", "ціна", "фото")
синт_рецепт = os.path.join(tempfile.mkdtemp(), "р.tsv")
with open(синт_рецепт, "w", encoding="utf8") as f:
    f.write("домен\tселектор_блоку\nt.example\tdiv.product.detail\n")
СТОРІНКИ = (("ricamare", gzip.open(os.path.join(Ф, "ricamare_3448.html.gz"), "rt", encoding="utf8").read(), "https://ricamare.com.ua/svitshot/3448/", "ricamare.com.ua", None),
            ("bella", open(os.path.join(Ф, "bella_6975_20261017_raw.html"), encoding="utf8").read(), "https://bella-bicchi.com/catalog/palto-122344/", "bella-bicchi.com", None),
            ("синтетична", open(os.path.join(Ф, "картка_чуже_5_1.html"), encoding="utf8").read(), "https://t.example/product/suknia-1/", "t.example", синт_рецепт),
            ("синтетична без межі", open(os.path.join(Ф, "картка_чуже_5_1.html"), encoding="utf8").read(), "https://t.example/product/suknia-1/", "t.example", None))
сума = 0


def вміст(v):
    """Склад поля без порядку: межа не міняє порядку знайденого, лише його кількість."""
    return sorted(map(str, v)) if isinstance(v, list) else v


for ім, т, url, дом, шл in СТОРІНКИ:
    p = після.факти_з_картки(т, url, після.рецепт_селекторів(дом, шл))
    рядок = "%s: межа=%s" % (ім, p.get("межа_блоку"))
    if до:
        a = до.факти_з_картки(т, url, до.рецепт_селекторів(дом, шл if шл and ім == "синтетична" else None))
        вилучено = [к for к in ПОЛЯ if a.get(к) and вміст(a.get(к)) != вміст(p.get(к))]
        рядок += " | ДО→ПІСЛЯ змінено полів: %s" % (вилучено or "—")
        сума += len(вилучено)
    print(рядок)
print("РАЗОМ змінено полів ДО→ПІСЛЯ:", сума)
