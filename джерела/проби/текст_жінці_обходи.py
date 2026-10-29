# -*- coding: utf-8 -*-
"""Е2-текст-жінці: лічба ОБХОДІВ — місць показу, де жінці в екран іде виняток чи службове поле повз точку виходу.
Точка — `збійЖінціП` / `текстЖінціП` (`показ/мовний_шар.js`). Обхід = присвоєння в екран (`textContent`, `innerHTML`,
`placeholder`, `.title`, `createTextNode`), правий бік якого читає `String(e)`, `e.message`, `р.помилка`, `.причина`, `.чому`.
Запуск: python3 проби/текст_жінці_обходи.py [тека-джерел]; ДО — на теці з `origin/main` (git worktree); друкує факт."""
import os, re, sys
ТУТ = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВИХІД = re.compile(r"(?:\.textContent|\.innerHTML|\.placeholder|\.title)\s*\+?=(?!=)\s*(.*)|createTextNode\((.*)")
СЛУЖБОВЕ = re.compile(r"String\(\s*\(?\s*(?:e|err|помилка)\b|\b(?:e|err)\.message|\bр\.помилка\b|\.(?:причина|чому|діагноз)\b(?!\s*\?)")
обходи = []
тека = os.path.join(ТУТ, "показ")
for ф in sorted(os.listdir(тека)):
    if not ф.endswith(".js") or ф == "мовний_шар.js":     # точка виходу живе в мовний_шар.js
        continue
    for н, р in enumerate(open(os.path.join(тека, ф), encoding="utf8"), 1):
        м = ВИХІД.search(р)
        if м and СЛУЖБОВЕ.search(м.group(1) or м.group(2) or "") and "збійЖінціП" not in р and "текстЖінціП" not in р:
            обходи.append("%s:%d" % (ф, н))
print("обходів поза точкою виходу:", len(обходи))
for о in обходи:
    print(" ", о)
