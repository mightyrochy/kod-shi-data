"""Е3-заміна-з-перевіркою, частина «погода»: ремонти погодного судді ДО → ПІСЛЯ, без моделі.
Виклик: python3 проби/заміна_погода_складова.py <джерела> <вихід.json.gz> [<вихід ДО.json.gz>]
Входи — `е3_погода_набори` (повний каталог × смуги, TMP — кеш) і ручні: можливий дощ, максі в дощ, шар ошатності."""
import collections, gzip, json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve())); sys.path.insert(1, str(pathlib.Path(__file__).parent))
import суд_погода as П, outfit as О
from е3_погода_набори import набори
р = [dict(id="сукня", слот="сукня", hex="#202020", довжина_рівень="максі", тип="сукня"),
     dict(id="туфлі", слот="взуття", hex="#202020", тип="туфлі")]
Е = О.елементи(р, стан="надворі")
ручні = [("можливий_дощ", "погода", [Е], dict(речі=р, смуга_погоди="mild", опади="можливий_дощ", стан="надворі")),
         ("максі_дощ", "погода", [Е], dict(речі=р, смуга_погоди="mild", опади="дощ", стан="надворі")),
         ("шар_ошатності", "погода", [Е], dict(речі=р, смуга_погоди="mild", стан="надворі", шар_ошатності=dict(
             верхній_шар=dict(порожньо=True, смуга=(6, 8), було=3, типи_знятих={"пальто": 3}))))]
вих = []
for назва, ф, a, kw in list(набори()) + ручні:
    for з in getattr(П, ф)(*a, **kw):
        вих.append([назва, з["правило"], з.get("суть"), з.get("сила_нп"), з.get("ремонт"),
                    [x.get("code") for x in з.get("ремонт_заяви") or []], [x.get("code") for x in з.get("заяви") or []]])
with gzip.open(sys.argv[2], "wt", encoding="utf-8") as ф:
    json.dump(вих, ф, ensure_ascii=False)
print("знахідок", len(вих), "правил", dict(collections.Counter(в[1] for в in вих)))
if len(sys.argv) > 3:
    до = json.load(gzip.open(sys.argv[3], "rt", encoding="utf-8"))
    print("знахідок ДО", len(до), "· ті самі назва/правило/сила:", [в[:2] + [в[3]] for в in до] == [в[:2] + [в[3]] for в in вих])
    зміни = collections.Counter()
    for д, п in zip(до, вих):
        for і, поле in ((2, "суть"), (4, "ремонт"), (5, "ремонт_заяви"), (6, "заяви")):
            if д[і] != п[і]:
                зміни[(д[1], поле, json.dumps(д[і], ensure_ascii=False)[:90], json.dumps(п[і], ensure_ascii=False)[:90])] += 1
    for к, n in sorted(зміни.items()):
        print(n, *к, sep=" · ")
    print("кодів ремонту-заміни ПІСЛЯ:", sum(1 for в in вих for к in в[5] if к in (
        "impregnate_or_smooth_or_textile", "smooth_protected_leather_or_rubber_or_treat", "warm_layer_under_or_instead_of_trench",
        "build_from_coat_or_colour_on_top", "rain_outer_layer_over_look")))
