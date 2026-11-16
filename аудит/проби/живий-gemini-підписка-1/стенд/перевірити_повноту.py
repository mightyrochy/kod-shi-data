"""Звірка доказів повтору: записи, дослівні слова, текст, фото й проходи.

python перевірити_повноту.py <тека_моделі> <файл_результату>
Не оцінює образів і не змінює даних прогону.
"""
from collections import Counter
from pathlib import Path
import gzip
import hashlib
import json
import re
import sys

out, target = map(Path, sys.argv[1:3])
source = out.parent.parent / 'живий-як-людина-1'
issues, scenes, images, bad_calls, read_errors = [], {}, Counter(), [], []
tools = Counter()
rows = [json.loads(s) for s in (out / 'стенд/журнал_моделі_продукту.jsonl').read_text(encoding='utf-8').splitlines()]
records = {p.stem.split('.')[0]: p for p in (out / 'стенд/записи').glob('*.json.gz')}
exchanges = {}
for p in out.glob('стенд/службове/*/обміни.jsonl'):
    exchanges[p.parent.name] = [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines()]
for p in sorted(out.glob('с*/підсумок.json')):
    scene = p.parent.name
    result = json.loads(p.read_text(encoding='utf-8'))
    raw = (source / scene / 'хід.md').read_text(encoding='utf-8')
    expected = []
    for step, text in re.findall(r'### (\d+) ·[^\n]*\n([\s\S]*?)(?=\n### |$)', raw):
        action = re.search(r'^- дія: ([\s\S]*?)(?=\n\n|$)', text, re.M)
        match = re.match(r'^надрукувала в «[\s\S]*?»: «([\s\S]*)»$', action[1]) if action else None
        if match:
            expected.append((int(step), match[1]))
    actual = [(w['крок'], w['текст']) for w in result['слова']]
    if actual != expected:
        issues.append({'ситуація': scene, 'проблема': 'порядок або текст реплік відрізняється від джерела'})
    frames = [json.loads(s) for s in (out / 'стенд/службове' / scene / 'екрани.jsonl').read_text(encoding='utf-8').splitlines()]
    missing = [x['крок'] for x in frames if not (p.parent / 'знімки' / f'{x["крок"]:04d}.jpg').exists()]
    if missing:
        issues.append({'ситуація': scene, 'немає_кадрів': missing})
    for shot in (p.parent / 'знімки').glob('*.jpg'):
        data = shot.read_bytes()
        if not (data.startswith(b'\xff\xd8') and data.endswith(b'\xff\xd9')):
            issues.append({'ситуація': scene, 'пошкоджений_jpeg': shot.name})
    http = Counter()
    photo_log = out / 'стенд/службове' / scene / 'фото_речей.txt'
    if photo_log.exists():
        for line in photo_log.read_text(encoding='utf-8').splitlines():
            if 'attico.ua' in line:
                http[line.split()[1]] += 1
    scenes[scene] = {'реплік_у_джерелі': len(expected), 'реплік_у_звіті': len(actual),
                     'дослівно_і_по_порядку': actual == expected,
                     'введено': result['слів_лягло'], 'пропущено': result['слів_пропущено'],
                     'проходів': result['проходів'], 'кадрів': len(frames),
                     'attico_200': http['200'], 'attico_403': http['403'], 'attico_всі_статуси': dict(http)}
    if result['проходів'] != 2:
        issues.append({'ситуація': scene, 'проходів': result['проходів']})
for row in rows:
    number = f'{row["н"]:04d}'
    if number not in records:
        issues.append({'немає_запису': number})
        continue
    record = json.loads(gzip.decompress(records[number].read_bytes()))
    scene, pass_no = record['прохід'].rsplit(' · ', 1)
    prompt = json.loads(record['stdin'])['message']['content'][0]['text']
    matches = []
    for exchange in exchanges.get(scene, []):
        if exchange['прохід'] != int(pass_no):
            continue
        request = json.loads(exchange['запит'])
        chunks = [b['text'] for m in request.get('messages', []) for b in m.get('content', []) if b.get('type') == 'text']
        if chunks and all(chunk in prompt for chunk in chunks):
            matches.append(exchange)
    if not matches:
        issues.append({'запис': number, 'проблема': 'немає відповідного дослівного входу сторінки'})
    reads, errors = set(), []
    for line in record['stdout'].splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        step = event.get('step_update', {})
        if step.get('step_type') == 'tool' and step.get('state') in ('DONE', 'ERROR'):
            tools[step.get('tool_name')] += 1
        if step.get('tool_name') == 'read_file':
            if step.get('state') == 'DONE':
                reads.add(Path(step['tool_info']['parameters']['Path']).name.lstrip('@'))
            elif step.get('state') == 'ERROR':
                errors.append(step['tool_info'])
    for photo in record.get('фото', []):
        images[str(photo['статус'])] += 1
        if not photo['дійшло']:
            continue
        path = out / 'стенд/записи' / photo['файл']
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != photo.get('sha256'):
            issues.append({'запис': number, 'фото': photo['файл'], 'проблема': 'не збігається архів SHA256'})
        if path.name not in reads:
            issues.append({'запис': number, 'фото': photo['файл'], 'проблема': 'немає успішного читання фото'})
    if errors:
        read_errors.append({'запис': number, 'помилки_read_file': errors,
                            'успішно_прочитані': sorted(reads)})
    if row['статус'] != 200:
        bad_calls.append({'запис': number, 'прохід': record['прохід'], 'статус': row['статус'],
                          'помилка': row.get('помилка'), 'код': record['код'],
                          'stderr': record['stderr'], 'сирий_вихід': str(records[number])})
if len(rows) != len(records):
    issues.append({'записів': len(records), 'рядків_журналу': len(rows)})
result = {'ситуації': scenes, 'викликів': len(rows), 'записів': len(records),
          'обмінів_браузера': sum(map(len, exchanges.values())),
          'статуси_моста': dict(Counter(str(r['статус']) for r in rows)),
          'фото_статуси': dict(images), 'помилки_повноти': issues,
          'помилки_спроб_читання': read_errors, 'збої_моделі': bad_calls,
          'виклики_інструментів': dict(tools)}
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(bool(issues))
