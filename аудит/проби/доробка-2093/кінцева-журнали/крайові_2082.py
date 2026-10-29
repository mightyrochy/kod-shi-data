"""Незалежне відтворення втрат на повторі мовного шару PR 2082."""
import json
import pathlib
import sys

sys.path.insert(0, sys.argv[1])
import мовний_шар as М


def виклик(перша, друга, **контекст):
    return json.loads(М.мова(dict(контекст, відповідь_моделі=json.dumps(друга),
                                 перша_відповідь=json.dumps(перша), завершити_договір=True)))


def main():
    """Надрукувати прийняту окремо другу відповідь і результат її злиття."""
    перша = {"actions": [{"op": "remove", "item": "r1"}, {"op": "add", "kind": "bad", "color": "red"}]}
    друга = {"actions": [{"op": "remove", "item": "r1"}, {"op": "add", "kind": "shirt", "color": "red"}]}
    окремо = М.прийняти_вхід("review_items_fix", json.dumps(друга))
    разом = виклик(перша, друга, вхід="review_items_fix", слова="додай червону сорочку")
    print(json.dumps(dict(випадок="додавання речі без id", окремо=окремо["внутрішня"],
                          разом=разом["внутрішня"]), ensure_ascii=False))

    запис = pathlib.Path(sys.argv[1]).parent / "аудит/проби/Е2-ремонт-шар/записи.json"
    сцена = json.loads(запис.read_text(encoding="utf-8"))[0]
    сирий = next(в["відповідь"] for к, в in сцена["відповіді"].items() if "seed3_01_" in к)
    перша, _ = М._обʼєкт(сирий)
    друга = json.loads(json.dumps(перша))
    друга["update"]["occasion"] = {"value": "concert"}
    разом = виклик(перша, друга, розмова={"нове": сцена["слова"]})
    паспорт = М.паспорт_з_шару(разом["внутрішня"], {}, слова_ходу=сцена["слова"],
                              частини=разом["частини"])["паспорт"]
    print(json.dumps(dict(випадок="повтор без уривка відхиленої нагоди", подія=паспорт.get("подія"),
                          нагода=паспорт.get("нагода"), місце=паспорт.get("місце")), ensure_ascii=False))

    друга = json.loads(json.dumps(перша))
    друга["update"]["occasion"]["value"] = "theatre"
    друга["update"]["formality"] = "neat"
    друга.pop("text", None)
    разом = виклик(перша, друга, розмова={"нове": сцена["слова"]})
    окремо = М.прийняти_розмову(json.dumps(друга))
    print(json.dumps(dict(випадок="виправлені поля без text у повторі",
                          окремо={к: окремо["внутрішня"].get(к) for к in ("occasion", "formality")},
                          разом={к: разом["внутрішня"].get(к) for к in ("occasion", "formality")}), ensure_ascii=False))


if __name__ == "__main__":
    main()
