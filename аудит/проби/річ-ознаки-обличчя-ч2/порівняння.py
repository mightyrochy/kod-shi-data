"""Звіряє утримання модельних ознак і сталість фізичних палітр на збережених профілях."""
import gzip
import json
from pathlib import Path


def main():
    """Друкує зміни за джерелом і перевіряє спостережувані рішення читачів."""
    т = Path(__file__).resolve().parent
    до, після = [json.loads(gzip.decompress((т / ("профілі-" + м + ".json.gz")).read_bytes()))
                 for м in ("до", "після")]
    assert len(до) == len(після) == 36
    підсумок = {}
    for дж in ("model_hex", "spectro", "protocolized", "uncontrolled"):
        пари = [(д, п) for д, п in zip(до, після) if д["джерело"] == дж]
        підсумок[дж] = dict(профілів=len(пари), зміни={к: sum(д[к] != п[к] for д, п in пари)
            for к in до[0] if any(д[к] != п[к] for д, п in пари)})
        for д, п in пари:
            assert д["профіль"] == п["профіль"] and д["джерело"] == п["джерело"]
            if дж == "model_hex":
                assert п["якір"] is None and п["контраст"] is None and п["L_ноги"] is None
                assert п["палітра"]["світлота"] is None and п["палітра"]["хрома"] is None
                assert not п["палітра"]["нейтралі"] and not п["палітра"]["родини"]["родини"]
                assert not п["спектри"] and п["регіони"]["ансамбль"] is None and not п["суд"]
                assert п["обраний_якір"] is not None
            elif дж in ("spectro", "protocolized"):
                assert all(д[к] == п[к] for к in д if к != "регіони")
    (т / "профілі-порівняння.json").write_text(json.dumps(підсумок, ensure_ascii=False, indent=2), encoding="utf8")
    print("варіантів 36; утримання 9/9; явний якір 9/9; сталі фізичні палітри й слоти 18/18")


if __name__ == "__main__":
    main()
