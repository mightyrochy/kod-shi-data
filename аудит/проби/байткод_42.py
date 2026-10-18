"""Крок 4.2: checked-hash імпорт без компіляції, змінене джерело й пошкоджений байткод."""
import importlib, json, os, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "джерела"))
from build_байткод import скомпілювати, ПЕРЕВІРКА
if sys.version_info[:3] != (3, 12, 1):
    sys.exit("НЕ ПЕРЕВІРЕНО: запустіть цю пробу CPython 3.12.1")
код = b"v = 42\n"; файли = скомпілювати({"проба42.py": код}, sys.executable)
assert файли == скомпілювати({"проба42.py": код}, sys.executable)
try:
    скомпілювати({"проба42.py": код}, "/неіснуючий-компілятор")
except OSError:
    pass
else:
    raise AssertionError("недоступний компілятор не відмовив")
with tempfile.TemporaryDirectory() as тека:
    корінь = pathlib.Path(тека)
    for імя, дані in dict(файли, **{"проба42.py": код}).items():
        шлях = корінь / імя
        шлях.parent.mkdir(parents=True, exist_ok=True)
        шлях.write_bytes(дані)
    перевірка = ПЕРЕВІРКА.replace("/показ/", тека + "/")
    стан = {}; exec(перевірка, стан)
    assert стан["БАЙТКОД_СТАН"]["придатних"] == 1
    компіляцій = []
    sys.addaudithook(lambda подія, арг: компіляцій.append(арг[1]) if подія == "compile" else None)
    sys.path.insert(0, тека)
    assert importlib.import_module("проба42").v == 42
    assert not компіляцій, компіляцій
    байткод = next((корінь / "__pycache__").glob("*.pyc"))
    байткод.write_bytes(b"broken")
    стан = {}; exec(перевірка, стан)
    assert стан["БАЙТКОД_СТАН"]["відкинуто"] == ["проба42.py"] and not байткод.exists()
    (корінь / "проба42.py").write_bytes(b"v = 43\n")
    try:
        exec(перевірка, {})
    except RuntimeError:
        print("ПЕРЕВІРЕНО: байткод детермінований; імпорт без compile; пошкодження відкинуто; інший SHA джерела відхилено")
    else:
        raise AssertionError("змінений SHA джерела прийнято")
