# -*- coding: utf-8 -*-
"""КОЛІР-КОДУВАННЯ (рядок 2692), п.12: де код продукту (`status.МОДУЛІ_ПРОДУКТУ`) ще ЧИТАЄ слова кольору, а не
числа. Лічить в AST (докстрінги — ні): (а) рядкові сталі — слово лексикону кольору (`verify.ЛЕКСИКОН` чи основа
`verify.ФОРМИ`); (б) читання полів зі словом кольору (`колір_назва*`, `колір_ім`, `["слово"]`) і виклики
`сім_я_слова` / `ЛЕКСИКОН[...]` — тобто рішення, що йде від слова. Межа (фід, лексикон, жнива, каталог) переводить
слово крамниці у вікно — це законний вхід; поза межею слово кольору в правилі — кошик Б п.12. (в) числа: скільки
місць читають `lab` точкою, а скільки — через межі з невизначеністю (`колір_річ.межі_кольору` і сусіди).
Запуск із джерела/: python3 проби/колір_слова_в_коді.py"""
import ast, sys, collections as K; sys.path.insert(0, "."); import status, verify as V
ЛЕКС = set(V.ЛЕКСИКОН) | set(V.ФОРМИ.values())
ОСНОВИ = tuple(V.ФОРМИ)
ПОЛЯ = {"колір_назва", "колір_ім", "колір_назва_фото", "колір_назва_крамниці", "слово", "колір_слово"}
МЕЖА = ("фід", "feed", "verify", "жнива", "каталог", "чистка", "звірка", "таблиця_каталогу", "річ_з_фото")
ЗАКІНЧЕННЯ = ("", "ий", "ій", "а", "я", "е", "є", "і", "ого", "ої", "им", "их", "ові")
def слово_кольору(s):   # слово лексикону чи його форма: основа `ФОРМИ` + закінчення прикметника
    s = s.strip().lower()
    return s in ЛЕКС or any(s.startswith(о) and s[len(о):] in ЗАКІНЧЕННЯ for о in ОСНОВИ)
ІНТЕРВАЛ = {"межі_кольору", "розкид_тону", "розкид_осі", "поруч_за_тоном", "de00_мін", "межі_b", "несе_тон", "не_вимір"}
Л, П = K.Counter(), K.defaultdict(K.Counter)
for м in sorted(status.МОДУЛІ_ПРОДУКТУ):
    try: дерево = ast.parse(open(м + ".py", encoding="utf-8").read())
    except OSError: continue
    докс = {id(в.body[0].value) for в in ast.walk(дерево) if isinstance(в, (ast.Module, ast.FunctionDef, ast.ClassDef))
            and в.body and isinstance(в.body[0], ast.Expr) and isinstance(в.body[0].value, ast.Constant)}
    бік = "межа" if м.startswith(МЕЖА) else "правила й показ"
    for в in ast.walk(дерево):
        if isinstance(в, ast.Constant) and isinstance(в.value, str) and id(в) not in докс and слово_кольору(в.value):
            П[м]["слово-стала"] += 1; Л[(бік, "слово-стала")] += 1
        ключ = в.slice.value if isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) else (
            в.args[0].value if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) and в.func.attr == "get"
            and в.args and isinstance(в.args[0], ast.Constant) else None)
        ім = в.func.attr if isinstance(в, ast.Call) and isinstance(в.func, ast.Attribute) else в.func.id if isinstance(в, ast.Call) and isinstance(в.func, ast.Name) else ""
        if ключ == "lab": Л[("числа", "читає lab точкою")] += 1
        if ім in ІНТЕРВАЛ: Л[("числа", "через межі (точка / вікно)")] += 1
        if ключ in ПОЛЯ or ім in ("сім_я_слова", "слово_крамниці", "назва_кольору") or (isinstance(в, ast.Subscript) and getattr(в.value, "attr", getattr(в.value, "id", "")) == "ЛЕКСИКОН"):
            П[м]["читає слово"] += 1; Л[(бік, "читає слово")] += 1
print("разом:", {"%s / %s" % к: n for к, n in sorted(Л.items())})
print("модулів поза межею, що читають слово кольору:", sum(1 for м, c in П.items() if not м.startswith(МЕЖА)))
for м, c in sorted(П.items(), key=lambda п: -sum(п[1].values()))[:22]:
    print("  %-28s %-6s %s" % (м, "межа" if м.startswith(МЕЖА) else "", dict(c)))
