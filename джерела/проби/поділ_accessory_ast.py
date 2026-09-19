# -*- coding: utf-8 -*-
"""Проба поділу accessory.py (19.09.2026, третя сесія хвилі стандарту): кожна функція й
константа, що переїхала в новий модуль, має ТОЙ САМИЙ AST, що й у accessory.py до поділу
(коміт b993a38), і `accessory.ім'я` — це той самий об'єкт, що й у модулі. Друкує факт,
падає на розбіжності. Запуск: cd джерела && python3 проби/поділ_accessory_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "b993a38"
МОДУЛІ = ("аксесуари_реєстр", "аксесуари_погода", "аксесуари_розмір", "аксесуари_край",
          "аксесуари_взуття", "аксесуари_носіння", "аксесуари_структура", "аксесуари_ціна",
          "аксесуари_суд", "accessory")
було = subprocess.run(["git", "show", "%s:джерела/accessory.py" % БАЗА],
                      capture_output=True, text=True, check=True).stdout

def вузли(текст):
    в = {}
    for n in ast.parse(текст).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            в[n.name] = ast.dump(n)
        elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            в[n.targets[0].id] = ast.dump(n)
    return в

до = вузли(було)
де, розбіжні, зайві = {}, [], []
for м in МОДУЛІ:
    if not os.path.exists(м + ".py"): continue
    for ім, д in вузли(open(м + ".py", encoding="utf-8").read()).items():
        if ім not in до: зайві.append((м, ім)); continue
        де.setdefault(ім, м)
        if до[ім] != д: розбіжні.append((м, ім))
загублені = sorted(set(до) - set(де))
import accessory
не_ті_самі = [ім for ім, м in де.items() if м != "accessory"
              and getattr(accessory, ім, None) is not getattr(__import__(м), ім)]
print("вузлів у accessory.py@%s: %d · знайдено після поділу: %d · AST розбіжні: %d · "
      "загублені: %d · нові імена: %d · accessory.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(загублені), len(зайві), len(не_ті_самі)))
for х in (розбіжні, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (розбіжні or загублені or не_ті_самі) else 0)
