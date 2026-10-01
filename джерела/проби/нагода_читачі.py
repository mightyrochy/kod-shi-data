# -*- coding: utf-8 -*-
"""НГ-2: які модулі продукту ТЛУМАЧАТЬ ключ нагоди сами, а не через виміри паспорта.

Тлумачить = порівнює значення нагоди з літералом (`нагода == "траур"`, `in (…)`), бере ним
рядок таблиці (`НАГОДА[нагода]`, `ваги.get(нагода)`), бере рядок таблиці літералом ключа
(`НАГОДА["весілля_гість"]`), читає таблиці нагод (`НАГОДА_У_МІСЦЕ`, `ПСЕВДОНІМИ_НАГОДИ`) чи
склеює поле «нагода» в слова для пошуку підрядків. Передати сценарій далі — не тлумачити.
Мета НГ-2: лишаються двоє — паспорт нагоди й мовний шар. Запуск: cd джерела && python3 проби/нагода_читачі.py"""
import ast, glob, os, re, sys; sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import паспорт_нагоди as ПН, формальність as Ф
КЛЮЧІ, ТАБЛ = set(ПН.ПСЕВДОНІМИ_НАГОДИ), {"НАГОДА_У_МІСЦЕ", "ПСЕВДОНІМИ_НАГОДИ", "ВИДИ_НАГОДИ"}
ЛИШЕ_НАГОДИ = КЛЮЧІ - set(Ф.МІСЦЯ_ДІАПАЗОНИ) - {"траур"}   # «театр» — ще й місце, «траур» — поле паспорта
НЕ = re.compile(r"^(тест_|батарея_|мутанти|стенд_|проба_|audit_|gate_|measure_|run_|build_|pair_test|verify|status)")
наг = lambda в: ((isinstance(в, ast.Name) and в.id == "нагода")
                 or (isinstance(в, ast.Subscript) and isinstance(в.slice, ast.Constant) and в.slice.value == "нагода")
                 or (isinstance(в, ast.Call) and getattr(в.func, "attr", "") == "get" and в.args
                     and isinstance(в.args[0], ast.Constant) and в.args[0].value == "нагода"))
def місця(д):
    for в in ast.walk(д):
        if isinstance(в, ast.Compare) and (наг(в.left) or any(наг(x) and not isinstance(о, (ast.In, ast.NotIn))
                                                               for x, о in zip(в.comparators, в.ops))):
            yield в.lineno, "порівнює"
        elif isinstance(в, ast.Subscript) and (наг(в.slice) or (isinstance(в.slice, ast.Constant) and в.slice.value in КЛЮЧІ)):
            yield в.lineno, "індекс"
        elif isinstance(в, ast.Call) and getattr(в.func, "attr", "") == "get" and в.args and (
                наг(в.args[0]) or (isinstance(в.args[0], ast.Constant) and в.args[0].value in КЛЮЧІ
                                   and re.match(r"^_*[А-ЯІЇЄҐA-Z_]+$", getattr(в.func.value, "id", "") or getattr(в.func.value, "attr", "")))):
            yield в.lineno, "індекс"
        elif isinstance(в, (ast.Name, ast.Attribute)) and (getattr(в, "id", "") in ТАБЛ or getattr(в, "attr", "") in ТАБЛ):
            yield в.lineno, "таблиця нагод"
        elif isinstance(в, ast.Dict) and any(isinstance(к, ast.Constant) and к.value in ЛИШЕ_НАГОДИ for к in в.keys):
            yield в.lineno, "таблиця нагод"
        elif isinstance(в, ast.Call) and getattr(в.func, "attr", "") == "join" and "'нагода'" in ast.dump(в):
            yield в.lineno, "слова"
рез = {ф: м for ф in sorted(glob.glob("*.py")) if not НЕ.match(ф)
       for м in [sorted(set(місця(ast.parse(open(ф, encoding="utf-8").read()))))] if м}
for ф, м in рез.items():
    print("%-24s %s" % (ф, ", ".join("%d %s" % x for x in м[:6]) + (" …+%d" % (len(м) - 6) if len(м) > 6 else "")))
print("модулів, що тлумачать ключ нагоди: %d (поза паспортом і мовним шаром: %d)"
      % (len(рез), len(set(рез) - {"паспорт_нагоди.py", "мовний_шар.py"})))
