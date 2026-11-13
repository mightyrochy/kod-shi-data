"""Сторінка «картка»: власник кадру — доказ для одноколірної, «невідомо» для кількох кольорів. Без мережі й аргументів."""
import json, sys
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka")]
import жниварка as ж, фід_власник_кадру as в

def сторінка(варіанти="", свотчі=""):
    """HTML з JSON-LD Product (sku 12345), двома кадрами, за потреби варіантами й свотчами."""
    ld = {"@type": "Product", "name": "Сукня", "sku": "12345", "image": ["https://s.ua/a.jpg", "https://s.ua/b.jpg"],
          "offers": {"price": "100", "priceCurrency": "UAH", "availability": "InStock"}}
    if варіанти: ld["hasVariant"] = [{"@type": "Product", "color": к, "offers": {"availability": "InStock"}} for к in варіанти.split()]
    return '<html><body><script type="application/ld+json">%s</script><div itemscope itemtype="https://schema.org/Product"><h1>Сукня</h1>%s</div></body></html>' % (json.dumps(ld), свотчі)

def доказ(html):
    """Факти сторінки → запис → доказ кадру читачем (джерело картки додано в таблицю лише тут)."""
    url = "https://s.ua/dress-12345/"
    з = ж.канонічний_запис(dict(ж.факти_з_картки(html, url), url=url), {"домен": "s.ua"}, "картка")
    return json.loads(з["власник_кадру"]), в.доказ_варіанта(dict(url=url, фото=з["фото"], параметри=dict(id_магазину=з["id_магазину"], власник_кадру=з["власник_кадру"])), з["фото"][0])

в.ДЖЕРЕЛА_ДОКАЗУ["картка:один_колір"] = "картка"
сві = '<span class="swatch" title="%s" style="background:%s"></span>'
одноколірна, два_варіанти, два_свотчі = доказ(сторінка()), доказ(сторінка("чорний білий")), доказ(сторінка("", сві % ("Чорний", "#000") + сві % ("Білий", "#fff")))
assert одноколірна[0]["джерело"] == "картка:один_колір" and одноколірна[1]["варіант"] == "картка:12345:товар", одноколірна
assert доказ(сторінка("чорний"))[1] is not None and два_варіанти == ("невідомо", None) and два_свотчі == ("невідомо", None)
print("кадр_варіант_кв2_одноколірна: ОК")
