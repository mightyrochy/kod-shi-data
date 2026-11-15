"""Id власної сторінки проходить до доказу; рекомендації, неоднозначність і відстеження — ні."""
import json, sys
from pathlib import Path
sys.path[:0] = [str(Path(__file__).resolve().parents[2] / т) for т in ("zhnyvarka", "джерела")]
import жниварка as ж, фід_власник_кадру as ч

def перевірити(назва, ід, ld=None, dom="", дані=None, запит="", доведено=None):
    """Ганяє сторінку через писача, канонічний запис і незмінений читач кожного кадру."""
    адреса = "https://s.ua/product/dress/" + запит
    товар = dict({"@type": "Product", "name": "Сукня", "color": "чорний", "image": "https://s.ua/dress.jpg"}, **(ld or {}))
    html = '<script type="application/ld+json">%s</script>' % json.dumps(товар)
    if дані is not None: html += '<script type="application/json">%s</script>' % json.dumps(дані)
    html += '<main itemscope itemtype="https://schema.org/Product"><h1>Сукня</h1>%s</main>' % dom
    ф = ж.факти_з_картки(html, адреса)
    assert ф["id_магазину"] == ід, (назва, ф["id_магазину"])
    з = ж.канонічний_запис(dict(ф, url=адреса), {"домен": "s.ua"}, "картка")
    запис = dict(url=адреса, фото=з["фото"], параметри=з)
    прийнято = bool(з["фото"]) and all(ч.доказ_варіанта(запис, к) for к in з["фото"])
    assert прийнято == (bool(ід) if доведено is None else доведено), назва

перевірити("JSON-LD productID", "42", {"productID": 42, "sku": "S-42"})
перевірити("JSON-LD sku", "S-42", {"sku": "S-42"})
перевірити("форма", "42", dom='<input name="product_id" value="42"><input name="product_id" value="42">')
перевірити("data", "42", dom='<button data-product-id="42">Купити</button>')
перевірити("microdata", "S-42", dom='<meta itemprop="sku" content="S-42">')
перевірити("вкладений чужий Product", None, dom='<aside itemscope itemtype="https://schema.org/Product"><meta itemprop="sku" content="чужий"></aside>')
перевірити("конфлікт", None, dom='<input name="product_id" value="42"><input name="product_id" value="43">')
перевірити("рекомендація LD", None, {"isRelatedTo": {"@type": "Product", "sku": "чужий", "url": "https://s.ua/other/"}})
перевірити("JSON платформи", "42", дані=[{"__typename": "Product", "slug": "other", "id": 43}, {"__typename": "Product", "slug": "dress", "id": 42}])
перевірити("чужий домен JSON", None, дані={"__typename": "Product", "slug": "dress", "url": "https://other.ua/product/dress/", "id": 42})
перевірити("sc_content", None, запит="?sc_content=37254_r2979v3594", доведено=False)
print("кадр_варіант_кв1_id_сторінки: 11 випадків ОК")
