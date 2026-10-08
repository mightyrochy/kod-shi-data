# -*- coding: utf-8 -*-
"""ПЕРЕВІРКИ ІНВАРІАНТІВ прототипу (записка §7.3). Друкують факт, не «✔».

I1 звуковість: інтервальний вердикт OK/VIOLATE (SUPPORT/ABSENT) не суперечить ЖОДНІЙ
   точковій підстановці входів (включно з невідомими, підставленими з області) і
   порогу зі смуги; BORDER/UNKNOWN дозволені бути «зайво обережними» — міряємо, наскільки.
I2 інкрементальність: після випадкових замін і змін нагоди знімок вердиктів
   збігається з повною перебудовою з нуля.
I3 позиції: стильовий розрив над PHYSICAL/PERSONAL завжди REJECTED; позиція над
   не-порушенням — VOID; прийнята позиція не міняє виміру (verdict у F той самий).
I4 детермінізм: дві побудови з тих самих входів — той самий знімок.

Синтетичні образи з фіксованим зерном; запуск: python3 перевірки.py [зерно] [образів]
"""
import random
import sys
sys.path.insert(0, ".")
from ядро import (Iv, Item, HG, classify, OK, VIOLATE, SUPPORT, ABSENT, BORDER, UNKNOWN, NA,
                  DELIBERATE_BREAK, STANCE_REJECTED, STANCE_VOID, STANCE_OK)
import шаблони as Ш

SLOTS = ["верх", "низ", "сукня", "верхній_шар", "взуття", "сумка", "шарф", "пояс", "сережки"]
WORDS = ["бордо", "хвоя", "кемел", "темно-синій", "бірюза", "мідь", "сірий", "чорний", "молочний"]
FABRICS = ["suede", "satin", "leather", "wool", "canvas", None]


def rnd_iv(r, lo, hi, maxw):
    a = r.uniform(lo, hi)
    w = r.uniform(0, maxw)
    return Iv(a, min(hi, a + w))


def rng(v):
    """Позначити інтервал як МНОЖИННИЙ діапазон (не невизначеність): точкова
    підстановка його не чіпає."""
    v.src = "range"
    return v


def rnd_item(r, slot, i):
    h0 = r.uniform(0, 359)
    unknown_col = r.random() < 0.1
    a = dict(
        L=None if unknown_col else rnd_iv(r, 5, 95, 15),
        C=None if unknown_col else rnd_iv(r, 0, 60, 12),
        h=None if unknown_col else Iv(h0, h0 + r.uniform(0, 40)),
        colour_word=r.choice(WORDS + [None]),
        formality=None if r.random() < 0.1 else rng(rnd_iv(r, 1, 9, 2)),
        interest=None if r.random() < 0.1 else rnd_iv(r, 0, 1, 0.3),
        volume=None if r.random() < 0.1 else rnd_iv(r, 0, 1, 0.3),
        fabric=r.choice(FABRICS),
        metal=r.choice(["gold", "silver", None, None]),
        anchor=r.random() < 0.2,
        closed=r.random() < 0.5,
        type=r.choice(["mini", "midi", "maxi", None]),
    )
    if a["L"] is None:
        a.pop("L"); a.pop("C"); a.pop("h")
    return Item("%s_%d" % (slot, i), slot, **a)


def rnd_outfit(r, n0):
    slots = r.sample(SLOTS, r.randint(3, 7))
    if "сукня" in slots and "верх" in slots:
        slots.remove("верх")
    return [rnd_item(r, s, n0 + k) for k, s in enumerate(slots)]


def rnd_ctx(r):
    return dict(formality=None if r.random() < 0.1 else rng(rnd_iv(r, 1, 9, 2)),
                precip=r.choice(["yes", "no", None]),
                intent=r.choice(["conventional", "statement", "context_optimal"]))


def rnd_person(r):
    return dict(contrast_L=None if r.random() < 0.2 else rnd_iv(r, 10, 60, 8),
                skin_L=None if r.random() < 0.2 else rnd_iv(r, 30, 80, 6),
                whr=None if r.random() < 0.3 else rnd_iv(r, 0.65, 0.9, 0.05),
                veto_types=r.choice([[], ["mini"]]), veto_colours=r.choice([[], ["бордо"]]))


def point_of(r, v):
    """Точкова підстановка: Iv → точка всередині (для тону — на дузі)."""
    if isinstance(v, Iv):
        if v.src == "range":
            return v
        x = r.uniform(v.lo, v.hi)
        return Iv(x)
    return v


def pointify(r, items, person, ctx):
    its = []
    for it in items:
        a = {}
        for k, v in it.a.items():
            if k == "h" and isinstance(v, Iv):
                x = r.uniform(v.lo, v.hi) % 360.0
                a[k] = Iv(x)
            else:
                a[k] = point_of(r, v)
        its.append(Item(it.id, it.slot, pinned=it.pinned, own=it.own, **a))
    pe = {k: point_of(r, v) for k, v in person.items()}
    cx = {k: point_of(r, v) for k, v in ctx.items()}
    # невідомі входи — підставити з області значень
    if pe.get("whr") is None:
        pe["whr"] = Iv(r.uniform(0.6, 0.95))
    if cx.get("precip") is None:
        cx["precip"] = r.choice(["yes", "no"])
    return its, pe, cx


def sample_threshold_verdict(r, hg, f):
    """Вердикт точкового екземпляра з порогом, узятим зі смуги навмання."""
    t = hg.T[f.tid]
    if f.verdict in (UNKNOWN, NA) or f.value is None:
        return f.verdict
    d, lo, hi, _ = f.band
    th = r.uniform(lo, hi)
    v, _ = classify(t.polarity, d, f.value, th, th)
    return v


def i1_soundness(seed, n_outfits, n_points=12):
    r = random.Random(seed)
    checked = contradictions = border_total = border_decidable = 0
    by_tid = {}
    for n in range(n_outfits):
        items, person, ctx = rnd_outfit(r, n * 10), rnd_person(r), rnd_ctx(r)
        hg = HG(Ш.ALL, person, ctx, items)
        pts = []
        for _ in range(n_points):
            its, pe, cx = pointify(r, items, person, ctx)
            pts.append(HG(Ш.ALL, pe, cx, its))
        for k, f in hg.F.items():
            vs = []
            for ph in pts:
                g = ph.F.get(k)
                if g is None:
                    continue           # прив'язка зникла через видимість у точковому світі
                vs.append(sample_threshold_verdict(r, ph, g))
            if not vs:
                continue
            checked += 1
            decided = [v for v in vs if v not in (UNKNOWN, NA)]
            if f.verdict in (OK, VIOLATE, SUPPORT, ABSENT):
                bad = [v for v in decided if v != f.verdict and v != BORDER]
                if bad:
                    contradictions += 1
                    by_tid.setdefault(f.tid, 0)
                    by_tid[f.tid] += 1
            elif f.verdict == BORDER:
                border_total += 1
                if decided and len(set(decided)) == 1:
                    border_decidable += 1
    return dict(instances_checked=checked, contradictions=contradictions, by_template=by_tid,
                border=border_total, border_all_points_agree=border_decidable)


def i2_incremental(seed, n_outfits, n_steps=8):
    r = random.Random(seed + 1)
    mismatches = steps = 0
    saved = 0
    for n in range(n_outfits):
        items, person, ctx = rnd_outfit(r, n * 100), rnd_person(r), rnd_ctx(r)
        hg = HG(Ш.ALL, person, ctx, items)
        for s in range(n_steps):
            steps += 1
            ev0 = hg.evals
            if r.random() < 0.75:
                slot = r.choice(list(hg.items) + ["шарф", "пояс"])
                new = None if (r.random() < 0.15 and len(hg.items) > 2) else rnd_item(r, slot, 10000 + n * 100 + s)
                if new is not None and new.slot == "сукня" and "верх" in hg.items:
                    continue
                hg.replace(slot, new)
            else:
                fld = r.choice(["formality", "precip", "intent"])
                hg.set_ctx(fld, rnd_ctx(r)[fld])
            inc = hg.evals - ev0
            full = HG(Ш.ALL, hg.person, hg.ctx, list(hg.items.values()))
            saved += len(full.F) - inc
            if full.snapshot() != hg.snapshot():
                mismatches += 1
    return dict(steps=steps, mismatches=mismatches, evaluations_saved_vs_full=saved)


def i3_stances(seed, n_outfits):
    r = random.Random(seed + 2)
    phys_rejected = phys_total = void_ok = void_total = measured_unchanged = acc = 0
    for n in range(n_outfits):
        items, person, ctx = rnd_outfit(r, n * 10), rnd_person(r), rnd_ctx(r)
        hg = HG(Ш.ALL, person, ctx, items)
        for k, f in list(hg.F.items()):
            t = hg.T[f.tid]
            ids = list((f.detail or {}).get("culprits") or [x.id for x in f.bind])
            before = f.verdict
            st = hg.declare(DELIBERATE_BREAK, f.tid, ids, "test", by="stylist")
            if t.cls in ("PHYSICAL", "PERSONAL") and before in (VIOLATE, BORDER):
                phys_total += 1
                phys_rejected += st["status"] == STANCE_REJECTED
            if before not in (VIOLATE, BORDER):
                void_total += 1
                void_ok += st["status"] == STANCE_VOID
            if st["status"] == STANCE_OK:
                acc += 1
                measured_unchanged += hg.F[k].verdict == before
            hg.stances.clear()
    return dict(physical_or_personal_breaks=phys_total, rejected=phys_rejected,
                non_violations=void_total, void=void_ok, accepted=acc, measurement_unchanged=measured_unchanged)


def i4_determinism(seed, n_outfits):
    r = random.Random(seed + 3)
    same = 0
    for n in range(n_outfits):
        items, person, ctx = rnd_outfit(r, n * 10), rnd_person(r), rnd_ctx(r)
        same += HG(Ш.ALL, person, ctx, items).snapshot() == HG(Ш.ALL, person, ctx, items).snapshot()
    return dict(outfits=n_outfits, identical=same)


if __name__ == "__main__":
    seed = int(sys.argv[1]) if len(sys.argv) > 1 else 20261008
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 150
    print("зерно", seed, "образів", n)
    print("I1 звуковість:", i1_soundness(seed, n))
    print("I2 інкрементальність:", i2_incremental(seed, n))
    print("I3 позиції:", i3_stances(seed, n))
    print("I4 детермінізм:", i4_determinism(seed, n))
