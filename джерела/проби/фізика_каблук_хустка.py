# -*- coding: utf-8 -*-
"""Рядки 1973 і 1976: невідоме стає значенням. Каталог руки 1 (пул «запити»).
1973 — пара зі смугою крамниці («від 4 до 6 см»: `каблук_від`, без `каблук_см`) з максі
не-об'ємного крою: скільки пар дають K-SIL-10 «максі без підйому» (смуга доводить ≥4 см).
1976 — хустка без `розмір_см`: скільки дістають `scarf_too_small_to_wrap_head` (розмір
невідомий → нуль) і скільки — заяву про невідомий формат. Запуск із `джерела`."""
import sys, json, pathlib
_К = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_К))
import feed as Ф, bridge as B, суд_силует as СС, аксесуари_структура as АС
вх = json.load(open(_К / "стенд_вх.json", encoding="utf-8"))
вх["каталог"] = Ф.каталог_на_диску("каталог_повний.xml"); вх["гілка"] = 0
json.loads(B.виклик("запити", json.dumps(вх, ensure_ascii=False)))
кат = B.каталог_останнього_пакета()
смуга = [c for c in кат if c.get("слот") == "взуття"
         and c.get("каблук_см") is None and c.get("каблук_від") is not None]
максі = next(c for c in кат if c.get("слот") == "низ" and c.get("тип") == "спідниця"
             and c.get("довжина_рівень") == "максі" and СС.крій_речі(c) not in СС.ОБ_ЄМНІ_КРОЇ_СПІДНИЦІ)
k10 = sum(any(з.get("правило") == "K-SIL-10" for з in СС.карта_спідниць([максі, п])) for п in смуга)
print("1973: пар зі смугою без числа %d (від ≥4 см: %d) · з максі дають K-SIL-10: %d"
      % (len(смуга), sum(п["каблук_від"] >= 4 for п in смуга), k10))
шарфи = [c for c in кат if c.get("слот") == "шарф"]
коди = lambda c: [з.get("code") for о in АС.команди_розкладки([c]) for з in о.get("опції_заяви") or []]
без = [c for c in шарфи if c.get("розмір_см") is None]
print("1976: шарфів %d, без розміру %d · без розміру з scarf_too_small_to_wrap_head %d, "
      "зі scarf_size_unknown %d · з розміром <90 см «замала» %d"
      % (len(шарфи), len(без), sum("scarf_too_small_to_wrap_head" in коди(c) for c in без),
         sum("scarf_size_unknown" in коди(c) for c in без),
         sum("scarf_too_small_to_wrap_head" in коди(c) for c in шарфи if (c.get("розмір_см") or 999) < 90)))
