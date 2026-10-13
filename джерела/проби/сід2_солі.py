# -*- coding: utf-8 -*-
"""СІД-2 (рядок 740): кирилиця в літералах солей перемішування коду + хеші перемішування. До/після збігаються.
Прогін: python3 проби/сід2_солі.py"""
import hashlib, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import порядок_запиту as ПЗ, уважний_вибір as УВ
import ast
к = 0
for ф in ("порядок_запиту.py", "уважний_вибір.py"):
    for в in ast.walk(ast.parse(open(ф, encoding="utf-8").read())):
        if isinstance(в, ast.Call) and getattr(в.func, "attr", getattr(в.func, "id", "")) in ("Random", "перемішати"):
            к += sum(1 for x in ast.walk(в) if isinstance(x, ast.Constant) and isinstance(x.value, str) and re.search("[а-яіїєґ]", x.value, re.I))
print("кириличних літералів у солях коду: %d" % к)
сіль = lambda к, д: ПЗ.сіль(к) if hasattr(ПЗ, "сіль") else д
ряд, об = list(range(40)), {"вердикт": [{"твій_образ": {"ід": "о%d" % і}} for і in range(9)]}
for с in (1, 2, 3):
    м = "".join(map(str, ПЗ.перемішати(ряд, с, сіль("tournament", "турнір") + "|в"))) + "".join(map(str, ПЗ.перемішати(ряд, с, сіль("set", "склад") + "|в")))
    г = list(range(30)); __import__("random").Random("%d|%s" % (с, сіль("groups", "групи"))).shuffle(г)
    о = ПЗ.перемішати_дріт(об, с, "select", образи=True)[1]["образи"]
    print("сід %d: мітки %s · групи %s · образи %s" % (с, hashlib.sha1(м.encode()).hexdigest()[:8], hashlib.sha1(str(г).encode()).hexdigest()[:8], hashlib.sha1(str(о).encode()).hexdigest()[:8]))
