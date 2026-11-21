"""Причина пунктів B7 (розмова мовною моделлю) і P8 (вибір схеми) чеклісту, коли мітку шляху передано й коли ні."""
import sys, os, io, contextlib, collections
sys.path.insert(0, os.getcwd())
import warnings; warnings.filterwarnings("ignore")
import паспорт_нагоди as ПН
src = open("pipeline.py", encoding="utf8").read()
i = src.index('if __name__ == "__main__":'); j = src.index("    в = перевірити_образ(F, речі", i)
блок = "\n".join(l[4:] for l in src[i:j].splitlines()[1:])
ns = {}
exec("from pipeline import *\nimport pipeline\n" + блок, ns)
from перевірка_образу import перевірити_образ
def чому(сц):
    в = перевірити_образ(ns["F"], ns["речі"], сц, тіло=ns["ТІЛО_П"])
    c = collections.Counter()
    def w(o):
        if isinstance(o, dict):
            if o.get("пункт") in ("B7", "P8") and o.get("стан") == "без входу": c[(o["пункт"], o.get("чому"))] += 1
            for v in o.values(): w(v)
        elif isinstance(o, list):
            for v in o: w(v)
    w(в.get("чеклісти")); return dict(c)
база = dict(нагода="побачення", смуга_погоди="cold")
print("мітки не передано:      ", чому(база))
print("передано (виклик 0):    ", чому(dict(база, розмова_шаром=ПН.розмова_для_суду({"джерело": "модель"}),
                                            вибір_схеми=__import__("вибір_палітри").для_суду({}))))
