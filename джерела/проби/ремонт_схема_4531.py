# -*- coding: utf-8 -*-
"""4531: схема остання у фактичному промпті `bridge.від_моделі` (за нею — лише рядок кінця, 5239); без моделі.
Запуск: cd джерела && python3 проби/ремонт_схема_4531.py [тека сирих промптів]."""
import json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import bridge as Б, feed as Ф
вх = dict(json.loads(Path("стенд_вх.json").read_text()), каталог=Ф.каталог_на_диску("каталог_brief.xml"),
          варіантів=1, ремонт_варіантів=1, без_фото=1)
вик = lambda дія, **д: json.loads(Б.виклик(дія, json.dumps(dict(вх, **д), ensure_ascii=False)))
пул = вик("запити")["пакети"]["1"]["пул"]
речі = [пул[с][0]["н"] for с in ("верх", "низ", "взуття", "сумка")]
for ім, склад in (("повний", речі), ("без_взуття", речі[:2] + речі[3:])):
    відповідь = dict(версія="1", образи=[dict(ід="о1", речі=склад)])
    в = вик("від_моделі", текст_моделі=json.dumps(відповідь, ensure_ascii=False))
    т = в["промпт_ремонту"]; п = json.loads(т)
    с = п.get("answer_schema", п["task"].get("answer_schema"))
    if len(sys.argv) > 1:
        тека = Path(sys.argv[1]); тека.mkdir(parents=True, exist_ok=True)
        (тека / (ім + ".json")).write_text(т, encoding="utf-8")
    поч = т.index(json.dumps(с, ensure_ascii=False, separators=(",", ":")))
    кінець = json.JSONDecoder().raw_decode(т, поч)[1]
    хвіст = т[кінець:]; гейти = sum(len(о.get("gates") or []) for о in п["verdict"])
    print("%s: гейтів %d, схема %s, за схемою %r, input %s, statement_codes %s" %
          (ім, гейти, "корінь" if "answer_schema" in п else "task", хвіст[:40],
           "input" in п["task"], "statement_codes" in п["task"]))
    # рядок 5239: за схемою — лише рядок кінця відповіді («now»)
    assert list(п)[-2:] == ["answer_schema", "now"] and "answer_schema" not in п["task"]
    assert хвіст == ',"now":%s}' % json.dumps(п["now"], ensure_ascii=False) and "input" in п["task"] and "statement_codes" in п["task"]
