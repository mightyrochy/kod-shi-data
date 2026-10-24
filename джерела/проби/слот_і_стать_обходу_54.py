"""Обхід: слот для групування — лише з розбору вже відомої речі (url → id@магазин); нова річ — «невідомо». Стать «чоловіче» — лише з коду."""
import json, os, sys
from pathlib import Path
корінь = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(корінь / "zhnyvarka"), str(корінь / "джерела")]
os.environ["ROZBIR_KODY"] = str(корінь / "аудит/розбір_каталогу/404_а1/розбір.json")
import жниварка as Ж, фід_розбір as ФР, каталог_коди as КК
розбір = json.load(open(os.environ["ROZBIR_KODY"], encoding="utf-8")); розбір.pop("причини", None)
ключі = list(розбір)[:6]
import фід_каталог as ФК; ФК.каталог_на_диску = lambda *а, **к: "каталог_повний.xml"
ФР.читати_yml = lambda шлях, показ=True: ([dict(id=к, url="https://m.test/catalog/known-%d" % і) for і, к in enumerate(ключі)], {})
нові = ["https://m.test/new/n%d" % і for і in range(6)]
відомі = Ж.відомі_слоти()
кандидати = [dict(url=u, факти=None) for u in нові + list(відомі)]            # нові стоять першими у вхідному порядку
порядок = [к["url"] in відомі for к in Ж.розподілити(кандидати, len(кандидати) - 1)]
частка_черги, частка_нових = порядок.count(False) / len(порядок), len(нові) / len(кандидати)
assert порядок[0] and abs(частка_черги - частка_нових) <= 1 / len(порядок), порядок     # група відомих першою, нові — своєю часткою
assert not Ж.відомі_слоти().get(нові[0]) and "m.test/catalog/zhinocha-suknya" not in " ".join(відомі)
рід = lambda а: Ж.застосувати_розбір(dict(id="ж-1", магазин="m", url="", слот=None, стать="невідомо"))["стать"]
for код, чекаю in (("men", "чоловіче"), ("unisex", "унісекс"), (None, "невідомо"), ("women", "жіноче")):
    КК.поля = lambda ід, тека=None, к=код: {"audience": к, "item_type": "dress"} if к else {"item_type": "dress"}
    assert рід(код) == чекаю, (код, рід(код))
print("обхід: слот відомий для %d з %d url (нові %d — «невідомо»: частка в черзі %.2f, частка нових %.2f); стать: лише men → чоловіче, unisex/нема коду лишаються" % (len(відомі), len(кандидати), len(нові), частка_черги, частка_нових))
