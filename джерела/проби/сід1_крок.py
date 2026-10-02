# -*- coding: utf-8 -*-
"""СІД-1 (рядок 221): кроки порядку запиту — які значення їдуть у журнал і чи тримається перемішування.
Прогін: python3 проби/сід1_крок.py [8 назв кроків через кому: складання,ремонт,повнота,вибір,оцінка,турнір,склад,фінал]
ДО — без аргументу (колишні кириличні); ПІСЛЯ — латинські коди в тому ж порядку. Хеші мають збігтися рядок у рядок."""
import hashlib, json, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, порядок_запиту as ПЗ, уважний_вибір as УВ
БУЛО = "складання,ремонт,повнота,вибір,оцінка,турнір,склад,фінал".split(",")
НАЗВИ = (sys.argv[1].split(",") if len(sys.argv) > 1 else БУЛО)
бачено, _запис = [], ПЗ.запис
def запис(сід, крок, *а, **к): бачено.append(крок); return _запис(сід, крок, *а, **к)
ПЗ.запис = запис
B.виклик("запити", json.dumps(dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=7, каталог=Ф.каталог_на_диску("каталог_повний.xml"))))
пак = next(p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати"))
def заглушка(т):
    о = json.loads(т)
    if "items" in о: return json.dumps({"version": "1", "ratings": {x["n"]: "fits" for р in о["items"].values() for x in р}})
    if "groups" in о: return json.dumps({"version": "1", "winners": {г: [x["n"] for x in р[:2]] for г, р in о["groups"].items()}})
    return json.dumps({"версія": "1", "образи": []})
for с in ("assess", "tournament"): УВ.прогнати(с, пак, заглушка, 7)
уник = sorted(set(бачено), key=бачено.index)
print("журнал (проба): кроки %s · кирилиця в кроці: %d з %d" % (уник, sum(1 for к in уник if re.search("[а-яіїєґ]", к, re.I)), len(уник)))
ряд = list(range(40))
for к in НАЗВИ:
    ід = [ПЗ.сід_запиту(с, к, *ще) for с in (1, 2, 3) for ще in ((), (0, 0), (1, 2))]
    пм = ["".join(map(str, ПЗ.перемішати(ряд, ПЗ.сід_запиту(с, к), "x"))) for с in (1, 2, 3)]
    print("крок №%d: сіди %s · перемішування %s" % (НАЗВИ.index(к) + 1, hashlib.sha1(str(ід).encode()).hexdigest()[:10],
          [hashlib.sha1(x.encode()).hexdigest()[:8] for x in пм]))
