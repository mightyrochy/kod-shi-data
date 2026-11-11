"""Зводить факти записів і зберігає кожне питання плану без вигаданої оцінки."""
from collections import Counter
import json
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
plan = json.loads((OUT / 'ПЛАН.json').read_text(encoding='utf-8-sig'))
attempts = {}
for line in (OUT / 'done.txt').read_text(encoding='utf-8').splitlines():
    entry = json.loads(line)
    if 'rc' in entry:
        command = entry['команда']
        attempts[command[command.index('--сцена') + 1]] = entry
rows = []
questions = []
for scene, items in plan['scenes'].items():
    candidates = [OUT / scene] + sorted((ROOT / 'аудит/проби/нічні').glob('*/' + scene), reverse=True)
    folder = next((p for p in candidates if (p / 'результат.json').is_file()
                   and json.loads((p / 'результат.json').read_text(encoding='utf-8')).get('sha') == '17151e1f1709790ba3af11fbcff6be18f6ff219e'), OUT / scene)
    result = json.loads((folder / 'результат.json').read_text(encoding='utf-8')) if (folder / 'результат.json').is_file() else {}
    log = (folder / 'лог.txt').read_text(encoding='utf-8') if (folder / 'лог.txt').is_file() else ''
    red = [line.strip() for line in log.splitlines() if re.match(r'\s*[✗✘]', line)]
    error = log[log.find('стенд не піднявся:'):] if 'стенд не піднявся:' in log else ''
    rows.append(dict(сцена=scene, тека=str(folder.relative_to(ROOT)), rc=result.get('rc', attempts.get(scene, {}).get('rc')),
                     запис_завершено=result.get('rc') in (0, 1), є_результат=bool(result),
                     секунд=result.get('секунд'), змінні=result.get('змінні', {}),
                     червоні=red, помилка=error))
    for item in items:
        questions.append(dict(сцена=scene, **item, тека=str(folder.relative_to(ROOT)),
                              стан='запис завершено; див. факти й червоні звірки' if result.get('rc') in (0, 1)
                              else 'питання не доведено: запис не завершено'))
(OUT / 'зведення.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'питання.json').write_text(json.dumps(questions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
text = ['# Зведення автоматичного прогону', '', '| Сцена | rc | Секунд | Червоних |', '|---|---:|---:|---:|']
for row in rows:
    text.append(f"| {row['сцена']} | {row['rc']} | {row['секунд']} | {len(row['червоні'])} |")
text += ['', '## Червоні звірки та збої', '']
for row in rows:
    if row['червоні'] or row['помилка']:
        text += [f"### {row['сцена']}", '']
        text += ['- ' + line for line in row['червоні']]
        if row['помилка']:
            text += ['', '```text', row['помилка'], '```']
        text.append('')
(OUT / 'ЗВЕДЕННЯ.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
print('Сцени:', len(rows), 'rc:', dict(Counter(str(row['rc']) for row in rows)))
