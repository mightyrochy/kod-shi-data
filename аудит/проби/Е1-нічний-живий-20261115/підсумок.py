"""Зводить незмінені докази прогону; оцінку правок лишає незалежній перевірці."""
from collections import Counter
from datetime import datetime, timezone
import csv
import json
import os
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
plan = json.loads((OUT / 'ПЛАН.json').read_text(encoding='utf-8'))
done_path = OUT / 'done.txt'
done = [json.loads(line) for line in done_path.read_text(encoding='utf-8').splitlines() if line.strip()] if done_path.exists() else []
locations = {p.parent.name: p.parent for p in OUT.glob('*/результат.json')}
attempts = {p.parent.name: json.loads(p.read_text(encoding='utf-8')) for p in OUT.glob('*/крок_запускача.json')}
locations.update({scene: OUT / scene for scene in attempts})
base = OUT / 'НОВА_БАЗА.md'
if base.exists():
    for name in re.findall(r'НОВА БАЗА: (\S+)', base.read_text(encoding='utf-8')):
        folder = ROOT / name
        if (folder / 'результат.json').exists():
            result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
            locations[result['сцена']] = folder
results = {name: json.loads((folder / 'результат.json').read_text(encoding='utf-8')) for name, folder in locations.items() if (folder / 'результат.json').exists()}
counts = Counter(str(result.get('rc', 'не записано')) for result in results.values())
relative = lambda folder: os.path.relpath(folder, OUT).replace('\\', '/')
lines = ['# Е1-нічний-живий-20261115 — звіт тестового прогону', '',
         'Час зведення UTC: ' + datetime.now(timezone.utc).isoformat(), '',
         f"Призначене дерево: `{plan['build']}`; штамп сторінки: `ef60e250a98cdb05d7f31fdf62bd296971807e94`.",
         'Предковість до origin/main і SHA тимчасового дерева — у середовище.json; точні команди, час та rc — у запуск.jsonl і done.txt.', '',
         f"План: {len(plan['scenes'])} сцен ноутбука, {sum(map(len, plan['scenes'].values()))} питань; {len(plan['cloud'])} сцени у хмарі; bad={len(plan['bad'])}. Спроб у done.txt: {sum('команда' in e for e in done)}; результат.json: {len(results)}; rc стенда з результат.json: {dict(counts)}. Код запускача після винятку не є кодом завершеної сцени.", '',
         'Це автоматичний тестовий прогін із записаними репліками. Жива людина образів не оцінювала. Незалежне приймання питань виконує окрема перевірка за записами.', '',
         'Рука 1 — продукт; рука 2 — навмисна поломка; руки 3–4 — модель без коду й каталогу. Червоні рук 2–4 не є окремими вадами продукту. Порядок і склади карток витягнуто в руки.md та руки.json.', '',
         'Чужу модель на початку не вивантажували; стан очікування — очікування.jsonl. Перевірка власного завантаження моделей із context_length 57344/16384 та parallel=1 — моделі_перевірка.json. NODE_OPTIONS і PYTHONPATH обгортки збережено.', '',
         'Фото її_річ.jpg відновлено з публічного URL крамниці; SHA256 збігся з попереднім прогоном. Походження — походження_фото.json. Саме фото до Git не включено.', '',
         '## Результати сцен', '', '| Сцена | Режим | rc | Час, с | Картки | Доказ |', '|---|---|---:|---:|---:|---|']
hands = ['# Руки записаних сцен', '', 'Рука 1 — продукт, рука 2 — навмисна поломка, руки 3–4 — модель без коду й каталогу. Якісних оцінок образів тут немає.', '', '| Сцена | Порядок | Поломка руки 2 | Рука | Речей | Фото | Джерело |', '|---|---|---|---:|---:|---:|---|']
hand_data = {}
failures = []
for scene in plan['scenes']:
    result = results.get(scene, {})
    folder = locations.get(scene, OUT / scene)
    prefix = relative(folder)
    env = result.get('змінні', {})
    mode = {'rozmova': 'розмова', 'palitra': 'палітра', 'koment': 'коментар', 'otsinka': 'оцінка'}.get(env.get('DO'), 'повне')
    if env.get('FOTO') == '1': mode += ' +фото'
    proof_file = folder / 'знімки/доказ.json'
    proof = json.loads(proof_file.read_text(encoding='utf-8')) if proof_file.exists() else {}
    refused = '; '.join(d.get('відмова', '') for d in done if d.get('сцена') == scene and d.get('відмова'))
    if scene in attempts:
        lines.append(f"| {scene} | {mode if result else 'див. крок_запускача.json'} | {result.get('rc', 'не записано')}; запускач {attempts[scene]['rc']} | {result.get('секунд', '—')} | {proof.get('факт', {}).get('карток', 'не виміряно')} | `{prefix}/крок_запускача.json` |")
    else:
        lines.append(f'| {scene} | — | відмова / не розпочато | — | — | {refused} |')
    log_file = folder / 'лог.txt'
    log = log_file.read_text(encoding='utf-8').splitlines() if log_file.exists() else []
    order = next((re.search(r'розклад рук: (\d+)', line)[1] for line in log if re.search(r'розклад рук: (\d+)', line)), 'не записано')
    mutation = next((re.search(r'поломка руки 2: "([^"]*)"', line)[1] for line in log if re.search(r'поломка руки 2: "([^"]*)"', line)), 'не записано')
    for number, line in enumerate(log, 1):
        match = re.search(r'\s+рука ([1-4]) (\{.*\})$', line)
        if match:
            data = json.loads(match[2])
            hand_data.setdefault(scene, []).append({'рука': int(match[1]), 'рядок': number, 'дані': data})
            hands.append(f"| {scene} | {order} | {mutation} | {match[1]} | {data.get('речей')} | {data.get('фото')} | `{prefix}/лог.txt:{number}` |")
    red = [(number, line.strip()) for number, line in enumerate(log, 1) if '✗' in line or 'стенд не піднявся:' in line]
    if red or (scene in attempts and result.get('rc') not in (0, 1)):
        failures += ['### ' + scene, '', f"rc={result.get('rc')}; журнал `{prefix}/лог.txt`.", '']
        failures += [f'- Рядок {number}: {line}' for number, line in red]
        exchanges = sorted((folder / 'VIDPOVIDI/обмін').glob('*.json'))
        if exchanges:
            exchange = json.loads(exchanges[-1].read_text(encoding='utf-8'))
            failures += ['', f"Останній вхід і сира відповідь: `{prefix}/VIDPOVIDI/обмін/{exchanges[-1].name}`; HTTP {exchange.get('відповідь', {}).get('status', 'не записано')}. Це посилання на запис, а не встановлена причина всіх попередніх червоних."]
        if not red:
            failures += ['', 'Стенд не залишив завершеного журналу звірок; причина потребує журналу запускача.']
        failures += ['']
lines += ['', '## Збої з записів', ''] + failures
coverage = []
for scope in ('scenes', 'cloud'):
    for scene, questions in plan[scope].items():
        result = results.get(scene, {})
        folder = locations.get(scene)
        state = 'у хмарі; ставить диспетчер' if scope == 'cloud' else 'запис завершено; оцінює перевірка' if result.get('rc') in (0, 1) else 'обрив / не виміряно'
        for question in questions:
            coverage.append({'місце': scope, 'сцена': scene, 'PR': question['pr'], 'стан': state, 'rc': result.get('rc', ''), 'доказ': relative(folder) + '/результат.json' if folder else '', 'питання': question['question']})
with (OUT / 'покриття.tsv').open('w', encoding='utf-8', newline='') as stream:
    writer = csv.DictWriter(stream, fieldnames=list(coverage[0]), delimiter='\t')
    writer.writeheader(); writer.writerows(coverage)
lines += ['', '## У хмарі', '']
for scene, questions in plan['cloud'].items():
    for question in questions:
        lines.append(f"- У хмарі `{scene}`, PR #{question['pr']}: {question['question']}")
lines += ['', 'Кожне питання плану, PR, стан запису й доказ — у покриття.tsv. Завершений запис сам собою не означає відповіді «так» на всі питання.', '', '## Нова база', '']
lines += base.read_text(encoding='utf-8').splitlines()[2:] if base.exists() else ['Крок нової бази ще не виконано.']
for name, content in [('ЗВІТ.md', lines), ('руки.md', hands)]:
    (OUT / name).write_text('\n'.join(content) + '\n', encoding='utf-8')
(OUT / 'руки.json').write_text(json.dumps(hand_data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'результатів': len(results), 'rc': dict(counts), 'питань': len(coverage)}, ensure_ascii=False))
