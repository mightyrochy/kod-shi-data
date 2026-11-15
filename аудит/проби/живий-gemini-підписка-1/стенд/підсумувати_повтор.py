"""Зведення записів повтору без оцінювання образів: python ... <тека_прогону>."""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import json
import sys

out = Path(sys.argv[1])
if '--стан' in sys.argv:
    journal = out / 'стенд/журнал_моделі_продукту.jsonl'
    rows = [json.loads(s) for s in journal.read_text(encoding='utf-8').splitlines()] if journal.exists() else []
    print('Завершених викликів:', len(rows), '; статуси:', dict(Counter(x['статус'] for x in rows)),
          '; фото:', sum(x['фото'] for x in rows))
    for path in out.glob('стенд/службове/*/екрани.jsonl'):
        x = json.loads(path.read_text(encoding='utf-8').splitlines()[-1])
        print(path.parent.name, 'крок', x['крок'], 'прохід', x['прохід'], x['опис'][:100])
        print(x['текст'].replace('\n', ' ')[:500])
    sys.exit(0)
summary = {}
hands = {}
for path in out.glob('стенд/службове/*/руки.jsonl'):
    screens = {x['крок']: x for x in (json.loads(line) for line in
               (path.parent / 'екрани.jsonl').read_text(encoding='utf-8').splitlines())}
    for line in path.read_text(encoding='utf-8').splitlines():
        x = json.loads(line)
        screen = screens.get(x['крок'], {})
        # Для раннього запущеного стенда: беремо лише кадри галереї,
        # де на видимому екрані є лічильник образів або навігація карток.
        if not any('попередній' in e or 'наступний ›' in e or 'Записати вердикт' in e for e in screen.get('елем', [])):
            continue
        hands[(path.parent.name, x['прохід'], x['прогін'])] = x
hand_lines = ['# Руки образів на видимих картках', '',
              'Ситуація · прохід · номер на екрані → рука; ідентифікатор прогону відрізняє старі картки від нового збирання.', '']
for (scene, pass_no, run), x in hands.items():
    for p in x['позиції']:
        broken = json.dumps(x['поломка_руки_2'], ensure_ascii=False) if p['рука'] == '2' else ''
        hand_lines.append(f"- {scene} · {pass_no} · {p['позиція']} → рука {p['рука']}; прогін {run}; {broken}")
(out / 'руки.md').write_text('\n'.join(hand_lines) + '\n', encoding='utf-8')
for path in sorted(out.glob('с*/підсумок.json')):
    x = json.loads(path.read_text(encoding='utf-8'))
    summary[path.parent.name] = {k: x.get(k) for k in
                               ['слів_лягло', 'слів_пропущено', 'проходів', 'початок', 'кінець']}
    summary[path.parent.name]['розбіжностей'] = len(x['розбіжності'])
rows = [json.loads(line) for line in (out / 'стенд/журнал_моделі_продукту.jsonl').read_text(encoding='utf-8').splitlines()]
exchanges = []
for path in out.glob('стенд/службове/*/обміни.jsonl'):
    exchanges.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
audit = []
photos = []
for path in sorted(out.glob('стенд/записи/*.json.gz')):
    record = json.loads(gzip.decompress(path.read_bytes()))
    prompt = json.loads(record['stdin'])['message']['content'][0]['text']
    candidates = [x for x in exchanges if x['прохід'] == int(record['прохід'].rsplit(' · ', 1)[-1])]
    texts = []
    for x in candidates:
        body = json.loads(x['запит'])
        chunks = [b['text'] for m in body.get('messages', []) for b in m.get('content', []) if b.get('type') == 'text']
        if chunks and all(chunk in prompt for chunk in chunks):
            texts = chunks
            break
    audit.append({'запис': path.name, 'прохід': record['прохід'],
                  'усі_текстові_блоки_дослівні': bool(texts), 'блоків': len(texts)})
    photos.extend(record.get('фото', []))
http_photos = Counter()
for path in out.glob('стенд/службове/*/фото_речей.txt'):
    for line in path.read_text(encoding='utf-8').splitlines():
        if 'attico.ua' in line:
            http_photos[line.split()[1]] += 1
intact = sum(bool(p.get('файл') and p.get('sha256') and
                  (out / 'стенд/записи' / p['файл']).exists() and
                  hashlib.sha256((out / 'стенд/записи' / p['файл']).read_bytes()).hexdigest() == p['sha256']) for p in photos if p['дійшло'])
result = {'ситуації': summary, 'викликів': len(rows),
          'статуси_моста': dict(Counter(str(x['статус']) for x in rows)),
          'токени': {k: sum(x.get(k) or 0 for x in rows) for k in ['вхід', 'кеш_читання', 'вихід', 'роздуми', 'усього']},
          'час_викликів_с': sum(x['с'] for x in rows),
          'фото_моста': {'всього': len(photos), 'доставлено_файлом': sum(bool(x['дійшло']) for x in photos),
                        'архів_із_первісним_sha256_підтверджено': intact,
                        'статуси': dict(Counter(str(x['статус']) for x in photos))},
          'attico_браузер': dict(http_photos),
          'текст_сторінки': audit}
(out / 'зведення.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'текст_сторінки'}, ensure_ascii=False, indent=2))
