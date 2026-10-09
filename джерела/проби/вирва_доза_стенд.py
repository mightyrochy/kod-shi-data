# -*- coding: utf-8 -*-
"""ВИРВА-СМІЛИВІСТЬ (рядки 841, 886): чи доходить доза сміливих образів (`set.bold`) до промпту ремонту 10→5 — і лише під
сміливим наміром. Стенд `стенд_вх.json`, 10 образів з пулу руки 1: парні — найхроматичніші верх і низ пулу різних тонів,
непарні — найтихіші. Наміри: statement, statement + мета «приховати», conventional. Нічого не викликає. Друкує факт.
Запуск: cd джерела && python3 проби/вирва_доза_стенд.py"""
import json, math, os, sys
Д = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, Д); os.chdir(Д)
import bridge as B, colorspace as cs
for намір, мета in (("statement", None), ("statement", "приховати"), ("conventional", None)):
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), варіантів=10, ремонт_варіантів=5, без_фото=1, намір=намір)
    if мета:
        вх["паспорт"] = dict(вх.get("паспорт") or {}, мета=мета)
    пул = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["пакети"]["1"]["пул"]
    C = lambda r: math.hypot(*cs.to_lab(tuple(int(r["hex"][1 + 2 * k:3 + 2 * k], 16) for k in range(3)))[1:]) if r.get("hex") else 0
    за = {с: sorted(пул[с], key=C) for с in ("верх", "низ", "взуття", "сумка")}
    н = lambda с, і, гучно: (за[с][-1 - і % len(за[с])] if гучно else за[с][і % len(за[с])])["н"]
    образи = [dict(ід="о%d" % (і + 1), підпис="образ %d" % (і + 1),
                   речі=[н("верх", і, і % 2 == 0), н("низ", і + 3, і % 2 == 0), н("взуття", і, і % 2 == 0), н("сумка", і, False)])
              for і in range(10)]
    в = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, текст_моделі=json.dumps(dict(версія="1", образи=образи), ensure_ascii=False)),
                                                    ensure_ascii=False)))
    смл = ((в.get("вердикт") or {}).get("набір") or {}).get("сміливі")
    дріт = json.loads(в["промпт_ремонту"]); bold = (дріт.get("set") or {}).get("bold")
    вибір = json.loads(в.get("промпт_лише_вибору") or "{}")
    print("ФАКТ · %s%s · обʼєкт: %s · ремонт set.bold: %s · рядок входу: %s · вибір set.bold: %s · помилки схеми: %s" % (
        намір, " + мета " + мета if мета else "",
        "сміливих %d, лишити %d" % (len(смл["образи"]), смл["лишити"]) if смл else "нема",
        json.dumps(bold, ensure_ascii=False) if bold else "нема",
        any(р.startswith('"bold"') for р in дріт["task"]["input"]), bool((вибір.get("set") or {}).get("bold")),
        len(в.get("протокол_помилки") or [])))
