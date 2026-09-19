# -*- coding: utf-8 -*-
"""Проба поділу gate_reach.py (19.09.2026, п'ята сесія хвилі стандарту): кожна функція й
константа, що переїхала в новий модуль `батарея_*`, має ТОЙ САМИЙ AST, що й у
gate_reach.py до поділу (коміт b8f70a4), і `gate_reach.ім'я` — це той самий об'єкт, що й
у модулі. Друкує факт, падає на розбіжності.
Запуск: cd джерела && python3 проби/поділ_gate_reach_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "b8f70a4"
МОДУЛІ = ("батарея_корпус", "батарея_входи", "батарея_образи", "батарея_слід",
          "батарея_міст", "батарея_труба", "батарея_трейс", "gate_reach")
було = subprocess.run(["git", "show", "%s:джерела/gate_reach.py" % БАЗА],
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
import gate_reach
не_ті_самі = [ім for ім, м in де.items() if м != "gate_reach"
              and getattr(gate_reach, ім, None) is not getattr(__import__(м), ім)]
print("вузлів у gate_reach.py@%s: %d · знайдено після поділу: %d · AST розбіжні: %d · "
      "загублені: %d · нові імена: %d · gate_reach.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(загублені), len(зайві), len(не_ті_самі)))
for х in (розбіжні, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (розбіжні or загублені or не_ті_самі) else 0)
