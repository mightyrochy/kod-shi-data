"""Повтор записаного концерту й придатність заміни прийнятих полів."""
import copy, json, os, pathlib, sys
sys.path.insert(0, os.environ.get("E2_SOURCES", str(pathlib.Path(__file__).resolve().parents[1])))
import мовний_шар as М


def main():
    """Надрукувати втрати уривка та результат злиття на однакових входах."""
    сцена = json.loads((pathlib.Path(__file__).resolve().parents[2] / "аудит/проби/Е2-ремонт-шар/записи.json").read_text(encoding="utf8"))[0]
    перша = next(в["відповідь"] for к, в in сцена["відповіді"].items() if "seed3_01_" in к)
    об, _ = М._обʼєкт(перша)
    факти = []
    for заміна in ({"value": "concert"}, {"quote": None, "value": "concert"}, {"quote": " ", "value": "concert"}, {"quote": 42, "value": "concert"}, "concert", None, {}):
        друга = copy.deepcopy(об); друга["update"]["occasion"] = заміна
        р = json.loads(М.мова(dict(розмова=dict(нове=сцена["слова"]), перша_відповідь=перша,
                                  відповідь_моделі=json.dumps(друга), завершити_договір=True)))
        факт = р["внутрішня"].get("event", {}).get("free_text") == "рок-концерт у клубі"
        print(json.dumps(dict(повтор=заміна, подія=р["внутрішня"].get("event"), пройдено=факт), ensure_ascii=False)); факти.append(факт)
    випадки = [("розмова", {"place": {"quote": "рок-концерт у клубі", "value": "cafe"}}, "place", "cafe"),
               ("розмова", {"place": {"value": "bad_code"}}, "place", "club"),
               ("розмова", {"place": None}, "place", "club"),
               ("розмова", {"place": "unknown"}, "place", "club"),
               ("розмова", {"place": {"value": "cafe"}}, "place", "cafe"),
               ("question", {"question_about": "look"}, "question_about", "look"),
               ("review_items_fix", {"actions": [{"item": "r2", "op": "remove"}, {"item": "r1", "op": "set", "color": "red", "slot": None}]}, "actions", [{"op": "set", "item": "r1", "color": "red", "slot": "shoes"}, {"op": "remove", "item": "r2"}]),
               ("review_items_fix", {"actions": [{"op": "add", "slot": "bag"}]}, "actions", [{"op": "set", "item": "r1", "color": "black", "slot": "shoes"}, {"op": "remove", "item": "r2"}, {"op": "add", "slot": "bag"}])]
    for вид, заміна, поле, очікуване in випадки:
        вхід = dict(розмова=dict(нове=сцена["слова"])) if вид == "розмова" else dict(вхід=вид)
        а = перша if вид == "розмова" else json.dumps(dict(question_about="app") if вид == "question" else dict(actions=[dict(op="set", item="r1", color="black", slot="shoes"), dict(op="remove", item="r2")]))
        б = dict(об, update=заміна) if вид == "розмова" else заміна
        р = json.loads(М.мова(dict(вхід, перша_відповідь=а, відповідь_моделі=json.dumps(б))))
        факт = р["внутрішня"].get(поле) == очікуване
        print(json.dumps(dict(вид=вид, заміна=заміна, значення=р["внутрішня"].get(поле), пройдено=факт), ensure_ascii=False)); факти.append(факт)
    return 0 if all(факти) else 1


if __name__ == "__main__":
    sys.exit(main())
