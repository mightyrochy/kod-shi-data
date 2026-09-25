# -*- coding: utf-8 -*-
"""Проба поділу pipeline.py: кожна функція/константа, що переїхала в новий модуль,
має ТОЙ САМИЙ AST, що й у pipeline.py до поділу (коміт ac8c2ca) — ОКРІМ пар
«модуль::ім'я» з `поділ_очікувані.txt`, свідомо змінених комітами докстрінгів
й наступними правилами (sha там-таки). Будь-яка ІНША розбіжність — падіння з іменем.
Запуск: cd джерела && python3 проби/поділ_pipeline_ast.py [БАЗОВИЙ_КОМІТ]"""
import ast, os, subprocess, sys
ДЖЕРЕЛА = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ДЖЕРЕЛА)
from поділ_спільне import dump_без_докстрінгів, очікувані
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "ac8c2ca"
МОДУЛІ = ("паспорт_нагоди", "пакет_моделі", "розбір_відповідей", "суд_від_моделі",
          "повнота_образу", "вердикт_моделі", "pipeline")
було = subprocess.run(["git", "show", "%s:джерела/pipeline.py" % БАЗА],
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
# «знесено::ім'я» у реєстрі — ім'я, свідомо прибране після поділу (замість нього — те,
# що названо в ноті запису); таке ім'я не «загублене», а знесене ще живим — падіння.
ОЧІК = очікувані("pipeline")
знесені = {к.split("::", 1)[1] for к in ОЧІК if к.startswith("знесено::")}
ОЧІК = {к for к in ОЧІК if к.split("::", 1)[1] not in знесені}   # і чужі записи знесеного імені
загублені = sorted(set(до) - set(де) - знесені) + sorted("живе знесене: " + і for і in знесені & set(де))
import pipeline
не_ті_самі = [ім for ім, м in де.items() if м != "pipeline"
              and getattr(pipeline, ім, None) is not getattr(__import__(м), ім)]
спост = {"%s::%s" % п for п in розбіжні}
поза_списком, не_справдилось = sorted(спост - ОЧІК), sorted(ОЧІК - спост)
print("вузлів у pipeline.py@%s: %d · знайдено: %d · AST розбіжні: %d (очікувані: %d) · "
      "загублені: %d · нові імена: %d · pipeline.ім'я ≠ модуль.ім'я: %d"
      % (БАЗА, len(до), len(де), len(розбіжні), len(ОЧІК), len(загублені), len(зайві), len(не_ті_самі)))
for х in (поза_списком, не_справдилось, загублені, зайві, не_ті_самі):
    if х: print("  ", х)
sys.exit(1 if (поза_списком or не_справдилось or загублені or не_ті_самі) else 0)
