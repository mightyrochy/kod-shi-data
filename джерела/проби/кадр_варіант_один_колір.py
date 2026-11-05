"""Одноколірний товар Shopify і Woo (рішення менеджера 05.11): уся галерея, з головним зображенням і кадрами без
прив'язки, має власника через XML і факти; кадр з id поза товаром, адреса з параметром, чужий товар і товар без
кадрів — «невідомо»."""
import json, sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела/прилади")]
import shopify_варіанти as ш, woo_варіанти as ва, жниварка as ж, складальник as с, feed, власник_кадру as ф, фід_власник_кадру as в
К, Б = "https://shop.test/%s.jpg", "https://shop.test"
Д = dict(схема="v1", ід="ж-00001", назва="Сукня", вихід={}, категорія="1", валюта="UAH", опис=None, ціна="100", параметри=[["магазин", "shop.test", "с"]])


def через_xml(записи):
    """Записи v1 → оферти фіду й факти власності (байти різні на кожен кадр)."""
    with tempfile.TemporaryDirectory() as тека:
        шлях = Path(тека) / "каталог.xml"
        шлях.write_text('<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers>'
                        + "".join(с.офер_xml(з) for з in записи) + "</offers></shop></yml_catalog>", encoding="utf-8")
        return feed.читати_yml(str(шлях))[0]


def власники(о):
    """Мітка варіанта кожного кадру запису `о`, коли вимір зроблено з нього (факти — з того самого кадру)."""
    вих = []
    for і, к in enumerate(о["фото"]):
        зб = {о["id"]: {"фото": к}}
        факти = ф.факти([о], зб, {к: [200, 1, 1, "image/jpeg", str(і % 10) * 64]})
        вих.append(в.запис(о, зб[о["id"]], факти=факти)["варіант"])
    return вих


def main():
    """Лічить доказ одноколірних записів обох платформ і відмови."""
    # Shopify: s1 прив'язано, s2 без прив'язки, s3 прив'язано й до id поза товаром.
    товар = dict(id=7, title="Сукня", options=[dict(name="Color"), dict(name="Size")], variants=[dict(id=11, option1="A", option2="S"), dict(id=12, option1="A", option2="M")],
                 images=[dict(src=К % "s1", variant_ids=[11, 12]), dict(src=К % "s2", variant_ids=[]), dict(src=К % "s3", variant_ids=[11, 99])])
    рецепт = dict(колір=["Color"], розмір=["Size"])
    варіант = ш.варіанти_shopify(товар, рецепт)[0]
    assert варіант["кадри"] == [К % н for н in ("s1", "s2", "s3")] and set(варіант["зв_язки"]) == {К % "s1", К % "s2"}
    о = через_xml([ш._запис(Д, товар, варіант, "ж-00009", "https://shop.test/products/dress", "2026-11-05")])[0]
    assert власники(о) == ["shopify:7:товар", "shopify:7:товар", "невідомо"], власники(о)
    assert в.доказ_варіанта(dict(о, url=о["url"] + "?variant=11"), К % "s1") is None
    assert в.доказ_варіанта(dict(о, параметри=dict(о["параметри"], id_магазину="8")), К % "s1") is None
    без_опції = dict(товар, options=[dict(name="Size")], variants=[dict(id=11, option1="S")], images=[dict(src=К % "s2")])
    assert json.loads(ш.власник_варіанта(без_опції, ш.варіанти_shopify(без_опції, рецепт)[0], "x"))["джерело"] == "shopify:один_колір"
    без = dict(товар, images=[])
    assert json.loads(ш.власник_варіанта(без, ш.варіанти_shopify(без, рецепт)[0], "x")) == "невідомо"
    # Woo: один терм кольору, дві розмірні варіації; головне зображення — теж кадр цього кольору.
    Р = dict(колір="pa_color", розмір="pa_size")
    вар = [dict(ід=91, адреса=Б + "/p/?attribute_pa_color=a&attribute_pa_size=s", є=True, кадри=[К % "main"]),
           dict(ід=92, адреса=Б + "/p/?attribute_pa_color=a&attribute_pa_size=m", є=False, кадри=[К % "main"])]
    т = dict(id=9, name="Сукня", permalink=Б + "/p/", type="variable", images=[dict(src=К % н) for н in ("main", "g2")], _варіації=вар,
             attributes=[dict(taxonomy="pa_color", has_variations=True, terms=[dict(name="A", slug="a")])])
    проста = dict(т, id=10, type="simple", _варіації=[], is_in_stock=True, images=[dict(src=К % "p1")],
                  attributes=[dict(taxonomy="pa_color", has_variations=False, terms=[dict(name="A", slug="a")])])
    записи = []
    for і, тт in enumerate((т, проста), 1):
        в_, = ж.варіанти_woo(тт, Б, Р)
        ф_, = ж.факти_woo(тт, Б, Р)
        записи.append(ва._запис(Д, тт, dict(в=в_, ф=ф_), "ж-%05d" % і, str(тт["id"]), "2026-11-05", False, ж, Р))
    оф = через_xml(записи)
    assert [власники(о) for о in оф] == [["woo:9:товар"] * 2, ["woo:10:товар"]], [власники(о) for о in оф]
    assert json.loads(dict(оф[1]["параметри"])["власник_кадру"])["варіанти"] == ["10"]
    assert в.доказ_варіанта(dict(оф[0], url=оф[0]["url"] + "?attribute_pa_color=a"), оф[0]["фото"][0]) is None
    свіжі = [dict(ж.канонічний_запис(x, dict(домен="shop.test", мова="укр", стать_типово="жіноче"), "woo:wc/store"), id="ж-%05d" % і)
             for і, x in enumerate(ж.факти_woo(т, Б, Р, lambda x: ж.кадр_закодований(ж.оригінал_фото(x))), 1)]
    with tempfile.TemporaryDirectory() as тека:
        ж.записати_каталог(свіжі, str(Path(тека) / "к.xml"), "проба")
        о, = feed.читати_yml(str(Path(тека) / "к.xml"))[0]
    assert власники(о) == ["woo:9:товар"] * 2
    assert json.loads(ж.власник_варіанта_woo(dict(т, images=[]), ж.варіанти_woo(dict(т, images=[]), Б, Р)[0], Б + "/p/", Р)) == "невідомо"
    print("Один колір: Shopify 2 кадри з доказом (без прив'язки — теж), кадр з чужим id — невідомо; Woo — галерея з головним "
          "зображенням і проста річ через адаптер і свіжі жнива; параметр адреси, чужий товар і порожня галерея — невідомо")

if __name__ == "__main__":
    main()
