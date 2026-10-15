"""Рядки 5310, 5273: форма списків у промпті; запис Г1 — контроль чинного парсера.

Запуск: python3 проби/розмова_список_цитата.py [шлях_до_seed3_01].
"""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import мовний_шар as М


def виміряти():
    """Друкує форму трьох полів і, за записом Г1, прийняття голого та цитованого списків."""
    промпт = json.loads(М.промпт_розмови({}))
    поля = ("goal_extra", "goal_zones", "registers")
    рядки = [р for р in промпт["task"]["codes"] if any(р.startswith("- " + п + " —") for п in поля)]
    форма = '{"quote": the fragment of her words, "value": [codes]}'
    print("Форма списку з цитатою: %d/%d" % (sum(форма in р for р in рядки), len(рядки)))
    if len(sys.argv) < 2:
        return
    запис = Path(sys.argv[1]).read_text()
    вхід = json.loads(запис.splitlines()[1])
    відповідь = запис.split("── ВІДПОВІДЬ", 1)[1].split("```json\n", 1)[1].split("```", 1)[0]
    об = json.loads(відповідь)
    for назва in ("голий список", "список з цитатою"):
        р = М.прийняти_розмову(json.dumps(об, ensure_ascii=False))
        взято, не_взято = М._тримається(р["внутрішня"], вхід["her_new_message"])
        print("%s: goal_extra=%s; не_взято=%s" % (назва, взято.get("goal_extra"), не_взято))
        об["update"]["goal_extra"] = {"quote": "хочу виглядати вищою", "value": ["taller"]}


if __name__ == "__main__":
    виміряти()
