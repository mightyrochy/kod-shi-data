"""Відтворює втрату походження у читачі, який належить іншій частині кореня."""
import json, pathlib, sys

К = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(К / "джерела"))
import міст_вхід as В, face_features as О, вибір_палітри as П, colorspace as С, bases as Б


def main():
    """Код 1 означає відтворений висновок до очей за нульової довіри до портрета."""
    висновки = []
    for шлях in sorted((К / "аудит/проби/жінки").glob("*.json")):
        ж = json.loads(шлях.read_text("utf8"))
        F = В.features(dict(шкіра=ж["skin"], волосся=ж["hair"], очі=ж["eyes"]))[0]
        запис = О.ознаки(F)
        assert запис["протокол"] == "model_hex" and not any(запис["надійність"].values())
        for hex in (ж["eyes"], "#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff", "#777777"):
            основа = dict(hex=hex, ахром=С.lch(С.hx(hex))[1] < Б.АХРОМАТИЧНА_МЕЖА)
            звʼязок = П._до_очей(основа, F)
            if звʼязок is not None:
                висновки.append(dict(профіль=шлях.stem, основа=hex, звʼязок=звʼязок,
                                     протокол=запис["протокол"], довіра=запис["очі"]["довіра"]))
    print(json.dumps(висновки, ensure_ascii=False, indent=2))
    return int(bool(висновки))


if __name__ == "__main__":
    sys.exit(main())
