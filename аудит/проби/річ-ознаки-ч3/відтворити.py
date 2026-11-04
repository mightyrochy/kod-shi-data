"""Зіставляє збережене походження портрета з безумовною емісією місць приладу."""
import ast
import json
import pathlib
import sys
from types import SimpleNamespace

корінь = pathlib.Path(__file__).resolve().parents[3]
sys.path[:0] = [str(корінь / "джерела"), str(корінь / "джерела/прилади")]
import face_features as О
import міст_вхід as М
from ознаки_стан import Стан

портрет = dict(photo="usable", skin=["#deb295"], hair=["#523321", "#735632"],
               eyes="#735632", limbal_ring="#111111")
прийнято = М.прийняти_колір(json.dumps(портрет))
assert прийнято["стан"] == "готово", прийнято
F = М.features(dict(шкіра=прийнято["шкіра"], волосся=прийнято["волосся"],
                    очі=прийнято["очі"], очі_кільце=прийнято["кільце"]))[0]
запис = О.ознаки(F)
assert запис["протокол"] == "model_hex" and not F["_meta"]["from_photo"]
assert not any(запис["надійність"].values())
assert all(р["джерело"] == "оцінка моделі" for р in запис["риси"].values())

місця = set()
стан = object.__new__(Стан)
стан.зерно = True
стан.м = SimpleNamespace(шлях="джерела/міст_вхід.py")
стан.а = SimpleNamespace(зерно={"ключі": set(портрет) - {"photo"}}, готові_поля=set(),
                         місце=lambda м, в, п, ч: місця.add((м.шлях, в.lineno)))
дерево = ast.parse((корінь / стан.м.шлях).read_text(encoding="utf-8"))
for в in ast.walk(дерево):
    if (isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get"
            and isinstance(в.func.value, ast.Name) and в.func.value.id == "об" and в.args
            and isinstance(в.args[0], ast.Constant) and в.args[0].value in стан.а.зерно["ключі"]):
        стан.індекс(frozenset(), в.args[0], в)
assert len(місця) == 3, місця
print(json.dumps(dict(протокол=запис["протокол"], риси=len(запис["риси"]),
                      довіра=запис["надійність"], місця=sorted(місця)), ensure_ascii=False))
