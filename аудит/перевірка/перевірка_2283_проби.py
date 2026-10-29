# -*- coding: utf-8 -*-
"""Проба перевірки #2283: переліки кодів запису речі (п.2 класу Річ-запис-речі), яких не лічить прилад.

Клас п.2 (паспорт, рішення 11335): місце — свій перелік чи словник кодів поза реєстром, що задає групу, порядок чи
властивість; не місце — лише порівняння з одним кодом. Проба шукає будь-який літерал (кортеж, список, множину, ключі
й константні значення словника, зокрема вкладені), усі рядкові елементи якого — коди реєстру, і їх не менше за поріг.
Реєстр і обсяг файлів беруться з приладу, детекція — своя.

    python3 аудит/перевірка/перевірка_2283_проби.py <корінь дерева> <поріг вбудованого> <поріг іменованого>
Друкує `файл:рядок [коди]` усіх збігів; поза приладом — звірити з його виводом (`comm`).
"""
import ast
import importlib.util
import sys
from pathlib import Path

корінь = Path(sys.argv[1])
межа_вбуд, межа_ім = int(sys.argv[2]), int(sys.argv[3])
spec = importlib.util.spec_from_file_location("прилад", корінь / "джерела/прилади/корінь_річ_запис_речі.py")
прилад = importlib.util.module_from_spec(spec)
spec.loader.exec_module(прилад)
коди = прилад.коди_реєстру(корінь)
for ф in прилад.зібрати_файли(корінь):
    if ф.name in прилад.РЕЄСТРИ:
        continue
    try:
        дерево = ast.parse(ф.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, ValueError):
        continue
    іменовані = set()
    for н in ast.walk(дерево):
        if isinstance(н, (ast.Assign, ast.AnnAssign)) and н.value is not None:
            іменовані.add(id(н.value))
            if isinstance(н.value, ast.Call) and н.value.args:
                іменовані.add(id(н.value.args[0]))
    for н in ast.walk(дерево):
        if isinstance(н, (ast.Tuple, ast.List, ast.Set)):
            ел = н.elts
        elif isinstance(н, ast.Dict):
            ел = [к for к in н.keys if к is not None] + [з for з in н.values if isinstance(з, ast.Constant)]
        else:
            continue
        рядки = [e.value for e in ел if isinstance(e, ast.Constant) and isinstance(e.value, str)]
        свої = [x for x in рядки if x in коди]
        if len(свої) >= (межа_ім if id(н) in іменовані else межа_вбуд) and len(свої) == len(рядки):
            print(f"{ф.relative_to(корінь).as_posix()}:{н.lineno} {свої}")
