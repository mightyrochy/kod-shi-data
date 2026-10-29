# -*- coding: utf-8 -*-
"""Рядки 6206, 6207, 6208, 6213: промпти складання, ремонту, вибору й повноти на мосту (`стенд_вх.json`, офіс) — ДО
(origin/main) і ПІСЛЯ на тих самих входах і тих самих відповідях: символи, кирилиця коду в «case» повноти, чи є
рядок заяв, «language», «or the outfit's «findings»»; повтор формату «no_outfits» — кирилиця.
Запуск із `джерела`: python3 проби/промпти3_стенд.py"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import промпти3_база as Б
КИР = re.compile(r"[А-Яа-яІіЇїЄєҐґ]")

if "--json" in sys.argv:
    sys.path.insert(1, os.getcwd())
    import bridge as B, feed
    вх = dict(json.load(open("стенд_вх.json")), варіантів=10, ремонт_варіантів=5, мова_тексту="English", без_фото=1,
              випадок="робочий день в офісі", сценарій=dict(нагода="робота", місце="офіс", година=9, темп_c=14))
    вх["каталог"] = feed.каталог_на_диску(вх["каталог"])
    міст = lambda **д: json.loads(B.виклик("від_моделі", json.dumps(dict(вх, **д), ensure_ascii=False)))
    з = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
    пул = з["пакети"]["1"]["пул"]; н = lambda с, i: пул[с][i % len(пул[с])]["н"]
    образи = [dict(ід="о%d" % і, підпис="a", речі=[н("верх", і), н("низ", і), н("взуття", і)]) for і in range(1, 5)]
    в1 = міст(ітерація=1, текст_моделі=json.dumps(dict(версія="1", образи=образи + [dict(ід="о5", речі=[н("сукня", 2)])])))
    в2 = міст(ітерація=2, текст_моделі=json.dumps(dict(версія="1", образи=образи)), попередній_вердикт=в1["вердикт"])
    п = dict(складання=з["руки"]["1"]["текст"] if isinstance(з["руки"]["1"], dict) else з["руки"]["1"],
             ремонт=в2["промпт_ремонту"], вибір=в2["промпт_лише_вибору"], повнота=в2["промпт_повноти"],
             повнота_всі=в2["промпт_повноти_до_вибору"])
    вих = {к: dict(симв=len(т), кир_case=len(КИР.findall(json.dumps(json.loads(т).get("case"), ensure_ascii=False))),
                   заяви=next((р[:22] for р in json.loads(т)["task"]["input"] if re.match(r'"(statements|fix)"', р)), None),
                   language="language" in json.loads(т), findings="or the outfit's «findings»" in т) for к, т in п.items()}
    пв = міст(ітерація=1, текст_моделі=json.dumps(dict(version="1", answer="no outfit")))["повторний_виклик"]
    вих["повтор"] = dict(кир=len(КИР.findall(пв)), errors=json.loads(пв)["errors"])
    print(json.dumps(вих, ensure_ascii=False))
else:
    до, після = Б.до_після(__file__)
    for к in до:
        print("%-12s ДО %s\n%-12s ПІСЛЯ %s" % (к, до[к], "", після[к]))
