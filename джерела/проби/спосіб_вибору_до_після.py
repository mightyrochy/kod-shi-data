# -*- coding: utf-8 -*-
"""БЕКЛОГ 741: спосіб уважного вибору — латинські коди. Той самий вхід → той самий вибір ДО/ПІСЛЯ.
Прогін: python3 проби/спосіб_вибору_до_після.py [способи через кому; без аргументу — «до»: список,оцінка,турнір]
ПІСЛЯ: list,assess,tournament; старі значення мають читатися псевдонімами (останній рядок)."""
import hashlib, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, уважний_вибір as УВ
С = (sys.argv[1] if len(sys.argv) > 1 else "список,оцінка,турнір").split(",")
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=7, каталог=Ф.каталог_на_диску("каталог_повний.xml"))))
пак = next(p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати"))
def заглушка(т):
    о = json.loads(т)
    if "items" in о: return json.dumps({"version": "1", "ratings": {x["n"]: "fits" if len(str(x["n"])) % 2 else "no" for р in о["items"].values() for x in р}})
    if "groups" in о: return json.dumps({"version": "1", "winners": {г: [x["n"] for x in р[:2]] for г, р in о["groups"].items()}})
    return json.dumps({"версія": "1", "образи": []})
for с in С:
    вр, обрані = УВ.прогнати(с, пак, заглушка, 7)
    х = hashlib.sha1(json.dumps([обрані, вр.get("текст_складання"), вр.get("промпт_фіналу")], ensure_ascii=False, default=str).encode()).hexdigest()[:12]
    print("спосіб №%d: обрано %d речей · хеш вибору %s · код у відповіді %r" % (С.index(с) + 1, len(обрані), х, вр.get("спосіб")))
print("ТИПОВИЙ=%r · СПОСОБИ=%r · старі значення читаються: %s" % (УВ.ТИПОВИЙ, УВ.СПОСОБИ, [УВ.спосіб(з) for з in ("список", "оцінка", "турнір", "rate", "TOURNAMENT", "", None, "?")]))
