# -*- coding: utf-8 -*-
"""Скретч: 300 образів, вердикти K-PAL-03 «річ тримає дугу ролі» — ДО (код) і кандидат ПІСЛЯ (exp.сила)."""
import json, sys, os, random, pickle, math
SP = "/tmp/claude-0/-home-user-kod-shi-data/9a5eb989-d513-548d-aefc-237879e686bd/scratchpad/"
sys.path.insert(0, SP); import exp as E
sys.path.insert(0, "проби"); import pal_вердикт as ПВ, колір_річ as КР, colorspace as cs
ЛОГ = []
_ориг = КР.тримає_дугу_схеми
def _лог(x, дуги, *a, **k):
    в = _ориг(x, дуги, *a, **k)
    if "суд_від_моделі" in sys._getframe(1).f_code.co_filename and isinstance(x, dict) and x.get("lab"):
        ЛОГ.append((x.get("id"), tuple(x["lab"]), tuple(tuple(map(float, д)) for д in дуги), в, КР.не_вимір(x) is not None))
    return в
КР.тримає_дугу_схеми = _лог
ЖІНКИ = [None] + ["ж%d" % i for i in (1, 2, 4, 6, 8)]
rnd = random.Random(11); О = []
for ж in ЖІНКИ:
    Ж = json.load(open("../аудит/проби/жінки/%s.json" % ж, encoding="utf-8")) if ж else None
    РИСИ = dict(шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) if Ж else {}
    for гілка in (0, 1, 2):
        вх, r, кат, спец = ПВ.стенд(гілка=гілка, намір="statement", **РИСИ); к = r["кандидати"]
        сх = (спец.get("слоти") or {}).get("_схема") or спец.get("схема")
        for n in range(17 if ж else 15):
            ід = [rnd.choice(к[с])["id"] for с in ("верх", "низ", "сукня", "верхній_шар", "взуття", "сумка", "шарф", "пояс", "сережки")
                  if к.get(с) and с not in (("верх", "низ") if n % 2 else ("сукня",)) and rnd.random() < 0.7]
            ЛОГ.clear(); ПВ.знахідки(вх, ід)
            слот = {x: (кат.get(x) or {}).get("слот") for x in ід}
            О.append(dict(ж=ж, гілка=гілка, схема=сх, ід=ід, виклики=list(ЛОГ),
                          ролі={с: (v.get("роль"), v.get("дуга_тону")) for с, v in (спец.get("слоти") or {}).items() if isinstance(v, dict)},
                          слот=слот, фото={x: ((кат.get(x) or {}).get("фото") or [None])[0] for x in ід},
                          назва={x: (кат.get(x) or {}).get("назва") for x in ід}))
print("образів", len(О), "викликів", sum(len(о["виклики"]) for о in О))
pickle.dump(О, open(SP + "о300.pkl", "wb"))
