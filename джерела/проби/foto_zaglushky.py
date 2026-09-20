# -*- coding: utf-8 -*-
"""Проба фото «заглушкових» крамниць: 10 речей × 5 крамниць, старий шлях (фід + розмір
до 19.09) проти нового (+ OpenCart -999x999, + сторінка товару). Факт: скільки речей
і фото проходять відсів, пікселі й байти найбільшого фото. Аргумент — каталог_повний.xml."""
import collections, gzip, os, re, statistics, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ)
import feed as F, жнива_v2 as Ж, жнива_фото as ЖФ   # _OPENCART читає `збільшити_url` зі СВОГО модуля — підміна там
КРАМНИЦІ = ("vilni.store", "ricamare.com.ua", "sezone.ua", "25union.com.ua", "emmeliedelage.com")
шлях = sys.argv[1] if len(sys.argv) > 1 else Ж.КАТАЛОГ
with (gzip.open if шлях.endswith(".gz") else open)(шлях, "rb") as f:
    offers, _ = F.читати_yml(f)
новий_opencart = ЖФ._OPENCART


def добір(o, новий):
    ЖФ._OPENCART = новий_opencart if новий else re.compile(r"(?!)")
    url_л, стелі = Ж._url_крамниць([x for x in offers if x.get("магазин") == o["магазин"]])
    відсів = lambda фф: Ж.позначити_одну(фф, lambda ф: url_л[o["магазин"]][Ж.збільшити_url(ф["url"])],
                                         стеля=стелі[o["магазин"]])
    фото = відсів(Ж.взяти_фото(o, 6, мітка="проба"))
    if новий and not any(ф.get("шлях") and not ф.get("заглушка") for ф in фото):
        фото += відсів(Ж.фото_зі_сторінки(o, 6, мітка="проба"))
    Ж.прибрати_кеш(фото)
    return [ф for ф in фото if ф.get("шлях") and not ф.get("заглушка")]


print("крамниця            у каталозі | речей з фото старий→новий | фото | найбільше фото (медіана) | джерело")
for м in КРАМНИЦІ:
    усі = sorted((o for o in offers if o.get("магазин") == м), key=lambda o: o["id"])
    ст = [добір(o, False) for o in усі[:10]]
    нв = [добір(o, True) for o in усі[:10]]
    def опис(р):
        б = [max(ф, key=lambda ф: ф["розмір"][0] * ф["розмір"][1]) for ф in р if ф]
        return ("%s px %d КБ" % ("×".join(map(str, statistics.median_low([ф["розмір"] for ф in б]))),
                                statistics.median([ф["байтів"] for ф in б]) // 1024)) if б else "—"
    дж = collections.Counter(ф["джерело"] for р in нв for ф in р)
    print("%-18s %5d | %2d → %2d | %2d → %2d | %s → %s | %s" % (
        м, len(усі), sum(map(bool, ст)), sum(map(bool, нв)), sum(map(len, ст)), sum(map(len, нв)),
        опис(ст), опис(нв), dict(дж)))
