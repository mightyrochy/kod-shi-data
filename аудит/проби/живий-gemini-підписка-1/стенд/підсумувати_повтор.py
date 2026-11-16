"""Зведення записів повтору без оцінювання образів: python ... <тека_прогону>."""
from pathlib import Path
from collections import Counter
import gzip
import hashlib
import json
import re
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
run_rules = {}
for path in out.glob('стенд/службове/*/руки.jsonl'):
    screens = {x['крок']: x for x in (json.loads(line) for line in
               (path.parent / 'екрани.jsonl').read_text(encoding='utf-8').splitlines())}
    for line in path.read_text(encoding='utf-8').splitlines():
        x = json.loads(line)
        broken = x.get('поломка_руки_2') or {}
        if broken.get('що') or broken.get('діагноз'):
            run_rules[(path.parent.name, x['прогін'])] = broken
        screen = screens.get(x['крок'], {})
        # Галерею підтверджує її заголовок або навігація. На першій картці
        # кнопки можуть мати короткі мітки «‹»/«›»; тільки довгі мітки
        # пропускали показаний другий прохід с2 обох моделей.
        if 'Твої образи.' not in screen.get('текст', '') and not any('попередній' in e or 'наступний ›' in e or 'Записати вердикт' in e for e in screen.get('елем', [])):
            continue
        hands[(path.parent.name, x['прохід'], x['прогін'])] = x
hand_lines = ['# Руки образів на видимих картках', '',
              'Ситуація · прохід · номер на екрані → рука; ідентифікатор прогону відрізняє старі картки від нового збирання.', '']
first_pass = {}
for scene, pass_no, run in hands:
    first_pass[(scene, run)] = min(pass_no, first_pass.get((scene, run), pass_no))
for (scene, pass_no, run), x in hands.items():
    for p in x['позиції']:
        broken = ''
        if p['рука'] == '2':
            details = run_rules.get((scene, run), x['поломка_руки_2'])
            m = re.search(r'"правила":(\[[^\]]*\])', details.get('що') or '')
            label = re.search(r'"правило":"([^\"]+)"', details.get('що') or '')
            if m:
                broken = 'зламані правила: ' + ', '.join(json.loads(m[1]))
            elif label:
                # Поле «що» старого записувача має 400 символів. Для довгої
                # поломки масив міг обірватися; назва містить повний список.
                broken = 'зламані правила: ' + ', '.join(label[1].split('+')) + '; джерело: поле правило, масив правила у записі обірвано'
            else:
                broken = json.dumps(details, ensure_ascii=False)
        repeated = f'; повторний показ карток проходу {first_pass[(scene, run)]}' if pass_no != first_pass[(scene, run)] else ''
        hand_lines.append(f"- {scene} · {pass_no} · {p['позиція']} → рука {p['рука']}; прогін {run}" + (f"; {broken}" if broken else '') + repeated)
(out / 'руки.md').write_text('\n'.join(hand_lines) + '\n', encoding='utf-8')
for path in sorted(out.glob('с*/підсумок.json')):
    x = json.loads(path.read_text(encoding='utf-8'))
    fixed = 0
    for mismatch in x['розбіжності']:
        if not mismatch['дія'].startswith('надрукувала в '):
            continue
        if any(w['крок'] == mismatch['крок'] and w['прохід'] == mismatch['прохід'] for w in x['слова']):
            continue
        m = re.match(r'^надрукувала в «[\s\S]*?»: «([\s\S]*)»$', mismatch['дія'])
        if m:
            x['слова'].append({'прохід': mismatch['прохід'], 'крок': mismatch['крок'], 'текст': m[1],
                               'лягло': False, 'джерело_уточнення': 'записана помилка вводу в розбіжностях'})
            x['слів_пропущено'] += 1
            fixed += 1
    if fixed:
        path.write_text(json.dumps(x, ensure_ascii=False, indent=2), encoding='utf-8')
    summary[path.parent.name] = {k: x.get(k) for k in
                               ['слів_лягло', 'слів_пропущено', 'проходів', 'початок', 'кінець']}
    summary[path.parent.name]['розбіжностей'] = len(x['розбіжності'])
rows = [json.loads(line) for line in (out / 'стенд/журнал_моделі_продукту.jsonl').read_text(encoding='utf-8').splitlines()]
exchanges = []
for path in out.glob('стенд/службове/*/обміни.jsonl'):
    exchanges.extend(json.loads(line) for line in path.read_text(encoding='utf-8').splitlines())
audit = []
photos = []
photo_reads = []
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
    if record.get('фото'):
        expected = {Path(p['файл']).name for p in record['фото'] if p['дійшло'] and p.get('файл')}
        seen = set()
        errors = []
        for line in record['stdout'].splitlines():
            step = json.loads(line).get('step_update', {})
            if step.get('step_type') != 'tool' or step.get('tool_name') != 'read_file':
                continue
            if step.get('state') == 'DONE':
                seen.add(Path(step['tool_info']['parameters']['Path']).name.lstrip('@'))
            elif step.get('state') == 'ERROR':
                errors.append(step['tool_info'])
        photo_reads.append({'запис': path.name, 'прохід': record['прохід'],
                            'доступно': sum(bool(p['дійшло']) for p in record['фото']),
                            'прочитано_унікальних': len(seen), 'непрочитані': sorted(expected - seen),
                            'помилки_читання': errors})
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
          'читання_фото': photo_reads,
          'текст_сторінки': audit}
(out / 'зведення.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in result.items() if k != 'текст_сторінки'}, ensure_ascii=False, indent=2))
