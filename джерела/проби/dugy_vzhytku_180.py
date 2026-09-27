# -*- coding: utf-8 -*-
"""Л-16 (рядок 180): чи дуга слова накриває ВЖИТОК крамниць. Точки — дизайни, як у `vikna_vzhytku.py`.
«Кадр поза дугою» — дизайн, чий тон суперечить дузі слова (`verify._тон_не_суперечить`, з допуском на
дріж): ДО — дугою ЛЕКСИКОНУ, ПІСЛЯ — чинною дугою вжитку. Запуск: cd джерела && python3 проби/dugy_vzhytku_180.py"""
import collections, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed, фід_розбір as FR, фід_збагачення as FZ, verify as V, colorspace as CS
from фід_фото import _спільні_фото, чужий_кадр, _файл_фото; from фід_розбір import _СЕП_КОЛЬОРУ
оф = FR.читати_yml(feed.каталог_на_диску())[0]; зб, сп = FZ.читати_збагачення(), _спільні_фото(оф)
ТОК = re.compile(r"[a-zа-яёєіїґ']+")
одне = lambda ч: not re.search(r"[\[(]", ч) and sum(1 for x in ТОК.findall(ч.lower().replace("-", " "))
                                                     if V.назва_кольору(x) or V.слово_крамниці(x)) <= 1
т = collections.defaultdict(dict)
for o in оф:
    z = зб.get(o["id"]); ч = [x.strip() for x in _СЕП_КОЛЬОРУ.split(o.get("колір_сирий") or o.get("колір_назва") or "") if x.strip()]
    if not FZ._збагачення_придатне(z) or (z.get("версія") or 1) < 2 or len(ч) != 1 or not одне(ч[0]):
        continue
    lab, ск = FZ._lab_з_hex(z["колір_основний"].get("hex")), V.слово_крамниці(ч[0])
    if lab is not None and ск and not чужий_кадр(z.get("фото"), сп.get(o.get("магазин") or o["id"].split("@")[-1]) or {}):
        т[ск["ім"]].setdefault(_файл_фото(z["фото"]), CS.lch(lab))
хром = [с for с, в in V.ЛЕКСИКОН.items() if в[4] is not None and с not in V.МЕТАЛИ]
ш = lambda д: (д[1] - д[0]) % 360
поза = lambda с, д, лекс=None: sum(1 for p in т.get(с, {}).values()
                                   if not V._тон_не_суперечить(p[2], д, p[1], лекс))
рядки = [(с, V.ЛЕКСИКОН[с][4], V.вікно_вжитку(с)[4]) for с in хром]
рядки = [(с, л, в, поза(с, л), поза(с, в, л), len(т.get(с, {}))) for с, л, в in рядки]
ширші = [r for r in рядки if r[2] != r[1]]
print("ФАКТ · хроматичних слів %d, дизайнів у вжитку %d; дуга ЛЕКСИКОНУ вужча за вжиток — %d слів; "
      "кадрів вжитку поза дугою %d → %d" % (len(хром), sum(len(x) for x in т.values()), len(ширші),
      sum(r[3] for r in рядки), sum(r[4] for r in рядки)))
for с, лекс, вжив, до, після, n in sorted(ширші, key=lambda r: r[3] - r[4], reverse=True):
    print("   %-14s %s–%s (%d°) → %s–%s (%d°) · поза дугою %d → %d з %d" % (
        с, *лекс, ш(лекс), *вжив, ш(вжив), до, після, n))
print("ФАКТ · слова, чия дуга лишилась лексиконовою: %s" % ", ".join(
    "%s %d" % (r[0], r[5]) for r in рядки if r[2] == r[1]))
print("ФАКТ · названі кадри рядка 180: %s; знахідка Л-14 (#409, графіт C* 7.7 тон 25°) проти «зелений»: %s"
      % ("; ".join("%s проти «%s» — %s" % (h, і, V.перевірити(FZ._lab_з_hex(h), ім=і)["вердикт"])
                   for h, і in (("#897680", "тауп"), ("#1d303a", "зелений"), ("#2a3a3f", "зелений"))),
         V.перевірити((22.82, 6.96, 3.32), ім="зелений")["вердикт"]))
