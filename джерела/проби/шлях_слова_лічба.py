# -*- coding: utf-8 -*-
"""Розбір шляху 7/8 (наказ власника 25.09): рахує іменовані МОДУЛЬНОГО РІВНЯ
словники/регулярки/переліки слів (dict/list/tuple/set/re.compile з ≥2 різними
кириличними словами ≥3 літер) у файлах ПРОДУКТУ (status.МОДУЛІ_ПРОДУКТУ) — не
тлумачить, лише лічить, щоб чистку міряти до/після ОДНИМ способом. Прогін:
python3 проби/шлях_слова_лічба.py"""
import ast, io, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import status
СЛОВО = re.compile(r"[а-яіїєґ]{3,}", re.I)


def _зібрати(в, слова):
    if isinstance(в, ast.Constant) and isinstance(в.value, str):
        слова.update(w.lower() for w in СЛОВО.findall(в.value))
    elif isinstance(в, ast.Call):
        [_зібрати(a, слова) for a in в.args]
    elif isinstance(в, (ast.Tuple, ast.List, ast.Set)):
        [_зібрати(e, слова) for e in в.elts]
    elif isinstance(в, ast.Dict):
        [_зібрати(x, слова) for k, v in zip(в.keys, в.values) for x in ([k, v] if k else [v])]


def сканувати(файл):
    конструкцій, слів = 0, set()
    for в in ast.parse(io.open(файл, encoding="utf-8").read(), filename=файл).body:
        if isinstance(в, (ast.Assign, ast.AnnAssign)) and isinstance(в.value, (ast.Dict, ast.List, ast.Tuple, ast.Set, ast.Call)):
            п = set(); _зібрати(в.value, п)
            if len(п) >= 2:
                конструкцій += 1; слів |= п
    return конструкцій, слів


рядки = sorted(((n, len(с), м + ".py") for м in status.МОДУЛІ_ПРОДУКТУ
                for n, с in [сканувати(м + ".py")] if n), reverse=True)
print("файлів продукту зі словниками слів: %d із %d · конструкцій разом: %d"
      % (len(рядки), len(status.МОДУЛІ_ПРОДУКТУ), sum(n for n, _, _ in рядки)))
for n, слів, ф in рядки:
    print("  %-28s конструкцій=%-4d унікальних_слів=%-4d" % (ф, n, слів))
