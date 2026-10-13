# -*- coding: utf-8 -*-
"""М-2, вада 1: ЦИТАТА ПОРУЧ ІЗ ПОЛЕМ. Перекладач пише поле з кодом чи числом парою {quote, value}
(уривок її слів — поруч із кодом, а не окремим `quotes` наприкінці, якого мала модель не писала);
шов (`прийняти_вхід`) розгортає пару в ту саму внутрішню мову, що доти, і сторож звіряє той самий
уривок. Друкує: чи просить промпт окреме поле quotes; для двох реплік — чи пара й давній запис
того самого змісту дають одну внутрішню мову, і паспорт із пари (нагода, місце, дрес-код, межі,
обов'язкове «куди йдеш», відкинуте сторожем). Та сама проба на main і на гілці.
Запуск із `джерела`: python3 проби/шлях_шар_пара.py"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import мовний_шар as МШ

п = МШ.промпт_входу("scenario", "слова")
print("промпт просить окреме поле quotes: %s · поле парою quote + value: %s"
      % ("\n- quotes —" in п, "quote" in п and "value" in п))
річ = lambda ц, н, с: {"quote": ц, "name": н, "status": "has", "slot": с}
ХОДИ = [("Збери образ під цю спідницю і чоботи для походу на концерт",
         {"place": {"quote": "для походу на концерт", "value": "theatre"}, "event": "похід на концерт",
          "own_items": [річ("цю спідницю", "спідниця", "bottom"), річ("чоботи", "чоботи", "shoes")]},
         {"place": "theatre", "event": {"free_text": "похід на концерт", "lang": "uk"},
          "own_items": [dict(річ("цю спідницю", "спідниця", "bottom"), name={"free_text": "спідниця", "lang": "uk"}),
                        dict(річ("чоботи", "чоботи", "shoes"), name={"free_text": "чоботи", "lang": "uk"})],
          "quotes": {"place": "для походу на концерт"}}),
        ("робочий день в офісі, дрес-код business casual, без підборів",
         {"occasion": {"quote": "робочий день", "value": "work"}, "place": {"quote": "в офісі", "value": "office_corporate"},
          "dress_code": {"quote": "дрес-код business casual", "code": "business_casual"},
          "vetoes": [{"quote": "без підборів", "feature": "heels"}], "hour": {"quote": "unknown", "value": 9}},
         {"occasion": "work", "place": "office_corporate", "dress_code": "business_casual", "hour": 9,
          "vetoes": [{"feature": "heels", "quote": "без підборів"}],
          "quotes": {"occasion": "робочий день", "place": "в офісі", "dress_code": "дрес-код business casual"}})]
for слова, пара, давній in ХОДИ:
    вн = МШ.прийняти_вхід("scenario", json.dumps(пара))["внутрішня"]
    р = МШ.паспорт_з_шару(вн, {}, None, None, слова_ходу=слова)
    пс = р["паспорт"]
    print("«%s»\n   пара = давній запис: %s · нагода=%s місце=%s дрес-код=%s межі=%s · обовʼязкове=%s · відкинув сторож: %s"
          % (слова[:48], вн == МШ.прийняти_вхід("scenario", json.dumps(давній))["внутрішня"], пс.get("нагода"), пс.get("місце"),
             пс.get("дрес_код"), (пс.get("вето") or {}).get("типи"), р["обовʼязкове"],
             [в.split(" · ")[2] for в in р["вигадки"]] or "—"))
