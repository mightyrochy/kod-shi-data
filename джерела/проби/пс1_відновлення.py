"""Готовий каталог показу не класифікує офери XML повторно."""
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import фід_розбір as Р
import фід_слот as С
import фід_атрибути as А
import фід_верхнє as В
import міст_опис as М

def головна():
    """Сирий XML → готова база → коди картки, без другого класифікатора."""
    def готова_база(*args):
        yield
        return база
    with tempfile.TemporaryDirectory() as т:
        шлях = Path(т) / "каталог.xml"
        шлях.write_text('<yml_catalog><shop><offers><offer id="пс1"><name>Сукня міді</name>'
                        '<price>1200</price></offer></offers></shop></yml_catalog>', encoding="utf-8")
        with patch.object(Р, "побудувати_запис_речі", side_effect=AssertionError("класифікація XML")):
            сирі = Р.офери_фіду(str(шлях))
        р = Р.побудувати_запис_речі(сирі[0])
        готовий = {к: з for к, з in р.items() if к != "ознаки_зі_слів"}
        готовий.update(id=сирі[0]["id"], довжина_рівень="литка", тип_верхнього=None)
        база = {"каталог": [готовий]}
        with patch.object(М._Ф, "база_прогону_кроками", готова_база), \
                patch.object(С, "_вид_зі_слів", side_effect=AssertionError("повторний тип")):
            оф, індекс, *_ = М._каталог_показу(str(шлях))
            о = dict(індекс[готовий["id"]], назва="Пальто максі з вовни", параметри={})
            assert С.тип_речі(о) == готовий["тип"]
            assert А.довжина_речі(о, "сукня")[0] == "литка"
            assert В.верхні_атрибути(о)["тип_верхнього"] is None
            assert оф[0]["запис_речі"] is готовий and "запис_речі" not in сирі[0]
    print("ПС-1: готова база й картка читають коди без класифікації XML — гаразд")


if __name__ == "__main__":
    головна()
