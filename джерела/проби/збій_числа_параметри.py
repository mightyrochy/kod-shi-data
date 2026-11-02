"""Е2: бите число лишає слід, параметри крамниці не губляться зі зміною форми."""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import паспорт_нагоди as П
import фід_верхнє as Ф

for шар in (False, True):
    об = dict(тривалість_год="бите", темп_c={}, ноги_вище_см="бите")
    п = П.паспорт_з_json(json.dumps(об), dict(темп_c=7), "", шар=шар)
    слід = п.get("не_взято_кодом", [])
    for поле in об:
        assert any("field=%s ·" % поле in с for с in слід), (поле, слід)
    assert п["темп_c"] == 7 and п.get("ноги_вище_см") is None
п = П.паспорт_з_json(json.dumps(dict(темп_c=12, ноги_вище_см=3)), {}, "", шар=True)
assert п["темп_c"] == 12 and п["ноги_вище_см"] == 3
о = dict(категорія="Пальта", назва="Пальто", параметри={"бортність": "двобортне", "x": True, "y": None})
еталон = Ф.верхні_атрибути(о)
assert еталон["бортність"] == "двобортне"
for пар in (json.dumps(о["параметри"]), repr(о["параметри"])):
    assert Ф.верхні_атрибути(dict(о, параметри=пар)) == еталон
for пар in ("{бите", "[]", "null"):
    try:
        Ф.верхні_атрибути(dict(о, параметри=пар))
    except ValueError as збій:
        assert "shop_params_" in str(збій)
    else:
        raise AssertionError("биті параметри стали звичайними атрибутами")
print("Е2: числа позначено; dict = JSON = літерал; биті параметри — збій")
