"""Перевіряє доказ Shopify через v1 → XML → фід → файл фактів → читач виміру."""
import copy, json, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела/прилади")]
import shopify_варіанти as ш, складальник as с, feed, власник_кадру as ф, фід_власник_кадру as в

def main():
    """Лічить допуски власного кадру й відмови для сестер, невідомого та старого доказу."""
    товар = dict(id=7, title="Сукня", options=[dict(name="Color")], variants=[dict(id=11, option1="A"), dict(id=12, option1="B")],
                 images=[dict(src="https://shop.test/a.jpg", variant_ids=[11]), dict(src="https://shop.test/b.jpg", variant_ids=[12])])
    рецепт = dict(колір=["Color"], розмір=[])
    д = dict(схема="v1", ід="ж-00001", назва="Сукня", вихід={}, категорія="1", валюта="UAH", опис=None, параметри=[["магазин", "shop.test", "с"]])
    записи = [ш._запис(д, товар, з, "ж-%05d" % і, "https://shop.test/products/dress", "2026-11-04") for і, з in enumerate(ш.варіанти_shopify(товар, рецепт), 1)]
    with tempfile.TemporaryDirectory() as тека:
        шлях = Path(тека) / "каталог.xml"
        шлях.write_text('<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers>' + ''.join(с.офер_xml(з) for з in записи) + '</offers></shop></yml_catalog>', encoding="utf-8")
        оф = feed.читати_yml(str(шлях))[0]
    зб = {о["id"]: {"фото": о["фото"][0]} for о in оф}
    кадри = {о["фото"][0]: [200, 1, 1, "image/jpeg", str(і) * 64] for і, о in enumerate(оф, 1)}
    факти = ф.факти(оф, зб, кадри)
    assert [в.запис(о, зб[о["id"]], факти=факти)["варіант"] for о in оф] == ["shopify:7:11", "shopify:7:12"]
    assert all(not в.чужий_кадр_кольору(о, зб[о["id"]], {}, lambda _: None, факти) for о in оф)
    о, вимір = оф[0], зб[оф[0]["id"]]
    for змінений in [dict(о, url=оф[1]["url"]), dict(о, фото=[]), dict(о, параметри=dict(о["параметри"], власник_кадру="{}")), dict(о, параметри=dict(о["параметри"], id_магазину="8"))]:
        assert в.запис(змінений, вимір, факти=факти)["варіант"] == "невідомо"
        assert в.чужий_кадр_кольору(змінений, вимір, {}, lambda _: None, факти)
    assert в.запис(о, вимір, {"слово": "A"}, факти={})["варіант"] == "невідомо"
    assert в.запис(о, вимір, факти={о["id"]: факти[о["id"]][:6]})["варіант"] == "невідомо"
    assert в.чужий_кадр_кольору(о, {"фото": "https://other.test/a.jpg"}, {}, lambda _: None, факти)
    спільні = copy.deepcopy(факти); спільні[о["id"]][3] = [оф[1]["id"]]
    assert в.чужий_кадр_кольору(о, вимір, {}, lambda _: None, спільні)
    for ід in ([12], [], [11, 999]):
        т = dict(товар, images=товар["images"] + [dict(src=товар["images"][0]["src"], variant_ids=ід)])
        assert all(товар["images"][0]["src"] not in з["кадри"] for з in ш.варіанти_shopify(т, рецепт))
    print("Власність: 2 докази через XML; 4 підміни, 2 старі формати, інший хост, спільні байти й 3 повтори URL — пройдено")

if __name__ == "__main__":
    main()
