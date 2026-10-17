# -*- coding: utf-8 -*-
# Рядок 3882: `a-line` у кроях слотів «верх» і «верхній_шар». Друкує для речей цих слотів зі словом a-line: причину
# `крої_слота`, крій у геометрії і слово на дроті моделі. ПІСЛЯ: причина cut_word_of_slot, у геометрії і на дроті a-line.
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, feed as Ф, outfit as O, пакет_моделі as П
вх = json.load(open("стенд_вх.json", encoding="utf-8")); вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
for c in B.каталог_останнього_пакета():
    if c.get("слот") in ("верх", "верхній_шар") and O._крій_слово(c) == "a-line":
        print("%-8s %-12s причина %-22s геометрія %-8s дріт %s" % (c["id"], c["слот"], O.крої_слота(c)[1], O.крій_речі(c), П._річ_пулу(c, {}).get("крій")))
