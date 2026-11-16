"""Розміри входів node ДО (один JSON) і ПІСЛЯ (рядки) з дампів дамп.py: аргумент — тека дампів."""
import gzip, json, sys
from pathlib import Path
тека = Path(sys.argv[1]); до, після = [], []
for і in range(10 ** 6):
    с, н = тека / f'старий_{і}.json.gz', тека / f'новий_{і}.ndjson.gz'
    if not с.exists():
        break
    вхід = json.loads(gzip.decompress(с.read_bytes()))
    до.append((len(json.dumps(вхід)), len(json.dumps(вхід, ensure_ascii=False).encode())))
    рядки = gzip.decompress(н.read_bytes()).decode().split('\n')[:-1]
    після.append((max(len(р.encode()) for р in рядки), sum(len(р.encode()) + 1 for р in рядки), len(рядки)))
print(f'викликів node: {len(до)} → {len(після)}')
print(f'ДО: найбільший вхід виклику одним рядком {max(д[0] for д in до)} байт (ASCII-міра старого друку), '
      f'{max(д[1] for д in до)} байт UTF-8 справді в stdin; викликів понад 1 МБ: {sum(д[1] > 10 ** 6 for д in до)}')
print(f'ПІСЛЯ: найбільший рядок входу {max(п[0] for п in після)} байт; найбільший вхід виклику загалом '
      f'{max(п[1] for п in після)} байт ({max(п[2] for п in після)} рядків); рядків понад 1 МБ: '
      f'{sum(п[0] > 10 ** 6 for п in після)}; сума входів {sum(д[1] for д in до)} → {sum(п[1] for п in після)} байт')
