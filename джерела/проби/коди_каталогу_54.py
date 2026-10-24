"""Читачі 5.4: цитати, шість назв із поясом, незнання, одиниці й межі; без моделі."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed, каталог_розбір as Р, catalog_fields as К, profile, outfit
from jsonschema import validate
for тип, назва, слот in [("dress_generic", "Плаття з поясом", "сукня"), *(('kimono', 'Кімоно з поясом', 'верхній_шар'),)*4, ("leggings", "Лосини з поясом", "низ")]:
    о = dict(назва=назва, опис="Тафта. Довжина 100 см. Еластан 5%.", параметри={"тип": "пояс", "слот": "пояс"})
    відповідь = dict(item_type=dict(value=тип, quote=назва), fabric=dict(value="taffeta", quote="Тафта"),
        length_cm=dict(value=100, unit="cm", quote="Довжина 100 см"), elastane_pct=dict(value=5, unit="percent", quote="Еластан 5%"))
    п, причини = Р.з_відповіді(json.dumps(відповідь), Р.вхід(о))
    validate(dict(п, id="проба"), Р.схема()["$defs"]["catalog_parse"])
    о["розбір"] = п
    assert feed.слот(о) == слот and К.число(о, "length_cm") == 100
    assert К.число(о, "elastane_pct", "percent") == 5 and К.тканина(о)["блиск"] == 1
    assert К.джерело(о, "fabric")["quote"] == "Тафта" and п["fabric"] != "polyester"
    assert not profile.жорстке_ні_фільтр([о], ["пояс"])[1]
невідомо, _ = Р.з_відповіді(json.dumps({"slot":{"value":"belt","quote":"пояс"}, "item_type":{"value":"dress_generic","quote":"ВИГАДАНО"}}), Р.вхід(о))
assert невідомо["item_type"] == невідомо["slot"] == "unknown" and feed.слот(dict(о, розбір=невідомо)) is None
п, _ = Р.з_відповіді(json.dumps({"item_type":{"value":"leggings","quote":"Лосини"}, "sleeve":"not_applicable", "fabric":"unknown"}), Р.вхід(о))
assert п["sleeve"] == "not_applicable" and п["fabric"] == "unknown"
for в, очікувано in [(dict(value=80,unit="mm"),8), (dict(value=True,unit="cm"),None), ("8 см",None), (0,None)]:
    assert К.число({"розбір":{"heel":{"height_cm":в}}}, "heel.height_cm") == очікувано
assert К.ознака({"розбір":{"belt":"unknown"}},"belt") is None
assert К.ознака({"розбір":{"belt":"no"}},"belt") is False
assert К.збіг_межі({"розбір":{"pattern":"check"}}, "принт", "принти")
assert not К.збіг_межі({"назва":"Картата блуза"}, "клітинка", "принти")
assert not outfit.зони_речі({"слот":"верх", "назва":"відкриті плечі"})[0]
print("6 назв: пояс 0; тафта окремо від поліестеру; цитати/schema/невідомо/одиниці/межі: гаразд")
import суд_від_моделі as С, каталог_розбір_прогін as П
assert not any(з['правило']=='K-KOH-06' for з in С.доповнення_судді([{'назва':'Паєтки','слот':'верх'}], {'година':13}))
assert any(з['правило']=='K-KOH-06' for з in С.доповнення_судді([{'назва':'A1','слот':'верх','розбір':{'decor':['sequins']}}], {'година':13}))
офери = [dict(id=str(i),назва='Плаття з поясом',параметри={}) for i in range(1000)]
в = П.вибірка(офери,30); assert len(в)==len({о['id'] for _,о in в})==300 and в==П.вибірка(офери[::-1],30)
print('K-KOH-06 читає код оздоби; перша вибірка без кодів: 300 різних речей, сталий добір')
