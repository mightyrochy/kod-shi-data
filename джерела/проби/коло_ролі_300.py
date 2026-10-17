# -*- coding: utf-8 -*-
"""КОЛО-РОЛІ (рядок 4780): вердикти ролей схем K-PAL-03 на 300 образах ДО → ПІСЛЯ. Образи — пул стенда (statement, гілки 0–2 —
різні схеми) для стенда й ж1, ж2, ж4, ж6, ж8 (різні якорі), сід 11; вердикт ролі — кожен виклик `колір_річ.тримає_дугу_схеми`
із суду (річ кольорова, дуги ролі слота й сімей схеми). ДО пише склади й вердикти (на дереві до правки), ПІСЛЯ судить ті самі
склади (`<ДО.json>` другим аргументом) і друкує лічбу та змінені вердикти.
Запуск із джерела/: python3 проби/коло_ролі_300.py <знімок.json> [<знімок ДО.json>]"""
import json, random, sys, collections as K; sys.path.insert(0, "."); sys.path.insert(0, "проби")
import pal_вердикт as ПВ, колір_річ as КР, colorspace as cs
Д = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 else None
ЛОГ, _тримає = [], КР.тримає_дугу_схеми
def _лог(x, дуги, *a, **k):
    в = _тримає(x, дуги, *a, **k)
    if "суд_від_моделі" in sys._getframe(1).f_code.co_filename and isinstance(x, dict) and x.get("id"):
        ЛОГ.append((x["id"], [list(map(float, д)) for д in дуги], в))
    return в
КР.тримає_дугу_схеми = _лог
З, rnd, n = dict(образи=[]), random.Random(11), 0
for ж in (None, "ж1", "ж2", "ж4", "ж6", "ж8"):
    Ж = json.load(open("../аудит/проби/жінки/%s.json" % ж, encoding="utf-8")) if ж else None
    for гілка in (0, 1, 2):
        вх, r, кат, спец = ПВ.стенд(гілка=гілка, намір="statement", **(dict(шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) if Ж else {}))
        к = r["кандидати"]
        for і in range(15 if ж is None else 17):
            ід = Д["образи"][n]["ід"] if Д else [rnd.choice(к[с])["id"] for с in ("верх", "низ", "сукня", "верхній_шар", "взуття", "сумка",
                 "шарф", "пояс", "сережки") if к.get(с) and с not in (("верх", "низ") if і % 2 else ("сукня",)) and rnd.random() < 0.7]
            del ЛОГ[:]; ПВ.знахідки(вх, ід); n += 1
            в = {"%s|%s" % (x, json.dumps(д)): (x, д, вв) for x, д, вв in ЛОГ}
            З["образи"].append(dict(ж=ж, гілка=гілка, схема=(спец.get("слоти") or {}).get("_схема"), ід=ід, вердикти=list(в.values()),
                                    hex={x: cs.hex_з_lab(tuple(кат[x]["lab"])) for x in ід if (кат.get(x) or {}).get("lab")}))
json.dump(З, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
if Д:
    Л, ЗМ = K.Counter(), []
    for до, пс in zip(Д["образи"], З["образи"]):
        вд = {x: вв for x, _, вв in до["вердикти"]}
        for x, д, вв in пс["вердикти"]:
            Л[(вд.get(x, "—"), вв)] += 1
            if x in вд and вд[x] != вв: ЗМ.append((до["ж"], до["гілка"], до["схема"], x, пс["hex"].get(x), д, вд[x], вв))
    print("образів %d; вердиктів ролі (річ у дугах слота) ДО → ПІСЛЯ:" % len(З["образи"]), dict(Л))
    print("змінених: %d" % len(ЗМ)); [print("  %s г%d %-26s %-36s %s %s %s→%s" % з) for з in ЗМ]
