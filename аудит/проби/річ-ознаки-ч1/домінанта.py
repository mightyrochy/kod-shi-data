"""Повтор невдалої звірки фізичного вводу на остаточному коді Ч1."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import colorspace as С
import palettes as П


def main():
    """Звіряє перевагу виміряної хроми над слабшим боком, названим її відповідями."""
    F = С.features(С.hx("#c9b183"), С.hx("#4a4644"), С.hx("#5e6361"))
    осі = П.осі(F, самозвіт=dict(метал="золото", білий="теплий"))
    assert осі["домінанта"] == "chroma" and осі["вторинна"] == "hue"
    assert abs(осі["позиція"]["hue"]) < abs(осі["позиція"]["chroma"])
    print(осі["домінанта"], осі["вторинна"], осі["позиція"], "порушень: 0")


if __name__ == "__main__":
    main()
