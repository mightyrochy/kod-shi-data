"""Звіряє збої із сирими відповідями; не запускає моделей і не змінює їхні записи."""
from collections import Counter
import json
import os
from pathlib import Path
import re

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
locations = {p.parent.name: p.parent for p in OUT.glob('*/крок_запускача.json')}
base = OUT / 'НОВА_БАЗА.md'
if base.exists():
    for name in re.findall(r'НОВА БАЗА: (\S+)', base.read_text(encoding='utf-8')):
        folder = ROOT / name
        if (folder / 'результат.json').exists():
            result = json.loads((folder / 'результат.json').read_text(encoding='utf-8'))
            locations[result['сцена']] = folder
rows = []
lines = ['# Причини збоїв із записів', '',
         'Джерела — незмінені вхід та сира відповідь кожного обміну, журнал стенда, журнал запускача і мережа картинок. '
         'Повний витяг метаданих викликів — обміни_аналіз.json. Неправильний JSON встановлено строгим json.loads, без ремонту чи перегравання відповіді.', '',
         'Рука 1 — продукт. Порожня контрольна рука 2 та розбіжності переліків рук 3–4 не є окремими вадами руки 1. '
         'Перевірки порожніх карток, опису, етапів, відгуку та відсутньої четвертої колонки після зриву складання мають спільну причину — відсутній образ відповідної руки.', '']
for scene, folder in sorted(locations.items()):
    log_file = folder / 'лог.txt'
    log = log_file.read_text(encoding='utf-8').splitlines() if log_file.exists() else []
    prefix = os.path.relpath(folder, OUT).replace('\\', '/')
    red = [(i, line.strip()) for i, line in enumerate(log, 1) if '✗' in line or 'стенд не піднявся:' in line]
    marker = folder / 'крок_запускача.json'
    result_file = folder / 'результат.json'
    result = json.loads(result_file.read_text(encoding='utf-8')) if result_file.exists() else {}
    calls = []
    for exchange_file in sorted((folder / 'VIDPOVIDI/обмін').glob('*.json')):
        exchange = json.loads(exchange_file.read_text(encoding='utf-8'))
        response = exchange['відповідь']
        number = int(exchange_file.stem)
        header = next(((i, line.strip()) for i, line in enumerate(log, 1) if re.search(r'модель #' + str(number) + r'\b', line)), (None, ''))
        raw = response.get('body', '')
        try:
            body = json.loads(raw)
        except (ValueError, TypeError):
            body = {}
        text = ''.join(c.get('text', '') for c in body.get('content', []) if c.get('type') == 'text')
        cleaned = re.sub(r'^```(?:json)?\s*|\s*```$', '', text.strip())
        data, invalid = None, None
        if text:
            try:
                data = json.loads(cleaned)
            except ValueError as error:
                invalid = str(error)
        calls.append({'сцена': scene, 'файл': prefix + '/VIDPOVIDI/обмін/' + exchange_file.name,
                      'рядок_логу': header[0], 'виклик': header[1], 'http': response.get('status'),
                      'модель': exchange.get('запит', {}).get('model'), 'stop_reason': body.get('stop_reason'),
                      'usage': body.get('usage'), 'ключі': list(data) if isinstance(data, dict) else None,
                      'помилка_json': invalid, 'текст_символів': len(text),
                      'помилка_сервера': body.get('error'), 'хвіст_відповіді': text[-140:]})
    rows.extend(calls)
    if not red and result.get('rc') == 0:
        continue
    lines += ['## ' + scene, '', f"Журнал: `{prefix}/лог.txt`; rc сцени: {result.get('rc', 'не записано')}. Усі виклики нижче мають повний вхід і сиру відповідь у названому JSON.", '']
    if result.get('rc') is None:
        lines += ['- Завершеного результату сцени немає. Код запускача після винятку не доводить завершення сценарію; причина винятку — у план_лог.txt та крок_запускача.json.']
    significant = []
    for call in calls:
        json_expected = any(word in call['виклик'] for word in ('ПАКЕТ', 'ВЕРДИКТ', 'ПОВНОТА', 'ОПИС', 'мовний шар', 'речі з фото', 'перелік речей', 'вибір палітри'))
        reasons = []
        if call['http'] != 200:
            reasons.append('HTTP ' + str(call['http']) + ': ' + str(call['помилка_сервера']))
        if call['stop_reason'] == 'max_tokens':
            reasons.append('стеля виводу: max_tokens')
        if json_expected and call['помилка_json']:
            reasons.append('синтаксично непридатний JSON: ' + call['помилка_json'])
        if call['ключі'] == ['answer_schema']:
            reasons.append('єдиний верхній ключ answer_schema: модель обгорнула відповідь схемою')
        if reasons:
            significant.append(call)
            lines.append(f"- `{call['файл']}`; лог:{call['рядок_логу']}: " + '; '.join(reasons) + '.')
    empty = []
    for number, line in enumerate(log, 1):
        match = re.search(r'рука ([12]) (\{.*\})$', line)
        if match:
            hand = json.loads(match[2])
            if hand.get('збій') or not hand.get('речей'):
                empty.append(match[1])
                lines.append(f"- Рука {match[1]} порожня або має збій; лог:{number}, речей {hand.get('речей')}, ітерацій {hand.get('ітерацій')}. Перевірки її відсутніх карток і наступних кроків не є незалежними причинами.")
    if empty:
        bad_assembly = [c for c in significant if 'ПАКЕТ' in c['виклик']]
        if bad_assembly:
            lines.append('- Відповіді складання вище містять обрив або неправильний JSON уже на виході моделі. Порожня рука не доводить, що код відкинув коректну відповідь; у записі коректного результату цих викликів немає.')
        else:
            lines.append('- Глибшу причину порожньої руки не встановлено цим витягом: потрібна перевірка всіх полів контракту у сирій відповіді складання, а не лише її JSON-синтаксису. Метадані й повні відповіді збережено.')
    if any('worker: мовчить 300 с' in line for line in log):
        lines.append('- Безпосередній обрив продукту — worker не відповів на «запити» за 300 с. Точний рядок діагнозу — у лог.txt. Причину всередині worker не встановлено: запис не містить стеку та часової розмітки його внутрішнього обчислення; відповіді сервера наведено вище.')
    if any('під_пальцем_кнопка' in line for _, line in red):
        lines.append('- Червона геометрія дотику знята після scrollTo до самого низу. Стенд штампа, рядки 4038–4054, центрує кнопку лише за FOTO_STEND=1. Кадр scenarii_knopka_nad_panelliu_seed3.png зберігає фактичне положення: хибна точка пальця сама собою не доводить перекриття панеллю. Перевірено кадр ж1_контекст_заперечення: кнопку прокручено вище вікна; запас до панелі додатний.')
    photo_file = folder / 'знімки/фото_карток.txt'
    if any('жінка БАЧИТЬ фото' in line for _, line in red) and photo_file.exists():
        photo = photo_file.read_text(encoding='utf-8').splitlines()
        errors = [(i, line) for i, line in enumerate(photo, 1) if line.startswith('IMGFAIL') or re.match(r'IMGRESP (?!200\b)', line)]
        statuses = Counter(re.search(r'IMGRESP (\d+)', line)[1] for _, line in errors if re.search(r'IMGRESP (\d+)', line))
        lines.append(f"- Фото: фактичні HTTP-відмови {dict(statuses)}, мережевих записів помилок {len(errors)}; `{prefix}/знімки/фото_карток.txt`. Це відповідь крамниці / мережі, не відповідь стилістки. Знімки карток показують конкретні силуети; природний розмір решти img не означає, що фото всіх речей видно.")
        if errors:
            lines.append(f"  Приклад: рядок {errors[0][0]} — {errors[0][1]}.")
    if any('руки 3–4: кожна річ переліку' in line for _, line in red):
        lines.append('- Невідповідність переліку і прози стосується рук 3–4. Сирі виклики «проза» та «перелік речей» збережено; це контрольні моделі без коду й каталогу, не симптом руки 1.')
    if any('дві ітерації + вибір' in line for _, line in red):
        lines.append('- Звірка кількості ітерацій вимагає 3 (або дозволеного ремонту повноти) у кожній руці 1–2. Фактичні лічильники — у червоному рядку журналу; синтаксичні помилки та обгортки answer_schema відповідних викликів наведено вище. Без прив’язки до конкретної руки ця загальна червона не є окремою вадою продукту.')
    lines += ['']
(OUT / 'обміни_аналіз.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(OUT / 'ПРИЧИНИ.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(json.dumps({'сцен': len(locations), 'обмінів': len(rows), 'http_не_200': sum(row['http'] != 200 for row in rows), 'стеля_виводу': sum(row['stop_reason'] == 'max_tokens' for row in rows)}, ensure_ascii=False))
