"""Перевіряє власність кадрів Shopify в обох читачах та заміну старої галереї запису."""
import copy
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
import жниварка as ж
import shopify_варіанти as ш
import woo_варіанти as в
def main():
    """Проганяє прив'язки, спільні й невідомі кадри без мережі та моделей."""
    рецепт = {"колір": ["Color"], "розмір": ["Size"], "шлях_сторінки": ""}
    товар = dict(id=7, title="Сукня", handle="dress", options=[dict(name="Color"), dict(name="Size")],
                 variants=[dict(id=11, option1="A", option2="S", available=True, price="10", sku="A-S"),
                           dict(id=12, option1="B", option2="M", available=False, price="20", sku="B-M")])
    випадки = [([[11]], [["https://shop.test/0.jpg"], []]), ([[11, 12]], [[], []]),
               ([[]], [[], []]), ([[11, 999]], [[], []]), ([], [[], []]),
               ([[11], [12]], [["https://shop.test/0.jpg"], ["https://shop.test/1.jpg"]])]
    for зв_язки, очікувані in випадки:
        т = dict(товар, images=[dict(src="https://shop.test/%d.jpg" % і, variant_ids=ід) for і, ід in enumerate(зв_язки)])
        копія = copy.deepcopy(т)
        варіанти, факти = ш.варіанти_shopify(т, рецепт), ж.факти_shopify(т, "https://shop.test")
        assert [в["кадри"] for в in варіанти] == [ф["фото"] for ф in факти] == очікувані
        assert [ф["available"] for ф in факти] == [True, False]
        assert [ф["артикул"] for ф in факти] == ["A-S", "B-M"] and т == копія
        assert [ф["url"] for ф in факти] == ["https://shop.test/products/dress?variant=11", "https://shop.test/products/dress?variant=12"]
        assert all(ф["власник_кадру"] == ш.власник_варіанта(т, в, ф["url"]) for в, ф in zip(варіанти, факти))
    старий = dict(схема="v1", ід="ж-00001", адреса="https://shop.test/products/dress", назва="Сукня",
                  параметри=[["магазин", "shop.test", "с"]], вихід={}, категорія="1", валюта="UAH", опис=None,
                  кадри=["https://shop.test/stale.jpg"])
    т = dict(товар, images=[dict(src="https://shop.test/stale.jpg", variant_ids=[])])
    записи = ш.перебрати([старий], {"shop.test": [т]}, {"shop.test": рецепт}, {}, {}, "2026-11-02")[0]
    assert len(записи) == 2 and all(not з["кадри"] for з in записи)
    assert записи == ш.перебрати(записи, {"shop.test": [т]}, {"shop.test": рецепт}, {}, {}, "2026-11-02")[0]
    assert в.останній_номер([старий, dict(старий, ід="ж53-abcdef")]) == 1 and в.останній_номер([]) == 0
    for опції in ([dict(name="Color")], []):
        т = dict(товар, options=опції, variants=товар["variants"][:1], images=[dict(src="https://shop.test/one.jpg")])
        assert ж.факти_shopify(т, "https://shop.test")[0]["фото"] == ["https://shop.test/one.jpg"]
    print("Shopify: 6 випадків × 2 читачі; стару галерею знято в обох варіантів; один колір і відсутня опція — пройдено")

if __name__ == "__main__":
    main()
