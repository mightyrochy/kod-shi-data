"""Знання шляху образу: суд і палітра — скільки рядків, коду, і яка частка коду в тілах функцій.

Запуск з кореня: python3 -I аудит/звіти/ядро-образу-наново/скрипти/знання_міра.py джерела /tmp/граф.json
(/tmp/граф.json пише граф.py). Код — непорожні рядки без коментарів і докстрінгів; «у функціях» — рядки коду
всередині def/class верхнього рівня модуля. Множини — за префіксами імен модулів замикання від bridge.
"""
import ast
import io
import json
import os
import re
import sys
import tokenize

ДЖ, ГРАФ = sys.argv[1], sys.argv[2]
МОДУЛІ = json.load(open(ГРАФ, encoding="utf-8"))["м"]
_КОЛО = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "коло_без_шляху.py"), encoding="utf-8").read()
ЗАМІНЯЄ = set(re.search(r"ЗАМІНЯЄ = set\('''(.*?)'''", _КОЛО, re.S).group(1).split())

МНОЖИНИ = {
    "суд": re.compile(r"^(суд_|перевірка_образу$|оцінка_образу$|аксесуари_|верхнє_|силует_)"),
    "палітра й колір": re.compile(r"^(palettes$|palette$|палітра_|personal_palette$|колір_|colorspace$|"
                                  r"відтінки_кольорів$|словник_кольору$)"),
}


def міра(шлях):
    src = open(шлях, encoding="utf-8").read()
    рядків = src.count("\n") + (0 if src.endswith("\n") else 1)
    дерево = ast.parse(src)
    док = set()
    for в in ast.walk(дерево):
        if isinstance(в, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and в.body:
            п = в.body[0]
            if isinstance(п, ast.Expr) and isinstance(п.value, ast.Constant) and isinstance(п.value.value, str):
                док.update(range(п.lineno, п.end_lineno + 1))
    код = set()
    for т in tokenize.generate_tokens(io.StringIO(src).readline):
        if т.type in (tokenize.COMMENT, tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT,
                      tokenize.ENDMARKER):
            continue
        for р in range(т.start[0], т.end[0] + 1):
            if р not in док:
                код.add(р)
    функції = set()
    for в in дерево.body:
        if isinstance(в, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            функції.update(range(в.lineno, в.end_lineno + 1))
    return рядків, len(код), len(код & функції)


def підсумок(назва, м):
    р = к = ф = 0
    for x in м:
        a, b, c = міра(f"{ДЖ}/{x}.py")
        р, к, ф = р + a, к + b, ф + c
    print(f"{назва}: модулів {len(м)}, рядків {р}, коду {к}, у функціях {ф} ({100 * ф / к:.0f} %)")
    print("  " + " ".join(м))


for назва, шаблон in МНОЖИНИ.items():
    м = sorted(x for x in МОДУЛІ if шаблон.search(x))
    підсумок(назва, м)
    if set(м) & ЗАМІНЯЄ:
        підсумок(f"{назва} без замінних ядром", sorted(set(м) - ЗАМІНЯЄ))
