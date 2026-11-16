# -*- coding: utf-8 -*-
"""Е3-з5: діагнози вузла й повторів ДО/ПІСЛЯ, без неперевірених замін; аргумент — SHA бази."""
import copy, importlib, pathlib, subprocess, sys, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))


def стара(імя):
    """Завантажує модуль бази без копії робочого дерева."""
    мод = types.ModuleType(імя)
    exec(subprocess.check_output(["git", "show", sys.argv[1] + ":джерела/" + імя + ".py"]).decode("utf-8"), мод.__dict__)
    return мод


if __name__ == "__main__":
    до, після = стара("graph"), importlib.import_module("graph")
    слоти = sorted(після.СЛОТИ)
    випадків = порад = 0
    for вузол in (слоти[0], sorted(після.ЗОНИ_ТІЛА)[0], "образ"):
        for сусід in (None, слоти[1]):
            в = dict(вузол=вузол, напруга=1.5, ребер=2)
            г = dict(ребра=[dict(вузли=[вузол] + ([сусід] if сусід else []), напруга=1.5, правило="K-FIT-03")])
            а, б = до.заяви_вузла(в, г), після.заяви_вузла(в, г)
            assert б == а[:1] and б[0]["code"] == "tension_knot", (а, б)
            порад += len(а) - len(б)
            випадків += 1
    assert після.заяви_вузла(None, {}) is None
    до, після = стара("вердикт_моделі"), importlib.import_module("вердикт_моделі")
    for кількість, власна, слоти_є in ((2, False, True), (6, False, True), (6, True, True), (6, False, False)):
        об = [dict(ід="о%d" % i, речі_н=[1, i + 2], слоти_н=({"1": "верх", str(i + 2): "низ"} if слоти_є else {}),
                   власні_н=([1] if власна else []), ід_за_номером={"1": "верх-1"}) for i in range(кількість)]
        а, б = до.різноманітність(copy.deepcopy(об)), після.різноманітність(copy.deepcopy(об))
        for i, з in enumerate(((а or {}).get("різноманітність") or {}).get("заяви", [])):
            if з["code"] == "variety_kind_one_item":
                з["code"] = "variety_shared_item"
                з.pop("key")
                б["різноманітність"]["заяви"][i].pop("key")
                порад += 1
        assert а == б, (а, б)
        випадків += 1
    print("Діагноз і виміри збережено: %d/%d; неперевірених порад ДО %d → ПІСЛЯ 0" % (випадків, випадків, порад))
