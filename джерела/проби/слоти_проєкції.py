"""Ф2/2.6: кожна похідна група зберігає тип, склад і порядок старого читача."""
import ast, gzip, json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import слоти as _СЛОТИ


def main():
    """Звірити збережені 182 значення ДО з виразами проєкцій ПІСЛЯ."""
    корінь = Path(__file__).resolve().parents[2]
    шлях = корінь / "аудит/проби/ф2_26/групи_проєкції.json.gz"
    записи = json.loads(gzip.decompress(шлях.read_bytes()))
    for з in записи:
        до = ast.literal_eval(з["before"])
        після = eval(з["after"], {"_СЛОТИ": _СЛОТИ})
        assert type(до) is type(після) and до == після, (з["file"], з["line"])
        assert з["after"] in (корінь / "джерела" / з["file"]).read_text(), з["file"]
    print("ПРОЙДЕНО: %d точних проєкцій у %d модулях" %
          (len(записи), len({з["file"] for з in записи})))


if __name__ == "__main__":
    main()
