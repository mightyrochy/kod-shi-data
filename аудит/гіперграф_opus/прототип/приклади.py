# -*- coding: utf-8 -*-
"""РОЗІБРАНІ ПРИКЛАДИ до записки §6. Усі речі, особи й числа — СИНТЕТИКА (SYN):
вони показують механіку, а не емпіричні норми. Колір «зі слова» — широке вікно,
«з фото» — вузький інтервал (порядки величин — тема-2 §6.0 і R-COL-06).

Запуск: python3 приклади.py  (CPython 3.10+ або Pyodide 0.26; без залежностей)
"""
import sys
sys.path.insert(0, ".")
from ядро import (Iv, Item, HG, repair, tradeoffs, DELIBERATE_BREAK, PERSON_CHOICE,
                  VIOLATE, BORDER, UNKNOWN, SUPPORT, CLASSES)
import шаблони as Ш


def show_profile(hg, title):
    p = hg.profile()
    row = "  ".join("%s:V%d B%d U%d S%d" % (c[:4], p[c]["VIOLATE"], p[c]["BORDER"], p[c]["UNKNOWN"],
                                             p[c]["SUPPORT"]) for c in CLASSES)
    print("  [%s] %s" % (title, row))


def show_explain(hg, kinds=("tensions", "borders", "unknowns", "supports")):
    e = hg.explain()
    for kind in kinds:
        for r in e[kind]:
            extra = ""
            if kind == "tensions":
                extra = " handles=%s" % r.get("repair_handles")
            elif kind == "borders":
                extra = " why=%s" % r.get("why")
            elif kind == "unknowns":
                extra = " missing=%s" % r.get("missing")
            if r.get("stance"):
                extra += " stance=%s/%s" % (r["stance"]["kind"], r["stance"]["status"])
            dd = r["detail"].get("decided_despite_missing")
            roles = {k: (v if not isinstance(v, list) or len(v) <= 4 else "%d речей" % len(v))
                     for k, v in r["roles"].items()}
            print("    %-9s %-22s %-4s roles=%s value=%s margin=%s%s" % (
                kind[:-1].upper(), r["rule"], r["cls"][:4], roles, r["value"], r["margin"], extra))
    dec = [(f.tid, k[1], f.detail["decided_despite_missing"]) for k, f in sorted(hg.F.items())
           if f.detail.get("decided_despite_missing")]
    for tid, ids, miss in dec:
        print("    DECIDED   %-22s %s без %s — питати не треба" % (tid, ids, miss))


def pairwise_baseline(hg, w=None):
    """Простіша ПОПАРНА модель для порівняння (записка §7): лише попарні шаблони,
    точкові оцінки (середини інтервалів), невідоме = 0, сума ваг категорій сили
    (як `hypergraph.ВАГА_СИЛИ`: default 0.40, soft 0.25, hint 0.12)."""
    w = w or {"COL.NEAR_MISS": 0.25, "COMP.ECHO": -0.12, "COL.WHEEL_COMPLEMENT": -0.12}
    tot, parts = 0.0, []
    for k, f in hg.F.items():
        t = hg.T[f.tid]
        if t.scope != "pair" or f.tid not in w or f.value is None:
            continue                       # множинні, особові й невідомі — поза моделлю
        mid = Iv((f.value.lo + f.value.hi) / 2)
        d, lo, hi, _ = f.band
        thr = (lo + hi) / 2
        bad = (mid.lo > thr) if d == "le" else (mid.lo < thr)
        hit = (not bad) if t.polarity == "support" else bad
        if hit:
            tot += w[f.tid]
            parts.append((f.tid, k[1]))
    return round(tot, 3), parts


# ═════════════════════════════════════════════════════════════════════════════
def example_1():
    print("\n== ПРИКЛАД 1. Невідомі дані: портрета й мірок нема, дощ невідомий ==")
    print("   нагода: офіс удень, ошатність [4,6]; намір не названо → conventional (припущення коду)")
    items = [
        Item("knit_oversize", "верх", L=Iv(70, 76, "photo"), C=Iv(6, 10), h=Iv(70, 85), colour_word="молочний",
             formality=Iv(3, 5), interest=Iv(0.2), volume=Iv(0.8)),
        Item("trousers_navy_wide", "низ", L=Iv(15, 30, "word"), C=Iv(5, 20), h=Iv(250, 290), colour_word="темно-синій",
             formality=Iv(4, 6), interest=Iv(0.2), volume=Iv(0.75)),
        Item("belt_cognac", "пояс", L=Iv(40, 44, "photo"), C=Iv(32, 38), h=Iv(55, 61), colour_word="коньячний",
             formality=Iv(4, 6), interest=Iv(0.3), metal="gold", anchor=True),
        Item("coat_camel_open", "верхній_шар", L=Iv(59, 65, "photo"), C=Iv(25, 30), h=Iv(70, 80), colour_word="кемел",
             formality=Iv(5, 7), interest=Iv(0.3), fabric="wool", closed=False),
        Item("bag_cognac_word", "сумка", L=Iv(35, 50, "word"), C=Iv(30, 45), h=Iv(50, 65), colour_word="коньячний",
             formality=Iv(4, 6), interest=Iv(0.4), metal="gold", fabric="leather"),
        Item("scarf_bordo", "шарф", L=Iv(20, 35, "word"), C=Iv(25, 40), h=Iv(5, 20), colour_word="бордо",
             formality=Iv(4, 7), interest=Iv(0.75)),
        Item("boots_black_suede", "взуття", L=Iv(18, 22, "photo"), C=Iv(0, 3), h=Iv(0, 359), colour_word="чорний",
             formality=Iv(4, 6), interest=Iv(0.2), fabric="suede", metal="silver"),
    ]
    hg = HG(Ш.ALL, person=dict(contrast_L=None, whr=None),
            ctx=dict(formality=Iv(4, 6), precip=None, intent="conventional"), items=items)
    print("   екземплярів гіперребер: %d, оцінок шаблонів: %d" % (len(hg.F), hg.evals))
    show_profile(hg, "профіль")
    show_explain(hg)
    b = pairwise_baseline(hg)
    print("   ПОПАРНА МОДЕЛЬ: сума=%s, спрацювання=%s" % b)
    print("   (вона не бачить: CONTRAST/ANCHOR/FOCAL/METAL — не попарні; невідомий дощ — як «сухо»)")

    print("\n  1a. Сумку зі слова замінено тією самою сумкою, виміряною з фото:")
    bag_photo = Item("bag_cognac_photo", "сумка", L=Iv(40, 45, "photo"), C=Iv(33, 39), h=Iv(54, 62),
                     colour_word="коньячний", formality=Iv(4, 6), interest=Iv(0.4), metal="gold", fabric="leather")
    ev0 = hg.evals
    d = hg.replace("сумка", bag_photo)
    print("   інкрементально переоцінено %d екземплярів (повна побудова — %d)" % (hg.evals - ev0, len(hg.F)))
    for k, (a, b2) in sorted(d["changed"].items()):
        print("    змінено %s %s: %s → %s" % (k[0], k[1], a, b2))
    for k, v in sorted(d["added"].items()):
        if v in (SUPPORT, VIOLATE, BORDER, UNKNOWN):
            print("    нове   %s %s: %s" % (k[0], k[1], v))

    print("\n  1b. Пояс прибрано (якоря нема), WHR невідомий:")
    ev0 = hg.evals
    d = hg.replace("пояс", None)
    print("   переоцінено %d екземплярів" % (hg.evals - ev0))
    f = [v for k, v in hg.F.items() if k[0] == "SIL.VOLUME_ANCHOR"][0]
    print("    SIL.VOLUME_ANCHOR: %s value=%s missing=%s" % (f.verdict, f.value, f.missing))
    print("    → питання «обхват талії/стегон» потрібне лише тепер; із поясом рішення не залежало від WHR")
    d = hg.set_ctx("whr", Iv(0.70, 0.72, "tape"), person=True)
    print("    після мірки WHR 0.70–0.72: ANCHOR → %s (переоцінено лише залежні від whr)" %
          [v for k, v in hg.F.items() if k[0] == "SIL.VOLUME_ANCHOR"][0].verdict)
    return hg


# ═════════════════════════════════════════════════════════════════════════════
def example_2():
    print("\n== ПРИКЛАД 2. Свідомий стилістичний розрив: два фокуси на театр ==")
    print("   нагода: театр увечері, ошатність [6,8], мряка; намір context_optimal; її слово: «хочу яскраво»")
    items = [
        Item("top_red_satin", "верх", L=Iv(40, 46, "photo"), C=Iv(55, 65), h=Iv(20, 30), colour_word="червоний",
             formality=Iv(6, 8), interest=Iv(0.85), volume=Iv(0.3), fabric="satin"),
        Item("skirt_leopard", "низ", L=Iv(45, 60, "photo"), C=Iv(20, 35), h=Iv(55, 75), colour_word="леопард",
             formality=Iv(5, 7), interest=Iv(0.8), volume=Iv(0.3)),
        Item("boots_black_heel", "взуття", L=Iv(15, 20, "photo"), C=Iv(0, 3), h=Iv(0, 359), colour_word="чорний",
             formality=Iv(6, 8), interest=Iv(0.2), fabric="leather", metal="gold"),
        Item("clutch_black_satin", "сумка", L=Iv(12, 16, "photo"), C=Iv(0, 2), h=Iv(0, 359), colour_word="чорний",
             formality=Iv(7, 9), interest=Iv(0.3), fabric="satin", metal="gold"),
        Item("earrings_gold", "сережки", L=Iv(70, 75, "photo"), C=Iv(30, 40), h=Iv(80, 90), colour_word="золото",
             formality=Iv(6, 9), interest=Iv(0.4), metal="gold"),
    ]
    hg = HG(Ш.ALL, person=dict(contrast_L=Iv(30, 40, "protocol_photo"), skin_L=Iv(62, 66), whr=Iv(0.70, 0.72)),
            ctx=dict(formality=Iv(6, 8), precip="yes", intent="context_optimal"), items=items)
    show_profile(hg, "до позицій")
    show_explain(hg, kinds=("tensions",))
    fk = [k for k in hg.F if k[0] == "COMP.FOCAL_COUNT"][0]
    wk = [k for k in hg.F if k[0] == "WEA.WET_FABRIC" and "clutch_black_satin" in k[1]][0]
    st = hg.declare(DELIBERATE_BREAK, fk[0], ["top_red_satin", "skirt_leopard"], "person_desire:bold", by="stylist")
    print("   стилістка: розрив над %s → %s; ліцензія K-KOH-03: %s" % (fk[0], st["status"], Ш.break_licence(hg, fk)))
    st2 = hg.declare(DELIBERATE_BREAK, wk[0], wk[1], "evening_look", by="stylist")
    print("   стилістка: розрив над %s → %s (фізичне не легітимізується стилем)" % (wk[0], st2["status"]))
    st3 = hg.declare(PERSON_CHOICE, wk[0], wk[1], "her_words:want_this_clutch", by="person")
    print("   людина: «хочу саме цей клатч» → %s; дія = умова (захист від вологи), не ремонт" % st3["status"])
    show_profile(hg, "після позицій")

    print("\n  2a. Відлуння як якір розриву: сережки замінено червоними емалевими")
    ear = Item("earrings_red_enamel", "сережки", L=Iv(41, 46, "photo"), C=Iv(55, 63), h=Iv(22, 30),
               colour_word="червоний", formality=Iv(6, 8), interest=Iv(0.45), metal="gold")
    ev0 = hg.evals
    hg.replace("сережки", ear)
    hg.revalidate_stances()
    print("   переоцінено %d; ліцензія: %s" % (hg.evals - ev0, Ш.break_licence(hg, fk)))

    print("\n  2b. Намір змінено на statement (вона: «хочу вразити»):")
    ev0 = hg.evals
    d = hg.set_ctx("intent", "statement")
    hg.revalidate_stances()
    print("   переоцінено %d екземплярів (лише ті, що читають intent): %s" % (hg.evals - ev0, d["changed"]))
    print("   позиція стилістки над FOCAL_COUNT тепер: %s (ламати вже нічого)" % hg.stances[fk]["status"])
    return hg


# ═════════════════════════════════════════════════════════════════════════════
def pool_bags():
    mk = lambda id, **a: Item(id, "сумка", **a)
    return {"сумка": [
        mk("bag_brown_gold", L=Iv(28, 34, "photo"), C=Iv(14, 20), h=Iv(55, 65), colour_word="коричневий",
           formality=Iv(4, 6), interest=Iv(0.3), metal="gold", fabric="leather"),
        mk("bag_black_gold", L=Iv(15, 19, "photo"), C=Iv(0, 2), h=Iv(0, 359), colour_word="чорний",
           formality=Iv(5, 7), interest=Iv(0.3), metal="gold", fabric="leather"),
        mk("bag_bordo_suede_gold", L=Iv(22, 30, "photo"), C=Iv(28, 36), h=Iv(8, 18), colour_word="бордо",
           formality=Iv(4, 6), interest=Iv(0.5), metal="gold", fabric="suede"),
        mk("bag_navy_silver", L=Iv(18, 24, "photo"), C=Iv(10, 18), h=Iv(255, 275), colour_word="темно-синій",
           formality=Iv(5, 7), interest=Iv(0.3), metal="silver", fabric="leather"),
        mk("bag_canvas_nometal", L=Iv(70, 78, "photo"), C=Iv(8, 14), h=Iv(75, 90), colour_word="бежевий",
           formality=Iv(2, 3), interest=Iv(0.2), fabric="canvas"),
    ]}


def example_3():
    print("\n== ПРИКЛАД 3. Закріплена власна річ: її замшеві черевики в дощ ==")
    print("   нагода: офіс, дощ, +8 °C, ошатність [4,6]; її вето: міні; черевики — її фото, закріплені")
    items = [
        Item("own_boots_brown_suede", "взуття", pinned=True, own=True, L=Iv(28, 32, "photo"), C=Iv(12, 18),
             h=Iv(55, 65), colour_word="коричневий", formality=Iv(3, 5), interest=Iv(0.3), fabric="suede", metal="gold"),
        Item("trousers_grey_wool", "низ", L=Iv(40, 60, "word"), C=Iv(0, 4), h=Iv(0, 359), colour_word="сірий",
             formality=Iv(4, 6), interest=Iv(0.2), volume=Iv(0.4)),
        Item("knit_cream", "верх", L=Iv(85, 92, "word"), C=Iv(5, 12), h=Iv(80, 95), colour_word="кремовий",
             formality=Iv(3, 5), interest=Iv(0.2), volume=Iv(0.5)),
        Item("coat_camel_closed", "верхній_шар", L=Iv(59, 65, "photo"), C=Iv(25, 30), h=Iv(70, 80),
             colour_word="кемел", formality=Iv(5, 7), interest=Iv(0.35), fabric="wool", closed=True),
        Item("bag_black_silver", "сумка", L=Iv(16, 20, "photo"), C=Iv(0, 2), h=Iv(0, 359), colour_word="чорний",
             formality=Iv(5, 7), interest=Iv(0.3), metal="silver", fabric="leather"),
    ]
    hg = HG(Ш.ALL, person=dict(contrast_L=Iv(28, 36, "protocol_photo"), skin_L=Iv(55, 60), whr=Iv(0.76, 0.80),
                               veto_types=["mini"]),
            ctx=dict(formality=Iv(4, 6), precip="yes", intent="conventional"), items=items)
    print("   видимі: %s (застебнуте пальто ховає верх)" % [x.id for x in hg.visible()])
    show_profile(hg, "профіль")
    show_explain(hg, kinds=("tensions", "supports"))
    wk = [k for k in hg.F if k[0] == "WEA.WET_FABRIC" and "own_boots_brown_suede" in k[1]][0]
    st = hg.declare(PERSON_CHOICE, wk[0], wk[1], "own_item_pinned", by="system")
    print("   позиція над замшею в дощ: %s — дія: умова носіння, не заміна (CLAUDE.md п.17)" % st["status"])
    mk = [k for k in hg.F if k[0] == "CRA.METAL_ORPHAN"][0]
    r = repair(hg, mk, pool_bags())
    print("   РЕМОНТ %s: ручки=%s; спробувано %d, оцінок шаблонів %d" % (
        mk[0], [x.id for x in __import__("ядро").handles(hg.F[mk])], r["tried"], r["evals"]))
    for c in r["candidates"]:
        print("    %-22s ціль→%-9s нові_VIOLATE=%s втрачено_SUPPORT=%d здобуто_SUPPORT=%s ранг=%s" % (
            c["inn"], c["target_after"], c["new_violations"], c["lost_supports"], c["gained_supports"], c["rank"]))
    print("   (однаковий ранг = рівноцінні для коду; вибір між ними — стилістки й людини)")

    print("\n  3a. Стан пальта як операція: розстебнути (верх стає видимим біля обличчя)")
    coat_open = Item("coat_camel_open", "верхній_шар", L=Iv(59, 65, "photo"), C=Iv(25, 30), h=Iv(70, 80),
                     colour_word="кемел", formality=Iv(5, 7), interest=Iv(0.35), fabric="wool", closed=False)
    ev0 = hg.evals
    d = hg.replace("верхній_шар", coat_open)
    print("   переоцінено %d; змінено: %s" % (hg.evals - ev0, {k[0]: v for k, v in d["changed"].items()}))
    print("   додано екземплярів (нові пари з верхом): %d" % len(d["added"]))
    cf = [v for k, v in hg.F.items() if k[0] == "COL.CONTRAST_MATCH"][0]
    print("    COL.CONTRAST_MATCH: %s value=%s detail=%s" % (cf.verdict, cf.value,
                                                           {k: v for k, v in cf.detail.items() if k != "culprits"}))

    print("\n  3b. Варіанти компромісу, коли чистої сумки в пулі нема (чорна й коричнева із золотом")
    print("      «закінчились»): слоти сумка+низ, Парето за класами, без суми й без SUPPORT")
    pool = {"сумка": [b for b in pool_bags()["сумка"] if b.id not in ("bag_black_gold", "bag_brown_gold")]}
    mk2 = lambda id, **a: Item(id, "низ", **a)
    pool["низ"] = [
        mk2("trousers_navy", L=Iv(18, 26, "photo"), C=Iv(8, 16), h=Iv(255, 275), colour_word="темно-синій",
            formality=Iv(4, 6), interest=Iv(0.2), volume=Iv(0.4)),
        mk2("skirt_mini_black", type="mini", L=Iv(14, 18, "photo"), C=Iv(0, 2), h=Iv(0, 359), colour_word="чорний",
            formality=Iv(4, 6), interest=Iv(0.4), volume=Iv(0.2)),
        mk2("trousers_brown_cord", L=Iv(26, 32, "photo"), C=Iv(12, 18), h=Iv(55, 65), colour_word="коричневий",
            formality=Iv(3, 4), interest=Iv(0.3), volume=Iv(0.5)),
    ]
    t = tradeoffs(hg, ["сумка", "низ"], pool, cap=6)
    print("   варіантів %d, фронт %d, оцінок шаблонів %d" % (t["variants"], t["front_size"], t["evals"]))
    print("   вектор = (VIOLATE за %s, BORDER, UNKNOWN)" % "/".join(c[:4] for c in CLASSES))
    for v, a in t["front"]:
        print("    %s  %s" % (v, a or "{поточний образ}"))
    return hg


# ═════════════════════════════════════════════════════════════════════════════
def example_4():
    print("\n== ПРИКЛАД 4. Багатосторонній якір об'єму: верх×низ×пояс×тіло ==")
    items = [
        Item("knit_oversize", "верх", L=Iv(70, 76, "photo"), C=Iv(6, 10), h=Iv(70, 85), colour_word="молочний",
             formality=Iv(3, 5), interest=Iv(0.2), volume=Iv(0.8)),
        Item("trousers_wide", "низ", L=Iv(20, 26, "photo"), C=Iv(2, 6), h=Iv(240, 280), colour_word="графіт",
             formality=Iv(4, 6), interest=Iv(0.2), volume=Iv(0.8)),
        Item("sneakers_white", "взуття", L=Iv(88, 93, "photo"), C=Iv(0, 3), h=Iv(0, 359), colour_word="білий",
             formality=Iv(2, 4), interest=Iv(0.3), fabric="leather"),
        Item("bag_grey", "сумка", L=Iv(50, 56, "photo"), C=Iv(0, 3), h=Iv(0, 359), colour_word="сірий",
             formality=Iv(3, 5), interest=Iv(0.2), fabric="leather"),
    ]
    hg = HG(Ш.ALL, person=dict(contrast_L=Iv(40, 50), skin_L=Iv(60, 64), whr=Iv(0.83, 0.86, "tape")),
            ctx=dict(formality=Iv(2, 4), precip="no", intent="conventional"), items=items)
    show_profile(hg, "профіль")
    show_explain(hg, kinds=("tensions",))
    ak = [k for k in hg.F if k[0] == "SIL.VOLUME_ANCHOR"][0]
    mk = lambda id, slot, **a: Item(id, slot, **a)
    pool = {"низ": [mk("trousers_tapered_cropped", "низ", L=Iv(20, 26), C=Iv(2, 6), h=Iv(240, 280),
                       colour_word="графіт", formality=Iv(3, 5), interest=Iv(0.2), volume=Iv(0.65), anchor=True),
                    mk("trousers_straight", "низ", L=Iv(20, 26), C=Iv(2, 6), h=Iv(240, 280), colour_word="графіт",
                       formality=Iv(4, 6), interest=Iv(0.2), volume=Iv(0.5)),
                    mk("jeans_wide_light", "низ", L=Iv(60, 68), C=Iv(10, 16), h=Iv(230, 250), colour_word="блакитний",
                       formality=Iv(2, 4), interest=Iv(0.3), volume=Iv(0.85))],
            "верх": [mk("blouse_tucked", "верх", L=Iv(88, 92), C=Iv(2, 5), h=Iv(80, 95), colour_word="білий",
                        formality=Iv(4, 6), interest=Iv(0.3), volume=Iv(0.65), anchor=True),
                     mk("sweater_chunky", "верх", L=Iv(65, 72), C=Iv(5, 9), h=Iv(70, 85), colour_word="вівсяний",
                        formality=Iv(2, 4), interest=Iv(0.3), volume=Iv(0.9))]}
    r = repair(hg, ak, pool)
    print("   РЕМОНТ %s: спробувано %d, оцінок шаблонів %d" % (ak[0], r["tried"], r["evals"]))
    for c in r["candidates"]:
        print("    %-26s у слоті %-5s ціль→%-9s нові_VIOLATE=%s ранг=%s як=%s" % (
            c["inn"], c["slot"], c["target_after"], c["new_violations"], c["rank"],
            {k: v for k, v in (c.get("target_detail") or {}).items() if k in ("anchors",)}))
    full = len(hg.F)
    ev0 = hg.evals
    hg.replace("низ", pool["низ"][0])
    print("   заміна низу: переоцінено %d із %d екземплярів (решта — без змін, бо поза областю)" % (
        hg.evals - ev0, full))
    return hg


if __name__ == "__main__":
    example_1()
    example_2()
    example_3()
    example_4()
