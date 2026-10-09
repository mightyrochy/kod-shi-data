# -*- coding: utf-8 -*-
"""Рядок 2882: скільки вузлів знахідок у дроті ремонту й вибору несуть ПРОЗУ коду (`what`), а скільки — заяви;
окремо K-COL-05 (сирота-акцент, matchy). Живий шлях `bridge` на каталозі руки 1: 4 сценарії × 12 сідів × 3 образи
(випадкові речі з перших 40 кандидатів слота). Запуск із `джерела`: python3 проби/дріт_сирота_2882.py"""
import os, sys, json, random, collections
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B, стенд_знімок as СЗ
вх0, Л, К5, проза = json.load(open("стенд_вх.json", encoding="utf-8")), collections.Counter(), collections.Counter(), collections.Counter()
for сід in range(1, 13):
    for назва in ("офіс·18°C", "дощ·ресторан·вечір", *[н for н in list(СЗ.СЦЕНАРІЇ)[:6] if н not in ("офіс·18°C", "дощ·ресторан·вечір")][:2]):
        вх = dict(вх0, сценарій=СЗ.СЦЕНАРІЇ[назва], випадок=назва)
        к, р = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["кандидати"], random.Random(сід)
        for _ in range(3):
            ід = [р.choice(к[с][:40])["id"] for с in к if к[с] and (с in ("верх", "низ", "взуття", "сумка") or р.random() < .5)]
            вм = json.loads(B.виклик("від_моделі", json.dumps(dict(вх, ід=ід), ensure_ascii=False)))
            for кл in ("промпт_ремонту", "промпт_лише_вибору"):
                п = json.loads(вм.get(кл) or "{}")
                for о in п.get("verdict") or []:
                    for z in (о.get("findings") or []) + ((о.get("structure") or {}).get("blockers") or []):
                        Л[кл, "вузлів"] += 1; Л[кл, "what прозою"] += "what" in z
                        if "what" in z: проза[z["what"][:60]] += 1
            for о in вм["вердикт"]["образи"]:
                for z in о.get("знахідки") or []:
                    if z.get("правило") == "K-COL-05": К5["K-COL-05 знахідок"] += 1; К5["із заявами"] += bool(z.get("заяви"))
for кв, в in sorted(Л.items()): print("%-22s %-12s %d" % (*кв, в))
print(dict(К5)); print("проза коду, топ:", проза.most_common(3))
