# -*- coding: utf-8 -*-
"""КВ-1 (прототип картки вердикту, 28.09): чи дають СЛОВА в полі вердикту те саме, що ДОТИКИ.
Друкує для кожного дотику картки (вісь «Вдягнеш?», вісь «твоє?», аспект зі знаком, річ) —
поле `verdict_comment`, у яке мовна модель кладе те саме з її слів, і чого дотик не скаже
зовсім (напрям, що замість). Далі — розбір трьох відповідей перекладачки швом `прийняти_вхід`
(коди поза переліком не проходять) і рядок промпта з контекстом дотиків.
Запуск: cd джерела && python3 проби/кв1_слова_як_дотики.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import внутрішня_мова as ВМ, мовний_шар as М
ПОЛЯ = ВМ.КОМЕНТАР_ВЕРДИКТУ
ДОТИКИ = {"Вдягнеш? (3 чипи)": "wear", "Це саме твоє? (3 чипи)": "mine", "аспект мінус (8 чипів)": "reasons",
          "аспект плюс (8 чипів)": "good", "«не ця» на речі": "about_items"}
def коди(с):
    с = с.get("items", с)
    return [к for к in с.get("enum", с.get("properties", [])) if к != ВМ.UNKNOWN]
for дотик, поле in ДОТИКИ.items():
    print("%-24s → %-12s %s" % (дотик, поле, ("є · коди: " + ", ".join(коди(ПОЛЯ[поле]))) if поле in ПОЛЯ else "НЕМА"))
print("лише зі слів (дотиком не сказати):", ", ".join(п for п in ПОЛЯ if п not in ДОТИКИ.values()))
ЧИПИ = {"colour", "cut", "combination", "style", "occasion", "weather", "comfort", "price"}
print("аспекти лише зі слів (чипа нема):", ", ".join(sorted(set(коди(ПОЛЯ["reasons"])) - ЧИПИ)))
ВІДПОВІДІ = [
    {"wear": "no", "mine": "pretty", "reasons": ["cut", "on_me"], "shift": {"attention": "less"},
     "about_items": [{"id": "ж-1", "opinion": "dislike", "reasons": ["cut"]}]},
    {"wear": "as_is", "mine": "mine", "good": ["colour", "combination"], "about_items": [{"id": "ж-2", "opinion": "like"}]},
    {"wear": "maybe", "reasons": ["color_not_mine"], "shift": {"formality": "down"}, "about_items": [{"id": "м-9"}]}]
for в in ВІДПОВІДІ:
    р = М.прийняти_вхід("verdict_comment", json.dumps(в), ід_речей={"ж-1", "ж-2"})
    print("розбір:", json.dumps(р["внутрішня"], ensure_ascii=False), "· незнайомі:", р["незнайомі"])
п = М.промпт_входу("verdict_comment", "слова", {"tapped": {"wear": "no", "question": "no.pretty"}})
print("у промпті контекст дотиків:", "КОНТЕКСТ.tapped" in п, "· межа «з натиснутого не переписуй»:", "не переписуй" in п)
