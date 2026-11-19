"""Тіла сторінки прогону 13.11 → JSONL `{id, с, час, тривав, запит, відповідь}` (id — `<ситуація>#NNN` у порядку
обмінів). Запуск: python3 сторінка.py <тека службове прогону> > сторінка.jsonl"""
import gzip, json, os, sys
к = sys.argv[1]
for с in sorted(os.listdir(к)):
    ф = os.path.join(к, с, 'обміни.jsonl.gz')
    if not os.path.exists(ф):
        continue
    for н, рядок in enumerate(gzip.open(ф, 'rt')):
        з = json.loads(рядок)
        print(json.dumps({'id': f'{с}#{н:03d}', 'с': с, 'час': з['час'], 'тривав': з['с'],
                          'запит': з['запит'], 'відповідь': з['відповідь']}, ensure_ascii=False))
