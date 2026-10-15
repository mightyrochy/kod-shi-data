# -*- coding: utf-8 -*-
"""Рядок 5628 (реєстр 5616, клас Г5): опис речей, дописаних жниварками 18.09, не доходить до продукту. Жниварка пише
опис у `<description>`, а читач фіду бере `param «опис»` (формат складальника 07.09). Факт: по видах записів — скільки
мають `<description>`, `param «опис»` і непорожнє `опис` після `feed.читати_yml`. Запуск: python3 джерела/проби/каталог_проблеми_г_опис.py"""
import collections, gzip, os, re, sys                                          # noqa: E401
Д = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
sys.path.insert(0, Д); os.chdir(Д)                                             # noqa: E702
import feed as F                                                               # noqa: E402
xml = gzip.open(os.path.join(Д, "..", "каталог_повний.xml.gz"), "rt", encoding="utf-8").read()
вид, сире = {}, collections.Counter()
for о in re.findall(r"<offer\b.*?</offer>", xml, re.S):
    і = re.search(r'<offer id="([^"]+)"', о).group(1)
    в = "складальник 07.09" if 'name="бал_інформації"' in о else "жниварка 18.09"
    вид[і] = в; сире[(в, "записів")] += 1
    сире[(в, "<description>")] += "<description>" in о; сире[(в, "param опис")] += 'name="опис"' in о
оф = F.читати_yml(F.каталог_на_диску("каталог_повний.xml"))[0]
дійшло = collections.Counter((вид.get(o["id"].split("@")[0]), bool(o.get("опис"))) for o in оф)
for в in ("складальник 07.09", "жниварка 18.09"):
    print("%-18s записів %5d · <description> %5d · param «опис» %5d · у фіді речей %5d, з них з описом %5d" % (в,
          сире[(в, "записів")], сире[(в, "<description>")], сире[(в, "param опис")],
          дійшло[(в, True)] + дійшло[(в, False)], дійшло[(в, True)]))
