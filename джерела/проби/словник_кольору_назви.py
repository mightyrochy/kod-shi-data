# -*- coding: utf-8 -*-
"""2.11, рядок 6671: одна назва — один код. Відповіді 3-го кола пілота 5190 (97 рядків, `попередні_спроби`, у git)
проти `словник_кольору`: назви, чий код закріплено, а відповідь дала інший, і назви без закріпленого коду з різними кодами.
Запуск: cd джерела && python3 -W ignore проби/словник_кольору_назви.py [етап: round3_c70011d9]"""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ)
import словник_кольору as СК
ТЕКА = os.path.join(ТУТ, "прилади", "рядки_5190"); етап = sys.argv[1] if len(sys.argv) > 1 else "round3_c70011d9"
пари, рядків = [], 0
for з in json.load(open(os.path.join(ТЕКА, "попередні_спроби.json"), encoding="utf-8"))["records"]:
    if з["stage"] != етап:
        continue
    відповідь = json.load(open(os.path.join(ТЕКА, "попередні_спроби", os.path.basename(з["file"])), encoding="utf-8"))
    for р in json.loads(відповідь["response"]["choices"][0]["message"]["content"])["rows"]:
        рядків += 1
        пари += [(к["quote"], к["code"]) for г in р.get("variants", []) for к in г["colors"]]
інший, вільні = СК.розбіжності_назв(пари)
print("ФАКТ · етап %s, рядків %d, пар назва→код %d, словник %s" % (етап, рядків, len(пари), СК.ВЕРСІЯ))
print("ФАКТ · закріплена назва, інший код (рядків-пар %d): %s" % (
    sum(1 for н, к in пари if СК.код_назви(н) and СК.код_назви(н) != к), {н: sorted(к) for н, к in інший.items()}))
print("ФАКТ · назва без закріпленого коду, різні коди (рішення власника): %s" % {н: sorted(к) for н, к in вільні.items()})
