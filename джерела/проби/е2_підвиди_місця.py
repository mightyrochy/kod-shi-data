"""Межа підвидів доходить із паспорта поля до схеми та промпту без читання її слів."""
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import внутрішня_мова as В
import мовний_шар as М
import паспорт_поля as П
import схема_відповіді as С


def main():
    """Звірити два споживачі опису та приймання загального й названих підвидів."""
    схема = В.схема()
    поле = схема["$defs"]["scenario"]["properties"]["place"]
    хід = С.форма_мовного_шару()["properties"]["update"]["properties"]["place"]
    assert поле == хід["properties"]["value"]
    промпт = "\n".join(М._коди_розмови())
    for опис in П.описи_підвидів("place"):
        assert опис in поле["description"] and опис in промпт
        assert опис not in М.промпт_репліки({"not_recorded": ["place"]})
    assert поле["title"] in М.промпт_репліки({"not_recorded": ["place"]})
    for код, цитата in (("office", "в офісі"), ("office_corporate", "у корпоративному офісі"),
                         ("office_creative", "у креативному офісі")):
        assert код in поле["enum"]
        відповідь = json.dumps({"update": {"place": {"quote": цитата, "value": код}},
                                "need": "none", "text": []}, ensure_ascii=False)
        прийнято = М.прийняти_розмову(відповідь)
        паспорт = М.паспорт_з_шару(прийнято["внутрішня"], {}, слова_ходу=[цитата])["паспорт"]
        факт = паспорт["картка_запиту"]["місце"]
        assert факт["значення"] == В.ключ("place", код), факт
        assert факт["джерело"] == (П.ЇЇ if код == "office" else П.ТЛУМАЧЕННЯ), факт
        assert факт["уривок"] == цитата, факт
        print(код, "→", факт["значення"], факт["джерело"])
    print("Межа підвидів у схемі й промпті: 1; прийнято місць: 3/3.")


if __name__ == "__main__":
    main()
