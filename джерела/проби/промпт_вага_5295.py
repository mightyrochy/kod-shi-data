# -*- coding: utf-8 -*-
"""Рядки 5295, 4140, 5672, 4493 (ПРОМПТ-ВАГА): вага промптів стилістки й ходу на стенді, без моделі.
Друкує: `statement_codes` ремонту (і оцінки 6б — з аргументом: вердикти.txt живих 1510 Б, `git show e6ce58e0:аудит/
живі_1510_Б/04_ж1_оціни_образ_6б/вердикти.txt`), з них визначення кодів лише з `not_run`; `item_type` і весь промпт
ходу; «тканина: невідомо» в пулі стенда — усього і на слотах без тканини; імена ключів у правилі кінця відповіді.
Запуск: cd джерела && python3 -W ignore проби/промпт_вага_5295.py [вердикти.txt]"""
import copy, json, re, sys, collections as C
sys.path.insert(0, ".")
import bridge as Б, feed as Ф, міст_пакет as МП, збирач_промптів as З, мовний_шар as М, оцінка_образу as О
дамп = lambda x: len(json.dumps(x, ensure_ascii=False))
def словник(п):
    sc, нр = п["task"].get("statement_codes", {}), set()
    for в in [о.get("checklist") or {} for о in п.get("verdict", [])] + [{"_": {"not_run": [x for в in (п.get("not_run_everywhere") or {}).values() for x in в]}}] + [{"_": у} for у in п.get("unknown", []) if "not_run" in у]:
        нр |= {x for б in в.values() for x in б.get("not_run") or []}
    без = lambda x: {к: без(в) for к, в in x.items() if к not in ("not_run", "not_run_everywhere")} if isinstance(x, dict) else [без(в) for в in x] if isinstance(x, list) else x
    лише = нр - set(З.коди_заяв(без({к: в for к, в in п.items() if к != "task"})))
    return "statement_codes %d знаків (%d кодів), з них лише not_run %d кодів · %d знаків" % (дамп(sc), len(sc), len(лише & set(sc)), дамп({к: sc[к] for к in лише if к in sc}))
вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), каталог=Ф.каталог_на_диску(), варіантів=1, ремонт_варіантів=1, без_фото=1)
вик = lambda дія, **д: json.loads(Б.виклик(дія, json.dumps(dict(вх, **д), ensure_ascii=False)))
пул = вик("запити")["пакети"]["1"]["пул"]; р = [пул[с][0]["н"] for с in ("верх", "низ", "взуття", "сумка")]
т = вик("від_моделі", текст_моделі=json.dumps(dict(версія="1", образи=[dict(ід="о1", речі=р), dict(ід="о2", речі=р[:2] + р[3:])]), ensure_ascii=False))["промпт_ремонту"]
print("ремонт: промпт %d знаків · %s" % (len(т), словник(json.loads(т))))
if len(sys.argv) > 1:
    d0 = json.load(open(sys.argv[1], encoding="utf-8")); е = d0["прогони"][0]["вердикти"][0]["етапи"]
    d = dict(d0["спільне"]["вхід_прогону"], речі=е["речі"]["речі"], пікселі={}, сценарій_оцінки=е.get("сценарій_екрана") or {})
    d.pop("каталог", None); О._виміри = lambda *а, **к: copy.deepcopy(е["суд"]["речі"])
    т = О.промпт_оцінки(О.суд(d), е.get("питання")); print("оцінка 6б: промпт %d знаків · %s" % (len(т), словник(json.loads(т))))
п = json.loads(М.промпт_розмови({"розмова": {"нове": "Хочу образ на роботу", "історія": []}}))
print("хід: item_type %d знаків, з дублем %d кодів · промпт ходу %d знаків" % (len(М._типи_речей()), М._типи_речей().count(" ("), дамп(п)))
пак = [п for п in МП._КЕШ_ПАКЕТА.values() if п.get("пакет")][0]["пакет"]["пул"]
нев = C.Counter(с for с, рр in пак.items() for р in рр if р.get("тканина") == "невідомо")
print("пул: «тканина: невідомо» %d · на слотах без тканини %d · у «прикраси» %d" % (sum(нев.values()), sum(в for с, в in нев.items() if с in {"сережки", "намисто", "кольє", "браслет", "каблучка", "брошка"}), нев["прикраси"]))
print("правило кінця: імен ключів %d" % len(re.findall(r"«(answer|answer_schema|input|statement_codes)»", З.КІНЕЦЬ_ВІДПОВІДІ_EN)))
