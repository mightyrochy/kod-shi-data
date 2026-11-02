"""Е2: непрочитане правило не повертає звичайне «не відсікати» жодному читачеві."""
import pathlib, sys
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import profile as П
import пакет_моделі as М

р = dict(id="broken", слот="взуття", тип="сандалі", назва="Пара", ціна=100, каблук_см="бите")
for читач in (lambda: П.сенсорний_збіг("підбори", р),
              lambda: П.жорстке_ні_фільтр([р], ["підбори"]),
              lambda: М.жорстке_відсічення(р, вето={"типи": ["підбори"]})):
    try:
        читач()
    except ValueError as збій:
        assert "sensory_limit_unreadable" in str(збій)
    else:
        raise AssertionError("бита висота пройшла сенсорну межу")
assert П.сенсорний_збіг("підбори", dict(р, тип="човники"))
assert not П.сенсорний_збіг("підбори", dict(р, каблук_см=0))
р = dict(р, слот="верх", тип="shirt", каблук_см=0)
for см in (["бите", 25], [], [5], "xx"):
    try:
        М.жорстке_відсічення(dict(р, сезон_тканини=см), темп_c=15)
    except ValueError as збій:
        assert "fabric_band_unreadable" in str(збій)
    else:
        raise AssertionError("бита смуга пройшла K-MAT-03")
assert М.жорстке_відсічення(р, темп_c=15) is None
assert М.жорстке_відсічення(dict(р, сезон_тканини=[5, 25]), темп_c=15) is None
with patch.object(М._ПОЛ, "злам", side_effect=ValueError("policy_broken")):
    try:
        М.жорстке_відсічення(dict(р, сезон_тканини=[5, 25]), темп_c=15)
    except ValueError as збій:
        assert str(збій) == "policy_broken"
    else:
        raise AssertionError("збій політики зник")
print("Е2: усі читачі сенсорної межі й K-MAT-03 не ковтають збою")
