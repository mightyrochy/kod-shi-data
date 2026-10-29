# -*- coding: utf-8 -*-
"""Рядок 6028: `param тип` у `каталог_повний.xml` — тип жниварки, не продукту. Проти `feed.тип_речі` лічить легінси
продукту (ними міряють пул спорту, рядок 5800) і розбіжності XML ≠ продукт. Висновки про продукт — з `тип_речі`,
не з XML. Запуск із теки `джерела`, каталог розпакований: python3 проби/тип_xml_проти_речі_6028.py"""
import sys, os, collections, xml.etree.ElementTree as E
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф
шлях = Ф.каталог_на_диску()
сирий = {о.get("id"): next((''.join(п.itertext()).strip() for п in о.findall("param") if п.get("name") == "тип"), "")
         for о in E.parse(шлях).getroot().iter("offer")}
речі = Ф.читати_yml(шлях, показ=False)[0]
лег, розб = collections.Counter(), collections.Counter()
for р in речі:
    т, с = Ф.тип_речі(р), сирий.get(р["id_жниварки"], "")
    лег["легінси за продуктом"] += т == "легінси"
    лег["з них XML «легінси»"] += т == "легінси" and с == "легінси"
    лег["з них XML інше"] += т == "легінси" and bool(с) and с != "легінси"
    лег["з них XML без типу"] += т == "легінси" and not с
    розб[(с, т)] += bool(с) and с != т
print("речей %d · %s" % (len(речі), dict(лег)))
print("розбіжних XML ≠ продукт: %d; найчастіші: %s" % (sum(розб.values()), розб.most_common(4)))
