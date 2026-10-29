# -*- coding: utf-8 -*-
"""Рядок 6756: шаблон промпта вибору ДО/ПІСЛЯ — ключ `"answer"` у «task» (скелет не наприкінці → наприкінці).
Запуск: cd джерела && python3 проби/вибір_без_answer_6756.py"""
import dataclasses, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import дріт_факти as Ф, дріт_моделі as Д, збирач_промптів as ЗП, повнота_образу as ПО
ДО = dataclasses.replace(ПО.ВИБІР, скелет_наприкінці=False, наприкінці="")
рахунок = [0, 0, 0]
for ім, п in Ф.сирі("*ВЕРДИКТ_V1_ВИБІР_V1*"):
    д = Д.вердикт(Ф.з_осями(Ф.дріт_вердикта(json.loads(п))), ремонти=False)
    для = [json.dumps(ЗП.зібрати(о, д, мова_тексту="English"), ensure_ascii=False).count('"answer"') for о in (ДО, ПО.ВИБІР)]
    рахунок[0] += 1; рахунок[1] += для[0]; рахунок[2] += для[1]
print('шаблонів %d · "answer" у промптах ДО %d → ПІСЛЯ %d' % tuple(рахунок))
