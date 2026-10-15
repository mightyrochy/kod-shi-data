# -*- coding: utf-8 -*-
"""Рядки 5745–5747: записаний промпт `ОЦІНКА` (VIDPOVIDI/*ОЦІНКА_відповідь.txt) → той самий вхід крізь «на фото нема»
і нове оголошення: блокери й знахідки ДО → ПІСЛЯ, `not_in_photo`, чи є в промпті правило «суди те, що на фото».
Запуск: python3 -W ignore проби/оцінка_нема_на_фото_5747.py <файл>…   (ід образу — латинкою, як на дроті)"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import оцінка_образу as О, суд_чеклісти as С, збирач_промптів as ЗП, внутрішня_мова as ВМ

for шлях in sys.argv[1:]:
    т = open(шлях, encoding="utf-8").read()
    до, кінець = json.JSONDecoder().raw_decode(т[т.index("{"):])
    дані = {к: v for к, v in до.items() if к != "task"}
    ч = dict(дані.get("check") or {})
    # блокер дроту → ядро → «на фото нема»; K-SHO-01 → взуття (ті самі таблиці, що в `відсутнє_на_фото`)
    нема = [С.БЛОКЕРИ_НА_ФОТО.get(ВМ.ключ("structural_blocker", б.get("code"))) for б in ч.get("blockers") or []]
    нема += [С.ПРАВИЛО_НА_ФОТО[з["rule"]] for з in ч.get("findings") or [] if з.get("rule") in С.ПРАВИЛО_НА_ФОТО]
    ч["blockers"] = [б for б in ч.get("blockers") or []
                     if ВМ.ключ("structural_blocker", б.get("code")) not in С.БЛОКЕРИ_НА_ФОТО]
    ч["findings"] = [з for з in ч.get("findings") or [] if з.get("rule") not in С.ПРАВИЛО_НА_ФОТО]
    дані["check"] = {к: v for к, v in ч.items() if v}
    коди = С.коди_нема_на_фото([dict(слот=с) for с in нема if с])
    if коди:
        дані["not_in_photo"] = коди
    після = ЗП.зібрати(О.ОЦІНКА, дані)
    п_т = json.dumps(після, ensure_ascii=False)
    print("==", "/".join(шлях.split("/")[-4:-2]), шлях.split("/")[-1][:9], "питання:", (дані.get("question") or {}).get("free_text"))
    print("  ДО   блокери", [б.get("code") for б in (до.get("check") or {}).get("blockers") or []],
          "знахідки", [з.get("rule") for з in (до.get("check") or {}).get("findings") or []],
          "not_in_photo" in json.dumps(до), "символів", len(json.dumps(до, ensure_ascii=False)))
    print("  ПІСЛЯ блокери", [б.get("code") for б in дані["check"].get("blockers") or []],
          "знахідки", [з.get("rule") for з in дані["check"].get("findings") or []], "not_in_photo", коди,
          "правило", О._НА_ФОТО[:40] in п_т, "символів", len(п_т))
