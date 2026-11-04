"""Друкує втрату походження на чинному шляху від оцінки очей до відлуння основи."""
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import colorspace as С
import face_features as О
import palettes as П
import вибір_палітри as В
import колір_річ as Р


def main():
    """Зіставляє довіру спільного запису з реальним записом кольору та рішенням про основу."""
    F = С.features(С.hx("#deb295"), С.hx("#523321"), С.hx("#735632"), джерело="model_hex")
    очі = О.ознаки(F)["очі"]
    запис = П.колір_очей(очі)
    print(json.dumps(dict(джерело=очі["джерело"], довіра_очей=очі["довіра"],
        свідок_запису=запис["свідок"], довіра_запису=запис["довіра"],
        довіра_сирого_Lab=Р.запис_кольору(dict(lab=С.hx("#735632")))["довіра"],
        відлуння=В._до_очей(dict(ахром=False, hex="#735632"), F),
        комплемент=В._до_очей(dict(ахром=False, hex="#1b3d6b"), F)), ensure_ascii=False))


if __name__ == "__main__":
    main()
