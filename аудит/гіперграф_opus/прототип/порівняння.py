# -*- coding: utf-8 -*-
"""ПОРІВНЯННЯ на тих самих прикладах (записка §1, §7): запропонована схема ↔ чинний
`джерела/graph.py` бази e70c3c3 (справжній модуль, імпорт лише для читання) ↔
простіша попарна модель.

Перетворення в знахідки чинного формату — наше, і воно ДОБРОЗИЧЛИВЕ до чинної
системи: VIOLATE → знахідка з `сила_нп` за категорією soft (0.5, `реєстр_сила._КАТ_У_НП`),
BORDER → hint (0.25), UNKNOWN → «питання», SUPPORT не емітується (позитивного каналу
нема — звіт субагента й `композитор_оцінка.py:165-183`). Тобто ми даємо чинному графу
рівно ту інформацію, яку дав би наш вимір, і дивимось, що він із нею робить.

Запуск: python3 порівняння.py  (потрібен робочий каталог репозиторію поруч: ../../../джерела)
"""
import contextlib
import io
import os
import sys
sys.path.insert(0, ".")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(1, os.path.normpath(os.path.join(HERE, "..", "..", "..", "джерела")))

import graph as G                    # чинний модуль бази (лише читання)
from ядро import VIOLATE, BORDER, UNKNOWN, SUPPORT, handles
import приклади as П

СИЛА = {VIOLATE: 0.5, BORDER: 0.25}


def to_findings(hg):
    зн = []
    for k, f in sorted(hg.F.items()):
        if f.verdict not in (VIOLATE, BORDER, UNKNOWN):
            continue
        cul = (f.detail or {}).get("culprits") or [x.id for x in f.bind]
        z = dict(правило=f.tid, речі=list(cul), суть=f.tid, чому="")
        if f.verdict == UNKNOWN:
            z.update(сила="питання", регістр="питання", сила_нп=0.25)
        else:
            z.update(сила="soft" if f.verdict == VIOLATE else "hint", сила_нп=СИЛА[f.verdict])
        зн.append(z)
    return зн


def current_graph(hg):
    речі = [dict(id=x.id, назва=x.id, слот=x.slot) for x in hg.items.values()]
    г = G.граф(to_findings(hg), речі)
    в = G.вузол_напруги(г)
    return г, в


def main():
    with contextlib.redirect_stdout(io.StringIO()):
        hgs = [("1 невідомі дані", П.example_1(True)), ("2 свідомий розрив", П.example_2(True)),
               ("3 власна річ", П.example_3(True)), ("4 якір об'єму", П.example_4(True))]
    for name, hg in hgs:
        print("\n== %s ==" % name)
        tens = [(k[0], [x.id for x in handles(f)]) for k, f in sorted(hg.F.items()) if f.verdict == VIOLATE]
        unk = [(k[0], f.missing) for k, f in sorted(hg.F.items()) if f.verdict == UNKNOWN]
        sup = sorted({k[0] for k, f in hg.F.items() if f.verdict == SUPPORT})
        print("  ЗАПРОПОНОВАНА: напруги з ручками %s" % tens)
        print("                 без входу %s" % unk)
        print("                 підтримки %s" % sup)
        г, в = current_graph(hg)
        print("  ЧИННИЙ graph.py: вузол напруги = %s (%.2f); вузли: %s" % (
            (в or {}).get("вузол"), (в or {}).get("напруга") or 0.0,
            [(u["вузол"], u["напруга"]) for u in г["вузли"]][:6]))
        print("                   рядок: %s" % G.рядок_вузла(в, г))
        b = П.pairwise_baseline(hg)
        print("  ПОПАРНА: сума=%s (%d спрацювань); невідоме → 0, множинне/особове — поза моделлю" % (b[0], len(b[1])))

    print("\n== ВЛАСТИВОСТІ ЧИННОГО graph.py, відтворені на справжньому модулі ==")
    речі = [dict(id="t", назва="t", слот="верх"), dict(id="b", назва="b", слот="низ"),
            dict(id="s", назва="s", слот="взуття"), dict(id="g", назва="g", слот="сумка")]

    def knot(зн):
        г = G.граф(зн, речі)
        в = G.вузол_напруги(г)
        return [(р["правило"], р["вузли"], р["напруга"]) for р in г["ребра"]], (в or {}).get("вузол"), (в or {}).get("напруга")
    print("  P1 зона з тексту, відмінок: «у стегнах» →", knot([dict(правило="K-FIT-03", речі=["b"], сила_нп=0.5, суть="край у стегнах")]))
    print("     те саме, «стегна» в лапках →", knot([dict(правило="K-FIT-03", речі=["b"], сила_нп=0.5, суть="край на рівні «стегна»")]))
    print("  P2 ребро над 3 із 4 слотів →", knot([dict(правило="K-X", речі=["t", "s", "g"], сила_нп=0.5, суть="x")]))
    print("  P3 симетричне ребро, нічия →", knot([dict(правило="K-SIL-01", речі=["t", "b"], сила_нп=0.6, суть="x")]))
    print("  P4 мовчання (жодної знахідки) →", knot([]))
    print("  P5 «лишити колону» K-COL-01 hint 0.25 (позитив) →",
          knot([dict(правило="K-COL-01", речі=["t", "b"], сила_нп=0.25, суть="колона — лишити")]))
    print("  P6 сума різнорідних правил на вузлі →",
          knot([dict(правило="K-COL-06", речі=["t", "b"], сила_нп=0.4, суть="x"),
                dict(правило="K-SIL-01", речі=["t", "b"], сила_нп=0.6, суть="y")]))


if __name__ == "__main__":
    main()
