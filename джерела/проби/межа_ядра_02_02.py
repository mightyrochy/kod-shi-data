# -*- coding: utf-8 -*-
"""Проба Н-02-02 (межа ядра): друкує факти, не тлумачить. Прогін: python3 проби/межа_ядра_02_02.py"""
import ast, io, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import status, склад
ядро = status.МОДУЛІ_ПРОДУКТУ
print("модулів у вантажі (status.МОДУЛІ_ПРОДУКТУ):", len(ядро))
порушники = []
for м in ядро:
    for в in ast.walk(ast.parse(io.open(м + ".py", encoding="utf-8").read())):
        імена = ([а.name for а in в.names] if isinstance(в, ast.Import)
                 else [в.module or ""] if isinstance(в, ast.ImportFrom) else [])
        порушники += ["%s → %s" % (м, і) for і in імена if і.split(".")[0] == "лабораторія"]
print("ядро імпортує лабораторію (AST, разом із імпортами в тілах функцій):", порушники or "жодного разу")
print("замикання від bridge == список ядра:", sorted(склад.модулі_системи(ТУТ)) == sorted(ядро))
for з in status.ЛАБОРАТОРІЯ:
    __import__(з["файл"][:-3].replace("/", "."))
    print("  %-42s імпортується · правила без входу: %s" % (з["файл"], ", ".join(з["правила"]) or "—"))
секція = io.open("аудит/ДОСЯЖНІСТЬ.md", encoding="utf-8").read().split("## Не виконано · мітка «ніхто»")
ніхто = [(р.split("`")[1], р.split("`")[3]) for р in (секція[1] if len(секція) > 1 else "").splitlines()
         if р.startswith("| `")]
у_ядрі = [ф for ф in ніхто if ф[0] in ядро]
print("«ніхто» за аудит/ДОСЯЖНІСТЬ.md: усього %d, у ядрі %d %s" % (len(ніхто), len(у_ядрі), у_ядрі or ""))
print("правил без входу в реєстрі:", sorted(status.ПРАВИЛА_БЕЗ_ВХОДУ),
      "· кожне має названий блокер у БЛОКЕРИ_МЕРТВИХ:",
      all(і in status.БЛОКЕРИ_МЕРТВИХ for і in status.ПРАВИЛА_БЕЗ_ВХОДУ))
