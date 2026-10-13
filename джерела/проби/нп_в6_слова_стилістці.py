# -*- coding: utf-8 -*-
"""НП-в6 крок 2: що стилістка (промпт складання руки 1) дістає про подію з розмови — подію її словами (`event`), решту
сказаного дослівно (`her_other_words`), пояснення мовної моделі (`language_model_note`, лише коли слова важко
тлумачити). `her_words` на шляху шару порожнє навмисно (показ `вхідМостаП`, 25.09). Хід шару → паспорт → `bridge`
«запити». Друкує поля `case`. Запуск із `джерела`: python3 проби/нп_в6_слова_стилістці.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, мовний_шар as МШ, стенд_знімок as СЗ
ХОДИ = [("на роботу в офіс, звичайний день", {"event": {"free_text": "робочий день в офісі", "lang": "uk"},
         "occasion": "work", "quotes": {"occasion": "на роботу"}}),
        ("йду на проводи до свекрухи, всі будуть",
         {"event": {"free_text": "проводи у свекрухи", "lang": "uk"}, "rest": {"free_text": "всі будуть", "lang": "uk"},
          "stylist_note": {"free_text": "«Проводи» here is the family remembrance meal at the in-laws' home on the "
                                        "Sunday after Easter, with a cemetery visit: modest and quiet.", "lang": "en"}})]
for слова, в in ХОДИ:
    п = МШ.паспорт_з_шару(в, {}, None, None, слова_ходу=слова)["паспорт"]
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сценарій=СЗ.СЦЕНАРІЇ["офіс·18°C"], випадок="",
              сід=3, паспорт=п)
    т = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["B"]
    case = json.JSONDecoder().raw_decode(т[т.index("{"):])[0].get("case") or {}
    print("«%s»\n   паспорт.пояснення_мови: %s" % (слова, п.get("пояснення_мови", "—")))
    for к in ("event", "her_words", "her_other_words", "language_model_note"):
        print("   case.%s: %s" % (к, json.dumps(case.get(к, "—"), ensure_ascii=False)[:160]))
    print("   визначення поля в task: %s" % ("language_model_note" in т.split('"pool"')[0] and "так" or "ні"))
