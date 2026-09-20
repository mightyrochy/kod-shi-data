# -*- coding: utf-8 -*-
"""Проба поділу composer.py: кожна функція/константа, що переїхала в новий модуль
`композитор_*`, має ТОЙ САМИЙ AST, що й у composer.py до поділу (коміт 2770569) — ОКРІМ
пар «модуль::ім'я» з `поділ_очікувані.json`, свідомо змінених комітом докстрінгів
(sha там-таки). Будь-яка ІНША розбіжність — падіння з іменем.
Запуск: cd джерела && python3 проби/поділ_composer_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ДЖЕРЕЛА)
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "2770569"
МОДУЛІ = ("композитор_реєстр", "композитор_придатні", "композитор_слоти", "композитор_річ",
          "композитор_оцінка", "композитор_полюси", "композитор_збирання", "composer")
було = subprocess.run(["git", "show", "%s:джерела/composer.py" % БАЗА],
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
    if not os.path.exists(os.path.join(ДЖЕРЕЛА, м + ".py")): continue
    for ім, д in вузли(open(os.path.join(ДЖЕРЕЛА, м + ".py"), encoding="utf-8").read()).items():
        if ім not in до: зайві.append((м, ім)); continue
        де.setdefault(ім, м)
        if до[ім] != д: розбіжні.append((м, ім))
загублені = sorted(set(до) - set(де))
import composer as фасад
не_ті_самі = [ім for ім, м in де.items() if м != "composer"
              and getattr(фасад, ім, None) is not getattr(__import__(м), ім)]
import json
ОЧІК = set(json.load(open(os.path.join(ДЖЕРЕЛА, "проби", "поділ_очікувані.json"), encoding="utf-8"))["composer"])
спост = {"%s::%s" % п for п in розбіжні}
поза_списком, не_справдилось = sorted(спост - ОЧІК), sorted(ОЧІК - спост)
print("вузлів у composer.py@%s: %d · знайдено: %d · AST розбіжні: %d (очікувані: %d) · "
      "загублені: %d · нові імена: %d · composer.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(ОЧІК), len(загублені), len(зайві), len(не_ті_самі)))
for х in (поза_списком, не_справдилось, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (поза_списком or не_справдилось or загублені or не_ті_самі) else 0)
