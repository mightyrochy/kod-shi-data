"""Витяг фактів рук із незмінених журналів; моделі не запускає."""
from pathlib import Path
import json
import os
import re

out = Path(__file__).resolve().parent
locations = {p.parent.name: p.parent for p in out.glob('*/результат.json')}
base = out / 'НОВА_БАЗА.md'
if base.exists():
    for name in re.findall(r'НОВА БАЗА: (\S+)', base.read_text(encoding='utf-8')):
        folder = Path(name)
        if (folder / 'результат.json').exists():
            result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
            locations[result['сцена']] = folder

lines = ['# Руки записаних сцен', '',
         'Рука 1 — продукт. Рука 2 — контроль із навмисною поломкою. Руки 3–4 — модель без коду й каталогу; відсутність їхніх товарних фото та цін передбачена побудовою досліду. Їхні червоні не рахуються вадами продукту руки 1. Якісної оцінки образів тут немає.', '',
         'Порядок визначено з журналу кожної сцени. Знімок першої відкритої картки не є автоматично знімком руки 1.', '',
         '| Сцена | Порядок | Поломка руки 2 | Рука | Речей | Зі своїм фото | Цін | Джерело |',
         '|---|---|---|---:|---:|---:|---:|---|']
raw = {}
for scene, folder in sorted(locations.items()):
    log = (folder / 'лог.txt').read_text(encoding='utf-8')
    order = re.search(r'розклад рук: (\d+)', log)
    mutation = re.search(r'поломка руки 2: "([^"]*)"', log)
    rows = []
    for number, line in enumerate(log.splitlines(), 1):
        match = re.search(r'\s+рука ([1-4]) (\{.*\})$', line)
        if match:
            data = json.loads(match[2])
            rows.append(dict(рядок=number, дані=data))
            prefix = os.path.relpath(folder, out).replace('\\', '/')
            lines.append(f"| {scene} | {order[1] if order else 'не записано'} | {mutation[1] if mutation else 'не записано'} | {match[1]} | {data.get('речей')} | {data.get('фото')} | {data.get('ціни')} | `{prefix}/лог.txt:{number}` |")
    if rows:
        raw[scene] = rows
    else:
        result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
        mode = result.get('змінні', {}).get('DO')
        reason = 'режим ' + mode if mode else 'повних карток не записано'
        lines.append(f'| {scene} | {reason} | — | — | — | — | — | `{scene}/результат.json` |')
(out / 'руки.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
(out / 'руки.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('Картки рук у сценах:', len(raw), 'із', len(locations))
