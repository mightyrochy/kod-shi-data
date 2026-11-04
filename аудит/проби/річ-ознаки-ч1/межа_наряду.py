"""Відтворює межу спільного запису й числового контракту без зміни продукту."""
import json
from pathlib import Path
import sys
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "джерела"))
import colorspace as Ц
import face_features as О
import palettes as П
import суд_чеклісти as С


def main():
    """Друкує факти оцінки моделі та місце відмови читача за відсутнього числа."""
    F = Ц.features(Ц.hx("#c9b183"), Ц.hx("#4a4644"), Ц.hx("#5e6361"))
    F["_meta"] = dict(protocol="model_hex", from_photo=True)
    запис = О.ознаки(F)
    осі = П.осі(F)
    assert all(v == "withheld" for v in осі["коди"].values())
    assert запис["контраст"]["value_gap"] is not None
    assert запис["надійність"]["contrast"] == 0
    С.входи_палітри(F)
    без_числа = dict(осі, позиція={k: None for k in осі["позиція"]})
    try:
        with patch.object(П, "осі", return_value=без_числа):
            С.входи_палітри(F)
    except TypeError as помилка:
        import traceback
        кадр = traceback.extract_tb(помилка.__traceback__)[-1]
        print(json.dumps(dict(числовий_контраст=запис["контраст"]["value_gap"],
                              довіра=0, коди=осі["коди"],
                              читач=f"{Path(кадр.filename).name}:{кадр.lineno}",
                              помилка=str(помилка)), ensure_ascii=False))
    else:
        raise AssertionError("читач уже приймає None: попередній блокер не відтворився")


if __name__ == "__main__":
    main()
