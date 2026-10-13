# -*- coding: utf-8 -*-
"""Р2-2в (рядок 551): чи мають R-PRN-03 і K-SIL-06 вхід на каталозі. Пул руки 1 (`запити`, каталог_повний,
сід 3) на трьох сценаріях; образи — 150 випадкових на сценарій (сукня чи верх+низ, взуття, сумка) і ВСІ пари
речей однієї сім'ї мотиву з різних слотів пулу. Друкує: речі з виміряним масштабом мотиву (вхід K-SIL-06),
образи з R-PRN-03 знахідкою (вхід є) і питанням (масштабу нема), образи з K-SIL-06.
Запуск: cd джерела && python3 проби/принти_вхід.py"""
import json, sys, random, pathlib, collections; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import bridge as B, pipeline as ПЛ
from композитор_річ import _у_річ
СЦ = {"office": dict(нагода="робота", місце="офіс", година=9, темп_c=18),
      "date": dict(нагода="побачення", місце="ресторан", година=20, темп_c=5),
      "wedding": dict(нагода="весілля_гість", місце="ресторан", година=16, темп_c=24)}
вх0 = json.load(open("стенд_вх.json", encoding="utf-8")); ІМЕНОВАНІ = lambda r: r.get("візерунок") not in (None, "solid", "принт")
def суд(F, T, kw, речі):
    зн = [z for ст in (ПЛ.перевірити_образ(F, речі, тіло=T, **dict(kw)).get("стани") or {}).values() for z in (ст or [])]
    return {(z.get("правило"), z.get("сила")) for z in зн if isinstance(z, dict) and z.get("правило") in ("R-PRN-03", "K-SIL-06")}
for ім, сц in СЦ.items():
    вх = dict(вх0, каталог="каталог_повний.xml", сід=3, сценарій=сц)
    к = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False))).get("кандидати") or {}
    за_ід = {x["id"]: x for x in B.каталог_останнього_пакета()}
    F, T, _з, kw = B._збірка(B._нормалізувати_вхід(B._застосувати_паспорт(dict(вх))))
    пул = {с: [за_ід[x.get("id") or x.get("ід")] for x in (к.get(с) or []) if (x.get("id") or x.get("ід")) in за_ід] for с in ("верх", "низ", "сукня", "взуття", "сумка")}
    річ = lambda r: _у_річ(dict(r), r.get("слот") or "верх", T)
    рнд, лік = random.Random(3), collections.Counter()
    for i in range(150):
        осн = [рнд.choice(пул["сукня"])] if (пул["сукня"] and i % 2) else [рнд.choice(пул["верх"]), рнд.choice(пул["низ"])]
        for п in суд(F, T, kw, [річ(r) for r in осн + [рнд.choice(пул[с]) for с in ("взуття", "сумка") if пул[с]]]):
            лік[п] += 1
    пари = [(a, b) for с1 in пул for с2 in пул if с1 < с2 for a in пул[с1] for b in пул[с2] if ІМЕНОВАНІ(a) and a.get("візерунок") == b.get("візерунок")]
    лп = collections.Counter(п for a, b in пари for п in суд(F, T, kw, [річ(a), річ(b)]))
    print("%-8s речей пулу %d · з масштабом мотиву %d · 150 образів: %s · пар однієї сім'ї мотиву %d: %s" % (ім,
          sum(map(len, пул.values())), sum(1 for рр in пул.values() for r in рр if r.get("масштаб_відн") is not None),
          dict(лік) or "—", len(пари), dict(лп) or "—"))
