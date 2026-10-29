"""Друкує повтор завершеної черги після зміни рецепта без втрати історії."""
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "zhnyvarka"))
from журнал_проходу import ЖурналПроходу, відбиток_рецепта
from json_прохід import позначити, завершено
from обхід import узгодити_рецепти, черга


def main():
    """Завершує SQLite і JSON, міняє селектор і звіряє рішення обходу."""
    with tempfile.TemporaryDirectory() as ж:
        р = dict(домен="store.test", сімейство="horoshop", старт="https://store.test/")
        файл = Path(ж) / "сирі/store.test.jsonl"; файл.parent.mkdir()
        п = ЖурналПроходу(Path(ж) / "проходи", р["домен"], відбиток_рецепта(р))
        url = "https://store.test/p1"; п.перелік([url])
        ід = п.відповідь(url, 200, b"product")
        запис = dict(url=url, стан="картка", відповідь=ід)
        файл.write_text(json.dumps(запис) + "\n", encoding="utf-8"); п.завершити(запис); п.закрити()
        узгодити_рецепти(ж, [р]); до = черга(ж, р["домен"])
        історія = файл.read_bytes(); р["селектор_характеристик"] = "table.specification"
        узгодити_рецепти(ж, [р]); після = черга(ж, р["домен"])
        assert до == (1, 1) and після == (1, 0) and файл.read_bytes() == історія
        р = dict(домен="json.test", сімейство="shopify", старт="https://json.test/")
        позначити(ж, р["домен"], True, підпис=відбиток_рецепта(р))
        узгодити_рецепти(ж, [р]); assert завершено(ж, р["домен"])
        р["селектор_характеристик"] = "table.specification"
        узгодити_рецепти(ж, [р]); assert not завершено(ж, р["домен"])
        print(f"SQLite DONE: {до} → {після}; JSON завершено: True → False; історія збережена")


if __name__ == "__main__":
    main()
