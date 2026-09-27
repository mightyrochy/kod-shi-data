# -*- coding: utf-8 -*-
"""П-5: місця, де КОД СКЛАДАЄ речення в `суть`/`ремонт` знахідки (наряд: «кодом заяви з
полями, а не реченням»). `складене` — аргумент, у якому є `%`, f-рядок, `.format`, `.join`
чи конкатенація зі змінною: речення пише сам код. `статичне` — літерал (чи кортеж
літералів): це СУТЬ КОРПУСУ, яку код лише везе, і вона за рішенням Ч-1/Ч-3 лишається
вільним текстом. Друге число — скільки знахідок живого вердикта вже несуть `заяви`
(внутрішня мова поруч із прозою). Запуск із `джерела`: python3 проби/суть_ремонт_складені.py"""
import ast, io, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
ЛІТ = lambda x: isinstance(x, ast.Constant) and isinstance(x.value, str)
СТАТ = lambda x: (ЛІТ(x) or (isinstance(x, ast.BinOp) and isinstance(x.op, ast.Add)
                             and СТАТ(x.left) and СТАТ(x.right))
                  or (isinstance(x, (ast.List, ast.Tuple)) and all(СТАТ(e) for e in x.elts)))
скл, стат = collections.Counter(), 0
for ф in sorted(x for x in os.listdir(".") if x.endswith(".py")):
    try:
        дерево = ast.parse(io.open(ф, encoding="utf-8").read(), filename=ф)
    except SyntaxError:
        continue
    for в in ast.walk(дерево):
        if isinstance(в, ast.keyword) and в.arg in ("суть", "ремонт"):
            if СТАТ(в.value):
                стат += 1
            else:
                скл[ф] += 1
print("СКЛАДЕНИХ КОДОМ (мета наряду — заява з полями): %d у %d файлах" % (sum(скл.values()), len(скл)))
for ф, к in скл.most_common(12):
    print("  %-26s %d" % (ф, к))
print("  …решта файлів: %d місць" % (sum(скл.values()) - sum(к for _, к in скл.most_common(12))))
print("СТАТИЧНИХ ЛІТЕРАЛІВ (суть КОРПУСУ, лишається вільним текстом): %d" % стат)
import json, bridge as B
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
ід = [x["id"] for с in ("верх", "низ", "взуття", "сумка") for x in (r["кандидати"].get(с) or [])[:1]]
вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
зн = [z for о in ((вм.get("вердикт") or {}).get("образи") or []) for z in (о.get("знахідки") or [])]
print("ЖИВИЙ ВЕРДИКТ: знахідок %d · із `заяви` %d · із `суть` %d · із `ремонт` %d"
      % (len(зн), sum(1 for z in зн if z.get("заяви")), sum(1 for z in зн if z.get("суть")),
         sum(1 for z in зн if z.get("ремонт"))))
