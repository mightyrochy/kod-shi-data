# -*- coding: utf-8 -*-
"""Рядок 8115 (ЖИВІ-27 С22, С26, `claude/zhyvi-27:аудит/живі_27/…/VIDPOVIDI/seed3_01`, `seed3_02`): replay першої відповіді
ходу й повтору за `unknown_key` без моделі. ДО — показ брав повтор цілим; ПІСЛЯ — `злити_повтор`. Друкує поля паспорта
й уривки. Запуск: cd джерела && python3 проби/паспорт_повтор_8115.py"""
import os, sys, json
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import мовний_шар as М
q = lambda т, з: {"quote": т, "value": з}
С = {"С22": ("Йду ввечері в клуб, але не хочу привертати уваги — хочу приховати живіт",
             {"occasion": q("ввечері в клуб", "club"), "goal_zones": q("приховати живіт", ["belly"]), "conceal": True,
              "formality": {"from": 6, "to": 8}, "open_zones": "one", "part_of_day": "evening"},
             {"occasion": q("ввечері в клуб", "club"), "goal": q("не хочу привертати уваги", ["conceal"]),
              "goal_zones": q("приховати живіт", ["belly"])}),
     "С26": ("На роботу пішки, увесь день дощ, взуття — замшеві чоботи",
             {"occasion": q("на роботу", "work"), "movement": q("пішки", "walk"), "weather_feel": q("дощ", "rain"),
              "shoes": q("замшеві чоботи", "over_knee_boots")},
             {"occasion": q("на роботу", "work"), "place": q("пішки", "walk"), "movement": q("дощ, увесь день пішки", "walk_a_lot"),
              "weather_feel": q("увесь день дощ", "rain"), "occasion_part": q("на роботу", "other"),
              "formality": {"from": 4, "to": 6}, "open_zones": q("", "one")})}
ПОЛЯ = ("нагода", "пора", "рух", "опади", "мета", "мета_зони", "ошатність", "відкриті_зони")
for сц, (слова, у1, у2) in С.items():
    в = lambda у: json.dumps({"update": у, "need": "none", "text": [{"about": list(у), "says": "Записала."}]}, ensure_ascii=False)
    р1, р2 = М.прийняти_розмову(в(у1)), М.прийняти_розмову(в(у2))
    print(сц, "повтор першої:", р1.get("повтор"))
    for назва, р in (("ДО", р2), ("ПІСЛЯ", М.злити_повтор(р1, р2))):
        п = М.паспорт_з_шару(р["внутрішня"], {"типові_поля": ["година", "темп_c"], "година": 11, "темп_c": 18},
                             слова_ходу=[слова])["паспорт"]
        print("  %-5s" % назва, " · ".join("%s=%s" % (к, json.dumps(п.get(к), ensure_ascii=False)) for к in ПОЛЯ),
              "· уривки:", ",".join(sorted((р["внутрішня"].get("quotes") or {}))), "· дописав:", р.get("повтор_дописав", "—"))
