"""Друкує байти запитів з вимкненими записами на стендовому каталозі й сцені с5."""
import gzip
import json
import os
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace


def main():
    джерела = Path(sys.argv[1]).resolve() / "джерела"
    sys.path.insert(0, str(джерела))
    os.chdir(джерела)
    import bridge
    from ядро.тести import обвязка
    from ядро.тести.тест_н3 import _складач

    протокол = SimpleNamespace(виклик=lambda запит: bridge.виклик("ядро", запит))
    with TemporaryDirectory() as тека:
        каталог = Path(тека) / "каталог_brief.xml"
        каталог.write_bytes(gzip.decompress((джерела / "каталог_brief.xml.gz").read_bytes()))
        вхід = обвязка.вхід_с5(каталог=str(каталог), модель={"вікно": 200_000})
        вхід["перемикачі"]["записи_речі"] = "без"
        кінець, журнал = обвязка.прогнати(протокол, вхід, _складач)
    assert кінець["кінець"] and журнал["запити"]
    for з in журнал["запити"]:
        print(json.dumps([з["рука"], з["вид"], з["модель"]["messages"]], ensure_ascii=False))


if __name__ == "__main__":
    main()
