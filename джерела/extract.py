# -*- coding: utf-8 -*-
"""Робастна статистика кольору зони: фільтри блиску й тіні, медоїд, `zone_stats`.

ЩО ЛИШИЛОСЬ І ЧОМУ (Н-02-02, 13.09.2026). Тут — рівно та частина колишнього
«маски → статистика зон», яку кличе ядро: `feed._зразок_пікселів` (шлях фото
речі, `ліміт_фото` > 0) відкидає блиск і тінь і бере `zone_stats`. Збірка
«маски сегментатора → зони» — `adaptive_k`, `erode`, `face_frame_band`,
`cheek_zone`, `illuminant_cast`, `build_zones` — переїхала в
`лабораторія/зони_з_масок.py`: нуль виконань на живому шляху, жодного
викликача (AST-пошук по дереву), сегментатор (yakhyo/face-parsing) не
підключений. Лабораторія імпортує звідси назад; ядро з лабораторії — ніколи
(сторож — `склад.модулі_системи`).
"""
import math, random
from colorspace import lch

# ── 2. ТИП ПІКСЕЛЯ: відкинути дзеркальні ─────────────────────────────────────
MAX_ВІДКИД = 0.35      # T3: більше третини зони — це вже не блиск, а хибний поріг

def reject_specular(labs, hi_pct=0.90, chroma_pct=0.40, max_відкид=MAX_ВІДКИД):
    """Блиск = колір ДЖЕРЕЛА: висока світлота ПРИ низькій хромі відносно
    розподілу самої зони. Поріг відносний, не абсолютний (T3).

    ВИПРАВЛЕНО ПІСЛЯ ПРОБИ: на ОДНОРІДНІЙ зоні всі пікселі одночасно мали
    L ≥ p90 і C ≤ p40, і фільтр викидав 100% (перевірено: 300 -> 0). Зона після
    цього тихо зникала з build_zones, а features_from_zones падав із «зона шкіри
    обов'язкова», хоча маска була подана. Це не екзотика: рендери try-on,
    flat-lay-фото товару і згладжені кадри саме такі.
    Тепер: строга нерівність по L + стеля відкиду. Якщо зона однорідна, блиску в
    ній нема — і викидати нема чого."""
    if len(labs) < 20: return labs, 0
    Ls = sorted(l[0] for l in labs); Cs = sorted(lch(l)[1] for l in labs)
    L_hi = Ls[int(hi_pct*len(Ls))]; C_lo = Cs[int(chroma_pct*len(Cs))]
    diffuse = [l for l in labs if not (l[0] > L_hi and lch(l)[1] <= C_lo)]
    if len(labs) - len(diffuse) > max_відкид*len(labs):
        return labs, 0          # поріг спрацював на всій зоні -> це не блиск
    return diffuse, len(labs)-len(diffuse)

def reject_shadow(labs, lo_pct=0.05, max_відкид=MAX_ВІДКИД):
    """Найтемніший хвіст — переважно тінь від геометрії, не пігмент.
    Та сама стеля: на однорідній зоні L_lo дорівнює всім значенням і `> L_lo`
    викидає все."""
    if len(labs) < 20: return labs, 0
    Ls = sorted(l[0] for l in labs); L_lo = Ls[int(lo_pct*len(Ls))]
    keep = [l for l in labs if l[0] > L_lo]
    if len(labs) - len(keep) > max_відкид*len(labs):
        return labs, 0
    return keep, len(labs)-len(keep)

# ── 4. РОБАСТНА СТАТИСТИКА ЗОНИ ──────────────────────────────────────────────
СІД = 17     # детермінізм: без нього та сама маска давала різну домінанту між прогонами,
             # а вся архітектура стоїть на порівнянні маржі рішення з точністю виміру

def medoid(labs, probe=200, metric="de00"):
    """Домінантний колір = МЕДОЇД: реально наявний піксель, найближчий до решти.
    Середнє при двомодальному розподілі (балаяж) дає колір, якого не існує ніде.
    Метрика: ΔE00 за замовчуванням. Усередині зони різниці МАЛІ — це саме зона
    валідності ΔE00 (на відміну від порівняння одяг↔шкіра, де він загейтований).
    На рівних зонах евклід дає те саме (Δ≈0.7), на балаяжі/ластовинні — Δ≈3.4."""
    if len(labs) <= 2: return labs[0]
    _r = random.Random(СІД)
    cand = labs if len(labs)<=probe else _r.sample(labs, probe)
    ref  = labs if len(labs)<=probe else _r.sample(labs, probe)
    if metric == "de00":
        from colorspace import de00 as _d
        dist = lambda c,r: _d(c,r)
    else:
        dist = lambda c,r: math.sqrt((c[0]-r[0])**2+(c[1]-r[1])**2+(c[2]-r[2])**2)
    best, bd = None, None
    for c in cand:
        d = sum(dist(c,r) for r in ref)
        if bd is None or d < bd: best, bd = c, d
    return best

def _se_медоїда(labs, n_boot=12, seed=3):
    """ПОХИБКА ЦЕНТРАЛЬНОЇ ОЦІНКИ — не те саме, що розкид пікселів.
    Складка дає розкид 12, але центральна оцінка по різних вибірках тієї ж речі
    гуляє лише на 1.3 (вимір: червоний светр, 8467 px). Око робить те саме, що
    медоїд: відкидає освітлення й бачить відбивну здатність (світлотна константність).
    Тому порівнювати маржу рішення треба з ЦИМ числом, а не з розкидом пікселів."""
    import random as _r
    if len(labs) < 60: return None
    rng = _r.Random(seed); оцінки = []
    for _ in range(n_boot):
        s_ = rng.sample(labs, max(30, len(labs)//n_boot))
        Ls = sorted(l[0] for l in s_); оцінки.append(Ls[len(Ls)//2])
    сер = sum(оцінки)/len(оцінки)
    return round((sum((x-сер)**2 for x in оцінки)/max(1,len(оцінки)-1))**0.5, 2)

def zone_stats(labs, sample=4000):
    if not labs: return None
    if len(labs) > sample: labs = random.Random(СІД).sample(labs, sample)
    Ls = sorted(l[0] for l in labs); n=len(Ls); p=lambda q: Ls[min(n-1,int(q*n))]
    dom = medoid(labs)
    L,C,h = lch(dom)
    mean = tuple(sum(l[i] for l in labs)/n for i in range(3))
    return dict(n=n, dominant=dom, dominant_kind="medoid",
                mean=tuple(round(v,1) for v in mean),
                mean_vs_medoid=round(math.dist(dom, mean),1),
                se_L=_se_медоїда(labs),
                L=round(L,1), C=round(C,1), h=round(h,1),
                p10=round(p(.1),1), p50=round(p(.5),1), p90=round(p(.9),1),
                spread=round(p(.9)-p(.1),1))          # робастно, НЕ max-min

# Кроки 1 (ерозія), 3 (просторовий поділ), 5 (каст зі склери) і збірка `build_zones`
# → лабораторія/зони_з_масок.py (Н-02-02): без входу, без викликача.
