# -*- coding: utf-8 -*-
"""Одна назва сім'ї схеми для моделі: бриф і `case` = суд (рядок 1500).

ж3 театр, тріада: ДО бриф/`case.palette_scheme.families` — «petrol, rose, mustard» (`слово_сім_ї`), а
`scheme_families_missing_on_big_items.missing` — слова речей добору («бірюза, бордовий, оливковий»).
ПІСЛЯ обидва — `палітра_схеми.код_сім_ї`. Запуск із `джерела`."""
import sys, pathlib, json
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import bridge as B, palette as P, суд_від_моделі as СВ

вх = json.load(open(pathlib.Path(__file__).resolve().parent.parent / "стенд_вх.json", encoding="utf-8"))
вх.update(шкіра="#f0d6d2", волосся=["#1f1c1f", "#2a2326"], очі="#5b6e82", гілка=0, схема="тріада",
          схему_обрала_вона=True, сценарій=dict(вх["сценарій"], нагода="театр"))
r = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
спец, _ = B.спец_останнього_пакета()
сім = спец.get("сім_ї_схеми") or []
assert len(сім) >= 2, "тріада без сімей: %r" % спец.get("схема")
бриф = [P.код_сім_ї(с) for с in сім]
кат = B.каталог_останнього_пакета()
пул = {с: (r["кандидати"].get(с) or []) for с in P.ВЕЛИКІ_ПОВЕРХНІ}
сірі = [{"id": "v", "слот": "верх", "lab": list(СВ._lab_з(80, 2, 90))}, {"id": "n", "слот": "низ", "lab": list(СВ._lab_з(25, 2, 90))}]
зн = P.обіцянка_великих(сірі, {"_сім_ї": сім, "_поверхні": "великі", "_схема": "тріада"},
                         {c["id"]: c for c in кат}, кандидати=пул)
з = next(x for f in зн for x in f.get("заяви") or [] if x["code"] == "scheme_families_missing_on_big_items")
до = list(P.слова_сімей(сім, P.площі_схеми(сірі, сім, None, None), None, None,
                        {с["роль"]: P.слова_у_речах([x for xs in пул.values() for x in xs], с, {c["id"]: c for c in кат}) for с in сім}).values())
print("бриф/case:", бриф, "· суд missing ПІСЛЯ:", з["values"]["missing"], "· ДО (слова добору):", до)
assert з["values"]["missing"] == бриф, (з["values"]["missing"], бриф)
