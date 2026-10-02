# -*- coding: utf-8 -*-
"""ПРОЗА-1 (рядки 970, 925, 976): кожен запис шару «out» / «out_messages» із сирою відповіддю моделі у файлі вердиктів стенда —
що з неї читає суворий розбір (`протокол.розбір`, ДО) і що читає `мовний_шар.прийняти` тепер (ПІСЛЯ).
ДРУКУЄ на запис: де, скільки JSON-об'єктів з початку рядка, ДО — причина або «ok», ПІСЛЯ — текстів
прочитано з M, нотатки, і чи є в тексті «Wait»/«correct» між об'єктами (самовиправлення моделі).
ЗАПУСК (тека `джерела`): python3 проби/проза1_шар.py <вердикти.txt[.gz]>…"""
import gzip, json, os, re, sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import мовний_шар as МШ, протокол as ПР


def записи(в):
    if isinstance(в, dict):
        if в.get("напрям") in ("out", "out_messages") and isinstance(в.get("вхід"), dict) and в.get("відповідь_моделі"):
            yield в
        for х in в.values():
            yield from записи(х)
    elif isinstance(в, list):
        for х in в:
            yield from записи(х)


for шлях in sys.argv[1:]:
    сир = (gzip.open if шлях.endswith(".gz") else open)(шлях, "rt", encoding="utf-8").read()
    print("==", шлях)
    бачені = set()
    for з in записи(json.loads(сир)):
        в = з["відповідь_моделі"]
        if (з.get("де"), в) in бачені:
            continue
        бачені.add((з.get("де"), в))
        об, чому = ПР.розбір(в)
        пов = з["напрям"] == "out_messages"
        розм = (МШ.розмітити_повідомлення if пов else МШ.розмітити)(з["вхід"])
        п = (МШ.прийняти_повідомлення if пов else МШ.прийняти)(розм, в)
        print("  %-22s об'єктів %d · ДО %-42s · ПІСЛЯ прочитано %d/%d %s · самовиправлення %s" % (
            з.get("де"), len(МШ._ПОЧАТОК_ОБʼЄКТА.findall(в)), "ok" if об else (чому or "")[:42],
            len(розм) - len(п["без_відповіді"]), len(розм), ",".join(п["нотатки"]) or "-",
            "так" if re.search(r"(?i)\bwait\b|\bcorrect", re.sub(r'"(?:[^"\\]|\\.)*"', "", в)) else "ні"))
