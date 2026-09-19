# -*- coding: utf-8 -*-
"""K-PER-00 («flattering» — функція мети; мінімальний перелік: conventional ·
fashion_forward · comfort_first · context_optimal). ДО ПРАВКИ: `реєстр_правил.INTENT`
знав три члени + statement; comfort_first і context_optimal діставали conventional
із попередженням «модулю невідомий». ПІСЛЯ: обидва — члени з лексиконом, і той
самий пул/суд під ними інший. Проба друкує один прогін `запити` (стенд_вх ×
каталог_brief, гілка 0) під трьома намірами: пул, взуття від стелі каблука,
підлога інтересу, рахункові ліміти, допуск формальності, і знахідки суду."""
import sys, pathlib, json
_КОРІНЬ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_КОРІНЬ))
import feed as Ф, bridge as B, реєстр_правил as Р, суд_образу as С, аксесуари_реєстр as АР
import outfit as O, colorspace as cs

вх = json.load(open(_КОРІНЬ / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_brief.xml"); вх["гілка"] = 0
стеля = АР.C["каблук_смуга_низ"]
E3 = O.елементи([dict(id=і, слот=с, hex=h, lab=cs.hx(h)) for і, с, h in
                 [("a", "верх", "#9a9a9a"), ("b", "низ", "#7a7a7a"), ("c", "взуття", "#5a5a5a")]], "як є")
пул = {}
for намір in ("conventional", "comfort_first", "context_optimal"):
    л = Р._намір(намір)
    з = json.loads(B.виклик("запити", json.dumps(dict(вх, намір=намір), ensure_ascii=False)))
    кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
    взут = [кат.get(x.get("id"), x) for x in (з.get("кандидати") or {}).get("взуття") or []]
    високі = [x for x in взут if x.get("каблук_см") is not None and float(x["каблук_см"]) >= стеля]
    суд = С.намір_комфорту(взут, намір)
    підл = С.підлога_інтересу_проактивно(E3, намір)[0]["суть"].split("при ")[1]
    print("%-16s пул %3d · взуття %2d, з них каблук ≥%g см: %2d · %s · рахункові %.0f · "
          "допуск формальності %s · знахідок K-PER-00 у суді: %d (hard %d)"
          % (намір, з.get("пул_речей") or 0, len(взут), стеля, len(високі), підл, л["рахункові"],
             Р.C[л["форм_допуск"]] if л["форм_допуск"] else Р.C["форм_розкид_макс"],
             len(суд), sum(1 for z in суд if z["сила"] == "hard")))
    assert not л["підпис"], "член K-PER-00 не може бути «модулю невідомий»: %s" % л["підпис"]
    пул[намір] = (з.get("пул_речей") or 0, len(високі), високі)
суд = С.намір_комфорту(пул["conventional"][2], "comfort_first")   # образ від моделі повернув каблук
print("ті самі %d пари під comfort_first у суді: %d знахідок K-PER-00, hard %d, регістр %s"
      % (len(суд), len(суд), sum(z["сила"] == "hard" for z in суд), sorted({z["регістр"] for z in суд})))
assert пул["comfort_first"][1] == 0 < пул["conventional"][1], "стеля каблука мусить діяти в пулі"
assert пул["context_optimal"][0] <= пул["conventional"][0], "допуск 1 крок не може розширити пул"
