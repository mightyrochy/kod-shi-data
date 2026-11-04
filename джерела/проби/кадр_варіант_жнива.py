"""Прив'язка Shopify проходить свіжі жнива та XML цілою, включно з довгою галереєю."""
import sys, tempfile
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka")]
import feed, жниварка as ж, фід_власник_кадру as в, shopify_варіанти as ш

def main():
    """Звіряє сирі id платформи на виході канонізації й XML нового обходу."""
    товар = dict(id=7, handle="dress", title="Сукня", options=[dict(name="Color")],
                 variants=[dict(id=11, option1="A", available=True), dict(id=12, option1="B", available=True)],
                 images=[dict(src="https://shop.test/%02d.jpg?v=123456789" % і, variant_ids=[11]) for і in range(30)])
    факти = ж.факти_shopify(товар, "https://shop.test")
    assert len(факти[0]["власник_кадру"]) > 400
    записи = [dict(ж.канонічний_запис(ф, dict(домен="shop.test", мова="укр", стать_типово="жіноче"), "shopify:products.json"), id="ж-%05d" % і) for і, ф in enumerate(факти, 1)]
    with tempfile.TemporaryDirectory() as тека:
        шлях = Path(тека) / "каталог.xml"
        ж.записати_каталог(записи, str(шлях), "проба")
        оф = feed.читати_yml(str(шлях))[0]
    assert len(оф) == 2 and оф[0]["параметри"]["власник_кадру"] == факти[0]["власник_кадру"]
    assert len(оф[0]["фото"]) == len(записи[0]["фото"]) == 8 and all(в.доказ_варіанта(оф[0], к) for к in оф[0]["фото"])
    assert not оф[1]["фото"] and not в.доказ_варіанта(оф[1], факти[0]["фото"][0])
    колізія = dict(товар, images=[dict(src="https://shop.test/a.jpg?v=1", variant_ids=[11]), dict(src="https://shop.test/a.jpg?v=2", variant_ids=[12])])
    assert all(not з["кадри"] for з in ш.варіанти_shopify(колізія, dict(колір=["Color"], розмір=[]), нормувати_кадр=lambda x: x.split("?")[0]))
    print("Свіжі жнива: 30 прив'язок → 8 відібраних кадрів із доказом; JSON %d символів цілий; сестра без кадру" % len(факти[0]["власник_кадру"]))

if __name__ == "__main__":
    main()
