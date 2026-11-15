"""#3962: вимір і вікно слова, порожній/чужий/оголошений фокус; без моделі й мережі."""
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / "джерела"))
import colorspace as КС
import outfit as О
import колір_хрома as Х
import суд_від_моделі as С
import внутрішня_мова as М

після = hasattr(Х, "акцент_у_оголошеному_фокусі")
результат = []
for слот in ("сумка", "шарф"):
    for тип in ("вимір", "інтервал"):
        річ = dict(id="контроль", слот=слот, площа=.02, площа_межі=(.02, .02), джерело_площі="маски")
        if тип == "вимір":
            річ.update(hex="#e04000", lab=tuple(КС.hx("#e04000")), колір_тип=тип)
        else:
            річ.update(колір_тип=тип, колір_не_вимір=dict(свідок="слово", слово="червоний",
                вікно=[45, 55, 60, 70, [20, 30]]))
        е = О.елементи([річ])
        е[0].update(площа=.02, площа_межі=(.02, .02), джерело_площі="маски")
        for фокус in (None, [], ["взуття"], [слот]):
            вироки = [Х.відлуння(е, фокус), С.бюджет_і_відлуння([річ], None, {річ["id"]: річ}, фокус)]
            сироти = [[з for з in зн if any(а.get("code") == "accent_orphan" for а in з.get("заяви", []))]
                      for зн in вироки]
            оч = [not (після and фокус == [слот]), фокус != [слот]]
            assert [bool(с) for с in сироти] == оч, (слот, тип, фокус, вироки)
            assert all(з is not None for зн in вироки for з in зн)
            результат.append(dict(слот=слот, тип=тип, фокус=фокус, сиріт=[len(с) for с in сироти]))
assert set(М.ХТО_ОГОЛОСИВ) == {"scheme", "her_wish"}
try:
    М.заява("loud_elements_over_budget", count=3, ceiling=2, keep=["bag"], quiet=["top"], keep_by=["zone"])
except ValueError:
    pass
else:
    raise AssertionError("zone не відкинуто")
print(json.dumps(dict(після=після, випадків=len(результат), результати=результат,
                     keep_by=М.ХТО_ОГОЛОСИВ, zone="відкинуто"), ensure_ascii=False, indent=2))
