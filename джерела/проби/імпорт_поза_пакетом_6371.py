# -*- coding: utf-8 -*-
"""Рядок 6371: чи імпортує код показу модуль, якого нема в пакеті Pyodide. Друкує факт: модулі, що є файлом .py у
репозиторії (`джерела/`, `zhnyvarka/`), але не входять у замикання `склад.модулі_системи` від `bridge` — тобто в
браузері `import` дає `ModuleNotFoundError`. Імпорти всередині функцій теж (AST, як у збирача). Запуск: з `джерела/`."""
import ast, os, sys, warnings
warnings.simplefilter("ignore")

sys.path.insert(0, ".")
import склад

пакет = set(склад.модулі_системи(".", "bridge"))
сторонні = {f[:-3]: d for d in (".", os.path.join("..", "zhnyvarka")) for f in os.listdir(d) if f.endswith(".py")}
знайдено = []
for м in sorted(пакет):
    for в in ast.walk(ast.parse(open(м + ".py", encoding="utf-8").read())):
        імена = ([а.name for а in в.names] if isinstance(в, ast.Import)
                 else [в.module] if isinstance(в, ast.ImportFrom) and в.level == 0 and в.module else [])
        for ім in (і.split(".")[0] for і in імена):
            if ім in сторонні and ім not in пакет:
                знайдено.append("%s:%d імпортує %s (%s)" % (м, в.lineno, ім, сторонні[ім]))
print("модулів у пакеті: %d · імпорт модуля, якого нема в пакеті Pyodide: %s" % (len(пакет), "ТАК" if знайдено else "ні"))
print("\n".join(знайдено))
sys.exit(1 if знайдено else 0)
