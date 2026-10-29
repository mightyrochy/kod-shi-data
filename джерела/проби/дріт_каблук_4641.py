# -*- coding: utf-8 -*-
"""Рядок 4641 · як трійка (тип, `каблук_є`, `каблук` фіду) стає `heel` дроту.
Запуск: cd джерела && python3 проби/дріт_каблук_4641.py
"""
import collections, os, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import дріт_моделі as Д
import каблук as КБ
import фід_каталог as ФК

кат = ФК._база_прогону(ФК.каталог_на_диску(), ліміт_фото=0)["каталог"]
пари = []
for р in кат:
    if р.get("слот") != "взуття":
        continue
    є = КБ.каблук(р.get("назва"), None, р.get("url"))["є"]
    фід = р.get("каблук")
    вхід = dict(р, каблук_є=є)
    вихід = Д.осі({}, вхід).get("heel")
    старе = "none" if є is False else ("unknown" if є is None else "yes")
    пари.append(((р.get("тип"), є, фід), старе, вихід))

переходи = collections.Counter((старе, вихід) for _, старе, вихід in пари if старе != вихід)
невідомі = sum(вихід == "unknown" and трійка[2] is not None for трійка, _, вихід in пари)
хибне_none = sum(вихід == "none" and трійка[2] is True for трійка, _, вихід in пари)
print("ФАКТ · пар %d · unknown при відомому фіді %d · none при каблуці фіду %d"
      % (len(пари), невідомі, хибне_none))
print("ФАКТ · змінено %d · переходи %s · без змін %d"
      % (sum(переходи.values()), dict(sorted(переходи.items())), len(пари) - sum(переходи.values())))
