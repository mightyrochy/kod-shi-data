"""Одноколірний Shopify: кадр, прив'язаний `variant_ids` до варіацій товару, має власника через XML і факти;
кадр без прив'язки, адреса з параметром і товар без жодної прив'язки — «невідомо»."""
import json, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела/прилади")]
import shopify_варіанти as ш, складальник as с, feed, власник_кадру as ф, фід_власник_кадру as в
К = "https://shop.test/%s.jpg"

def main():
    """Лічить доказ одноколірного запису й відмови для неприв'язаного кадру, параметра адреси й товару без прив'язки."""
    д = dict(схема="v1", ід="ж-00001", назва="Сукня", вихід={}, категорія="1", валюта="UAH", опис=None, параметри=[["магазин", "shop.test", "с"]])
    товар = dict(id=7, title="Сукня", options=[dict(name="Color"), dict(name="Size")], variants=[dict(id=11, option1="A", option2="S"), dict(id=12, option1="A", option2="M")],
                 images=[dict(src=К % "s1", variant_ids=[11, 12]), dict(src=К % "s2", variant_ids=[])])
    рецепт = dict(колір=["Color"], розмір=["Size"])
    записи = [ш._запис(д, товар, з, "ж-00009", "https://shop.test/products/dress", "2026-11-05") for з in ш.варіанти_shopify(товар, рецепт)]
    with tempfile.TemporaryDirectory() as тека:
        шлях = Path(тека) / "каталог.xml"
        шлях.write_text('<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers>' + "".join(с.офер_xml(з) for з in записи) + "</offers></shop></yml_catalog>", encoding="utf-8")
        о = feed.читати_yml(str(шлях))[0][0]
    зб = {о["id"]: {"фото": К % "s1"}}
    факти = ф.факти([о], зб, {К % "s1": [200, 1, 1, "image/jpeg", "1" * 64]})
    assert в.запис(о, зб[о["id"]], факти=факти)["варіант"] == "shopify:7:товар"
    assert в.доказ_варіанта(о, К % "s2") is None and в.доказ_варіанта(dict(о, url=о["url"] + "?variant=11"), К % "s1") is None
    чужий = dict(товар, images=товар["images"] + [dict(src=К % "s3", variant_ids=[11, 99])])
    assert set(ш.варіанти_shopify(чужий, рецепт)[0]["зв_язки"]) == {К % "s1"}
    без = dict(товар, images=[dict(src=К % "s2", variant_ids=[])])
    assert json.loads(ш.власник_варіанта(без, ш.варіанти_shopify(без, рецепт)[0], "x")) == "невідомо"
    print("Один колір Shopify: 1 доказ через XML; неприв'язаний кадр, параметр адреси, чужий id і товар без прив'язки — невідомо")

if __name__ == "__main__":
    main()
