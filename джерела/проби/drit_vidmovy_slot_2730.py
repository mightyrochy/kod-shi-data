# -*- coding: utf-8 -*-
"""Рядок 2730: межа, сказана про один слот, доїжджає до стилістки зі слотом (`case.refusals`).
Стенд (сід 4242), паспорт із коментарем, як його віддає мовна модель шару: «взуття без чорного» (колір,
слот є в `вето_тверде.слоти` з давніх пір) і «взуття без принта» (принт, слот — з #725). Друкує
`case.refusals` промпту складання й чи стоїть у ньому рядок опису `only_on`.
До правки: `refusals.colors: ["black"]` — без слота, тобто «без чорного на весь образ».
Прогін: cd джерела && python3 проби/drit_vidmovy_slot_2730.py      (~1 хв)"""
import json, os, sys
ТУТ = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); sys.path.insert(0, ТУТ); os.chdir(ТУТ)
import feed as Ф, bridge as B, міст_пакет as МП, мовний_шар as МШ, пакет_моделі as ПМ
кат = Ф.каталог_на_диску("каталог_повний.xml")
def промпт(коментар):
    вх = dict(json.load(open("стенд_вх.json", encoding="utf-8")), сід=4242, каталог=кат)
    п = {"перекладено_шаром": True, "вето": {}}
    вх["паспорт"] = МШ.паспорт_з_коментаря({"vetoes": коментар}, паспорт_досі=п)["паспорт"]
    МП._КЕШ_ПАКЕТА.clear(); B.виклик("запити", json.dumps(вх, ensure_ascii=False))
    пак = [p for p in МП._КЕШ_ПАКЕТА.values() if p.get("кандидати")][0]
    return json.loads(ПМ.промпт_складання(пак["пакет"] if "пакет" in пак else пак))
for назва, к in (("взуття без чорного", [{"slot": "shoes", "color_name": "black"}]),
                 ("взуття без принта", [{"slot": "shoes", "pattern": "print_generic"}]),
                 ("весь образ без принта", [{"pattern": "print_generic"}])):
    т = промпт(к)
    print("%-22s refusals %s · рядок only_on у task.input: %s" % (назва, json.dumps((т.get("case") or {}).get("refusals"),
          ensure_ascii=False), any("only_on" in str(x) for x in (т.get("task") or {}).get("input", []))))
