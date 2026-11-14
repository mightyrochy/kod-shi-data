"""Механічна карта питань до доказів; оцінку правок робить окрема перевірка."""
from collections import Counter
from pathlib import Path
import csv
import json
import os
import re

out = Path(__file__).resolve().parent
plan = json.loads((out / 'ПЛАН.json').read_text(encoding='utf-8'))
done = [json.loads(line) for line in (out / 'done.txt').read_text(encoding='utf-8').splitlines() if line.strip()]
refused = {(row['сцена'], row['pr']): row['відмова_питання'] for row in done if row.get('відмова_питання')}
locations = {p.parent.name: p.parent for p in out.glob('*/результат.json')}
if (out / 'НОВА_БАЗА.md').exists():
    for name in re.findall(r'НОВА БАЗА: (\S+)', (out / 'НОВА_БАЗА.md').read_text(encoding='utf-8')):
        folder = Path(name)
        if (folder / 'результат.json').exists():
            result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
            locations[result['сцена']] = folder
rows = []
for scope in ('scenes', 'cloud'):
    for scene, questions in plan[scope].items():
        folder = locations.get(scene)
        result = json.loads((folder / 'результат.json').read_text(encoding='utf-8')) if folder else {}
        for question in questions:
            refusal = refused.get((scene, question['pr']))
            if scope == 'cloud': state = 'у хмарі; ставить диспетчер'
            elif refusal: state = 'відмова режиму питання'
            elif not result: state = 'запису немає'
            elif result.get('rc') in (0, 1): state = 'запис завершено; оцінює перевірка'
            else: state = 'обрив; питання не доведено'
            replay = out / 'повтор_обміну' / scene / 'результат.json'
            if (out / 'повтор_обміну_1800' / scene / 'результат.json').exists():
                replay = out / 'повтор_обміну_1800' / scene / 'результат.json'
            rows.append({'місце': scope, 'сцена': scene, 'PR': question['pr'], 'стан': state,
                         'rc': result.get('rc', ''), 'режим_запису': json.dumps(result.get('змінні', {}), ensure_ascii=False),
                         'доказ': os.path.relpath(folder, out).replace('\\', '/') + '/результат.json' if folder else '',
                         'повтор': os.path.relpath(replay, out).replace('\\', '/') if replay.exists() else '',
                         'відмова': refusal or '', 'питання': question['question']})
with (out / 'покриття.tsv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(rows[0]), delimiter='\t')
    writer.writeheader(); writer.writerows(rows)
counts = Counter(row['стан'] for row in rows)
(out / 'покриття.md').write_text('# Покриття плану\n\n'
    'Кожне дослівне питання, PR, стан запису, відмова й посилання на доказ — у покриття.tsv. '
    'Завершений запис не означає відповіді «так» на всі його питання; оцінює окрема перевірка за сирими даними.\n\n'
    + '\n'.join(f'- {state}: {count} питань.' for state, count in counts.items()) + '\n', encoding='utf-8')
print(dict(counts))
