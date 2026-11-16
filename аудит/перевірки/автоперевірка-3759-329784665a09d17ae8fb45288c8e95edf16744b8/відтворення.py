import gzip
import json
import os
from pathlib import Path
import subprocess
import sys
import types

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parent / 'pr3759'
SRC = ROOT / 'джерела'
OUT = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else Path(__file__).resolve().parent / 'evidence3759'
OUT.mkdir(parents=True, exist_ok=True)
os.chdir(SRC)
sys.path.insert(0, str(SRC))
import мовний_шар as layer
import паспорт_нагоди as after

assert subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip() == '329784665a09d17ae8fb45288c8e95edf16744b8'
base_sha = '8dafc1113ba09cdc5459cead2c0878fbc14b2b37'
base_source = subprocess.check_output(['git', 'show', base_sha + ':джерела/паспорт_нагоди.py'])
before = types.ModuleType('base_passport')
before.__file__ = str(SRC / 'паспорт_нагоди.py')
exec(compile(base_source, before.__file__, 'exec'), before.__dict__)

def row(name, passport):
    old = before.паспорт_шматками_людині(passport)
    new = after.паспорт_шматками_людині(passport)
    return {'сцена': name, 'паспорт': {k: passport[k] for k in ('нагода', 'подія', 'місце', 'місце_слова', 'пора') if k in passport}, 'до': old, 'після': new,
            'рядок_до': ' · '.join(x['текст'] for x in old),
            'рядок_після': ' · '.join(x['текст'] for x in new)}

rows = []
for file in sorted((ROOT / 'аудит/проби/живий-як-людина-1/стенд/службове').glob('*/обміни.jsonl.gz')):
    for num, line in enumerate(gzip.open(file, 'rt', encoding='utf-8')):
        data = json.loads(line)
        try:
            response = json.loads(json.loads(data['відповідь'])['content'][0]['text'])
        except (ValueError, KeyError, IndexError):
            continue
        if not isinstance(response, dict) or 'event' not in (response.get('update') or {}):
            continue
        words = [x for part in response.get('text') or [] for x in part.get('her_words') or []] + [response['update']['event']]
        for label, item in [('запис', response), ('без нагоди', dict(response, update={k: v for k, v in response['update'].items() if k != 'occasion'}))]:
            parsed = layer.прийняти_розмову(json.dumps(item, ensure_ascii=False))
            passport = layer.паспорт_з_шару(parsed['внутрішня'], {}, None, None, слова_ходу=words, частини=parsed.get('частини'))['паспорт']
            rows.append(row(f'{file.parent.name} #{num} {label}', passport))

special = [row('с4 живий рядок', {'подія': 'побачення в ресторані', 'місце': 'ресторан_районний', 'місце_слова': 'ресторані', 'пора': 'вечір'}),
           row('кафедра / слова моделі', {'подія': 'зустріч кафедри', 'місце': 'кафе', 'місце_слова': 'Кафе', 'пора': 'вечір'}),
           row('кафедра / підпис довідника', {'подія': 'зустріч кафедри', 'місце': 'кафе', 'пора': 'вечір'}),
           row('барбекю', {'подія': 'вечір барбекю з друзями', 'місце': 'бар', 'місце_слова': 'бар'})]
# Той самий вхід через справжній читач відповіді й писач паспорта.
text = 'Зустріч кафедри ввечері в кафе'
response = {'update': {'event': 'зустріч кафедри', 'place': {'value': 'cafe', 'quote': 'кафе'},
                       'place_words': 'кафе', 'part_of_day': {'value': 'evening', 'quote': 'ввечері'}},
            'text': [{'about': ['event', 'place'], 'says': 'Записала зустріч кафедри в кафе.', 'her_words': [text]}], 'need': 'none'}
parsed = layer.прийняти_розмову(json.dumps(response, ensure_ascii=False))
passport = layer.паспорт_з_шару(parsed['внутрішня'], {}, слова_ходу=[text], частини=parsed.get('частини'))['паспорт']
special.append(row('кафедра / мовний шар', passport))
all_rows = rows + special
(OUT / 'rows.json').write_text(json.dumps(all_rows, ensure_ascii=False, indent=2), encoding='utf-8')
for item in rows:
    if item['до'] != item['після']:
        print(item['сцена'], '|', item['рядок_до'], '->', item['рядок_після'])
print('Записаних паспортів:', len(rows), '; ситуацій:', len({r['сцена'].split(' #')[0] for r in rows}), '; змінених рядків:', sum(r['до'] != r['після'] for r in rows))
for item in special:
    print(item['сцена'], '|', item['рядок_до'], '->', item['рядок_після'])
print('Паспорт мовного шару:', json.dumps(special[-1]['паспорт'], ensure_ascii=False))
