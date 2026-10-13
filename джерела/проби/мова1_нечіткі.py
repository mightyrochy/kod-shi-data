# -*- coding: utf-8 -*-
"""МОВА-1 (рішення власника 02.10: мовна модель інтерпретує нечіткі й надиктовані голосом запити). 12 нечітких + 3 чіткі
контрольні; кожен — один хід розмови (`промпт_розмови` → жива модель → `прийняти_розмову` → шов `мова`). Очікуване:
нагода (occasion/place), частина дня (з години теж; «-» — можна не знати), ошатність-смуга орієнтовно (перетин), чи потрібна `stylist_note`
(None — байдуже), умова на вимір. Друкує влучно/частково/хибно з причиною. Запуск: cd джерела && ZHYVA=sonnet python3
проби/мова1_нечіткі.py [номери через кому]; VIDPOVIDI=<тека> — зберегти сирі відповіді (без ZHYVA — перечитати їх)."""
import json, os, sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import мова_спільне as С; М = С.М
ВИПАДКИ = [  # (її слова, нагоди, частини дня, смуга, stylist_note, {вимір: значення})
    ("е-е ну короче мені треба щось на роботу завтра зранку бо в нас там е-е нарада з керівництвом", "work office_corporate office_creative", "morning", (5, 7), False, {}),
    ("у офіс ні стоп не в офіс а на співбесіду в айтішну компанію о десятій", "job_interview", "morning", (4, 6), None, {}),
    ("шо одіть на днюху до подруги в суботу ввечері в кафешці нічо такого", "celebration cafe restaurant_casual", "evening", (3, 5), None, {}),
    ("йду на тусу в клуб на районі хочу бути норм але не вирвиоко", "celebration club", "evening night", (3, 6), None, {}),
    ("о так звісно найкращий день у моєму житті корпоратив з бухгалтерією в пʼятницю", "celebration work festive_dinner restaurant_casual", "evening day -", (4, 7), True, {}),
    ("на проводи в неділю з мамою на цвинтар а потім посидимо там же", "mourning church everyday", "day morning -", (3, 5), True, {}),
    ("гостини до свекрухи в неділю на обід хочу шоб вона нічо не сказала", "celebration everyday home", "day", (3, 6), True, {}),
    ("в театр о пів на восьму вечора", "theatre", "evening", (5, 7), False, {"hour": 19}),
    ("спершу робота а ввечері театр і я не встигну переодягтися", "work theatre office_corporate office_creative", "day evening morning", (5, 7), True, {}),
    ("щось на вечір але не дуже ну ти зрозуміла", "", "evening", (3, 6), None, {}),
    ("на прогулянку з дитиною в парк а там е-е обіцяли дощ і градусів дванадцять десь по обіді", "walk park playground", "day", (2, 4), False, {"precipitation": "rain", "temperature_c": 12}),
    ("весілля подруги я свідкова в серпні на природі вдень спека жах", "wedding_guest wedding_day", "day", (5, 7), True, {"reserved_colour": "near_white"}),
    ("На побачення в ресторан у суботу ввечері", "date restaurant_casual restaurant_upscale", "evening", (4, 6), False, {}),
    ("Співбесіда в банку о 10 ранку", "job_interview", "morning", (6, 8), False, {"hour": 10}),
    ("Прогулянка парком у неділю вдень, +18", "walk park", "day", (2, 4), False, {"temperature_c": 18}),
]
def частина(в): г = в.get("hour"); return в.get("part_of_day") if г is None else ("morning" if г < 12 else "day" if г < 17 else "evening" if г < 23 else "night")
номери, підс, тека = [int(х) for х in sys.argv[1].split(",")] if len(sys.argv) > 1 else range(1, 16), {"влучно": 0, "частково": 0, "хибно": 0}, os.environ.get("VIDPOVIDI")
for н in номери:
    слова, нагоди, части, (а, б), нота, ще = ВИПАДКИ[н - 1]
    ф = os.path.join(тека or ".", "%02d.json" % н)
    if not С.МОДЕЛЬ and not (тека and os.path.exists(ф)): print("%2d %s" % (н, слова)); continue
    відп, с = С.модель(М.промпт_розмови({"розмова": {"нове": слова, "історія": []}, "сценарій": {}, "паспорт": {}})) if С.МОДЕЛЬ else (open(ф).read(), 0.0)
    if тека and С.МОДЕЛЬ: os.makedirs(тека, exist_ok=True); open(ф, "w").write(відп or "")
    р = М.прийняти_розмову(відп); п = json.loads(М.мова({"паспорт_з": р["внутрішня"], "сценарій": {}, "паспорт": {}, "слова_розмови": [слова], "частини": р["частини"]}))["паспорт"]
    в, з = С.ПН.виміри_нагоди(п, {}); в, пн = {к: (v if з[к] != "default" else None) for к, v in в.items()}, (п.get("пояснення_мови") or "").strip()  # свіжі виміри без типових коду (рядок 860)
    ош = в.get("formality") or [0, 0]; хиби = (["нагода %s/%s" % (в["occasion"], в["place"])] if нагоди and not {в["occasion"], в["place"]} & set(нагоди.split()) else []) \
        + (["частина %s" % частина(в)] if (частина(в) or "-") not in части.split() else []) + (["смуга %s" % ош] if ош[1] < а or ош[0] > б else []) \
        + (["нота %s" % ("бракує" if нота else "зайва")] if нота is not None and bool(пн) != нота else []) + ["%s=%s" % (к, в.get(к)) for к, v in ще.items() if в.get(к) != v]
    оц = "влучно" if not хиби else "хибно" if len(хиби) >= 2 or хиби[0].startswith("нагода") else "частково"; підс[оц] += 1
    print("%2d %-8s %s/%s %s %s ош%s %.0fс | %s%s" % (н, оц, в["occasion"], в["place"], частина(в), в.get("hour"), ош, с, "; ".join(хиби), (" | нота: " + пн) if пн else ""))
print("РАЗОМ (%s): %s" % (С.МОДЕЛЬ, " · ".join("%s %d" % кв for кв in підс.items())))
