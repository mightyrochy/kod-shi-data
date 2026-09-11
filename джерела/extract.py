# -*- coding: utf-8 -*-
"""Кроки 1–5: маски -> статистика зон. Сегментатор НЕ входить сюди — він зовнішня
залежність (yakhyo/face-parsing, MIT). Модуль приймає готові маски й доводить
пікселі до чисел, придатних для colorspace.features()."""
import math, random
import colorspace as cs
from colorspace import to_lab, lch

# ── 1. ЕРОЗІЯ: крайові пікселі змішані з сусіднім матеріалом ──────────────────
try:
    import numpy as np, cv2
    _FAST = True
except ImportError:
    _FAST = False
# scipy — ОКРЕМА залежність: _FAST її не гарантує, а face_frame_band під ним її імпортував
# і падав на середовищі, де є numpy+cv2, але нема scipy. Перевіряємо те, що вживаємо.
try:
    from scipy import ndimage as _ndimage
    _SCIPY = True
except ImportError:
    _SCIPY = False

def adaptive_k(mask, k=2):
    """Дрібні зони (райдужка, склера) ерозія k=2 може стерти повністю."""
    n=len(mask)
    return 0 if n < 300 else (1 if n < 3000 else k)

def erode(mask, k=2):
    """Прибирає k шарів по краю. cv2, якщо доступний — чистий Python на 500k
    пікселів помітно гальмує."""
    k = adaptive_k(mask, k)
    if k == 0 or not mask: return set(mask)
    if _FAST:
        xs=[p[0] for p in mask]; ys=[p[1] for p in mask]
        pad = k+1                      # ВІДСТУП: без нього cv2 вважає край заповненим
        x0,y0 = min(xs)-pad, min(ys)-pad
        img=np.zeros((max(ys)-y0+pad+1, max(xs)-x0+pad+1), np.uint8)
        for (x,y) in mask: img[y-y0, x-x0]=1
        img=cv2.erode(img, np.ones((3,3),np.uint8), iterations=k)
        ys_,xs_=np.nonzero(img)
        return {(int(x)+x0, int(y)+y0) for x,y in zip(xs_,ys_)}
    m=set(mask)
    for _ in range(k):
        m={(x,y) for (x,y) in m
           if all((x+dx,y+dy) in m for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)))}
    return m

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

# ── 3. ПРОСТОРОВИЙ ПОДІЛ ─────────────────────────────────────────────────────
def face_frame_band(hair_mask, face_mask, width=40):
    """Смуга волосся вздовж КОНТУРУ обличчя. Круговий радіус від центроїди
    завищував захоплення біля щік, бо обличчя овальне: max-радіус задають
    підборіддя/лоб, і коло виходить далеко за щоки."""
    if not face_mask or not hair_mask: return set(), set(hair_mask)
    if _FAST and _SCIPY:
        ndimage = _ndimage
        allp = list(face_mask)+list(hair_mask)
        x0=min(p[0] for p in allp); y0=min(p[1] for p in allp)
        W=max(p[0] for p in allp)-x0+1; H=max(p[1] for p in allp)-y0+1
        face=np.ones((H,W), np.uint8)
        for (x,y) in face_mask: face[y-y0, x-x0]=0          # 0 = обличчя
        dist=ndimage.distance_transform_edt(face)            # відстань до контуру
        band={p for p in hair_mask if dist[p[1]-y0, p[0]-x0] <= width}
        return band, set(hair_mask)-band
    fpts=list(face_mask)
    step=max(1, len(fpts)//400)
    contour=fpts[::step]
    band={p for p in hair_mask if min(math.dist(p,f) for f in contour) <= width}
    return band, set(hair_mask)-band

def cheek_zone(face_mask):
    """Щоки: смуга однакового нахилу поверхні. Стандартна точка колориметрії —
    щока, бо ніс/підборіддя мають інший кут до світла.
    `frac` прибрано: смуга задана перцентилями 0.45–0.70 прямо в тілі, і параметр
    роками обіцяв налаштовуваність, якої не було."""
    if not face_mask: return set()
    ys = sorted(p[1] for p in face_mask); xs = sorted(p[0] for p in face_mask)
    y0,y1 = ys[int(0.45*len(ys))], ys[int(0.70*len(ys))]
    xl,xr = xs[int(0.15*len(xs))], xs[int(0.85*len(xs))]
    mid_l, mid_r = xs[int(0.35*len(xs))], xs[int(0.65*len(xs))]
    return {(x,y) for (x,y) in face_mask
            if y0<=y<=y1 and (xl<=x<=mid_l or mid_r<=x<=xr)}   # обидві щоки, без носа

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

# ── 5. КАСТ ОСВІТЛЕННЯ з нейтральної опори ───────────────────────────────────
MIN_SCLERA_PX = 40      # T3: нижче цього оцінка касту — шум, не вимір
def illuminant_cast(sclera_labs, min_px=MIN_SCLERA_PX):
    """Склера ~нейтральна. Її зсув від a*=b*=0 — оцінка касту.
    НЕ для корекції шкіри (замкнене коло), а для ВПЕВНЕНОСТІ.
    Перевіряється НЕ лише порожність, а й достатність вибірки: кілька пікселів
    дають число, але не вимір."""
    n = len(sclera_labs)
    if n == 0:
        return dict(available=False, n=0, причина="склеру не знайдено")
    if n < min_px:
        return dict(available=False, n=n,
                    причина=f"замало пікселів ({n} < {min_px}) — оцінка касту недостовірна")
    a = sum(l[1] for l in sclera_labs)/n
    b = sum(l[2] for l in sclera_labs)/n
    sd_a = (sum((l[1]-a)**2 for l in sclera_labs)/n)**0.5
    sd_b = (sum((l[2]-b)**2 for l in sclera_labs)/n)**0.5
    mag = math.hypot(a,b)
    noisy = (sd_a+sd_b)/2 > mag          # розкид більший за сам сигнал
    return dict(available=True, n=n, a=round(a,1), b=round(b,1),
                magnitude=round(mag,1), розкид=round((sd_a+sd_b)/2,1),
                verdict=("сигнал слабший за шум — каст не визначений" if noisy else
                         "нейтральне" if mag<cs.КАСТ_ББ[0] else "помірний каст" if mag<cs.КАСТ_ББ[1]
                         else "сильний каст — абсолютний колір ненадійний"))

# ── ЗБІРКА: маски -> структура зон для colorspace.features() ─────────────────
def build_zones(px, masks, erode_k=2):
    """masks: {'шкіра':set, 'волосся':set, 'райдужка':set, 'склера':set}
    Повертає зони + `_пікселі` (СИРІ лічильники масок — саме пікселі, не частки:
    частка від поля ОСОБИ непорівнянна з часткою від поля ОБРАЗУ; потрібні outfit.py,
    щоб порахувати волосся в бюджет хром K-PC-04 без вигаданих чисел)
    + `_втрачені` (зони, що зникли після ерозії чи фільтрів — раніше вони просто
    не з'являлись у виході, і падіння траплялось на два модулі пізніше)."""
    out={}; diag={}; втрати={}
    face = masks.get("шкіра", set()); hair = masks.get("волосся", set())
    band, bulk = face_frame_band(hair, face)
    zones = {"шкіра_щоки": cheek_zone(face), "волосся_обрамлення": band,
             "волосся_маса": bulk, "райдужка": masks.get("райдужка", set()),
             "склера": masks.get("склера", set())}
    сирі = {nm: len(m) for nm, m in zones.items() if m}
    for nm, m in zones.items():
        якщо_було = len(m)
        m = erode(m, erode_k)          # adaptive_k сам захистить дрібні зони
        if not m:
            if якщо_було: втрати[nm]="ерозія стерла зону повністю"
            continue
        labs=[to_lab(px[x,y]) for (x,y) in m]
        if nm != "склера":
            labs, n_spec = reject_specular(labs)
            labs, n_shad = reject_shadow(labs)
            diag[nm]=dict(відкинуто_блиск=n_spec, відкинуто_тінь=n_shad)
        s=zone_stats(labs)
        if s: out[nm]=s
        else: втрати[nm]=f"після фільтрів не лишилось пікселів (було {якщо_було})"
    # Каст рахувався на СИРІЙ масці склери, хоча решта зон еродується: крайові пікселі
    # склери змішані з віями/райдужкою/повікою, а саме каст гейтує надійність усього
    # профілю (infer_source). Беремо ту саму еродовану зону, що й решта.
    _скл = erode(zones["склера"], erode_k) or zones["склера"]
    out["_каст"]=illuminant_cast([to_lab(px[x,y]) for (x,y) in _скл])
    out["_каст"]["маска"]=("еродована" if _скл is not zones["склера"] else "сира (ерозія стерла)")
    out["_діагностика"]=diag
    # ПІКСЕЛІ, не частки. Частка від поля ОСОБИ (шкіра+волосся+очі) непорівнянна
    # з часткою від поля ОБРАЗУ: волосся дало б 0.89 проти светра 0.42, і бюджет
    # хром порівнював би різні знаменники. Спільна одиниця — піксель.
    out["_пікселі"]={nm: n for nm, n in сирі.items()}
    out["_втрачені"]=втрати
    return out
