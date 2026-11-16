"""Латки-свідки огляду 15.11: медіана Lab прямокутника на речі, hex і слово `surface.слово_з_lab` (`main`), ΔE00 до
запису. Свідок огляду, не вимір речі й не поріг вердикту (як `../річ_колір_розкид_очима_1411/латки.py`).

З кореня, після `вибірка.py <тека> --фото` (вона ж розпаковує дерево `main` у `<тека>/main`):
    python3 -I аудит/проби/річ_колір_приймання_1511/латки.py <тека>
"""
import csv, statistics, sys
from pathlib import Path
ТУТ = Path(__file__).resolve().parent
ТЕКА = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ТЕКА / "main" / "джерела"))
from PIL import Image
import colorspace as CS, колір_простір_перетворення as P, surface as S
ЛАТКИ = {"1.1": (307, 467, 533, 733), "4.1": (517, 750, 617, 1083), "5.1": (412, 591, 536, 824),
         "8.1": (210, 250, 330, 390), "11.1": (160, 400, 300, 560), "13.1": (316, 618, 508, 1030),
         "23.1": (296, 296, 667, 889), "24.1": (260, 380, 330, 540), "29.1": (367, 583, 700, 950),
         "33.1": (367, 367, 534, 701)}
б = str(ТЕКА / "фото" / "аудит/проби/річ_колір_перезбір_0411") + "/"; т = str(ТУТ)
р = {f"{x['номер']}.{x['кадр']}": x for x in csv.DictReader(open(т + "/вибірка.tsv", encoding="utf-8"), delimiter="\t")}
вих = [["кадр", "рамка", "латка_hex", "латка_слово", "запис_hex", "код_main", "ΔE00"]]
for к, рам in ЛАТКИ.items():
    з = Image.open(б + р[к]["фото"]).convert("RGB").crop(рам)
    пікс = list(з.getdata())
    labs = [P.to_lab(p) for p in пікс]
    м = tuple(statistics.median(l[i] for l in labs) for i in range(3))
    hx = CS.hex_з_lab(м); rh = р[к]["hex"]
    rl = P.to_lab([int(rh[i:i + 2], 16) for i in (1, 3, 5)])
    вих.append([к, ",".join(map(str, рам)), hx, S.слово_з_lab(м)[0], rh, р[к]["код_main"], "%.2f" % CS.de00(м, rl)])
with open(т + "/латки.tsv", "w", encoding="utf-8", newline="") as ф:
    csv.writer(ф, delimiter="\t", lineterminator="\n").writerows(вих)
for в in вих: print("\t".join(в))
