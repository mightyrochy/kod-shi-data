"""Розмітка вибору кольору → писач → чинний читач; неоднозначний кадр лишається невідомим."""
import json
from pathlib import Path
import sys

КОРІНЬ = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / "zhnyvarka"), str(КОРІНЬ / "джерела")]
import жниварка as ж
import фід_власник_кадру as читач
from вибір_кольору import факти_вибору
from bs4 import BeautifulSoup

АДРЕСА = "https://s.ua/dress-12345/"
КНОПКА = '<button class="sku-props__value sku-props__value--pict %s" data-onevalue="%s" title="%s"></button>'


def кнопки(значення):
    """Будує блок кольору зі значеннями платформи, включно з активним."""
    return '<div class="sku-props--pict" data-id="339">Колір: ' + "".join(
        КНОПКА % ("sku-props__value--active" if н == 0 else "", к, к) for н, к in enumerate(значення)) + "</div>"


def сторінка(блок, кольори=None):
    """Прив'язує два кадри до Product, залишаючи власника варіанта розмітці вибору."""
    товар = {"@type": "Product", "productID": "12345", "name": "Сукня",
             "image": ["https://s.ua/a.jpg", "https://s.ua/b.jpg"],
             "offers": {"price": "100", "priceCurrency": "UAH", "availability": "InStock"}}
    if кольори:
        товар["hasVariant"] = [{"@type": "Product", "color": к} for к in кольори]
    return '<script type="application/ld+json">%s</script><div itemscope itemtype="https://schema.org/Product"><h1>Сукня</h1>%s</div>' % (json.dumps(товар), блок)


def доведено(html):
    """Проводить усю галерею через штатний канонічний запис і читач доказу."""
    факти = ж.факти_з_картки(html, АДРЕСА, {})
    з = ж.канонічний_запис(dict(факти, url=АДРЕСА), {"домен": "s.ua"}, "картка")
    запис = dict(url=АДРЕСА, фото=з["фото"], параметри=dict(id_магазину=з["id_магазину"], власник_кадру=з["власник_кадру"]))
    return bool(з["фото"]) and all(читач.доказ_варіанта(запис, к) for к in з["фото"])


def main():
    """Звіряє власні та сестринські сторінки, кнопки, оферти й відмови від неоднозначності."""
    свотч = '<span class="swatch" title="білий" style="background:#fff"></span>'
    свій = '<span class="product-color"><img src="/thumb.jpg" alt="білий"></span>'
    сестра = '<a class="product-color" href="%s"><img src="/black.jpg" alt="чорний"></a>'
    оферти = '<template class="offers-template-json">%s</template>'
    дерево = [{"ID": 1, "TREE": {"PROP_339": 73}}, {"ID": 2, "TREE": {"PROP_339": 80}}]
    випадки = [
        ("один свотч", сторінка(свотч), True),
        ("одна кнопка", сторінка(кнопки([73])), True),
        ("активна серед двох без прив'язки кадрів", сторінка(кнопки([73, 80])), False),
        ("TREE бачить другий колір поза кнопками", сторінка(кнопки([73]) + оферти % json.dumps(дерево)), False),
        ("TREE без фото не дає власника галереї", сторінка(кнопки([73, 80]) + оферти % json.dumps(дерево)), False),
        ("пошкоджений перелік оферт", сторінка(кнопки([73]) + оферти % "{"), False),
        ("сестра на іншій сторінці", сторінка('<div class="product-colors">' + свій + сестра % "/dress-67890/" + '</div>'), True),
        ("сестра з варіацією у запиті", сторінка(свій + сестра % (АДРЕСА + "?variant=2")), False),
        ("лише сестри без свого кольору", сторінка(сестра % "/dress-67890/"), False),
        ("колір фільтра", сторінка('<aside class="sidebar">' + свотч + '</aside>'), False),
        ("pict не кольору", сторінка(кнопки([73]).replace('Колір:', 'Розмір:')), False),
        ("кілька кольорів JSON-LD", сторінка(свотч, ["чорний", "білий"]), False),
        ("select кольорів", сторінка('<select name="color"><option value="white">білий</option><option value="black">чорний</option></select>'), False),
    ]
    for назва, html, очікувано in випадки:
        факт = bool(доведено(html))
        assert факт == очікувано, (назва, факт, очікувано)
    html = '<span class="swatch inactive" aria-checked="false" style="background:#fff"></span>'
    assert факти_вибору(BeautifulSoup(html, "lxml"), АДРЕСА)["свотчі"][0]["активний"] is False
    print("кадр_варіант_кв3_вибір_кольору: 14 перевірок — ОК")


if __name__ == "__main__":
    main()
