# -*- coding: utf-8 -*-
"""Проба переносу реєстру: множина пар «модуль → новий_модуль::ім'я» у рядковому
`поділ_очікувані.txt` — ТА САМА, що в json-реєстрі до переносу (`поділ_очікувані.json`
у БАЗА-коміті). Друкує лічбу до/після і будь-яку різницю поіменно; rc 1 — є різниця.
Запуск: cd джерела && python3 проби/поділ_реєстр_перенос.py [БАЗОВИЙ_КОМІТ]"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from поділ_спільне import очікувані, РЕЄСТР
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "de0d834"
було_текст = subprocess.run(["git", "show", "%s:джерела/проби/поділ_очікувані.json" % БАЗА],
                            capture_output=True, text=True, check=True).stdout
було_json = json.loads(було_текст)
було = {(бак, ключ) for бак, пари in було_json.items() if бак != "_опис" for ключ in пари}
баки = sorted(бак for бак in було_json if бак != "_опис")
стало = {(бак, ключ) for бак in баки for ключ in очікувані(бак)}
рядків = sum(1 for р in open(РЕЄСТР, encoding="utf-8")
             if р.strip() and not р.lstrip().startswith("#"))
зникли, зайві = sorted(було - стало), sorted(стало - було)
print("реєстр@%s: %d пар у %d модулях · рядковий реєстр: %d записів (рядків: %d) · "
      "зникло: %d · зайвих: %d" % (БАЗА, len(було), len(баки), len(стало), рядків,
                                   len(зникли), len(зайві)))
for х in (зникли, зайві):
    if х: print("  ", х)
sys.exit(1 if (зникли or зайві) else 0)
