# -*- coding: utf-8 -*-
"""Проба поділу pipeline.py (19.09.2026): кожна функція й константа, що переїхала в
новий модуль, має ТОЙ САМИЙ AST, що й у pipeline.py до поділу (коміт ac8c2ca), і
`pipeline.ім'я` — це той самий об'єкт, що й у модулі. Друкує факт, падає на розбіжності.
Запуск: cd джерела && python3 проби/поділ_pipeline_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "ac8c2ca"
МОДУЛІ = ("паспорт_нагоди", "пакет_моделі", "розбір_відповідей", "суд_від_моделі",
          "повнота_образу", "вердикт_моделі", "pipeline")
було = subprocess.run(["git", "show", "%s:джерела/pipeline.py" % БАЗА],
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
import pipeline
не_ті_самі = [ім for ім, м in де.items() if м != "pipeline"
              and getattr(pipeline, ім, None) is not getattr(__import__(м), ім)]
print("вузлів у pipeline.py@%s: %d · знайдено після поділу: %d · AST розбіжні: %d · "
      "загублені: %d · нові імена: %d · pipeline.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(загублені), len(зайві), len(не_ті_самі)))
for х in (розбіжні, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (розбіжні or загублені or не_ті_самі) else 0)
