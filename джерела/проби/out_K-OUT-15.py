# -*- coding: utf-8 -*-
"""K-OUT-15 (fill power без грамажу — ВЕТО) — БЕЗ ВХОДУ, і тепер це названо.

Емітент живий (`fp_без_грамажу` ставить `feed.верхні_атрибути`), але fill power
оголошено в НУЛІ з 618 речей слота «верхній_шар» (грамаж — у 8). Правило стало
УМОВНИМ записом `outer.БЕЗ_ВХОДУ` поруч із K-OUT-16 і K-OUT-47: щойно магазин
оголосить число, черга на вхід зникає, а вето оживає."""
import sys, pathlib, json
_КОРІНЬ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_КОРІНЬ))
import feed as Ф, bridge as B, outer as OU

вх = json.load(open(_КОРІНЬ / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml")
вх["гілка"] = 0
вх["сценарій"].update(темп_c=-5, опади="ні")
з = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
вш = [c for c in кат.values() if c.get("слот") == "верхній_шар"]
print("речей слота «верхній_шар»: %d · із fill_power: %d · із грамажем: %d"
      % (len(вш), sum(1 for c in вш if c.get("fill_power")), sum(1 for c in вш if c.get("грамаж_г"))))
к = з["кандидати"]
взяти = lambda сл, ум: next((кат[r["id"]] for r in (к.get(сл) or [])
                             if r["id"] in кат and ум(кат[r["id"]])), None)
пуховик = взяти("верхній_шар", lambda c: c.get("тип_верхнього") == "пуховик")
ід = [r["id"] for r in (пуховик, взяти("сукня", lambda c: True),
                        взяти("взуття", lambda c: True)) if r]
вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
пит = [z for z in (вм.get("питання") or []) if z.get("правило") == "K-OUT-15"]
print("пуховик:", пуховик["назва"][:52], "· fill_power", пуховик.get("fill_power"))
print("K-OUT-15 у черзі на вхід:", (пит[0]["суть"] if пит else "НЕМА"))
# той самий емітент на оголошеному fill power без ваги — вето говорить
з15 = OU.теплові_знахідки([dict(пуховик, слот="верхній_шар", fill_power=900,
                                fp_без_грамажу=True)], темп_c=-5)
в15 = next((z for z in з15 if z["правило"] == "K-OUT-15"), None)
print("той самий емітент на 900 FP без грамажу: %s %s %.2f"
      % (в15["правило"], в15["сила"], в15["сила_нп"]))
print("черга зникає, щойно число прийшло:",
      "K-OUT-15" not in [z["правило"] for z in
                         OU.без_входу([dict(пуховик, слот="верхній_шар", fill_power=900)])])
