# -*- coding: utf-8 -*-
"""Рядок 1449: «її слова → коди». Друкує розмір промпта уточнення до оцінки (вид `scenario` доти, `question` тепер),
нотатки розробника й мертві поля в промпті сценарію, тип речі з внутрішнім словом («жакет» ≠ jacket) і що лишає
шов із записаної відповіді перекладача, яка зробила з питання бажання (14 з 31 у розборі 02.10).
Запуск: cd джерела && python3 проби/питання_не_бажання_1449.py"""
import json, os, re, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import мовний_шар as М
П = "А якщо з чорними ботильйонами?"
for вид in ("scenario", "question"):
    print("промпт %-9s: %5d знаків" % (вид, len(М.промпт_входу(вид, П))))
сц = М.промпт_входу("scenario", П)
print("нотатки розробника (НП-в, `модуль.ІМ'Я`):", len(re.findall(r"НП-в|`[^`]*\.[А-ЯҐЄІЇ_]{3,}`", сц)),
      "· мертві поля kind/like/event_formality:", len(re.findall(r"\b(kind|like|event_formality)\b", сц)))
print("тип речі:", ", ".join(x for x in re.findall(r"\b(?:blazer|jacket|coat|cardigan) \([^)]*\)", сц)[:4]))
print("правило wants:", [р for р in сц.split("\n") if р.startswith("- wants")][0])
ЗАПИС = {"question": П, "question_about": "look",   # записана відповідь: питання стало ще й бажанням
         "wants": [{"quote": "з чорними ботильйонами", "item_type": "ankle_boots", "color_name": "black"}]}
for вид in ("scenario", "question"):
    р = М.прийняти_вхід(вид, json.dumps(ЗАПИС, ensure_ascii=False))
    print("шов %-9s: поля %s · відкинуто %s" % (вид, sorted(р["внутрішня"]), р["незнайомі"]))
