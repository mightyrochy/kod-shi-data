"""Повторно завантажити фото ранніх завершених запитів, до появи архівування.
Це реконструкція за URL, а не доказ побайтової тотожності першому завантаженню.
Жоден наявний збережений файл не переписується; невдалі первісні фото не повторюються.
"""
from pathlib import Path
import gzip
import hashlib
import json
import sys
import urllib.request

out = Path(sys.argv[1]) / 'стенд/записи'
rows = []
for record in sorted(out.glob('*.json.gz')):
    x = json.loads(gzip.decompress(record.read_bytes()))
    for photo in x.get('фото', []):
        if not photo['дійшло'] or not photo.get('url'):
            continue
        folder = out / 'фото' / record.name.split('.')[0]
        if list(folder.glob(f"{photo['н']:02d}.*")):
            continue
        row = {'запис': record.name, 'фото': photo['н'], 'url': photo['url'],
               'джерело': 'повторне завантаження за первісною адресою', 'первісних_байтів': photo['байтів']}
        try:
            req = urllib.request.Request(photo['url'], headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=20) as response:
                data = response.read()
            ext = '.webp' if data[8:12] == b'WEBP' else '.png' if data[:4] == b'\x89PNG' else '.jpg'
            folder.mkdir(parents=True, exist_ok=True)
            dest = folder / f"{photo['н']:02d}{ext}"
            dest.write_bytes(data)
            row.update({'файл': dest.relative_to(out).as_posix(), 'байтів': len(data),
                        'розмір_збігається': len(data) == photo['байтів'], 'sha256': hashlib.sha256(data).hexdigest()})
        except Exception as e:
            row['помилка'] = str(e)
        rows.append(row)
(out / 'реконструкція_ранніх_фото.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
print('Реконструйовано:', len(rows), '; однаковий розмір:', sum(x.get('розмір_збігається', False) for x in rows))
