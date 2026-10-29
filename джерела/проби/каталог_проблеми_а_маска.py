# -*- coding: utf-8 -*-
"""Реєстр А (рядок 5630), клас А7: маска речі на кадрі. Друкує джерела масок кадрів галерей
(`каталог_кадри.json.gz`: ATR, SAM, «чекає_sam» — прогін «лише ATR» поряд із мовною моделлю,
«нема» — SAM речі не знайшов, без маски — кадр не скачався чи заглушка), частку кадрів із маскою
< 5 % кадру, і чи збагачення (кадр жнив) зберігає джерело й частку маски.
Запуск: cd джерела && python3 проби/каталог_проблеми_а_маска.py"""
import collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import feed as Ф, фід_кадр_колір as ФКК
кадри, зб = ФКК.читати_кадри(), Ф.читати_збагачення()
джерела, чому, малі = collections.Counter(), collections.Counter(), 0
for вв in кадри.values():
    for в in вв:
        д = в.get("маска") or "без маски"
        джерела[д] += 1
        if д == "без маски":
            чому[str(в.get("чому") or "")[:28]] += 1
        малі += д in ("ATR", "SAM") and (в.get("частка_маски") or 0) < 0.05
print("кадрів %d · джерела масок:" % sum(джерела.values()), dict(джерела.most_common()))
print("  без маски — чому:", чому.most_common(6))
print("  ATR/SAM з маскою < 5 %% кадру: %d" % малі)
з_маскою = sum(1 for з in зб.values() if isinstance(з, dict) and any(к in з for к in ("маска", "частка_маски")))
print("записів збагачення з джерелом/часткою маски кадру жнив: %d з %d" % (з_маскою, len(зб)))
print("моделі записів збагачення:", collections.Counter(str(з.get("модель")) for з in зб.values() if isinstance(з, dict)).most_common())
