"""Реальні речі для огляду #3962; оголошений фокус дає продуктовий писач palettes."""
import json
import pathlib
import sys
sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / "джерела"))
import colorspace as КС
import outfit as О
import palettes as П
import колір_хрома as Х
import суд_від_моделі as С

кат = json.loads(pathlib.Path(sys.argv[2]).read_text(encoding="utf-8"))
мір = [x for x in кат if x.get("колір_hex_фото") and x.get("lab") and x.get("колір_тип") == "вимір"]
нейтр = [next(x for x in мір if x["слот"] == с and КС.lch(tuple(x["lab"]))[1] < 6)
         for с in ("верх", "низ", "взуття")]
def входи(склад):
    речі = [dict(id=x["id"], слот=x["слот"], hex=x["колір_hex_фото"], lab=tuple(x["lab"]), колір_тип="вимір") for x in склад]
    ел = О.елементи(речі)
    for е in ел:
        п = {"верх": .3, "низ": .3, "взуття": .03}.get(е["слот"], .02)
        е.update(площа=п, площа_межі=(п, п), джерело_площі="маски")
    return речі, ел
def сироти(зн):
    return [з for з in зн if any(а.get("code") == "accent_orphan" for а in з.get("заяви", []))]
зразки = []
for слот in ("сумка", "шарф"):
    for х in мір:
        if х["слот"] != слот or КС.lch(tuple(х["lab"]))[1] < 20:
            continue
        склад = нейтр + [х]
        речі, ел = входи(склад)
        if not сироти(Х.відлуння(ел, None)):
            continue
        фокус = П.слоти_акценту_схеми(речі, {слот: {"роль": "акцент"}})
        assert фокус == {слот}
        поля = ("id", "назва", "слот", "ціна", "валюта", "url", "фото", "фото_усі", "колір_ім", "колір_hex_фото")
        зразки.append(dict(акцент=х["id"], фокус=sorted(фокус),
            речі=[{к: x[к] for к in поля if к in x} for x in склад],
            review=сироти(Х.відлуння(ел, фокус)),
            суд_моделі=сироти(С.бюджет_і_відлуння(речі, None, {r["id"]: r for r in речі}, фокус))))
        break
assert len(зразки) == 2
print(json.dumps(зразки, ensure_ascii=False, indent=2))
