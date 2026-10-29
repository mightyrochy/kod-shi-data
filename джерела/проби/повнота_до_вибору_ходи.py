# -*- coding: utf-8 -*-
"""Н2 (рядки 5238, 5246): ремонт повноти ДО вибору — хід на блокер (`ДОПОВНЕННЯ_V1`), склад рахує код.
Друкує ФАКТ на мосту (`стенд_вх.json`, +5 °C): схема відповіді в промпті, `options` діри; дві відповіді того
самого прогону — ходами (по першій з `options`, дублю — перша річ групи, плюс вигаданий hex) і старою формою
(цілі образи, як писала модель ДО) — і блокери образів після злиття. Запуск із `джерела`:
  python3 проби/повнота_до_вибору_ходи.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B
вх = dict(json.load(open("стенд_вх.json")), сценарій=dict(нагода="побачення", місце="ресторан", година=19, темп_c=5),
          випадок="побачення, ресторан, 19:00", варіантів=10, ремонт_варіантів=5, мова_тексту="English", без_фото=1)
міст = lambda **д: json.loads(B.виклик("від_моделі", json.dumps(dict(вх, **д), ensure_ascii=False)))
пул = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["пакети"]["1"]["пул"]
н = lambda с, i: пул[с][i % len(пул[с])]["н"]
образи = [dict(ід="о1", підпис="a", речі=[н("верх", 1), н("взуття", 1), н("взуття", 2)]),
          dict(ід="о2", підпис="b", речі=[н("сукня", 2)]),
          dict(ід="о3", підпис="c", речі=[н("сукня", 3), н("взуття", 3), н("сумка", 3), н("сережки", 3), н("верхній_шар", 3)])]
в2 = міст(ітерація=2, текст_моделі=json.dumps(dict(версія="1", образи=образи), ensure_ascii=False))
п = json.loads(в2["промпт_повноти_до_вибору"])
бл = [б for о in п["verdict"] for б in о["structure"]["blockers"]]
print("відповідь:", п["task"]["answer"], "· скелет:", json.dumps(п["task"]["answer_schema"], ensure_ascii=False)[:90], "…")
print("блокерів %d · з options %d · з items %d · без обох %s" % (len(бл), sum(bool(б.get("options")) for б in бл),
      sum(bool(б.get("items")) for б in бл), [б["code"] for б in бл if not б.get("options") and not б.get("items")]))
ходи = [dict(blocker=б["id"], add=[б["options"][0]]) if б.get("options") else dict(blocker=б["id"], keep=б["items"][0])
        for б in бл if б.get("options") or б.get("items")] + [dict(blocker="b-o2-1", add=["#2d2326"])]
стара = dict(version="1", outfits=[dict(id="o1", items=образи[0]["речі"][:2],
             done=[dict(finding="Added %s" % next(б["options"][0] for б in бл if б.get("options")))])])
for як, відп in (("ходами", dict(version="1", fixes=ходи)), ("старою формою", стара)):
    вД = міст(ітерація=2, текст_моделі=json.dumps(відп, ensure_ascii=False), попередній_вердикт=в2["вердикт"],
              спроба_повноти=1, до_вибору=1)
    print("%-14s" % як, "; ".join("%s %d речей, блокерів %d" % (о["ід"], len(о["речі"]), len((о.get("структура") or {}).get("блокери") or []))
                                 for о in вД["вердикт"]["образи"]), "· неторканих", вД.get("неторканих_до_вибору"))
