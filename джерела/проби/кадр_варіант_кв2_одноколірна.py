"""Сторінка «картка»: власник кадру — доказ лише коли сторінка свідчить про один колір, інакше «невідомо». Без мережі й аргументів."""
import json, sys
from pathlib import Path
КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "джерела"), str(КОРІНЬ / "zhnyvarka")]
import жниварка as ж, фід_власник_кадру as в

def сторінка(колір="", варіанти="", блок=""):
    """HTML з JSON-LD Product (кольором і варіантами за потреби), двома кадрами й блоком вибору кольору."""
    ld = {"@type": "Product", "name": "Сукня", "image": ["https://s.ua/a.jpg", "https://s.ua/b.jpg"],
          "offers": {"price": "100", "priceCurrency": "UAH", "availability": "InStock"}}
    if колір: ld["color"] = колір
    if варіанти: ld["hasVariant"] = [{"@type": "Product", "color": к, "offers": {"availability": "InStock"}} for к in варіанти.split()]
    return '<script type="application/ld+json">%s</script><div itemscope itemtype="https://schema.org/Product"><h1>Сукня</h1>%s</div>' % (json.dumps(ld), блок)

def доказ(html):
    """Факти сторінки → запис → доказ кадру читачем."""
    url = "https://s.ua/dress-12345/"
    з = ж.канонічний_запис(dict(ж.факти_з_картки(html, url), url=url), {"домен": "s.ua"}, "картка")
    return json.loads(з["власник_кадру"]) != "невідомо", в.доказ_варіанта(dict(url=url, фото=з["фото"], параметри=dict(id_магазину=з["id_магазину"], власник_кадру=з["власник_кадру"])), з["фото"][0]) is not None

сві = '<span class="swatch" title="%s" style="background:%s"></span>'
вибір = '<select name="attribute_pa_color"><option value="">Оберіть</option>%s</select>'
опц = "".join('<option value="%s">%s</option>' % (к, к) for к in ("black", "white", "red"))
посилання = "".join('<a href="/dress-12345/?attribute_pa_color=%s">x</a>' % к for к in ("black", "white"))
випадки = {"колір у JSON-LD": (сторінка("чорний"), True), "один варіант": (сторінка("", "чорний"), True),
           "нема свідчень": (сторінка(), False), "два варіанти": (сторінка("", "чорний білий"), False),
           "два свотчі": (сторінка("чорний", "", сві % ("Чорний", "#000") + сві % ("Білий", "#fff")), False),
           "Woo: три кольори в select": (сторінка("", "", вибір % опц), False), "два кольори в посиланнях": (сторінка("чорний", "", посилання), False),
           "Woo: один колір у select": (сторінка("", "", вибір % '<option value="black">black</option>'), True)}
for ім, (html, чекаю) in випадки.items():
    assert доказ(html) == (чекаю, чекаю), (ім, доказ(html))
print("кадр_варіант_кв2_одноколірна: ОК")
