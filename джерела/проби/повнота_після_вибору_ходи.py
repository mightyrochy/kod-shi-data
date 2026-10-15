# -*- coding: utf-8 -*-
"""Рядок 5826: ремонт повноти ПІСЛЯ вибору (`ПОВНОТА`) — хід на блокер (`ДОПОВНЕННЯ_V1`), склад рахує код, як Н2 до
вибору. Друкує ФАКТ на мосту (`стенд_вх.json`, +5 °C): схема відповіді промпта `промпт_повноти`, `options` діри; дві
відповіді на нього — ходами на блокери о1 (по першій з `options`, дублю — перша річ групи, плюс вигаданий hex) і старою
формою (цілий образ, додане лише в «done») — і що з них іде на картку (`повнота`). Запуск із `джерела`:
  python3 проби/повнота_після_вибору_ходи.py"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(sys.path[0])
import bridge as B
вх = dict(json.load(open("стенд_вх.json")), сценарій=dict(нагода="побачення", місце="ресторан", година=19, темп_c=5),
          випадок="побачення, ресторан, 19:00", варіантів=10, ремонт_варіантів=5, мова_тексту="English", без_фото=1)
міст = lambda **д: json.loads(B.виклик("від_моделі", json.dumps(dict(вх, **д), ensure_ascii=False)))
пул = json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))["пакети"]["1"]["пул"]
н = lambda с, i: пул[с][i % len(пул[с])]["н"]
образи = [dict(ід="о1", підпис="a", день="d1", речі=[н("верх", 1), н("взуття", 1), н("взуття", 2), н("сережки", 1)]),
          dict(ід="о2", підпис="b", речі=[н("сукня", 2)])]
в2 = міст(ітерація=2, текст_моделі=json.dumps(dict(версія="1", образи=образи), ensure_ascii=False))
п = json.loads(в2["промпт_повноти"])
бл = [б for о in п["verdict"] for б in о["structure"]["blockers"] if б["id"].startswith("b-o1")]
print("відповідь:", п["task"]["answer"], "· блокерів о1 %d · з options %d · з items %d" % (
      len(бл), sum(bool(б.get("options")) for б in бл), sum(bool(б.get("items")) for б in бл)))
пер = lambda б: (б.get("options") or [р["n"] for р in п.get("showcase") or []] or [None])[0]   # ДО `options` нема
ходи = [dict(blocker=б["id"], keep=б["items"][0]) if б.get("items") else dict(blocker=б["id"], add=[пер(б)]) for б in бл] + [dict(blocker=бл[-1]["id"], add=["#2d2326"])]
стара = dict(version="1", outfits=[dict(id="o1", items=образи[0]["речі"][:2], day="x",
                                        done=[dict(finding="Added %s" % пер(бл[1]))])])
for як, відп in (("ходами", dict(version="1", fixes=ходи)), ("старою формою", стара)):
    вП = міст(ітерація=2, текст_моделі=json.dumps(відп, ensure_ascii=False), попередній_вердикт=в2["вердикт"],
              спроба_повноти=2)
    о, пв = вП["вердикт"]["образи"], вП.get("повнота") or {}
    print("%-14s" % як, "; ".join("%s %d речей, блокерів %d" % (x["ід"], len(x["речі"]), len((x.get("структура") or {}).get("блокери") or []))
                                 for x in о), "· картка: повний=%s, речей %d (дібрав код %d), підпис=%s" % (
                                     пв.get("повний"), len(пв.get("ід") or []), len(пв.get("дібрані") or []), пв.get("підпис")))
