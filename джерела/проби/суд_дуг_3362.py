# -*- coding: utf-8 -*-
"""КОЛІР-СХЕМИ (рядок 3362): суд дуг на тих самих образах ДО → ПІСЛЯ — K-PAL-02/13 (дуга очей на колі), K-PAL-07 (сім'ї великих
одним тоном кола); контроль — K-PAL-03 (дуга схеми), K-PAL-09/10/14 (вікна палітри), K-COL-03 (їхніх дуг правка не міняє). Образи — пул стенда (statement, гілки 0–2 —
різні схеми), сід 7; ДО пише склади й знахідки, ПІСЛЯ судить ті самі склади (`<ДО.json>` другим аргументом) і друкує лічбу й зміни.
`-ж ж4` — риси жінки з `аудит/проби/жінки/ж4.json` замість стенда.
Запуск із джерела/: python3 проби/суд_дуг_3362.py <знімок.json> [<знімок ДО.json>] [-о N] [-ж ж4]"""
import json, random, sys, collections as K; sys.path.insert(0, "."); sys.path.insert(0, "проби")
import pal_вердикт as ПВ, colorspace as cs
ПР = ("K-PAL-02", "K-PAL-03", "K-PAL-07", "K-PAL-09", "K-PAL-10", "K-PAL-13", "K-PAL-14", "K-COL-03")
N = int(sys.argv[sys.argv.index("-о") + 1]) if "-о" in sys.argv else 60
Д = json.load(open(sys.argv[2], encoding="utf-8")) if len(sys.argv) > 2 and not sys.argv[2].startswith("-") else None
Ж = json.load(open("../аудит/проби/жінки/%s.json" % sys.argv[sys.argv.index("-ж") + 1], encoding="utf-8")) if "-ж" in sys.argv else None
РИСИ = dict(шкіра=Ж["skin"][0], волосся=Ж["hair"], очі=Ж["eyes"]) if Ж else {}
З, rnd = dict(образи=[]), random.Random(7)
for гілка in (0, 1, 2):
    вх, r, кат, спец = ПВ.стенд(гілка=гілка, намір="statement", **РИСИ); к = r["кандидати"]
    склади = [о["ід"] for о in Д["образи"] if о["гілка"] == гілка] if Д else [
        [rnd.choice(к[с])["id"] for с in ("верх", "низ", "сукня", "верхній_шар", "взуття", "сумка", "шарф", "пояс", "сережки")
         if к.get(с) and с not in (("верх", "низ") if n % 2 else ("сукня",)) and rnd.random() < 0.7] for n in range(N)]
    for ід in склади:
        зн = [z for z in ПВ.знахідки(вх, ід)[0] if z.get("правило") in ПР]
        З["образи"].append(dict(гілка=гілка, схема=(спец.get("слоти") or {}).get("_схема") or спец.get("схема"), ід=ід,
                                зн=sorted("%s|%s|%s" % (z["правило"], z.get("ярлик"), ",".join(map(str, z.get("речі") or ()))) for z in зн)))
json.dump(З, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
if Д:
    Л, ЗМ, ключ = K.Counter(), [], lambda оо: K.Counter("|".join(z.split("|")[:2]) for z in оо["зн"])
    for до, пс in zip(Д["образи"], З["образи"]):
        for м, оо in (("ДО", до), ("ПІСЛЯ", пс)): Л.update((z.split("|")[0], м) for z in оо["зн"])
        if ключ(до) != ключ(пс): ЗМ.append((до["гілка"], до["схема"], dict(ключ(до) - ключ(пс)), dict(ключ(пс) - ключ(до))))
    print("образів %d; знахідки ДО → ПІСЛЯ:" % len(З["образи"]))
    for п in ПР: print("  %-9s %4d → %4d" % (п, Л[(п, "ДО")], Л[(п, "ПІСЛЯ")]))
    print("образів зі зміною (правило|ярлик; номери речей пакета різняться між ДО і ПІСЛЯ): %d" % len(ЗМ))
    for з in ЗМ[:30]: print("  гілка %d %-26s − %s + %s" % з)
