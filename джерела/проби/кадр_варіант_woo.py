"""Доказ кадру Woo через адаптер і свіжі жнива → XML → фід → факти → читач; головне зображення доказом не стає."""
import sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела/прилади")]
import жниварка as ж, woo_варіанти as ва, складальник as с, feed, власник_кадру as ф, фід_власник_кадру as в
К, Б, Р = "https://shop.test/%s.jpg", "https://shop.test", dict(колір="pa_color", розмір="pa_size")
Д = dict(схема="v1", ід="ж-00001", назва="Сукня", вихід={}, категорія="1", валюта="UAH", опис=None, ціна="100", параметри=[["магазин", "shop.test", "с"]])

def фід(xml):
    """XML → оферти, вимір з першого кадру, факти власності (байти різні на кожен запис)."""
    with tempfile.TemporaryDirectory() as тека:
        шлях = Path(тека) / "каталог.xml"
        xml(str(шлях)); оф = feed.читати_yml(str(шлях))[0]
    зб = {о["id"]: {"фото": о["фото"][0]} for о in оф}
    return оф, зб, ф.факти(оф, зб, {о["фото"][0]: [200, 1, 1, "image/jpeg", str(і) * 64] for і, о in enumerate(оф, 1)})

def main():
    вар = [dict(ід=51, адреса=Б + "/p/?attribute_pa_color=a", є=True, кадри=[К % "a"]), dict(ід=52, адреса=Б + "/p/?attribute_pa_color=b", є=True, кадри=[К % "б-копія"]),
           dict(ід=53, адреса=Б + "/p/?attribute_pa_color=a&attribute_pa_size=m", є=True, кадри=[К % "main"])]
    т = dict(id=5, name="Сукня", permalink=Б + "/p/", type="variable", images=[dict(src=К % н) for н in ("main", "a", "б-копія")], _варіації=вар,
             attributes=[dict(taxonomy="pa_color", has_variations=True, terms=[dict(name="A", slug="a"), dict(name="B", slug="b")])])
    варіанти = ж.варіанти_woo(т, Б, Р)
    assert варіанти[0]["кадри"] == [К % "a", К % "main"] and варіанти[0]["зв_язки"] == {К % "a": ["51"]}
    записи = [ва._запис(Д, т, dict(в=в_, ф=ф_), "ж-%05d" % і, "5", "2026-11-05", True, ж, Р) for і, (в_, ф_) in enumerate(zip(варіанти, ж.факти_woo(т, Б, Р)), 1)]
    оф, зб, факти = фід(lambda ш: Path(ш).write_text('<yml_catalog><shop><categories><category id="1">Сукні</category></categories><offers>' + "".join(с.офер_xml(з) for з in записи) + "</offers></shop></yml_catalog>", encoding="utf-8"))
    assert [в.запис(о, зб[о["id"]], факти=факти)["варіант"] for о in оф] == ["woo:5:a", "woo:5:b"]
    for змінений in [dict(оф[0], url=оф[1]["url"]), dict(оф[0], параметри=dict(оф[0]["параметри"], id_магазину="6"))]:
        assert в.запис(змінений, зб[оф[0]["id"]], факти=факти)["варіант"] == "невідомо"
    assert в.доказ_варіанта(оф[0], К % "main") is None and в.доказ_варіанта(оф[0], оф[1]["фото"][0]) is None
    свіжі = [dict(ж.канонічний_запис(x, dict(домен="shop.test", мова="укр", стать_типово="жіноче"), "woo:wc/store"), id="ж-%05d" % і)
             for і, x in enumerate(ж.факти_woo(т, Б, Р, lambda x: ж.кадр_закодований(ж.оригінал_фото(x))), 1)]
    оф, зб, факти = фід(lambda ш: ж.записати_каталог(свіжі, ш, "проба"))
    assert [о["url"] for о in оф] == [Б + "/p?attribute_pa_color=a", Б + "/p?attribute_pa_color=b"] and "%D0%B1" in оф[1]["фото"][0]
    assert [в.запис(о, зб[о["id"]], факти=факти)["варіант"] for о in оф] == ["woo:5:a", "woo:5:b"]
    assert ж.власник_варіанта_woo(т, ж.варіанти_woo(dict(т, attributes=[dict(т["attributes"][0], terms=т["attributes"][0]["terms"][:1])]), Б, Р)[0], Б + "/p/", Р) is None
    print("Woo: адаптер і свіжі жнива — по 2 докази через XML (кирилиця в кадрі); головне зображення, сестра й 2 підміни — невідомо; один колір — без параметра")

if __name__ == "__main__":
    main()
