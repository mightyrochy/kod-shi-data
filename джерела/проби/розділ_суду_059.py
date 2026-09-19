# -*- coding: utf-8 -*-
"""Приймальна проба Н-02-01 (сесія 4): фасад `outfit` знято. Друкує ФАКТ:
жодне ВИЗНАЧЕНЕ в новому модулі ім'я більше не відповідає на адресу `outfit.X`,
і суд на фіксованому образі дає ті самі знахідки, що й через колишній фасад."""
import sys, os, ast
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import outfit as O, суд_образу as С

ФАЙЛИ = ("реєстр_правил.py", "колір_образу.py", "формальність.py", "суд_образу.py",
         # поділ суд_образу.py (19.09.2026): імена суду стоять у дев'яти модулях за фасадом
         "суд_погода.py", "суд_блиск.py", "суд_інтерес.py", "суд_ремесло.py", "суд_чеклісти.py",
         "суд_силует.py", "суд_річ.py", "суд_намір.py", "суд_огляд.py")
def визначені(ф):
    т = ast.parse(open(os.path.join(os.path.dirname(O.__file__), ф), encoding="utf-8").read())
    return {n.name for n in т.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))} | {
            t.id for n in т.body if isinstance(n, ast.Assign)
            for t in n.targets if isinstance(t, ast.Name)}
ІМЕНА = {і for ф in ФАЙЛИ for і in визначені(ф)}
СВОЇ = {a.name for n in ast.parse(open(O.__file__, encoding="utf-8").read()).body
        if isinstance(n, ast.ImportFrom) for a in n.names}      # що `outfit` бере СОБІ
print("імен у чотирьох модулях: %d · реекспортує їх `outfit`: %s · бере собі на вхід: %s"
      % (len(ІМЕНА), sorted(і for і in ІМЕНА if hasattr(O, і) and і not in СВОЇ) or "жодного",
         ", ".join(sorted(ІМЕНА & СВОЇ))))
print("рядків: outfit %d (ціль наряду < 800), " % len(open(O.__file__, encoding="utf-8").read().split("\n"))
      + ", ".join("%s %d" % (ф[:-3], len(open(os.path.join(os.path.dirname(O.__file__), ф),
                                              encoding="utf-8").read().split("\n"))) for ф in ФАЙЛИ))

ОБРАЗ = [dict(id="сукня", слот="сукня", hex="#7a1020", площа=0.50, near=0.9),
         dict(id="пальто", слот="верхній_шар", hex="#1d3f7a", площа=0.30, near=0.7),
         dict(id="сумка", слот="сумка", hex="#c8a23a", площа=0.08, near=0.1)]
ОСОБА = dict(шкіра=dict(L=62.0, a=8.0, b=16.0), волосся=dict(L=22.0, a=3.0, b=5.0),
             очі=dict(L=30.0, a=1.0, b=4.0))
рез = С.review(ОСОБА, ОБРАЗ, нагода="весілля_гість", місце="весілля_вечірнє",
               година=19, темп_c=20)
for ст, d in рез["стани"].items():
    print("%-14s знахідок %d: %s" % (ст, len(d["знахідки"]),
          sorted("%s/%s" % (z["правило"], z["сила"]) for z in d["знахідки"])))
