"""Зняти промпти, схему й повний повтор записів із цілісного дерева коду."""
import json
import sys
from pathlib import Path


def main():
    """Виміряти задане дерево без підміни окремих його залежностей."""
    корінь, вихід = map(Path, sys.argv[1:])
    код = корінь / "джерела"
    sys.path[:0] = [str(код), str(код / "прилади")]
    import мовний_шар as м
    import внутрішня_мова as в
    from replay_картки import виміряти

    схема = в.схема()
    дані = {
        "коди_розмови": "\n".join(м._коди_розмови()),
        "репліка": м.промпт_репліки({"not_recorded": ["place"]}),
        "схема": схема,
        "json_схема_тотожна": json.loads((код / "внутрішня_мова.schema.json").read_text(
            encoding="utf-8")) == схема,
        "повтор": виміряти(код / "проби/дані/картка_запиту.json", код),
    }
    вихід.write_text(json.dumps(дані, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Схема тотожна JSON:", дані["json_схема_тотожна"])
    print("Кодів розмови:", len(дані["коди_розмови"]), "символів; репліки:", len(дані["репліка"]))
    print(json.dumps(дані["повтор"]["лічба"], ensure_ascii=False))


if __name__ == "__main__":
    main()
