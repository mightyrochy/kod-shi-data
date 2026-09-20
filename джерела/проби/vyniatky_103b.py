# -*- coding: utf-8 -*-
"""Проба рядка 103б · СТАНДАРТ §4 п.14 у сім'ї «суд / аксесуари / fit / граф / конвеєр».
Друкує ФАКТ: скільки широких `except` було в кожному файлі сім'ї на main і скільки
лишилось; і показує на ЖИВОМУ місці, що змінилось для споживача, коли шар падає.
Таблиця «що ловилось · клас · як закрито» — у тілі PR.
Прогін:  cd джерела && python3 проби/vyniatky_103b.py"""
import ast, json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ); os.chdir(ТУТ)
БУЛО = {"суд_чеклісти": 5, "суд_від_моделі": 3, "суд_блиск": 1, "суд_інтерес": 1, "суд_річ": 1,
        "суд_огляд": 1, "аксесуари_структура": 3, "верхнє_суд": 1, "fit": 1, "outfit": 1,
        "hypergraph": 1, "graph": 1, "language_gate": 1, "дистанція": 1, "pipeline": 3, "profile": 2}


def широких(мод):
    д = ast.parse(open(мод + ".py", encoding="utf-8").read())
    return sum(1 for x in ast.walk(д) if isinstance(x, ast.ExceptHandler)
               and (x.type is None or (isinstance(x.type, ast.Name)
                                       and x.type.id in ("Exception", "BaseException"))))


print("── §4 п.14 у сім'ї: файл · було на main · стало")
разом_б = разом_с = 0
for мод, б in sorted(БУЛО.items()):
    с = широких(мод); разом_б += б; разом_с += с
    print("   %-22s %d → %d%s" % (мод, б, с, "" if с == 0 else "   ⚠ лишилось"))
print("   РАЗОМ %d → %d" % (разом_б, разом_с))

print("── демонстрація на живому місці: `суд_чеклісти.входи_палітри`, колірний шар упав")
import palettes, суд_чеклісти as Ч
palettes.осі = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("колірний шар упав"))
try:
    вх = Ч.входи_палітри({"шкіра": {"L": 60}})
    print("   ПІСЛЯ: не впало — проба недійсна")
except Exception as e:                                   # саме це й летить у bridge.виклик
    print("   ДО   : `except Exception → return {}` — усі 7 пунктів чекліста палітри")
    print("          ставали «без входу», і причини не було ніде")
    print("   ПІСЛЯ: летить у `bridge.виклик` → %s"
          % json.dumps(dict(помилка="%s: %s" % (type(e).__name__, e)), ensure_ascii=False))
    print("          (форма `міст_http`; показ.html: `if (r.помилка) throw new Error(...)`)")
