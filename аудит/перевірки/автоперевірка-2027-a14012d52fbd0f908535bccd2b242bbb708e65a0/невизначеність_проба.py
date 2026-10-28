"""Друкує, чи суд палітри зберігає невідомий тон виміру поверхні.

Аргумент — окреме дерево перевірюваного PR; жодних мережевих викликів чи правок.
"""
import json
import math
from pathlib import Path
import sys


def main():
    """Два контрольовані градієнти → вимір поверхні → суд палітри."""
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root / "джерела"))
    import colorspace as C
    import річ_з_фото as R
    import міст_вхід as M
    import palettes as P
    вхід = json.loads((root / "джерела/стенд_вх.json").read_text(encoding="utf-8"))
    F, _T = M.збірка(M.нормалізувати_вхід(dict(вхід)))[:2]
    палітра = P.палітра_практична(F)
    for h in (0, 180):
        a, b = 12.5 * math.cos(math.radians(h)), 12.5 * math.sin(math.radians(h))
        rgb = []
        for _y in range(64):
            for x in range(64):
                d = (x % 32 - 15.5) * .5
                hx = C.hex_з_lab((65, a-d*math.sin(math.radians(h)), b+d*math.cos(math.radians(h))))
                rgb.append(tuple(int(hx[j:j+2], 16) for j in (1, 3, 5)))
        вимір = R._вимір_плями(rgb, 64, 64, [True]*4096, 1, "контрольований градієнт", None, True, поправка=False)
        сегмент = вимір["поверхня"]["сегменти"][0]
        print(json.dumps(dict(h=h, придатна=вимір["поверхня"]["придатна"], тон=сегмент["тон"],
                              хрома=сегмент["хрома"], lab=вимір["lab"],
                              палітра=R.членство_в_палітрі(вимір["lab"], палітра)), ensure_ascii=False))


if __name__ == "__main__":
    main()
