# -*- coding: utf-8 -*-
"""Е2-текст-жінці: лічба ОБХОДІВ — текст моделі, винятку чи службового поля, що йде в екран повз точку виходу
(`збійЖінціП` / `текстЖінціП`, `показ/мовний_шар.js`). Екран = `textContent`, `innerHTML`, `placeholder`, `.title`,
`createTextNode`. Джерело = `String(e)`, `e.message`, `.помилка`, `.тексти`, `.причина`, `.чому`, `.діагноз`, текст репліки
(`р.текст`, `ш.текст`) і змінні, у які воно потрапило в тому ж файлі (потік значення: присвоєння, `+=`, `.push`, одна ітерація).
Запуск: python3 проби/текст_жінці_обходи.py [тека-джерел]; ДО — на теці з `origin/main` (git worktree); друкує факт."""
import os, re, sys
ТУТ = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ВИХІД = re.compile(r"(?:\.textContent|\.innerHTML|\.placeholder|\.title)\s*\+?=(?!=)\s*(.*)|createTextNode\((.*)")
ДЖЕРЕЛО = (r"String\(\s*\(?\s*(?:e|err|помилка)\b|\b(?:e|err)\.message|\.помилка\b|\.тексти\b|\bр\.текст\b"
           r"|\.(?:причина|чому|діагноз)\b(?!\s*\?)")
ПРИСВОЄННЯ = re.compile(r"(?:^|[\s;{(,])(?:let |const |var )?([^\W\d]\w*)\s*(?:\+?=(?!=)|:(?!:))\s*(.*)")
тека = os.path.join(ТУТ, "показ")
обходи = []
for ф in sorted(os.listdir(тека)):
    if not ф.endswith(".js") or ф == "мовний_шар.js":     # точка виходу живе в мовний_шар.js
        continue
    код = re.sub(r"/\*.*?\*/", lambda м: "\n" * м.group(0).count("\n"), open(os.path.join(тека, ф), encoding="utf8").read(), flags=re.S)
    сирі, рядки, початки = re.sub(r"(?m)(^|\s)//.*$", "", код).split("\n"), [], []     # коментарі не код
    for н, р in enumerate(сирі, 1):     # оператор на кілька рядків — один рядок (до `;`, `{` чи `}`)
        if рядки and not re.search(r"[;{}]\s*(?://.*|/\*.*\*/)?$", рядки[-1]):
            рядки[-1] += " " + р.strip()
        else:
            рядки.append(р); початки.append(н)
    забруднені = set()
    for _ in range(2):
        шаблон = re.compile(ДЖЕРЕЛО + ("|\\b(?:%s)\\b" % "|".join(map(re.escape, забруднені)) if забруднені else ""))
        for р in рядки:
            if "збійЖінціП" in р or "текстЖінціП" in р:
                continue
            for м in ПРИСВОЄННЯ.finditer(р):
                if шаблон.search(м.group(2)) and not ВИХІД.search(р):
                    if len(м.group(1)) > 2:
                        забруднені.add(м.group(1))
    шаблон = re.compile(ДЖЕРЕЛО + ("|\\b(?:%s)\\b" % "|".join(map(re.escape, забруднені)) if забруднені else ""))
    for н, р in enumerate(рядки, 1):
        м = ВИХІД.search(р)
        if м and шаблон.search(м.group(1) or м.group(2) or "") and "збійЖінціП" not in р and "текстЖінціП" not in р:
            обходи.append("%s:%d" % (ф, початки[н - 1]))
print("обходів поза точкою виходу:", len(обходи))
for о in обходи:
    print(" ", о)
