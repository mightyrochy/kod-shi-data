"""Незалежні прицільні проби #2246; аргумент — дерево коду, другий — JSON доказу."""
import gzip
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

код = Path(sys.argv[1]).resolve() / "джерела"
sys.path.insert(0, str(код))
import внутрішня_мова as В
import мовний_шар as М
import розбір_відповідей as Р
import дріт_моделі as Д

фід = ET.parse(gzip.open(код / "каталог_brief.xml.gz"))
речі = []
for короткий, слот, тип, колір in [("ж-00001", "сукня", "сукня", "білий"),
                                 ("ж-08686", "взуття", "чоботи", "чорний")]:
    е = next(е for е in фід.iter("offer") if е.get("id") == короткий)
    домен = urlparse(е.findtext("url")).hostname
    речі.append(dict(id=короткий + "@" + домен, слот=слот, тип=тип, колір=колір,
                     назва=е.findtext("name"), фото=е.findall("picture")[2 if короткий == "ж-08686" else 0].text,
                     ціна=float(е.findtext("price")), url=е.findtext("url")))

# Окрема межа: вхідний переклад коментаря до речей каталогу.
коментар = json.loads(М.мова(dict(вхід="verdict_comment", слова="Хочу інше взуття.", речі=речі)))["промпт"]
витік_коментаря = dict(назв=sum(р["назва"] in коментар for р in речі),
                      повних_id=sum(р["id"] in коментар for р in речі))
if "--коментар" in sys.argv:
    print("Вхідний переклад коментаря:", json.dumps(витік_коментаря, ensure_ascii=False))
    Path(sys.argv[2]).write_text(json.dumps(dict(коментар=витік_коментаря,
        промпт_коментаря=коментар), ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0)

відповідь = dict(version="1", text="Біла сукня й чорні чоботи. Додай червону сумку.",
    about_items=[dict(n="x2", text="Чорні чоботи."), dict(n="x1", text="Біла сукня."),
                 dict(n="x3", text="Червона сумка.")],
    named=[dict(n="x1", what="сукня"), dict(n="x2", what="чоботи"),
           dict(n="x3", what="червона сумка")], how_to_wear=["Візьми червону сумку."])
розбір = Р.опис_відповідь_з_json(json.dumps(відповідь, ensure_ascii=False),
    каталог=речі, склад=[р["id"] for р in речі])
assert [х["id"] for х in розбір["про_речі"]] == [р["id"] for р in речі]
assert not розбір["помилки"], розбір["помилки"]
assert len(розбір["названо_поза_образом"]) >= 1
assert "Червона сумка." not in [х["текст"] for х in розбір["про_речі"]]
неповний = Р.опис_відповідь_з_json(json.dumps(dict(version="1", text="Сукня.",
    about_items=[dict(n="x1", text="Біла сукня.")], named=[dict(n="x1", what="сукня")])),
    каталог=речі, склад=[р["id"] for р in речі])
assert неповний["не_описано"] == ["x2"]
assert all(р["id"] not in неповний["повторний_виклик"] for р in речі)

заяви = [В.заява("scarf_size_unknown", item=В.річ_заяви(р), item_id=р["id"]) for р in речі]
п = М.промпт_повідомлень(М.розмітити_повідомлення({"к": В.повідомлення("card_unchecked", *заяви)}))
assert all(р["id"] not in п and р["назва"] not in п for р in речі)
вхід = {"образ": {"речі": [dict(н="x1", слот="взуття", тип="чоботи", фото_номери=[1])]},
    "заміна_запасні": {"річ": "x1", "чому": "kind", "запасні": [
        dict(н="x2", слот="взуття", тип="лофери", фото_номери=[2])]}}
запасна = Д.опис(вхід)["swap_spares"]["spares"][0]
assert (запасна["kind"], запасна["type"]) == ("shoes", "loafers")
assert "loafers" in Р.підписи_кадрів(вхід, 2)[1]

print("Розбір: порядок складу збережено; чужий абзац знято; повтор без пулу: x2.")
print("Повідомлення: назв 0, повних id 0; запасна й підпис: shoes / loafers.")
print("Окремий вхідний переклад коментаря:", json.dumps(витік_коментаря, ensure_ascii=False))
Path(sys.argv[2]).write_text(json.dumps(dict(речі=речі, розбір=розбір,
    коментар=витік_коментаря, промпт_коментаря=коментар), ensure_ascii=False, indent=2), encoding="utf-8")
