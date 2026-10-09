# -*- coding: utf-8 -*-
"""Проба (рядок 3161а): −15 °C, сніг, пішки (живі 12, К7п) — рука 1, заглушка, каталог_повний. Друкує: (1) пул —
скільки шапок/шарфів/верхніх шарів і скільки з них теплого волокна, скільки знято `fabric_off_temperature`;
(2) чи стилістка дістає опору `frost_layers_and_cold_accessories` у пакеті; (3) суд образу блуза + джинси + пальто
+ чоботи + сумка (як рука 1 живцем): знахідки K-WEA-01 з регістром і `сила_нп`. Моделі не кличе.
Запуск: cd джерела && python3 проби/шари_мороз_3161.py"""
import json, os, sys, collections
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, пакет_моделі as PL, суд_погода as СП, верхнє_погода as ВП  # noqa: E401
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), каталог=Ф.каталог_на_диску("каталог_повний.xml"), гілка=0)
вх["сценарій"] = dict(вх["сценарій"], темп_c=-15, опади="сніг")
вх["випадок"] = "робочий день, пішки, −15 °C, сніг"
B.виклик("запити", json.dumps(вх, ensure_ascii=False))
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
пак = [p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")][0]
п = пак["кандидати"]
ТЕПЛІ = {"вовна", "кашемір", "альпака", "ангора", "мохер", "вʼязане"}
for сл in ("головний_убір", "шарф", "верхній_шар", "рукавиці"):
    знято = collections.Counter(PL._жорстке_відсічення(r, -15) for r in кат.values() if r.get("слот") == сл)
    у_пулі = [кат.get(r["id"], r) for r in п.get(сл) or []]
    print("%-14s каталог %3d · знято тканиною %3d · у пулі %2d · з них теплого волокна %2d" % (
        сл, sum(знято.values()), знято["fabric_off_temperature"], len(у_пулі),
        sum(r.get("волокно") in ТЕПЛІ for r in у_пулі)))
print("верхніх шарів із міткою «тепло» (пальто, пуховик, шуба…) у пулі:",
      sum((ВП.ТЕПЛОВІ_ФУНКЦІЇ.get(r.get("тип_верхнього") or r.get("тип")) or ("",))[0] == "тепло" for r in СП.пальта_пулу(п)))
шлях = [к for к, v in пак.items() if "frost_layers_and_cold_accessories" in json.dumps(v, ensure_ascii=False, default=str)]
print("опора стилістці frost_layers_and_cold_accessories у пакеті, поля:", шлях or "НЕМА")
ід = ["ж-01851@onebyone.ua", "ж-06937@cooshwear.com", "ж-12200@musthave.ua", "ж-10673@cooshwear.com", "ж-08148@welfare.ua"]
for н, дод in (("без шапки й шарфа", []), ("+ вовняна шапка й кашеміровий шарф", ["ж-07712@rito.ua", "ж-08338@morandi.ua"])):
    о = ((json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід + дод), ensure_ascii=False))).get("вердикт") or {})
         .get("образи") or [{}])[0]
    print("суд, %s:" % н)
    for z in о.get("знахідки") or []:
        if z.get("правило") in ("K-WEA-01", "K-MAT-03"):
            print("   %s %s/%s %.2f: %s" % (z["правило"], z["сила"], z["регістр"], z["сила_нп"],
                  [x.get("code") for x in z.get("заяви") or []]))
