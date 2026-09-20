# -*- coding: utf-8 -*-
"""Проба поділу реєстр_правил.py: кожна функція/константа, що переїхала в новий модуль
`реєстр_*`, має ТОЙ САМИЙ AST, що й у реєстр_правил.py до поділу (коміт d1dbd9a) — ОКРІМ
пар «модуль::ім'я» з `поділ_очікувані.json` (ключ «реєстр_правил»), свідомо змінених пізнішими
комітами (sha там-таки; на день поділу список порожній — перенесення чисте). Будь-яка ІНША розбіжність — падіння з іменем.
Запуск: cd джерела && python3 проби/поділ_реєстр_правил_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ДЖЕРЕЛА)
from поділ_спільне import dump_без_докстрінгів
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "d1dbd9a"
МОДУЛІ = ("реєстр_політика", "реєстр_константи", "реєстр_тіри", "реєстр_сила", "реєстр_намір",
          "реєстр_осі", "реєстр_правил")
було = subprocess.run(["git", "show", "%s:джерела/реєстр_правил.py" % БАЗА],
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
import реєстр_правил as фасад
не_ті_самі = [ім for ім, м in де.items() if м != "реєстр_правил"
              and getattr(фасад, ім, None) is not getattr(__import__(м), ім)]
import json
ОЧІК = set(json.load(open(os.path.join(ДЖЕРЕЛА, "проби", "поділ_очікувані.json"), encoding="utf-8"))["реєстр_правил"])
спост = {"%s::%s" % п for п in розбіжні}
поза_списком, не_справдилось = sorted(спост - ОЧІК), sorted(ОЧІК - спост)
print("вузлів у реєстр_правил.py@%s: %d · знайдено: %d · AST розбіжні: %d (очікувані: %d) · "
      "загублені: %d · нові імена: %d · реєстр_правил.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(ОЧІК), len(загублені), len(зайві), len(не_ті_самі)))
for х in (поза_списком, не_справдилось, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (поза_списком or не_справдилось or загублені or не_ті_самі) else 0)
