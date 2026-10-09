# -*- coding: utf-8 -*-
"""Рядок 1440: вето «взуття без принта» з коментаря діє на взуття, а не на весь образ.
Стенд (сід 4242), паспорт з коментарем `{slot: shoes, pattern: print_generic}` (як його віддає
мовна модель шару): речей із візерунком у пулі по слотах. До правки слот не писався для принтів
(лише для кольорів), і `refusals.prints` різало візерунчасте з усіх слотів: 64 → 3.
Прогін: cd джерела && python3 проби/пул_вето_принт_слот.py      (~30 с)"""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, мовний_шар as МШ
кат = Ф.каталог_на_диску("каталог_повний.xml")
def пул(коментар):
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=4242, каталог=кат)
    if коментар:
        п = {"перекладено_шаром": True, "вето": {}}
        вх["паспорт"] = МШ.паспорт_з_коментаря({"vetoes": коментар}, паспорт_досі=п)["паспорт"]
    МП._КЕШ_ПАКЕТА.clear(); B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    return [p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")][0]["кандидати"]
for назва, к in (("без коментаря", None), ("взуття без принта", [{"slot": "shoes", "pattern": "print_generic"}]),
                 ("весь образ без принта", [{"pattern": "print_generic"}])):
    кан = пул(к)
    візер = {с: sum(1 for r in р if (r.get("візерунок") or "solid") != "solid") for с, р in кан.items() if isinstance(р, list)}
    print("%-22s речей із візерунком у пулі %3d · по слотах %s" % (назва, sum(візер.values()),
          ", ".join("%s %d" % t for t in sorted(візер.items()) if t[1])))
