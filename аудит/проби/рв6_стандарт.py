# -*- coding: utf-8 -*-
"""Проба РВ-6 · `СТАНДАРТ_КОДУ.md` переміряно на цьому тілі тим самим способом, що
10.09 (AST/grep по `джерела/*.py`), щоб «залишки для наступного етапу» мали числа, а не
слова. Ядро = `status.МОДУЛІ_ПРОДУКТУ` (37); «поза ядром» = решта .py верхнього рівня
(прилади, тести, збирачі); теки `прилади/`, `лабораторія/`, `проби/` — окремим рядком.

Прогін:  cd джерела && python3 ../аудит/проби/рв6_стандарт.py
"""
import ast, collections, os, re, sys
ДЖ = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "джерела"))
sys.path.insert(0, ДЖ); os.chdir(ДЖ)
import status
ЯДРО = set(status.МОДУЛІ_ПРОДУКТУ)
КИР = "а-яіїєґА-ЯІЇЄҐ"
ЗМІШ = re.compile(r"[%s][A-Za-z]|[A-Za-z][%s]" % (КИР, КИР))
ГОМ = re.compile(r"[%s][acepxyikb]|[acepxyikb][%s]" % (КИР, КИР))


def міра(файл):
    т = open(файл, encoding="utf-8").read(); дерево = ast.parse(т)
    ф = [x for x in ast.walk(дерево) if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))]
    без_док = sum(1 for x in ф if not ast.get_docstring(x))
    широкі = sum(1 for x in ast.walk(дерево) if isinstance(x, ast.ExceptHandler)
                 and (x.type is None or (isinstance(x.type, ast.Name) and x.type.id in ("Exception", "BaseException"))))
    нечитані = 0
    for x in ф:
        імена = {a.arg for a in x.args.args + x.args.kwonlyargs + x.args.posonlyargs} - {"self", "cls"}
        вжиті = {y.id for y in ast.walk(x) if isinstance(y, ast.Name)}
        нечитані += sum(1 for n in імена if n not in вжиті and not n.startswith("_"))
    імена = ({y.id for y in ast.walk(дерево) if isinstance(y, ast.Name)} | {x.name for x in ф}
             | {y.attr for y in ast.walk(дерево) if isinstance(y, ast.Attribute)})
    return dict(рядків=len(т.splitlines()), функцій=len(ф), без_док=без_док, широкі_except=широкі,
                нечитані=нечитані, змішані={i for i in імена if ЗМІШ.search(i)}, гомогліфи={i for i in імена if ГОМ.search(i)})


разом = {"ядро": collections.Counter(), "поза": collections.Counter()}
змішані, гомогліфи, великі, топ = {"ядро": set(), "поза": set()}, {"ядро": set(), "поза": set()}, [], {"except": [], "без_док": []}
for ф in sorted(f for f in os.listdir(".") if f.endswith(".py")):
    м = міра(ф); к = "ядро" if ф[:-3] in ЯДРО else "поза"
    for поле in ("рядків", "функцій", "без_док", "широкі_except", "нечитані"):
        разом[к][поле] += м[поле]
    змішані[к] |= м["змішані"]; гомогліфи[к] |= м["гомогліфи"]
    if м["рядків"] > 1500: великі.append((ф, м["рядків"]))
    if к == "ядро":
        топ["except"].append((м["широкі_except"], ф)); топ["без_док"].append((м["без_док"], ф))

def тека(п):
    return sum(len(open(os.path.join(d, f), encoding="utf-8").read().splitlines())
               for d, _, fs in os.walk(п) for f in fs if f.endswith((".py", ".js")))

print("── §5 п.16 · файли > 1500 рядків: %d" % len(великі))
for ф, n in sorted(великі, key=lambda x: -x[1]): print("   %-18s %5d" % (ф, n))
for к, назва in (("ядро", "ЯДРО (status.МОДУЛІ_ПРОДУКТУ, %d модулів)" % len(ЯДРО)), ("поза", "ПОЗА ЯДРОМ (.py верхнього рівня)")):
    r = разом[к]
    print("── %s: рядків %d · функцій %d" % (назва, r["рядків"], r["функцій"]))
    print("   §5 п.17 без докстрінга %d (%.0f %%) · §4 п.14 except Exception/голих %d · §4 п.13 нечитаних параметрів %d"
          % (r["без_док"], 100.0 * r["без_док"] / max(1, r["функцій"]), r["широкі_except"], r["нечитані"]))
    print("   §2 п.3 змішаних імен %d · §2 п.4 гомогліфів %d %s" % (len(змішані[к]), len(гомогліфи[к]), sorted(гомогліфи[к])))
print("   ядро, except по модулях (топ 5):", sorted(топ["except"], reverse=True)[:5])
print("   ядро, без докстрінга (топ 5):", sorted(топ["без_док"], reverse=True)[:5])
print("── теки: прилади/ %d · лабораторія/ %d · проби/ %d рядків (.py/.js)" % (тека("прилади"), тека("лабораторія"), тека("проби")))
print("── показ.html %d · worker.js %d · тест_показу.js %d рядків" % tuple(len(open(f, encoding="utf-8").read().splitlines()) for f in ("показ.html", "worker.js", "тест_показу.js")))
print("── §6 п.24 списки приладів:", {ім: bool(re.search(r"^\s*%s\s*=" % ім, open(ф, encoding="utf-8").read(), re.M))
      for ф, ім in (("gate_reach.py", "ПРИЛАДИ_КИРИЛИЦЕЮ"), ("audit_contracts.py", "ІНСТРУМЕНТИ_ІМЕНАМИ"), ("відбиток.py", "_НЕ_СИСТЕМА"), ("прилади.py", "ПРИЛАДИ"))})
print("── §1 п.1 status.py імпортує з приладів:", sorted(set(re.findall(r"^\s*(?:import|from)\s+([\wЀ-ӿ]+)", open("status.py", encoding="utf-8").read(), re.M)) - ЯДРО) or "нічого")
print("── §2 п.5 форми наміру у ядрі:", sorted({m for ф in ЯДРО for m in re.findall(r"fashion[-_]forward", open(ф + ".py", encoding="utf-8").read())}))
print("── §6 п.23 у zbirka.yml є кроки:", {к: bool(re.search(к, open("../.github/workflows/zbirka.yml", encoding="utf-8").read())) for к in ("build_артефакт", "звірка_вантажу", "jsdom", "тест_живого_шляху", "розділи_гейтів", "тест_протоколу", "досяжність", "audit_contracts")})
