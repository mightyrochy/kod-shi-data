"""Ф2/2.6: тип визначає слот попри назву й хибний слот; невідоме не вгадується."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import слоти as С, внутрішня_мова as ВМ, фід_слот as Ф


def main():
    """Перевірити договір усіх кодів типу та повноту словника, без мережі."""
    assert ВМ.ТАБЛИЦЯ["slot"] is С.КЛЮЧІ
    assert ВМ.СЛОТ_ТИПУ is С.СЛОТ_ТИПУ
    assert len(С.СЛОТИ) == len(set(С.СЛОТИ)) == 25
    assert len(С.група("основні_пулу")) == 3
    assert len(С.група("необовязкові_пулу")) == 18
    перевірок = 0
    for тип, слот in С.СЛОТ_ТИПУ.items():
        for чужий in С.СЛОТИ:
            о = dict(item_type=тип, назва="Лосини базові з широким поясом",
                     параметри={"слот": чужий})
            assert Ф.слот(о) == С.КЛЮЧІ[слот], (тип, чужий)
            assert Ф.тип_речі(о) == ВМ.ключ("item_type", тип)
            перевірок += 1
    assert Ф.слот(dict(item_type="leggings", назва="Пояс")) == "низ"
    assert Ф.слот(dict(назва="Лосини базові з широким поясом")) is None
    assert Ф.слот(dict(item_type="unknown", назва="Рукавиці")) is None
    assert Ф.слот(dict(item_type=["leggings"])) is None
    assert Ф.слот(dict(параметри={"тип": "штани", "слот": "пояс"})) == "низ"
    assert Ф.слот(dict(item_type="gloves", параметри={"стать": "чоловіче"})) is None
    assert Ф._альтернативні_слоти(dict(item_type="cardigan"), "верх") == ("верхній_шар",)
    assert Ф._альтернативні_слоти(dict(назва="Кардиган"), "верх") == ()
    try:
        С.група("одяг", порядок="пояс")
        raise AssertionError("Чужий порядок змінив склад групи")
    except ValueError:
        pass
    print("ПРОЙДЕНО: 25 слотів, %d пар тип/чужий слот; назва не впливає" % перевірок)


if __name__ == "__main__":
    main()
