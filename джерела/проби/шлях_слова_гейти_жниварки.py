# -*- coding: utf-8 -*-
"""Рядок 6856: скільки речей ріже кожна причина `жниварка.гейти_речі` — «словом» (регулярка чи словник назви, крихт,
адреси) і «кодом» (довжина, число, поле). Записи — як у жниварці: знімок Shopify — як `shopify_варіанти.основа_нового`;
каталог — `канонічний_запис` з назви, адреси, фото, ціни й `категорія_магазину` замість крихт (крихт каталог не
зберігає; кадри частини речей лише в `каталог_кадри.json.gz` — фото-гейт на каталозі не лічиться). «Нема в наявності»
не лічиться (п.16). Прогін: python3 проби/шлях_слова_гейти_жниварки.py [тека з `zhnyvarka/shopify_знімок.py`]"""
import collections, glob, gzip, json, os, sys, xml.etree.ElementTree as ET
ЖН = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "zhnyvarka"); sys.path.insert(0, ЖН)
import жниварка as ж, shopify_варіанти as шв
СЛОВОМ = ("назва: сміття", "рядок інтерф", "відгук", "рекламний", "промо", "назва розд", "назва рос", "поза слот",
          "слот не", "дитяче")                                     # порожня назва (< 3 знаків) під «сміттям» — код
МАГ = {м["домен"]: м for м in ж.читати_магазини(os.path.join(ЖН, "магазини.tsv"))}


def з_знімка(тека):
    for ф in sorted(glob.glob(os.path.join(тека, "*.json.gz"))):
        д = os.path.basename(ф)[:-8]; адреса = "https://" + д + шв.читати_рецепти()[д]["шлях_сторінки"] + "/products/"
        for т in json.load(gzip.open(ф, "rt", encoding="utf-8")):
            ф_ = dict(ж.факти_shopify(т, "https://" + д)[0], характеристики={}, url=адреса + т["handle"])
            yield д, ж.канонічний_запис(ф_, dict(МАГ[д], платформа="Shopify"), шв.КАНАЛ)

def з_каталогу():
    for _, о in ET.iterparse(gzip.open(os.path.join(ЖН, "..", "каталог_повний.xml.gz"))):
        if о.tag == "offer":
            п = {x.get("name"): x.text for x in о.findall("param")}; д = п["магазин"]
            ф = dict(назва=о.findtext("name"), url=о.findtext("url"), фото=[x.text for x in о.findall("picture")],
                     ціна=float(о.findtext("price") or 0) or None, валюта=о.findtext("currencyId"),
                     available=о.get("available") == "true", крихти=[п.get("категорія_магазину") or ""])
            yield д, ж.канонічний_запис(ф, МАГ.get(д) or {"домен": д}, п.get("канал") or ""); о.clear()

for під, записи, поза in ([("знімок Shopify", з_знімка(sys.argv[1]), ("нема в",))] if sys.argv[1:] else []) \
        + [("каталог", з_каталогу(), ("нема в", "фото нема"))]:
    л, ріже, словом = collections.Counter(), collections.Counter(), collections.Counter()
    for д, з in записи:
        пр = {(п.split(" (")[0], "слово" if п.startswith(СЛОВОМ) and (len(з["назва"]) > 2 or п[:6] != "назва:")
               else "код") for п in ж.гейти_речі(з) if not п.startswith(поза)}
        л.update(пр | {("", "")}); ріже[д] += bool(пр); словом[д] += bool(пр) and all(в == "слово" for _, в in пр)
    print("%s: речей %d · ріже %d · лише словом %d" % (під, л.pop(("", "")), sum(ріже.values()), sum(словом.values())))
    [print("  %-6s %5d  %s" % (в, n, п)) for (п, в), n in л.most_common()]
    print("  крамниці (ріже/словом):", ", ".join("%s %d/%d" % (д, n, словом[д]) for д, n in ріже.most_common(8)))
