# -*- coding: utf-8 -*-
"""Е2-втрата-слова, акцент у прикрасах: `why_her_metal` при `case.jewelry` не знімається звіркою; `accent_place` стилістки
доходить до ноти заявою `stylist_accent_place`. Друкує факт. Запуск: cd джерела && python3 -W ignore проби/е2_акцент_прикраси.py"""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import вибір_палітри as ВП
Т = dict(зріст=168, обхвати={"плечі": 98, "груди": 92, "талія": 74, "стегна": 99}, шкіра="#e8c4ad", волосся=["#2b1d16"], очі="#5a3a22")
for ім, прикраси, місце in (("срібло+jewellery", "срібло", "jewellery"), ("без прикрас", "без прикрас", "jewellery"), ("перли", "перли", "jewellery"), ("без прикрас+none", None, "none"), ("поза переліком", "срібло", "ears")):
    паспорт = dict(подія="співбесіда в банку", нагода="співбесіда", **({"прикраси": прикраси} if прикраси else {}))
    d = dict(Т, паспорт=паспорт); пер = ВП.перелік(d)
    відп = json.dumps(dict(scheme=пер["схеми"][0]["код"], scheme_reasons=["why_her_metal"], base=пер["основи"][0]["id"],
                           base_reasons=["why_her_metal"], saturation="muted", accent_place=місце))
    р = ВП.прийняти(d, відп); п = р["повідомлення"] or {}
    ід = [з["code"] for з in p["statements"]] if (p := п) else []
    print("%s · jewelry=%s · причини=%s · відхилено=%s · місце_акценту=%s · заява=%s" % (
        ім, пер["випадок"].get("jewelry"), р["вибір"]["причини"], [x[:48] for x in р["відхилено"]], р["вибір"]["місце_акценту"],
        "stylist_accent_place" in ід))
