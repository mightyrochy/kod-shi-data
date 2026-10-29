"""Звірити id, типи й виміри сегментів: порівняти.py [ДО.json ПІСЛЯ.json]."""
import collections
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import colorspace as КС, колір_річ as КР, outfit as О, композитор_річ as КП


def головна():
    """Надрукувати втрати каталогу й вимірів, включно зі зниклими точками кольору."""
    тека = Path(__file__).resolve().parent
    шляхи = [Path(а) for а in sys.argv[1:]] or [тека / ("каталог-" + н + ".json") for н in ("ДО", "ПІСЛЯ")]
    if len(шляхи) != 2:
        raise SystemExit("Потрібні два шляхи: ДО.json ПІСЛЯ.json")
    до, після = [{р["id"]: р for р in json.loads(шлях.read_text(encoding="utf-8"))["каталог"]}
                 for шлях in шляхи]
    підсумок = dict(до=len(до), після=len(після), втрачено_id=len(до.keys() - після.keys()),
                    змінено_записів=sum(р != до.get(і) for і, р in після.items()),
                    типи=dict(collections.Counter(map(КР.тип_кольору, після.values()))),
                    невимір_з_lab=sum(bool(р.get("lab")) for р in після.values() if КР.тип_кольору(р) != "вимір"),
                    виміряних_сегментів=0, зниклих_точок=0, спотворених_понад_1=0, найбільша_de00=0.0)
    for р in після.values():
        if not р.get("colors") or р.get("слот") == "верхній_шар":
            continue
        елементи = О.елементи([КП.у_річ(р, р["слот"], {})])
        assert len(елементи) == len(р["colors"])
        for колір, елемент in zip(р["colors"], елементи):
            очікуваний, отриманий = КР.точка_кольору(колір), КР.точка_кольору(елемент)
            if очікуваний:
                підсумок["виміряних_сегментів"] += 1
                підсумок["зниклих_точок"] += отриманий is None
                if отриманий:
                    d = КС.de00(очікуваний, отриманий)
                    підсумок["спотворених_понад_1"] += d > 1
                    підсумок["найбільша_de00"] = max(підсумок["найбільша_de00"], d)
            else:
                assert отриманий is None
                assert КР.межі_кольору(колір) == КР.межі_кольору(елемент)
    (тека / "каталог-підсумок.json").write_bytes(json.dumps(підсумок, ensure_ascii=False, indent=2).encode())
    print(json.dumps(підсумок, ensure_ascii=False))
    assert not any(підсумок[к] for к in ("втрачено_id", "невимір_з_lab", "зниклих_точок", "спотворених_понад_1"))


if __name__ == "__main__":
    головна()
