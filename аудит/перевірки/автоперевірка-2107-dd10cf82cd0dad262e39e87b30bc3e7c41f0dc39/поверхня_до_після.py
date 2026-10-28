"""Ізолювати регресію 10668: незмінний читач і дві версії виробника."""
import ast
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

дж = Path.cwd()
sys.path.insert(0, str(дж))
import colorspace as CS
import verify as V
import жнива_колір as Ж

спец = importlib.util.spec_from_file_location("мірила", дж / "проби/поверхня_212.py")
прилад = importlib.util.module_from_spec(спец)
спец.loader.exec_module(прилад)
база = "7561309d7644bff3600a3cc1b07704661a85150f"
текст = subprocess.check_output(["git", "show", база + ":джерела/жнива_колір.py"],
                                encoding="utf-8")
вузол = next(в for в in ast.parse(текст).body
             if isinstance(в, ast.FunctionDef) and в.name == "за_вікном_слова")
простір = dict(V=V, CS=CS)
exec(compile(ast.get_source_segment(текст, вузол), "база:за_вікном_слова", "exec"), простір)
поточна = Ж.за_вікном_слова
факт = {}
try:
    for назва, виробник in (("ДО", простір["за_вікном_слова"]), ("ПІСЛЯ", поточна)):
        Ж.за_вікном_слова = виробник
        try:
            факт[назва] = dict(результат=прилад.споживачеві(None, ["кремовий"]))
        except KeyError as помилка:
            факт[назва] = dict(помилка=type(помилка).__name__, поле=помилка.args[0])
finally:
    Ж.за_вікном_слова = поточна
print(json.dumps(факт, ensure_ascii=False, indent=2))
assert факт["ДО"]["результат"][0] == "кремовий"
assert факт["ПІСЛЯ"] == dict(помилка="KeyError", поле="hex")
