# -*- coding: utf-8 -*-
"""CI-7, рядок 198: з чого складається вантаж і що зняв вибір способу стиску на запис.

Друкує факт із ЗІБРАНОГО `index.html` кореня: скільки важить кожен великий запис
у тому способі, яким він лежить, і скільки важив би в іншому.

Стелі показу нема з 28.09.2026 (власник, CLAUDE.md п.2), тож рядка «запас» тут
теж нема: розмір — число для порівняння двох збірок, а не поріг.
"""
import base64, bz2, io, os, re, sys, zipfile, zlib

КОРІНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
шлях = sys.argv[1] if len(sys.argv) > 1 else os.path.join(КОРІНЬ, "index.html")
сторінка = io.open(шлях, encoding="utf-8").read()
b64 = max(re.finditer(r"[A-Za-z0-9+/=]{10000,}", сторінка), key=lambda м: len(м.group(0))).group(0)
вантаж = base64.b64decode(b64)
z = zipfile.ZipFile(io.BytesIO(вантаж))

СПОСІБ = {zipfile.ZIP_DEFLATED: "deflate", zipfile.ZIP_BZIP2: "bzip2"}
знято = 0
рядки = []
for і in sorted(z.infolist(), key=lambda і: -і.compress_size):
    дані = z.read(і.filename)
    з_deflate, з_bzip2 = len(zlib.compress(дані, 9)), len(bz2.compress(дані, 9))
    знято += max(з_deflate, з_bzip2) - min(з_deflate, з_bzip2) if з_bzip2 < з_deflate else 0
    if і.compress_size > 100_000:
        рядки.append("  %-28s %-7s %9d Б (deflate %9d · bzip2 %9d)"
                     % (і.filename[:28], СПОСІБ.get(і.compress_type, "?"),
                        і.compress_size, з_deflate, з_bzip2))
print("сторінка %s: %d Б · вантаж %d Б · записів %d · base64 %d Б · сторінка поза вантажем %d Б"
      % (os.path.basename(шлях), len(сторінка.encode()), len(вантаж), len(z.infolist()),
         len(b64), len(сторінка.encode()) - len(b64)))
print("\n".join(рядки))
print("на bzip2 записів %d зі %d · вибір способу зняв %d Б вантажу (%d Б сторінки)"
      % (sum(1 for і in z.infolist() if і.compress_type == zipfile.ZIP_BZIP2),
         len(z.infolist()), знято, (знято + 2) // 3 * 4))
