"""Перевірка повноти журналів і крайніх значень без звернення до моделей.
Запуск: python -X utf8 перерахунок.py <корінь перевіреної голови PR>.
"""
import collections
import gzip
import json
import pathlib
import sys

root = pathlib.Path(sys.argv[1]) / 'аудит/проби/модель-текст-claude/дані'
for model in ('sonnet_low', 'haiku_low'):
    with gzip.open(root / (model + '.jsonl.gz'), 'rt', encoding='utf-8') as stream:
        rows = [json.loads(line) for line in stream]
    longest = max(rows, key=lambda row: row['с'])
    largest = max(rows, key=lambda row: row['вихід'])
    print(json.dumps({
        'модель': model, 'рядків': len(rows), 'унікальних_id': len({row['id'] for row in rows}),
        'статуси': dict(collections.Counter(row['статус'] for row in rows)),
        'моделі_журналу': sorted({str(row['моделі']) for row in rows}),
        'вихід_разом': sum(row['вихід'] for row in rows),
        'думки_разом': sum(row['думки'] or 0 for row in rows),
        'понад_16000': sum(row['вихід'] > 16000 for row in rows),
        'понад_85с': sum(row['с'] > 85 for row in rows),
        'макс_вихід': largest['вихід'], 'id_макс_вихід': largest['id'],
        'макс_с': longest['с'], 'id_макс_с': longest['id'],
    }, ensure_ascii=False))
