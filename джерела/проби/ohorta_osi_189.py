# -*- coding: utf-8 -*-
"""Л-18 (рядок 189): огорта L*/C* — по осі окремо, а на малій вибірці викид мусить бути ВІДІРВАНИЙ.
ДО — огорта точок, що пройшли паркан по ОБОХ осях (як до Л-18); ПІСЛЯ — чинний `verify.вікно_з_вжитку`.
Точки — ті самі дизайни, що в `vikna_vzhytku.py`. Запуск: cd джерела && python3 проби/ohorta_osi_189.py"""
import collections, math, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as CS
from фід_фото import _спільні_фото, чужий_кадр, _файл_фото; from фід_розбір import _СЕП_КОЛЬОРУ
оф = FR.читати_yml(feed.каталог_на_диску())[0]; зб, сп = FZ.читати_збагачення(), _спільні_фото(оф)
ТОК = re.compile(r"[a-zа-яёєіїґ']+"); одне = lambda ч: not re.search(r"[\[(]", ч) and sum(
    1 for x in ТОК.findall(ч.lower().replace("-", " ")) if V.назва_кольору(x) or V.слово_крамниці(x)) <= 1
т = collections.defaultdict(dict)
for o in оф:
    z = зб.get(o["id"]); ч = [x.strip() for x in _СЕП_КОЛЬОРУ.split(o.get("колір_сирий") or o.get("колір_назва") or "") if x.strip()]
    if not FZ._збагачення_придатне(z) or (z.get("версія") or 1) < 2 or len(ч) != 1 or not одне(ч[0]):
        continue
    lab, ск = FZ._lab_з_hex(z["колір_основний"].get("hex")), V.слово_крамниці(ч[0])
    if lab is not None and ск and not чужий_кадр(z.get("фото"), сп.get(o.get("магазин") or o["id"].split("@")[-1]) or {}):
        т[ск["ім"]].setdefault(_файл_фото(z["фото"]), CS.lch(lab))
def вікно_до(сл, точки):
    """Вікно слова методом до Л-18: викид по будь-якій осі викидав точку з ОБОХ огорт."""
    в = V.ЛЕКСИКОН[сл]
    if в[4] is not None:  # хроматичне слово: у межі L*/C* ідуть лише точки в дузі вжитку
        д = V._дуга_з_вжитку([p[2] for p in точки if p[1] > V.ДРІЖ_AB], в[4])
        точки = [p for p in точки if p[1] < V.ТОН_ВІД_C or V._у_дузі(p[2], д)]
    if len(точки) < V.ВЖИТОК_МІН:
        return в[:4]  # мало точок — межі лексикону, як і в чинному коді
    пL, пC = V._паркан([p[0] for p in точки], V.ВЖИТОК_КРАЙ), V._паркан([p[1] for p in точки], V.ВЖИТОК_КРАЙ)
    ц = [p for p in точки if пL[0] <= p[0] <= пL[1] and пC[0] <= p[1] <= пC[1]] or точки
    о = (min(p[0] for p in ц), max(p[0] for p in ц), min(p[1] for p in ц), max(p[1] for p in ц))
    return (min(в[0], math.floor(о[0])), max(в[1], math.ceil(о[1])),
            min(в[2], math.floor(о[2])), max(в[3], math.ceil(о[3])))
слова = [с for с in V.ЛЕКСИКОН if с not in V.МЕТАЛИ and т.get(с)]
змін = [x for x in ((с, вікно_до(с, list(т[с].values())), tuple(V.вікно_вжитку(с))[:4]) for с in слова) if x[1] != x[2]]
print("ФАКТ · слів із точками %d; огорта по осі + відрив на вибірці < %d ширшають вікно в %d: %s" % (
    len(слова), V.ВЖИТОК_ДРІБНО, len(змін), "; ".join("%s L%d–%d C%d–%d → L%d–%d C%d–%d" % (с, *д, *п) for с, д, п in змін)))
РЕЧІ = (("ж-00396@feelyou.com.ua", "#fef0ed", "ніжно-рожевий"), ("ж-04426@likeangel.com.ua", "#513c32", "тауп"),
        ("ж-02473@ricamare.com.ua", "#248751", "м'ятний"))  # третя — блуза «Mint» L* 51.7 при парканi 51.90
print("ФАКТ · названі речі рядка 189: %s" % "; ".join("%s %s проти «%s» — %s" % (
    i, h, с, V.перевірити(CS.hx(h), ім=с)["вердикт"]) for i, h, с in РЕЧІ))
