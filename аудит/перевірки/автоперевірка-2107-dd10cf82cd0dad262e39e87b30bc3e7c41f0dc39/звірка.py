"""Відтворення доказів звіту #2107 без моделі та зміни реалізації."""
import collections
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

дерево = Path(sys.argv[1]).resolve()
тут = Path(__file__).resolve().parent
дж = дерево / "джерела"
докази = дерево / "аудит/перевірка/2075"
os.environ.update(PYTHONUTF8="1", PYTHONIOENCODING="utf-8")


def читати(ім):
    return json.loads((докази / ім).read_text("utf-8-sig"))


def виконати(назва, команда, cwd=дж):
    початок = time.monotonic()
    з = subprocess.run(команда, cwd=cwd, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT)
    (тут / (назва + ".txt")).write_bytes(з.stdout)
    р = dict(назва=назва, команда=[str(к) for к in команда], cwd=str(cwd),
             код=з.returncode, секунд=round(time.monotonic() - початок, 2))
    print(json.dumps(р, ensure_ascii=False), flush=True)
    return р


зведення = {}
for ім in ("батарея.json", "доповнення.json", "фінальна-батарея.json"):
    записи = читати(ім)
    зведення[ім] = dict(команд=len(записи), коди=dict(collections.Counter(
        р["код"] for р in записи)), ненульові=[р["назва"] for р in записи if р["код"]])
assert зведення["батарея.json"]["коди"] == {0: 94, 1: 5, 4294967295: 1}
assert зведення["доповнення.json"]["коди"] == {0: 13, 1: 8}
assert зведення["фінальна-батарея.json"]["коди"] == {0: 7, 1: 1}
до, після = [читати(ім + "-стенд.json") for ім in ("ДО", "ПІСЛЯ")]
assert до["ід"] == після["ід"]
assert len(до["знімок"]) == 6
сцени = []
for ім in до["знімок"]:
    а, б = [з["знімок"][ім] for з in (до, після)]
    правила = [dict(з["суд"]["знахідки_правила"]) for з in (а, б)]
    різниця = {к: [правила[0].get(к, 0), правила[1].get(к, 0)]
               for к in правила[0].keys() | правила[1].keys()
               if правила[0].get(к, 0) != правила[1].get(к, 0)}
    assert not any(к.startswith(("K-PAL", "K-WEA")) for к in різниця)
    сцени.append(dict(сцена=ім, пул=[а["запити"]["пул"], б["запити"]["пул"]],
                      зміни_правил=різниця))
без_входу = [sum(sum(с["суд"]["без_входу_кольору"].values())
                for с in з["знімок"].values()) for з in (до, після)]
assert без_входу == [20, 20]
зведення.update(сцени=сцени, без_входу=без_входу)
(тут / "звірка-журналів.json").write_text(json.dumps(зведення, ensure_ascii=False,
                                                  indent=2), "utf-8")
print("Журнали: 100/21/8 команд; шість наборів id однакові; без входу 20 → 20.", flush=True)

sys.path.insert(0, str(дж))
os.chdir(дж)
спец = importlib.util.spec_from_file_location("прилад_поверхні", дж / "проби/поверхня_212.py")
прилад = importlib.util.module_from_spec(спец)
спец.loader.exec_module(прилад)
try:
    прилад.споживачеві(None, ["кремовий"])
except KeyError as помилка:
    assert помилка.args == ("hex",)
    print("10668: споживачеві(None, ['кремовий']) → KeyError: 'hex'.", flush=True)
else:
    raise AssertionError("10668 не відтворено")

команди = [("частковий-вимір", [sys.executable, "-X", "utf8", str(докази / "поверхня_злиття.py")]),
           ("невизначеність", [sys.executable, "-X", "utf8", "проби/поверхня_1993_невизначеність.py"]),
           ("тотожність", [sys.executable, "-X", "utf8", "проби/поверхня_1993_тотожність.py"]),
           ("дошка", [sys.executable, "-X", "utf8", "прилади/згорнути_дошку.py", "--лише-перевірити"])]
for шлях in sorted((дж / "проби").glob("колір_тип_213*.py")):
    команди.append((шлях.stem, [sys.executable, "-X", "utf8", str(шлях)]))
результати = []
for назва, команда in команди:
    результати.append(виконати(назва, команда))
(тут / "результати.json").write_text(json.dumps(результати, ensure_ascii=False,
                                              indent=2), "utf-8")
assert all(р["код"] == 0 for р in результати)
print("Усі прицільні проби завершилися успішно.", flush=True)
