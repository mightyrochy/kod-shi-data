# -*- coding: utf-8 -*-
"""Правило схеми називає види, де колір у пулі Є (рядок 1291).

ж3 (холодна, «нейтрали+акцент», основа петроль #2c5158): ДО `colour_kinds` будувався зі спеки
й першим називав взуття — носіїв тону там 0. ПІСЛЯ — ті самі види, що в ноті
`scheme_colour_lies_in_kinds` (де носії справді лежать). Запуск із `джерела`."""
import sys, pathlib, json, re
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import bridge as B, колір_річ as КР

вх = json.load(open(pathlib.Path(__file__).resolve().parent.parent / "стенд_вх.json", encoding="utf-8"))
вх.update(шкіра="#f0d6d2", волосся=["#1f1c1f", "#2a2326"], очі="#5b6e82", гілка=0, схема="нейтрали+акцент",
          вибір_кольору={"база_hex": "#2c5158", "база_тип": "колір"})
r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
спец, _ = B.спец_останнього_пакета()
кат = {c["id"]: c for c in B.каталог_останнього_пакета()}
несуть = {}
for с, v in спец["слоти"].items():
    if isinstance(v, dict) and v.get("роль") == "акцент" and v.get("дуга_тону"):
        n = sum(1 for x in (r["кандидати"].get(с) or []) if КР.несе_тон(кат.get(x["id"]) or x, v["дуга_тону"]))
        if n: несуть[с] = n
м = re.search(r'colour_kinds\\*"\s*:\s*\[([^\]]*)\]', json.dumps(r, ensure_ascii=False))
види = re.findall(r'(\w+)', м.group(1)) if м else []
print("носії тону в пулі:", несуть, "· colour_kinds у промпті:", види)
import внутрішня_мова as ВМ
assert види and all(ВМ.ТАБЛИЦЯ["slot"].get(к) in несуть for к in види), (види, несуть)
