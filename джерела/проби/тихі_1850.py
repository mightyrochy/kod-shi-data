# -*- coding: utf-8 -*-
"""Проба (рядок 1850): B1 (K-INT-04) поза трауром — чи рахуються тихі джерела i1/i2 (тема-4 XII.3:
меню загальне; XIV.1 крок 9: «in conservative contexts prefer quiet sources»). База — та сама, що в
`прикр2_b4_траур.py`: усі різні образи рук 1–2 збережених прогонів (`аудит/перевірки/**/вердикти*.gz`),
речі з каталогу. Друкує провали B1 на нетраурних образах (`тихо=False`, conventional) і скільки з них
мають i1/i2 (`суд_інтерес.тихі_джерела`) — тобто підлога стоїть, хоч тихе джерело в образі є.
Червоне — таких > 0. Моделі не кличе. Запуск: python3 джерела/проби/тихі_1850.py"""
import collections, glob, gzip, os, re, sys                                   # noqa: E401
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ТУТ)
import фід_каталог as ФК, композитор_річ as КР, outfit as O                    # noqa: E401,E402
import суд_інтерес as СІ                                                      # noqa: E402
за_ід = {r["id"]: r for r in ФК._прочитати_каталог(ФК.каталог_на_диску(), ліміт_фото=0)["каталог"]}
набори = {}
for ф in sorted(glob.glob(os.path.join(ТУТ, "..", "аудит", "перевірки", "**", "вердикти*.gz"), recursive=True)):
    for м in re.finditer(r'\\?"ід\\?": ?\[([^\]]*)\]', gzip.open(ф).read().decode()):
        ід = tuple(sorted(set(re.findall(r'ж-[^"\\,]+', м.group(1)))))
        if len(ід) >= 2 and all(і in за_ід for і in ід):
            набори.setdefault(ід, "похорон" in ф)
b1, вид, хибні = collections.Counter(), collections.Counter(), 0
for ід, траур in набори.items():
    if траур:
        continue
    E = O.елементи([КР._у_річ(за_ід[і], за_ід[і]["слот"], None) for і in ід])
    провал = bool(СІ.підлога_інтересу_проактивно(E, "conventional", тихо=False))
    b1["провал" if провал else "пройдено"] += 1
    тихі = СІ.тихі_джерела(E)
    for д in тихі:
        вид[д["важелі"][0].split(":")[0]] += 1
    хибні += провал and bool(тихі)
print("нетраурних образів рук 1–2: %d" % sum(b1.values()))
print("B1 (K-INT-04, conventional, тихо=False): %s" % dict(b1))
print("тихі джерела в цих образах: %s" % dict(вид))
print("B1 провал, хоч i1/i2 в образі є: %d — %s" % (хибні, "ЧЕРВОНЕ" if хибні else "зелене"))
