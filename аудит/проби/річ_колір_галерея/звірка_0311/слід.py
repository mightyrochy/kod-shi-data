"""Звірка продовження #2799: збій доходить до всіх трьох споживачів."""
import ast
import pathlib
import subprocess
import sys
from unittest.mock import patch

корінь = pathlib.Path(__file__).resolve().parents[4]
sys.path.insert(0, str(корінь / "джерела"))
import фід_кадр_колір as К
import кадри_групи as Г

база = "d02813036b3c195513ade2723fe6116682d301c3"
текст = subprocess.check_output(
    ["git", "show", база + ":джерела/фід_кадр_колір.py"], cwd=корінь).decode("utf-8")
функція = next(ф for ф in ast.parse(текст).body
               if isinstance(ф, ast.FunctionDef) and ф.name == "вимір_кадру")
імена = dict(vars(К))
exec(compile(ast.Module(body=[функція], type_ignores=[]), база, "exec"), імена)
кадр = dict(файл="b.jpg", клас="ціла_річ", слово="чорний", lab=[10, 0, 0],
            hex="#1b1b1b", колір_тип="вимір", придатна=True, розкид=0.0)
збагачення = dict(фото="https://x/a.jpg", колір_основний=dict(слово="чорний", hex="#1b1b1b"))
шляхи = {
    "читач": lambda: bool(К.вимір_кадру(кадр)),
    "групи_кадрів": lambda: bool(Г.групи_кадрів(збагачення, [кадр])["групи"]),
    "після_спору": lambda: bool(К.після_спору(dict(id="річ"), збагачення,
        dict(крамниця="білий"), dict(кадри={"річ": [кадр]}))["позначка"]),
}
новий = К.вимір_кадру
for тип in (TypeError, ValueError):
    for назва, виклик in шляхи.items():
        збій = тип("наведений збій читача")
        with patch.object(К._КР_ТИП, "точка_кольору", side_effect=збій):
            with patch.object(К, "вимір_кадру", імена["вимір_кадру"]), patch.object(Г, "вимір_кадру", імена["вимір_кадру"]):
                assert виклик() is False
            with patch.object(К, "вимір_кадру", новий), patch.object(Г, "вимір_кадру", новий):
                try:
                    виклик()
                except тип as помилка:
                    assert помилка is збій
                else:
                    raise AssertionError("Збій не дійшов до споживача: " + назва)
        print("%s / %s: ДО — звичайний стан; ПІСЛЯ — той самий виняток" % (тип.__name__, назва))
