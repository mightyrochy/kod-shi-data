"""ПС-1: після класифікації слова й формат промпту не міняють коди речі."""
import sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import feed as Ф
import фід_слот as С
import каталог_коди as К
import пакет_моделі as П
import дріт_моделі as Д
import знання_речі as З
import outfit as О


def головна():
    """Пройти вхід, читачів складу й обидва формати справжнього промпту."""
    о = dict(id="пс1", назва="Сукня міді з поясом", категорія="сукня", параметри={"склад": "100% бавовна"})
    р = Ф.побудувати_запис_речі(о)
    отрута = dict(о, запис_речі=р, назва="Чоловічі джинси з вовни", назва_показу="Джинси", параметри={})
    with patch.object(С, "_вид_зі_слів", side_effect=AssertionError("повторний розбір")):
        assert Ф.тип_речі(отрута) == "сукня_без_уточнення" and Ф.слот(отрута) == "сукня"
        assert Ф.матеріал_речі(отрута)[0] == "100% бавовна"
    assert З.властивість(р, "composition")["value"] == ["cotton"]
    з = Ф.завершити_запис_речі(dict(р, id=о["id"], назва="Сукня", довжина="литка", крій="straight"))
    з["розбір"] = {"item_type": "jeans", "cut": "bodycon", "length": "mini"}
    assert О.елементи([dict(з, hex="#303030")])[0]["матеріал_коди"] == з["матеріал_коди"]
    with patch.object(К, "поля", side_effect=AssertionError("пізнє читання розбору")), patch.object(К, "увімкнено", return_value=True):
        п = П.річ_пулу(з, {})
        повний, короткий = Д.річ(п), Д.річ(п, короткий=True)
        assert повний["type"] == короткий["item_type"] == "dress_generic"
        assert короткий["cut"] == повний["cut"] and короткий["length"] == повний["length"]
    assert К.склад_комплекту(dict(назва="Костюм жакет і штани"))[0] is None
    assert Ф.тип_речі(dict(слот="верх", назва="Джинси")) is None
    print("ПС-1: незмінність кодів, склад, повний і короткий промпт — гаразд")


if __name__ == "__main__":
    головна()
