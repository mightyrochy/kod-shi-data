# -*- coding: utf-8 -*-
"""Рядок 5637 (а): відновлені адреси `каталог_показ.json.gz`, спільні для ≥2 речей РІЗНОГО кольору
(варіанти однієї картки: перший кадр сторінки — один на всі кольори). Друкує кількість адрес і
речей, по крамницях. Запуск: cd джерела && python3 проби/показ_спільні_відновлені.py [файл.json.gz]"""
import collections, gzip, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф
д = json.load(gzip.open(sys.argv[1] if len(sys.argv) > 1 else "каталог_показ.json.gz"))
оф = {o["id"]: o for o in Ф.читати_yml(Ф.каталог_на_диску("каталог_повний.xml"), показ=False)[0]}
групи = collections.defaultdict(list)
for і, а in (д.get("адреси") or {}).items():
    групи[а[0]].append(і)
кол = lambda і: ((оф.get(і) or {}).get("параметри") or {}).get("колір")
хибні = {u: g for u, g in групи.items() if len({кол(і) for і in g}) > 1}
речі = [і for g in хибні.values() for і in g]
print("відновлено %d · адрес %d · спільних різнокольорових адрес %d · речей на них %d"
      % (len(д.get("адреси") or {}), len(групи), len(хибні), len(речі)))
print("по крамницях:", collections.Counter(і.split("@")[-1] for і in речі).most_common(8))
