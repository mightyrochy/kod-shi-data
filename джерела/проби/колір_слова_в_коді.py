# -*- coding: utf-8 -*-
"""КОЛІР-КОДУВАННЯ (рядок 2692), п.12: де код продукту (`status.МОДУЛІ_ПРОДУКТУ`) ще ЧИТАЄ слова кольору, а не
числа. Лічить в AST (докстрінги — ні): (а) рядкові сталі — слово лексикону кольору (`verify.ЛЕКСИКОН` чи основа
`verify.ФОРМИ`); (б) читання полів зі словом кольору (`колір_назва*`, `колір_ім`, `["слово"]`) і виклики
`сім_я_слова` / `ЛЕКСИКОН[...]` — тобто рішення, що йде від слова. Межа (фід, лексикон, жнива, каталог) переводить
слово крамниці у вікно — це законний вхід; поза межею слово кольору в правилі — кошик Б п.12. (в) числа: скільки
місць читають `lab` точкою, через межі (`колір_річ.межі_кольору` і сусіди), з них через одне API відношень
(`відношення`, `запис_кольору`, `гучність_меж`, КОЛІР-Р4), і тоном точкою на колі (`кут_на_колі`); з іменами модулів
у аргументах — їхні рядки (і «lab точкою» / «API» помодульно). Запуск із джерела/: python3 проби/колір_слова_в_коді.py"""
import ast, os, sys, collections as K; sys.path.insert(0, "."); import status, verify as V
ЛЕКС, ОСНОВИ = set(V.ЛЕКСИКОН) | set(V.ФОРМИ.values()), tuple(V.ФОРМИ)
ПОЛЯ = {"колір_назва", "колір_ім", "колір_назва_фото", "колір_назва_крамниці", "слово", "колір_слово"}
КОШИК_А = ("внутрішня_мова",)   # коди → ядро: вже внутрішня мова, слів не читає (п.12) — не рахувати
МЕЖА = ("фід", "feed", "verify", "жнива", "каталог", "чистка", "звірка", "таблиця_каталогу", "річ_з_фото")
ЗАКІНЧЕННЯ = ("", "ий", "ій", "а", "я", "е", "є", "і", "ого", "ої", "им", "их", "ові")
def слово_кольору(s):   # слово лексикону чи його форма: основа `ФОРМИ` + закінчення прикметника
    s = s.strip().lower()
    return s in ЛЕКС or any(s.startswith(о) and s[len(о):] in ЗАКІНЧЕННЯ for о in ОСНОВИ)
ІНТЕРВАЛ = {"межі_кольору", "розкид_тону", "розкид_осі", "поруч_за_тоном", "de00_мін", "межі_b", "несе_тон", "не_вимір",
            "розкид_тону_на_колі", "відлуння_тону", "відношення", "запис_кольору", "гучність_меж"}; АПІ = {"відношення", "запис_кольору", "гучність_меж"}
Л, П = K.Counter(), K.defaultdict(K.Counter)
for м in sorted(status.МОДУЛІ_ПРОДУКТУ):
    if м.startswith(КОШИК_А) or not os.path.exists(м + ".py"): continue
    дерево = ast.parse(open(м + ".py", encoding="utf-8").read())
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
        if ключ == "lab": Л[("числа", "читає lab точкою")] += 1; П[м]["lab точкою"] += 1
        if ім in ІНТЕРВАЛ: Л[("числа", "через межі (точка / вікно)")] += 1
        if ім in АПІ or ім == "кут_на_колі": Л[("числа", "через API відношень" if ім in АПІ else "тон точкою на колі")] += 1; П[м]["API" if ім in АПІ else "кут"] += 1
        if ключ in ПОЛЯ or ім in ("сім_я_слова", "слово_крамниці", "назва_кольору") or (isinstance(в, ast.Subscript) and getattr(в.value, "attr", getattr(в.value, "id", "")) == "ЛЕКСИКОН"):
            П[м]["читає слово"] += 1; Л[(бік, "читає слово")] += 1
print("разом:", {"%s / %s" % к: n for к, n in sorted(Л.items())})
print("модулів поза межею, що читають слово кольору:", sum(1 for м, c in П.items() if not м.startswith(МЕЖА) and (c["слово-стала"] or c["читає слово"])))
for м, c in [(м, П[м]) for м in sys.argv[1:]] or sorted(П.items(), key=lambda п: -sum(п[1].values()))[:22]:
    print("  %-28s %-6s %s" % (м, "межа" if м.startswith(МЕЖА) else "", dict(c)))
