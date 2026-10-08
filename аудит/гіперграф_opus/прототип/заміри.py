# -*- coding: utf-8 -*-
"""ЗАМІРИ СКЛАДНОСТІ прототипу (записка §8). Той самий файл ганяється в CPython і в
Pyodide 0.26.4 (Node) — числа в записці взято з обох прогонів.

Синтетичний пул: 17 слотів продукту (міст_пакет.УСІ_СЛОТИ) × 25 речей = 425 — порядок
середнього пулу руки 1 (аудит «405–441, сер. ~425»). Атрибути випадкові (зерно фіксоване):
це заміри ЧАСУ механіки, не якості.

Запуск: python3 заміри.py [зерно]
"""
import random
import sys
import time
sys.path.insert(0, ".")
from ядро import Iv, Item, HG, repair, tradeoffs, VIOLATE
import шаблони as Ш

SLOTS17 = ("верх", "низ", "сукня", "комплект", "верхній_шар", "взуття", "сумка", "пояс",
           "головний_убір", "шарф", "прикраси", "сережки", "намисто", "кольє",
           "браслет", "каблучка", "брошка")
WORDS = ["бордо", "хвоя", "кемел", "темно-синій", "бірюза", "мідь", "сірий", "чорний", "молочний"]


def item(r, slot, i):
    h0 = r.uniform(0, 359)
    L0, C0 = r.uniform(10, 90), r.uniform(0, 50)
    wide = r.random() < 0.5                      # половина кольорів «зі слова»
    return Item("%s#%d" % (slot, i), slot,
                L=Iv(L0, L0 + (15 if wide else 4)), C=Iv(C0, C0 + (15 if wide else 4)),
                h=Iv(h0, h0 + (30 if wide else 8)), colour_word=r.choice(WORDS),
                formality=Iv(r.randint(1, 7), r.randint(7, 9), "range"),
                interest=Iv(r.uniform(0, 1)), volume=Iv(r.uniform(0, 1)),
                fabric=r.choice(["suede", "satin", "leather", "wool", "canvas"]),
                metal=r.choice(["gold", "silver", None]), anchor=r.random() < 0.15,
                closed=r.random() < 0.5)


def make_pool(r, per_slot=25):
    return {s: [item(r, s, i) for i in range(per_slot)] for s in SLOTS17}


OUTFIT_SLOTS = ("верх", "низ", "верхній_шар", "взуття", "сумка", "шарф", "сережки")


def ms(t0):
    return (time.perf_counter() - t0) * 1000.0


def main(seed=20261008, n_outfits=60):
    r = random.Random(seed)
    pool = make_pool(r)
    person = dict(contrast_L=Iv(30, 40), skin_L=Iv(60, 64), whr=Iv(0.74, 0.78), veto_types=["mini"])
    ctx = dict(formality=Iv(4, 6, "range"), precip="yes", intent="conventional")
    out = {}

    # M1: повна побудова образу з 7 речей
    t, inst, evs, hgs = 0.0, 0, 0, []
    for k in range(n_outfits):
        its = [r.choice(pool[s]) for s in OUTFIT_SLOTS]
        t0 = time.perf_counter()
        hg = HG(Ш.ALL, person, ctx, its)
        t += ms(t0)
        inst += len(hg.F)
        evs += hg.evals
        hgs.append(hg)
    out["M1_full_build_ms"] = round(t / n_outfits, 3)
    out["M1_instances"] = round(inst / n_outfits, 1)

    # M2: інкрементальна заміна однієї речі проти повної перебудови
    ti = tf = 0.0
    ei = ef = 0
    for hg in hgs:
        s = r.choice(OUTFIT_SLOTS)
        y = r.choice(pool[s])
        e0 = hg.evals
        t0 = time.perf_counter()
        hg.replace(s, y)
        ti += ms(t0)
        ei += hg.evals - e0
        t0 = time.perf_counter()
        full = HG(Ш.ALL, person, ctx, list(hg.items.values()))
        tf += ms(t0)
        ef += full.evals
    out["M2_incremental_ms"] = round(ti / n_outfits, 3)
    out["M2_incremental_evals"] = round(ei / n_outfits, 1)
    out["M2_full_rebuild_ms"] = round(tf / n_outfits, 3)
    out["M2_full_evals"] = round(ef / n_outfits, 1)

    # M3: ремонт одного VIOLATE по всіх ручках (25 кандидатів на ручку)
    tr, tried, n = 0.0, 0, 0
    for hg in hgs[:20]:
        vs = [k for k, f in hg.F.items() if f.verdict == VIOLATE]
        if not vs:
            continue
        t0 = time.perf_counter()
        res = repair(hg, vs[0], pool)
        tr += ms(t0)
        tried += res["tried"]
        n += 1
    out["M3_repair_ms"] = round(tr / max(1, n), 2)
    out["M3_candidates"] = round(tried / max(1, n), 1)

    # M4: компроміси 0–2 заміни у 2 слотах (1+50+625 варіантів) і в 3 слотах
    for slots, k, tag in ((("сумка", "низ"), None, "M4_tradeoffs_2slots_full"),
                          (("сумка", "низ"), 5, "M4_tradeoffs_2slots_beam5"),
                          (("сумка", "низ", "шарф"), 5, "M4_tradeoffs_3slots_beam5")):
        hg = hgs[0]
        t0 = time.perf_counter()
        res = tradeoffs(hg, list(slots), pool, k_per_slot=k)
        out[tag + "_ms"] = round(ms(t0), 1)
        out[tag + "_variants"] = res["variants"]
        out[tag + "_front"] = res["front_size"]

    # M5: закріплена річ × увесь пул — лише попарні шаблони (повна матриця сумісності з нею)
    pin = Item("own#1", "взуття", pinned=True, own=True, L=Iv(28, 32), C=Iv(12, 18), h=Iv(55, 65),
               colour_word="кемел", formality=Iv(3, 5, "range"), interest=Iv(0.3), fabric="suede", metal="gold")
    pair_t = [t for t in Ш.ALL if t.scope == "pair"]
    t0 = time.perf_counter()
    cnt = 0
    for s in SLOTS17:
        for y in pool[s]:
            if y.slot == pin.slot:
                continue
            g = HG(pair_t, person, ctx, [pin, y])
            cnt += len(g.F)
    out["M5_pinned_x_pool_ms"] = round(ms(t0), 1)
    out["M5_pair_instances"] = cnt

    # M6: наївний перебір 7 слотів по 25 — лише оцінка порядку, не прогін
    combos = 25 ** len(OUTFIT_SLOTS)
    out["M6_naive_combinations"] = combos
    out["M6_naive_hours_at_M1"] = round(combos * out["M1_full_build_ms"] / 3.6e6, 1)
    return out


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261008
    import platform
    print("runtime:", platform.python_implementation(), sys.version.split()[0], sys.platform)
    for k, v in main(seed).items():
        print("%-32s %s" % (k, v))
