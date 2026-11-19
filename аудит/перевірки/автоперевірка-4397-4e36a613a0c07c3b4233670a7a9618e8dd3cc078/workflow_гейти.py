"""Дві штатні перевірки workflow після викладення пропущених sparse-фікстур."""
import ast
import json
import os
from pathlib import Path
import sys

джерела = Path(sys.argv[1]).resolve() / 'джерела'
файл = джерела / 'прилади/розділи_гейтів.py'
дерево = ast.parse(файл.read_text(encoding='utf-8'))
тіло = next(в.body for в in дерево.body if isinstance(в, ast.FunctionDef) and в.name == 'main')
почато, блок, результати = False, [], []
for вузол in тіло:
    if isinstance(вузол, ast.Import) and any(а.asname == '_ast89' for а in вузол.names):
        почато = True
    if почато:
        блок.append(вузол)
        if (isinstance(вузол, ast.Expr) and isinstance(вузол.value, ast.Call)
                and isinstance(вузол.value.func, ast.Name) and вузол.value.func.id == 'тест'
                and isinstance(вузол.value.args[0], ast.Constant)
                and str(вузол.value.args[0].value).startswith('жоден крок `run:`')):
            break


def тест(назва, умова, доказ, без_входу=False):
    результати.append(dict(назва=назва, пройдено=bool(умова), без_входу=без_входу, доказ=доказ))


exec(compile(ast.Module(body=блок, type_ignores=[]), str(файл), 'exec'),
     dict(_os=os, _тут=str(джерела), тест=тест))
assert len(результати) == 2
print(json.dumps(результати, ensure_ascii=False, indent=2))
sys.exit(int(any(not р['пройдено'] or р['без_входу'] for р in результати)))
