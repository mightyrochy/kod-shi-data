# -*- coding: utf-8 -*-
"""П-6: вузли дроту функціональної моделі, що несуть знахідку (`verdict[].findings`, `set.findings`,
`verdict[].structure.blockers` у промптах ремонту, вибору й повноти), — скільки з них везуть
`statements` (коди `внутрішня_мова.ЗАЯВИ`) і скільки ще прозу коду (`what`, ремонт текстом).
Живий шлях `bridge` на `стенд_вх.json`: два сіди × два сценарії × три образи. Нижче — місця в
коді, що народжують знахідку (`_зн(…)` чи `правило=` + `суть=`), і скільки з них уже несуть заяви.
Запуск із `джерела`: python3 проби/дріт_заяви_лічба.py"""
import ast, io, os, sys, json, random, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, стенд_знімок as СЗ
вх0, Л, без = json.load(open("стенд_вх.json", encoding="utf-8")), collections.Counter(), collections.Counter()
for сід in (3, 5):
    for назва in ("офіс·18°C", "дощ·ресторан·вечір"):
        вх = dict(вх0, сценарій=СЗ.СЦЕНАРІЇ[назва], випадок=назва)
        к, р = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["кандидати"], random.Random(сід)
        for _ in range(3):
            ід = [р.choice(к[с][:10])["id"] for с in к if к[с] and (с in ("верх", "низ", "взуття", "сумка") or р.random() < .5)]
            вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
            сирі = {z["ід"]: z.get("правило") for о in вм["вердикт"]["образи"] for z in о.get("знахідки") or []}
            for кл in ("промпт_ремонту", "промпт_лише_вибору", "промпт_повноти"):
                п = json.loads(вм.get(кл) or "{}")
                for о in п.get("verdict") or []:
                    for z in (о.get("findings") or []) + ((о.get("structure") or {}).get("blockers") or []):
                        Л["вузлів"] += 1; Л["із statements"] += bool(z.get("statements")); Л["what прозою"] += "what" in z
                        Л["ремонт кодами"] += isinstance(z.get("fix"), list); Л["ремонт прозою"] += isinstance(z.get("fix"), str)
                        if "what" in z: без[сирі.get(z["id"]) or z.get("code")] += 1
                for z in (п.get("set") or {}).get("findings") or []:
                    Л["вузлів"] += 1; Л["із statements"] += bool(z.get("statements")); Л["what прозою"] += "what" in z
print("ДРІТ:", " · ".join("%s %d" % кв for кв in Л.items()))
print("  прозою ще:", ", ".join("%s ×%d" % кв for кв in без.most_common()) or "нічого")
С = collections.Counter()
for ф in sorted(x for x in os.listdir(".") if x.endswith(".py") and not x.startswith(("audit", "батарея", "тест", "measure", "gate", "проба_"))):
    for в in ast.walk(ast.parse(io.open(ф, encoding="utf-8").read())):
        кл = {k.arg for k in getattr(в, "keywords", ())}
        if isinstance(в, ast.Call) and (getattr(в.func, "id", None) == "_зн" or {"правило", "суть"} <= кл):
            С["місць"] += 1; С["із заявами"] += bool(кл & {"заяви", "ремонт_заяви"})
print("КОД: місць народження знахідки %(місць)d · із заявами %(із заявами)d" % С)
