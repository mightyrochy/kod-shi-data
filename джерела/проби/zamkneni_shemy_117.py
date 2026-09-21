# -*- coding: utf-8 -*-
"""Рядок 117: чи бачить жінка схеми, яких цей вихід НЕ пропонує. Профіль стенда
(`стенд_вх.json`), чотири наміри: скільки схем пропонується, скільки замкнено, їхні імена й
перший рядок причини. Звіряє: (а) «пропоновані + замкнені» однакове в усіх чотирьох намірах —
жодна схема не зникає безслідно; (б) під statement замкнених нема; (в) причина не порожня в
жодної замкненої. До (origin/main): поля `замкнені` не було, на екран їхало 4 плитки й жодного
слова про решту. Запуск із теки `джерела`: `python3 проби/zamkneni_shemy_117.py`."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B
вх = json.load(open("стенд_вх.json", encoding="utf-8"))
НАМІРИ = ("conventional", "comfort_first", "context_optimal", "statement")
суми, під_statement, без_причини = set(), None, []
for намір in НАМІРИ:
    r = json.loads(B.палітри(json.dumps(dict(вх, намір=намір), ensure_ascii=False)))
    проп, зам = r["гілки"], r.get("замкнені") or []
    суми.add(len(проп) + len(зам))
    if намір == "statement":
        під_statement = len(зам)
    print("%-16s пропонується %d: %s" % (намір, len(проп), ", ".join(г["схема"] for г in проп)))
    print("%-16s замкнено    %d: %s" % ("", len(зам), ", ".join(з["схема"] for з in зам) or "—"))
    for з in зам:
        рядок = ((з.get("чому") or "") + " " + (з.get("відкриває") or "")).strip()
        if not рядок:
            без_причини.append((намір, з["схема"]))
        print("      %-18s %s" % (з["схема"], рядок.split(". ")[0] + "."))
print("ПІДСУМОК: «пропоновані + замкнені» = %s (однакове в усіх %d намірах: %s) · "
      "замкнених під statement %d · замкнених без причини %d"
      % (sorted(суми), len(НАМІРИ), "так" if len(суми) == 1 else "НІ", під_statement, len(без_причини)))
assert len(суми) == 1, "схема зникає безслідно: сум %s" % sorted(суми)
assert під_statement == 0, "під statement замкнених бути не може: %d" % під_statement
assert not без_причини, "замкнена без причини: %s" % без_причини
print("ВСІ ТРИ ЗВІРКИ ПРОЙДЕНО")
