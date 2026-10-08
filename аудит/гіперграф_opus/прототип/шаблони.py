# -*- coding: utf-8 -*-
"""ЗРАЗКОВІ ШАБЛОНИ ГІПЕРРЕБЕР для прототипу (НЕ перенесення правил продукту).

Кожен шаблон — ілюстрація типу взаємодії з записки §4: попарна, множинна,
річ×людина, річ×нагода, позитивна, керована видимістю. Пороги взято з бази
знань там, де вона їх дає, з її ж тіром; де бази нема — позначено SYN (синтетика,
лише для демонстрації механіки). Якорі `kb` — файл/правило бази на e70c3c3.

Жоден поріг тут не калібрований на людських оцінках. Смуга [lo, hi] — це
розмитість ПОРОГУ в самій базі, не наш допуск; ширина смуги — теж конвенція.
"""
from ядро import Iv, Template, hue_dist, box_dist, iv_max, iv_min

CHROMA_ACHROM = 5.0          # C* < 5 — ахроматичне (тема-2 L572–575: опубліковано 5; код має 2.0)
LARGE = ("верх", "низ", "сукня", "верхній_шар")
NEAR_FACE = ("верх", "сукня", "верхній_шар", "шарф")


def lab_box(it):
    """L/C/h-інтервали речі → коробка в Lab (для ΔE76). None, якщо колір невідомий."""
    L, C, h = it.get("L"), it.get("C"), it.get("h")
    if L is None or C is None or h is None:
        return None
    import math
    # межі a/b для сектора (C ∈ [c0,c1], h ∈ [h0,h1]) — по кутах і осях усередині дуги
    pts = []
    hs = [h.lo, h.hi] + [ang for ang in (0, 90, 180, 270) if (ang - h.lo) % 360 <= (h.hi - h.lo)]
    for c in (C.lo, C.hi):
        for ang in hs:
            r = math.radians(ang)
            pts.append((c * math.cos(r), c * math.sin(r)))
    a = [p[0] for p in pts]
    b = [p[1] for p in pts]
    return {"L": L, "a": Iv(min(a), max(a)), "b": Iv(min(b), max(b))}


def chromatic(it):
    C = it.get("C")
    return C is not None and C.lo >= CHROMA_ACHROM


# ── 1. ВЕТО ЛЮДИНИ (PERSONAL, річ×людина) ──────────────────────────────────
def _veto_measure(hg, bind, p):
    x = bind[0]
    vetoed = set(hg.person.get("veto_types") or ()) | set(hg.person.get("veto_colours") or ())
    hit = {x.get("type"), x.get("colour_word")} & vetoed
    return Iv(1.0 if hit else 0.0), [], ({"hit": sorted(hit)} if hit else {})


VETO = Template(
    "PERSON.VETO", "PERSONAL", "constraint", "item", _veto_measure,
    band=lambda hg, p: ("le", 0.5, 0.5, "bool"),
    reads=("veto_types", "veto_colours"), tier="her_word",
    kb="паспорт_нагоди.СХЕМА_ПАСПОРТА[вето]; profile.ЛЮДИНА_ПИТАННЯ[жорстке_ні]; K-PC-08",
    uses_visibility=False)


# ── 2. ПОГОДА × ТКАНИНА (PHYSICAL, річ×нагода) ─────────────────────────────
def _wet_applies(hg, bind):
    if hg.ctx.get("precip") == "no":
        return "no", {}, "dry"
    return "yes", {}, ""


def _wet_measure(hg, bind, p):
    x = bind[0]
    f = x.get("fabric")
    if f is None:
        return None, ["item.fabric"], {}
    sens = {"suede": 1.0, "satin": 1.0, "nubuck": 1.0, "canvas": 0.6}.get(f, 0.0)
    pr = hg.ctx.get("precip")
    wet = Iv(0.0, 1.0) if pr is None else Iv(1.0)      # невідомо → уся область
    return wet.mul(sens), (["ctx.precip"] if pr is None else []), {"fabric": f}


WET = Template(
    "WEA.WET_FABRIC", "PHYSICAL", "constraint", "item", _wet_measure,
    band=lambda hg, p: ("le", 0.5, 0.5, "sensitivity"),
    applies=_wet_applies, accepts=lambda hg, it: it.slot in ("взуття", "сумка", "верхній_шар"),
    reads=("precip",), tier="T2", kb="тема-11 K-OUT-44/45; K-WEA-04..08; CLAUDE.md п.17 (замша з умовою)",
    uses_visibility=False)


# ── 3. ДОРЕЧНІСТЬ НАГОДІ (CONTEXTUAL, річ×нагода, порядкова шкала 1–10) ────
def _form_measure(hg, bind, p):
    x = bind[0]
    fi, band = x.get("formality"), hg.ctx.get("formality")
    if fi is None:
        return None, ["item.formality"], {}
    if band is None:
        return None, ["ctx.formality"], {}
    # ОШАТНІСТЬ — МНОЖИННИЙ ДІАПАЗОН, НЕ ЕПІСТЕМІЧНИЙ ІНТЕРВАЛ. «Річ доречна на 5–7» і
    # «нагода приймає 4–6» — це множини рівнів (тема-5 VIII: |a−b|≤2 ⇔ перетин
    # [a−1,a+1] і [b−1,b+1]), а не «невідома точка десь між». Перша версія віднімала
    # їх як невизначеності (Iv(band.lo−fi.hi, band.lo−fi.lo)) — перевірка I1 знайшла
    # 23 суперечності саме тут. Розрив — точка: на скільки щаблів НАЙВИЩИЙ рівень
    # речі нижчий за НАЙНИЖЧИЙ рівень нагоди (порядкова різниця, не метрика).
    gap = max(0.0, band.lo - fi.hi)
    return Iv(gap), [], {"item": repr(fi), "occasion": repr(band)}


FORMALITY = Template(
    "CTX.FORMALITY_BELOW", "CONTEXTUAL", "constraint", "item", _form_measure,
    # «явно чуже» — 3+ щаблі нижче (CLAUDE.md п.17); 1–2 — «трохи нижче смуги», у пулі
    band=lambda hg, p: ("le", 1.0, 2.0, "steps"),
    reads=("formality",), tier="owner_decision+T3",
    kb="CLAUDE.md п.17 (3+ щаблі — поза пулом, 1–2 — суд); тема-3 §14 (драбина формальності)",
    uses_visibility=False)


# ── 4. ВІДЛУННЯ АКЦЕНТУ (STYLISTIC, позитивна, пара) ───────────────────────
def _echo_accepts(hg, it):
    return chromatic(it)


def _echo_applies(hg, bind):
    a, b = bind
    if a.slot in LARGE and b.slot in LARGE:
        return "no", {}, "two_large_surfaces"   # відлуння — між віддаленими точками, не дві площі
    return "yes", {}, ""


def _echo_measure(hg, bind, p):
    a, b = bind
    # нормовані відхилення: тон / 25°, світлота / 15, хрома / 15 (SYN-масштаби);
    # «відлуння» — коли ВСІ три малі, тож міра — максимум (монотонний за інтервалами)
    dh = hue_dist(a.get("h"), b.get("h")).mul(1 / 25.0)
    dL = (a.get("L") - b.get("L")).abs().mul(1 / 15.0)
    dC = (a.get("C") - b.get("C")).abs().mul(1 / 15.0)
    return iv_max([dh, dL, dC]), [], {"dh": repr(dh), "dL": repr(dL), "dC": repr(dC)}


ECHO = Template(
    "COMP.ECHO", "STYLISTIC", "support", "pair", _echo_measure,
    band=lambda hg, p: ("le", 0.8, 1.1, "norm_max"),
    applies=_echo_applies, accepts=_echo_accepts, roles=("a", "b"), tier="T3/SYN",
    kb="тема-4 K-COMP-05 (акцент ≥2 точки або єдиний фокус); тема-3 §6 (числа — hint)")


# ── 5. ДОПОВНЕННЯ ЗА КОЛОМ ХУДОЖНИКА (STYLISTIC, позитивна, понятійна) ────
COMPLEMENTS = {frozenset(("бордо", "хвоя")), frozenset(("кемел", "темно-синій")),
               frozenset(("бірюза", "мідь"))}


def _compl_measure(hg, bind, p):
    a, b = bind
    wa, wb = a.get("colour_word"), b.get("colour_word")
    if wa is None or wb is None:
        return None, ["item.colour_word"], {}
    return Iv(1.0 if frozenset((wa, wb)) in COMPLEMENTS else 0.0), [], {"words": [wa, wb]}


COMPLEMENT = Template(
    "COL.WHEEL_COMPLEMENT", "STYLISTIC", "support", "pair", _compl_measure,
    band=lambda hg, p: ("ge", 0.5, 0.5, "bool"),
    accepts=lambda hg, it: it.get("colour_word") is not None, roles=("a", "b"), tier="T2(practice)",
    kb="тема-4 K-COL-03 §4 (бордо↔хвоя, кемел↔темно-синій, бірюза↔мідь); CLAUDE.md п.18 КОЛО-1")


# ── 6. ОДНА ЗОНА ФОКУСУ (STYLISTIC, множинна, лічильна; параметри від наміру) ─
def _focal_applies(hg, bind):
    intent = hg.ctx.get("intent")
    if intent == "statement":
        return "yes", {"max": 2}, ""
    return "yes", {"max": 1}, ""


def _focal_measure(hg, bind, p):
    lo = hi = 0
    unknown = []
    for x in bind:
        it = x.get("interest")
        if it is None:
            unknown.append(x.id)
            hi += 1                     # невідомий інтерес може бути фокусом
            continue
        if it.lo >= 0.7:
            lo += 1; hi += 1
        elif it.hi >= 0.7:
            hi += 1
    foc = [x.id for x in bind if x.get("interest") is not None and x.get("interest").hi >= 0.7]
    if lo == 0 and hi == 0:
        return Iv(0), [], {"focal": 0}
    return Iv(lo, hi), [], {"focal_lo": lo, "focal_hi": hi, "interest_unknown": unknown,
                            "culprits": foc + unknown}


FOCAL = Template(
    "COMP.FOCAL_COUNT", "STYLISTIC", "constraint", "set", _focal_measure,
    band=lambda hg, p: ("le", p["max"], p["max"], "count"),
    applies=_focal_applies, roles=("all",), reads=("intent",), tier="T3",
    kb="тема-4 K-CRA-02 L558 (рівно один фокус); K-INT-04 (джерела інтересу); поріг інтересу 0.7 — SYN")


def _focal_any_measure(hg, bind, p):
    m = _focal_measure(hg, bind, p)[0]
    return m, [], {}


FOCAL_ANY = Template(
    # «хоча б одна» — n-арна частина «рівно одної»; попарно не виражається (записка §4.2)
    "COMP.FOCAL_PRESENT", "STYLISTIC", "support", "set", _focal_any_measure,
    band=lambda hg, p: ("ge", 1.0, 1.0, "count"),
    roles=("all",), tier="T3", kb="тема-4 cohesion test (рівно один фокус); тема-10 K-ACC-06")


# ── 7. КОНТРАСТ БІЛЯ ОБЛИЧЧЯ ↔ ОСОБИСТИЙ КОНТРАСТ (STYLISTIC, множина×людина) ─
def _contrast_measure(hg, bind, p):
    kp = hg.person.get("contrast_L")          # Iv: розмах L* волосся↔шкіра(↔очі) з σ
    skin = hg.person.get("skin_L")            # шкіра — ВЕРШИНА цього ребра, не лише параметр
    miss = [m for m, v in (("person.contrast_L", kp), ("person.skin_L", skin)) if v is None]
    if miss:
        return None, miss, {}
    Ls = [x.get("L") for x in bind if x.slot in NEAR_FACE and x.get("L") is not None]
    if not Ls:
        return None, ["item.L(near_face)"], {}
    Ls = Ls + [skin]
    span = Iv(max(0.0, max(l.lo for l in Ls) - min(l.hi for l in Ls)),
              max(l.hi for l in Ls) - min(l.lo for l in Ls))
    # повтор ступеня контрасту: |розмах образу біля обличчя − її розмах|
    return (span - kp).abs(), [], {"outfit_span": repr(span), "person": repr(kp),
                                   "culprits": [x.id for x in bind if x.slot in NEAR_FACE]}


CONTRAST = Template(
    "COL.CONTRAST_MATCH", "STYLISTIC", "constraint", "set", _contrast_measure,
    band=lambda hg, p: ("le", 15.0, 25.0, "dL"),   # SYN: класи контрасту — фольклор T3 (K-CON-01)
    roles=("near_face",), reads=("contrast_L", "skin_L"), tier="T3",
    kb="тема-2 L1720–1724 (Flusser: повторити ступінь контрасту біля обличчя); K-PAL-08/10; K-CON-01")


# ── 8. ЯКІР ОБ'ЄМУ (STYLISTIC/тіло, множина над слотами; верхній шар — як стан) ─
def _anchor_pair(bind):
    by = {x.slot: x for x in bind}
    return (by.get("верх") or by.get("сукня")), by.get("низ")


def _anchor_applies(hg, bind):
    """Передумова — ПАРА ОБ'ЄМІВ. Нема пари → NA (правилу нема що казати), а не OK:
    «не застосовне» і «виконано» — різні стани (тема-4 K-IO-04 розводить і «без входу»)."""
    top, bot = _anchor_pair(bind)
    if top is None or bot is None:
        return "no", {}, "no_top_bottom_pair"
    vt, vb = top.get("volume"), bot.get("volume")
    if vt is None or vb is None:
        return "unknown", {"missing": ["item.volume"]}, "volume_unknown"
    if min(vt.hi, vb.hi) < 0.6:                    # SYN-поріг «об'ємне»
        return "no", {}, "no_volume_pair"
    return "yes", {"possible_pair": min(vt.lo, vb.lo) < 0.6}, ""


def _anchor_measure(hg, bind, p):
    top, bot = _anchor_pair(bind)
    anchors = [x.id for x in bind if x.get("anchor")]   # пояс/заправка/звужений чи вкорочений низ
    whr = hg.person.get("whr")
    # без вираженої талії (WHR ≥ 0.8, SYN-межа) якір мусить зробити річ: потреба 1.0;
    # з вираженою — 0.5; WHR невідомий → уся область [0.5, 1.0], а не дефолт
    if whr is None:
        need, miss = Iv(0.5, 1.0), ["person.whr"]
    else:
        need, miss = (Iv(1.0) if whr.lo >= 0.8 else Iv(0.5) if whr.hi < 0.8 else Iv(0.5, 1.0)), []
    val = Iv(0.0) if anchors else need
    return val, ([] if anchors else miss), {"anchors": anchors, "whr": repr(whr) if whr else None,
                                            "culprits": [top.id, bot.id],
                                            "possible_pair": p.get("possible_pair", False)}


ANCHOR = Template(
    "SIL.VOLUME_ANCHOR", "STYLISTIC", "constraint", "slots", _anchor_measure,
    band=lambda hg, p: ("le", 0.25, 0.75, "need"), applies=_anchor_applies,
    slots=("верх", "сукня", "низ", "пояс", "верхній_шар"), roles=("silhouette",),
    reads=("whr",), uses_visibility=False, tier="T3",
    kb="hypergraph.py якір_обʼєму (K-SIL-03, репліка); тема-1 L1818–1830, L3811–3835 (намір+якорі)")


# ── 9. ПАРА КОЛЬОРІВ «МАЙЖЕ ЗБІГ» (STYLISTIC, пара, керована видимістю) ────
def _near_miss_accepts(hg, it):
    return it.slot in LARGE + ("взуття", "сумка") and it.get("L") is not None


def _near_miss_measure(hg, bind, p):
    a, b = bind
    ba, bb = lab_box(a), lab_box(b)
    if ba is None or bb is None:
        return None, ["item.colour"], {}
    d = box_dist(ba, bb)
    # «майже збіг»: ΔE у вузькій смузі між «той самий» і «явно інший» → вимір = відстань
    # до середини смуги неоднозначності; добре, якщо далеко від неї
    mid, half = 9.0, 4.0                          # SYN: смуга 5–13 ΔE76
    dev = (d - Iv(mid)).abs()
    return dev, [], {"dE76": repr(d)}


NEAR_MISS = Template(
    "COL.NEAR_MISS", "STYLISTIC", "constraint", "pair", _near_miss_measure,
    band=lambda hg, p: ("ge", 3.0, 5.0, "dE76_from_ambiguous_mid"),
    accepts=_near_miss_accepts, roles=("a", "b"), tier="T3/SYN",
    kb="тема-2 R-COL-02 (драбина ΔE — без джерела, hint); тема-10 K-ACC-10 (точний збіг — провал)")


# ── 10. МЕТАЛ: ЄДНІСТЬ АБО ПОВТОРЕНА СУМІШ (STYLISTIC, множина) ───────────
def _metal_measure(hg, bind, p):
    ms = [x.get("metal") for x in bind if x.get("metal")]
    unknown = [x.id for x in bind if x.get("metal_unknown")]
    if len(ms) < 2:
        return (None, ["item.metal"], {}) if unknown else (Iv(0), [], {"metals": ms})
    counts = {}
    for m in ms:
        counts[m] = counts.get(m, 0) + 1
    orph = {m for m, n in counts.items() if n == 1 and len(counts) > 1}
    orphans = len(orph)
    cul = [x.id for x in bind if x.get("metal") in orph]
    if unknown:
        return Iv(orphans, orphans + len(unknown)), ["item.metal"], {"metals": counts, "unknown": unknown,
                                                                     "culprits": cul + unknown}
    return Iv(orphans), [], {"metals": counts, "culprits": cul}


METAL = Template(
    "CRA.METAL_ORPHAN", "STYLISTIC", "constraint", "set", _metal_measure,
    band=lambda hg, p: ("le", 0.0, 0.0, "orphans"),
    roles=("hardware",), tier="T3", kb="тема-4 K-CRA-07 (самотній другий метал — «сирота»); тема-10 K-ACC-03")


# ── 11. «MATCHY»: ВЕРХНЯ МЕЖА КООРДИНАЦІЇ (STYLISTIC, множина) ─────────────
def _matchy_measure(hg, bind, p):
    xs = [x for x in bind if chromatic(x)]
    sure, maybe = {}, {}
    for i, a in enumerate(xs):
        for b in xs[i + 1:]:
            m = _echo_measure(hg, (a, b), {})[0]
            if m.hi <= 0.8:
                sure.setdefault(a.id, set()).add(b.id); sure.setdefault(b.id, set()).add(a.id)
            if m.lo <= 1.1:
                maybe.setdefault(a.id, set()).add(b.id); maybe.setdefault(b.id, set()).add(a.id)

    def biggest(adj):
        seen, best = set(), []
        for v in adj:
            if v in seen:
                continue
            comp, stack = set(), [v]
            while stack:
                u = stack.pop()
                if u not in comp:
                    comp.add(u); stack.extend(adj.get(u, ()))
            seen |= comp
            if len(comp) > len(best):
                best = sorted(comp)
        return best
    lo, hi = biggest(sure), biggest(maybe)
    return Iv(len(lo) or 1, len(hi) or 1), [], {"culprits": hi, "sure": lo}


MATCHY = Template(
    "COMP.MATCHY", "STYLISTIC", "constraint", "set", _matchy_measure,
    band=lambda hg, p: ("le", 3.0, 3.0, "items_in_one_colour"),
    roles=("echo_cluster",), tier="T3/hint",
    kb="тема-10 K-ACC-10 (точний збіг — провал; оголошена колона — виняток L826–827); "
       "тема-3 §8 L573–576 («2–3 точки — добре, 4+ — matchy» без джерела); тема-4 K-COMP-01 (обернене U)")


ALL = [VETO, WET, FORMALITY, ECHO, COMPLEMENT, FOCAL, FOCAL_ANY, CONTRAST, ANCHOR, NEAR_MISS, METAL, MATCHY]


def break_licence(hg, key):
    """Умови K-KOH-03 для оголошеного розриву — ВИМІР коду, не вирок:
    single — це єдиний прийнятий розрив; anchored — хоч один учасник розриву має
    підтримане відлуння (SUPPORT у COMP.ECHO); fit_clean — нема VIOLATE у PHYSICAL.
    База: «два розриви руйнуються» — не виміряно (тема-3 §21), тому це примітка."""
    from ядро import SUPPORT, VIOLATE, STANCE_OK
    f = hg.F.get(key)
    ids = {x.id for x in f.bind} if f else set()
    cul = set((f.detail or {}).get("culprits") or ids) if f else set()
    accepted = [k for k, st in hg.stances.items() if st["kind"] == "DELIBERATE_BREAK" and st["status"] == STANCE_OK]
    echoed = any(v.verdict == SUPPORT and v.tid == "COMP.ECHO" and cul & {x.id for x in v.bind}
                 for v in hg.F.values())
    phys = [k for k, v in hg.F.items() if v.verdict == VIOLATE and hg.T[v.tid].cls == "PHYSICAL"
            and not (hg.stances.get(k) or {}).get("status") == STANCE_OK]
    return dict(single=len(accepted) <= 1, anchored=echoed, physical_clean=not phys,
                accepted_breaks=len(accepted))
