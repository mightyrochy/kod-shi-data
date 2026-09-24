# -*- coding: utf-8 -*-
"""Проба поділу gate_reach.py: кожна функція/константа, що переїхала в новий модуль
`батарея_*`, має ТОЙ САМИЙ AST, що й у gate_reach.py до поділу (коміт b8f70a4) — ОКРІМ
пар «модуль::ім'я» з `поділ_очікувані.txt`, свідомо змінених комітом докстрінгів і
хвилі `except` (`8a9b247`, sha там-таки). Будь-яка ІНША розбіжність — падіння з іменем;
і навпаки, зникла очікувана розбіжність теж падає: список, який не справджується, —
не сторож, а застарілий спогад. Плюс `gate_reach.ім'я` — той самий об'єкт, що й у модулі.
Запуск: cd джерела && python3 проби/поділ_gate_reach_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ДЖЕРЕЛА)
from поділ_спільне import dump_без_докстрінгів, очікувані
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "b8f70a4"
МОДУЛІ = ("батарея_корпус", "батарея_входи", "батарея_образи", "батарея_слід",
          "батарея_міст", "батарея_труба", "батарея_трейс", "gate_reach")
було = subprocess.run(["git", "show", "%s:джерела/gate_reach.py" % БАЗА],
                      capture_output=True, text=True, check=True).stdout

def вузли(текст):
    в = {}
    for n in ast.parse(текст).body:
        if isinstance(n, (ast.FunctionDef, ast.ClassDef)):
            в[n.name] = dump_без_докстрінгів(n)
        elif isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name):
            в[n.targets[0].id] = dump_без_докстрінгів(n)
    return в

до = вузли(було)
де, розбіжні, зайві = {}, [], []
for м in МОДУЛІ:
    if not os.path.exists(os.path.join(ДЖЕРЕЛА, м + ".py")): continue
    for ім, д in вузли(open(os.path.join(ДЖЕРЕЛА, м + ".py"), encoding="utf-8").read()).items():
        if ім not in до: зайві.append((м, ім)); continue
        де.setdefault(ім, м)
        if до[ім] != д: розбіжні.append((м, ім))
загублені = sorted(set(до) - set(де))
import gate_reach
не_ті_самі = [ім for ім, м in де.items() if м != "gate_reach"
              and getattr(gate_reach, ім, None) is not getattr(__import__(м), ім)]
ОЧІК = очікувані("gate_reach")
спост = {"%s::%s" % п for п in розбіжні}
поза_списком, не_справдилось = sorted(спост - ОЧІК), sorted(ОЧІК - спост)
print("вузлів у gate_reach.py@%s: %d · знайдено: %d · AST розбіжні: %d (очікувані: %d) · "
      "загублені: %d · нові імена: %d · gate_reach.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(ОЧІК), len(загублені), len(зайві), len(не_ті_самі)))
for х in (поза_списком, не_справдилось, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (поза_списком or не_справдилось or загублені or не_ті_самі) else 0)
