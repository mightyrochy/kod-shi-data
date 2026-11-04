"""Перевіряє межу між спільним записом рис та універсальним читачем кольору."""
import json, pathlib, sys

К = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
import міст_вхід as В, face_features as О, колір_річ as Р


def main():
    """Друкує тип, свідка та доступність точного запису на реальних профілях."""
    вих = []
    for шлях in sorted((К / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text("utf8"))
        for джерело in ("model_hex", "spectro"):
            F = В.features(dict(шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"], source=джерело))[0]
            for назва, риса in О.ознаки(F)["риси"].items():
                нв = Р.не_вимір(риса)
                запис = dict(профіль=шлях.stem, джерело=джерело, риса=назва,
                             тип=Р.тип_кольору(риса), свідок=нв["свідок"] if нв else "measure",
                             точка=Р.точка_кольору(риса), запис=Р.запис_кольору(риса),
                             відношення=Р.відношення(dict(hex="#557755"), риса, "echo"))
                вих.append(запис)
                if "--перевірити" in sys.argv:
                    if джерело == "model_hex":
                        assert запис["тип"] == "невідомо" and запис["свідок"] == "model_hex"
                        assert запис["точка"] is None and запис["запис"] is None
                        assert запис["відношення"] == "невідомо"
                    else:
                        assert запис["тип"] == "вимір" and запис["точка"] is not None
    if "--перевірити" in sys.argv:
        до = json.loads(pathlib.Path(__file__).with_name("читач-кольору-до.json").read_text("utf8"))
        assert [x for x in до if x["джерело"] == "spectro"] == [x for x in вих if x["джерело"] == "spectro"]
    print(json.dumps(вих, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
