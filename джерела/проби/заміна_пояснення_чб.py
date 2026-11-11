# -*- coding: utf-8 -*-
"""Суд від моделі не пропонує заміни без суду образу: ДО/ПІСЛЯ на метал K-CRA-07 і принти K-COL-10.

Запуск: python проби/заміна_пояснення_чб.py [SHA бази]; каталог не потрібен."""
import importlib, pathlib, subprocess, sys, types
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
БАЗА = sys.argv[1] if len(sys.argv) > 1 else "8f2627cdfd7dd70d7fa3f933e53cdeef0172fb26"
РЕЧІ = [dict(id="а", слот="сережки", назва="срібні сережки"), dict(id="б", слот="верх", назва="квітковий топ"),
        dict(id="в", слот="низ", назва="спідниця в клітинку")]
def знахідки(модуль):
    return [з for з in модуль.доповнення_судді(РЕЧІ, None, dict(метал="золото"))
            if з.get("правило") in ("K-CRA-07", "K-COL-10")]
if __name__ == "__main__":
    до = types.ModuleType("суд_до")
    exec(subprocess.check_output(["git", "show", БАЗА + ":джерела/суд_від_моделі.py"]).decode("utf-8"), до.__dict__)
    було, стало = знахідки(до), знахідки(importlib.import_module("суд_від_моделі"))
    assert {з["правило"] for з in стало} == {з["правило"] for з in було} == {"K-CRA-07", "K-COL-10"}, (було, стало)
    assert all(з.get("ремонт_заяви") for з in було) and not any(з.get("ремонт_заяви") for з in стало)
    assert all("зв'язати" not in з["суть"] for з in стало)
    print("ДО: ремонт_заяви у %d знахідок; ПІСЛЯ: 0; правила й учасники ті самі" % len(було))
