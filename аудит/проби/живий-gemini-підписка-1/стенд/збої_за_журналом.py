"""Збої завершених ситуацій із консолі браузера й повного журналу моста.

python збої_за_журналом.py <тека_моделі> <тека_звіту>
Причини всередині worker без записаної траси не домислює.
"""
from pathlib import Path
from collections import Counter
import datetime as dt
import json
import re
import sys

model, report = map(Path, sys.argv[1:3])
report.mkdir(parents=True, exist_ok=True)
rows = [json.loads(s) for s in (model / 'стенд/журнал_моделі_продукту.jsonl').read_text(encoding='utf-8').splitlines()]
result = []
for summary_path in sorted(model.glob('с[1-8]_*/підсумок.json')):
    scene = summary_path.parent.name
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    folder = model / 'стенд/службове' / scene
    frames = [json.loads(s) for s in (folder / 'екрани.jsonl').read_text(encoding='utf-8').splitlines()]
    console = folder / 'консоль.txt'
    if not console.exists():
        continue
    for line_no, line in enumerate(console.read_text(encoding='utf-8').splitlines(), 1):
        if not re.search(r'Error:|мовчить \d+ с|Uncaught|SyntaxError', line):
            continue
        event_time = line.split()[0]
        if not re.match(r'^\d{4}-', event_time):
            continue
        stamp = dt.datetime.fromisoformat(event_time.replace('Z', '+00:00'))
        calls = []
        for row in rows:
            if not row['прохід'].startswith(scene + ' · '):
                continue
            when = dt.datetime.fromisoformat(stamp.date().isoformat() + 'T' + row['початок_utc'] + '+00:00')
            if when <= stamp:
                calls.append((when, row))
        before = max(calls, key=lambda x: x[0])[1] if calls else None
        active = [row for when, row in calls if when + dt.timedelta(seconds=row['с']) >= stamp]
        entries = (summary_path.parent / 'хід.md').read_text(encoding='utf-8')
        timed = [(int(n), t) for n, t in re.findall(r'### (\d+) · (\S+) ·', entries) if t <= event_time]
        prior_frame = max(timed, key=lambda x: x[1])[0] if timed else None
        frame = next((f for f in frames if f['крок'] == prior_frame), {})
        boundary = None
        if 'мовчить 300 с' in line:
            boundary = ('У момент скидання тривав HTTP/CLI-виклик; початок, тривалість і відповідь — у перелічених записах.'
                        if active else 'Що відбувалося всередині worker до наступного HTTP, не встановлено: стенд не записує трасу внутрішнього кроку запити.')
        result.append({'ситуація': scene, 'прохід': frame.get('прохід'), 'utc': event_time,
                       'консоль': str(console), 'рядок': line_no, 'подія': line,
                       'кадр_перед_подією': prior_frame, 'останній_розпочатий_до_події_запис': before,
                       'доказ_відповіді': f'стенд/записи/{before["н"]:04d}.json.gz' if before else None,
                       'активні_під_час_скидання_виклики': active,
                       'причина_обриву': 'Сторож сторінки скинув worker після 300 с без повідомлень.' if 'мовчить 300 с' in line else 'Подія консолі; подробиці у сирому записі.',
                       'межа_доказу': boundary})
(report / 'збої.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
lines = ['# Збої завершених ситуацій за журналом', '',
         f'Модель: {model.name}. Подій: {len(result)}.', '',
         'Це записи прогону на зафіксованій збірці серії, без оцінювання образів і без висновку про поточний main.', '']
for x in result:
    lines += [f'- {x["ситуація"]} · прохід {x["прохід"]} · {x["utc"]}: {x["причина_обриву"]} '
              f'Консоль: `{x["консоль"]}`, рядок {x["рядок"]}; кадр перед подією {x["кадр_перед_подією"]}. '
              f'Останній розпочатий перед подією виклик: `{x["доказ_відповіді"]}`. '
              f'Активні виклики під час події: {[r["н"] for r in x["активні_під_час_скидання_виклики"]]}. '
              + (x['межа_доказу'] or '')]
lines += ['', 'CLI й браузерний worker мають різні стелі: зовнішні 660 с та CLI 630 с не змінюють '
          '300-секундного сторожа мовчання worker. Відповіді CLI слід читати з вказаних сирих записів; '
          'статус 200 сам по собі не доводить правильності змісту.', '']
(report / 'збої.md').write_text('\n'.join(lines), encoding='utf-8')
print(model.name, 'подій консолі:', len(result), 'ситуації:', dict(Counter(x['ситуація'] for x in result)))
