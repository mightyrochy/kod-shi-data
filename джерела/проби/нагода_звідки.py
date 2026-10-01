# -*- coding: utf-8 -*-
"""НГ-1: сила джерела виміру й «Інше» через `like`.

Друкує, чим стає вимір на чотирьох сходинках `ЗВІДКИ_СИЛА`, які працюють у НГ-1:
her_words (її слово чи плитка) → preset (вид) → like (найближчий вид для «Іншого») →
default (типове коду). Слабше джерело сильніше не перебиває, і незвична нагода не
потребує нового ключа: `вид=other` + `like` дає набір вимірів припущенням.
Запуск: cd джерела && python3 проби/нагода_звідки.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import паспорт_нагоди as ПН

СЦ = dict(нагода="церква", місце="церква_служба", година=11)
ВИПАДКИ = (
    ("плитка «церква»", {}, ("religious_place", "movement", "audience")),
    ("вона сказала «сидіти»", dict(рух="сидіти"), ("movement",)),
    ("«Інше», найближче весілля", dict(нагода=None, вид="other", like="wedding"), ("kind", "role", "reserved_colour")),
    ("«Інше» без найближчого", dict(нагода=None, вид="other"), ("kind", "role", "audience")),
    ("вінчання → банкет", dict(частини_дня=["church", "celebration"]), ("parts",)),
)
for ім, поверх, дивимось in ВИПАДКИ:
    п = dict(поверх)
    сц = dict(СЦ, **{k: v for k, v in поверх.items() if k == "нагода"})
    if поверх.get("нагода", "є") is None:
        сц.pop("нагода", None)
        п.pop("нагода", None)
    в, з = ПН.виміри_нагоди(п, сц)
    print("%-28s %s" % (ім, " · ".join("%s=%s (%s)" % (д, в[д], з[д]) for д in дивимось)))

п_плитка, _ = ПН.виміри_нагоди({}, СЦ)
п_слово, з_слово = ПН.виміри_нагоди(dict(рух="сидіти"), СЦ)
assert п_плитка["movement"] == "stand" and з_слово["movement"] == "her_words"
assert п_слово["movement"] == "sit", "її слово не перебило пресет виду"
в_л, з_л = ПН.виміри_нагоди(dict(вид="other", like="wedding"), dict(година=11))
assert в_л["kind"] == "other" and в_л["reserved_colour"] == "near_white" and з_л["role"] == "like"
в_б, з_б = ПН.виміри_нагоди(dict(вид="other"), dict(година=11))
assert в_б["role"] == "unknown" and з_б["role"] == "unknown", "«Інше» без like не вигадує ролі"
assert в_б["audience"] == "usual" and з_б["audience"] == "default", "типове коду не поставлено"
в_ч, _ = ПН.виміри_нагоди(dict(частини_дня=["church", "celebration"]), СЦ)
assert в_ч["parts"] == ["church", "celebration"], в_ч["parts"]
