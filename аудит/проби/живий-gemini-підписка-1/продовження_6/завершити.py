"""Звіт продовження /6 з перевірених записів; без викликів моделей.

Запускати після завершення продовжити_вікно.py, з кореня репозиторію.
Попередній звіт збережений у СПРОБА_6_ПЕРШЕ_ВІКНО.md; завершених ситуацій не повторює.
"""
from pathlib import Path
from collections import defaultdict
import datetime
import json
import os
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
STAND = BASE / 'стенд'
ENV = dict(os.environ, PYTHONUTF8='1', PYTHONIOENCODING='utf-8')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


state = read(BASE / 'спроба_6/стан.json')
before = read(HERE / 'стан_до.json')
added = state['завершено'][len(before['завершено']):]
assert state['статус'].startswith('ГОТОВО'), state['статус']
models = {}
errors = []
for name in ['gemini-3.8-flash', 'gemini-4-hydrogen']:
    folder = BASE / name
    report = HERE / name
    report.mkdir(exist_ok=True)
    if name == 'gemini-4-hydrogen':
        for script, args, logname in [
            ('перевірити_повноту.py', [str(folder), str(report / 'перевірка_даних.json')], 'повнота'),
            ('збої_за_журналом.py', [str(folder), str(report)], 'збої'),
        ]:
            proc = subprocess.run([sys.executable, str(STAND / script), *args], capture_output=True, env=ENV)
            (report / (logname + '.stdout.txt')).write_bytes(proc.stdout)
            (report / (logname + '.stderr.txt')).write_bytes(proc.stderr)
            assert proc.returncode == 0, script
        audit = read(report / 'перевірка_даних.json')
    else:
        audit = read(BASE / 'спроба_6' / name / 'перевірка_даних.json')
    errors.extend(audit['помилки_повноти'])
    if any(k != 'read_file' and n for k, n in audit['виклики_інструментів'].items()):
        errors.append({'модель': name, 'інші_інструменти': audit['виклики_інструментів']})
    summary = read(folder / 'зведення.json')
    groups = defaultdict(list)
    hands_path = folder / 'руки.md'
    hands = hands_path.read_text(encoding='utf-8').split('\n<!-- відсутні-картки -->')[0]
    for line in hands.splitlines():
        match = re.match(r'^- (.+?) · ([12]) · ([1-4]) → рука ([1-4]); прогін (\S+)', line)
        if match:
            scene, phase, position, hand, run = match.groups()
            groups[(scene, int(phase), run.rstrip(';'))].append((int(position), int(hand)))
            if hand == '2' and 'зламані правила:' not in line:
                errors.append({'модель': name, 'рука_2_без_правил': line})
    first = {}
    for scene, phase, run in groups:
        first[(scene, run)] = min(phase, first.get((scene, run), phase))
    shown = {(s, p) for s, p, run in groups if p == first[(s, run)]}
    missing = [(s, p) for s in summary['ситуації'] for p in (1, 2) if (s, p) not in shown]
    for group, positions in groups.items():
        if sorted(p for p, h in positions) != [1, 2, 3, 4] or sorted(h for p, h in positions) != [1, 2, 3, 4]:
            errors.append({'модель': name, 'група': group, 'позиції': positions})
    if missing and name == 'gemini-4-hydrogen':
        hands += '\n<!-- відсутні-картки -->\n\nПроходи без показаного нового збирання:\n\n'
        hands += ''.join(f'- {s} · {p} · нові картки не показані; повторний показ попередніх карток позначено вище. Подія й докази — у звіті збоїв.\n' for s, p in missing)
        hands_path.write_text(hands, encoding='utf-8')
    models[name] = {
        'ситуацій': len(summary['ситуації']), 'проходів': 2 * len(summary['ситуації']),
        'викликів': summary['викликів'], 'статуси_моста': summary['статуси_моста'],
        'знімків': sum(x['кадрів'] for x in audit['ситуації'].values()),
        'введено': sum(x['введено'] for x in audit['ситуації'].values()),
        'пропущено': sum(x['пропущено'] for x in audit['ситуації'].values()),
        'фото': summary['фото_моста'], 'attico': summary['attico_браузер'],
        'роздуми': summary['токени']['роздуми'], 'груп_карток': len(groups),
        'збої_моделі': audit['збої_моделі'],
        'без_нового_збирання': missing, 'ситуації': summary['ситуації'],
    }
assert not errors, errors
result = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'додано': added, 'лишилось': state['лишилось'],
          'квота_до': before['квота_після'], 'квота_після': state['квота_після'],
          'моделі': models, 'помилки_перевірки': errors}
write(HERE / 'підсумок.json', result)
total = sum(x['ситуацій'] for x in models.values())
q = state['квота_після']
lines = ['# Живий прогін Gemini за підпискою — продовження /6', '',
         f'**ГОТОВО: {total} із 16 пар моделі й ситуації, {2 * total} проходів.** '
         f'До продовження було 12 пар; додано {len(added)}. Завершених ситуацій не повторювали.', '',
         f'Час продовження UTC: {read(HERE / "початок.json")["utc"]} — {state["кінець_utc"]}. '
         'Точний початок кожного браузерного запуску записаний у його `запуск.json`.', '',
         f'Квота Gemini Models на старті продовження: 91 % за п’ять годин, 36 % за тиждень; '
         f'після — {q["п’ять_годин"]["залишок"]} % і {q["тиждень"]["залишок"]} %. '
         'Показник груповий і округлений, його падіння не приписуємо лише нашому процесу. '
         f'Наступні скидання: {q["п’ять_годин"]["скидання"]} та {q["тиждень"]["скидання"]}.', '',
         'Лишилось:', '']
lines += [f'- {x["модель"]}: {x["ситуація"]} — два проходи.' for x in state['лишилось']] or ['- Немає.']
lines += ['', 'Після кожної ситуації перевірено межі наряду: не починати наступної нижче 10 % '
          'за п’ять годин або 20 % за тиждень; розпочату ситуацію доводити до двох проходів.', '',
         '[Наряд дослівно](продовження_6/НАРЯД.md), [попередній звіт](СПРОБА_6_ПЕРШЕ_ВІКНО.md), '
          '[машинний підсумок](продовження_6/підсумок.json), '
          '[квоти й час по ситуаціях](спроба_6/README.md).', '',
          'Жінка — скрипт зі словами першого прогону, за словом власника 14.11 07:08 UTC. '
          'Текст і порядок реплік перевірені за джерелом. Пропущені слова й дії записані у розбіжностях. '
          'Слова про образи стосуються першого прогону; вони не є оцінкою образів Gemini. '
          'Суддю призначає диспетчер окремо.', '',
          '| ситуація | Flash: введено / пропущено · розбіжностей | Hydrogen: введено / пропущено · розбіжностей |',
          '|---|---:|---:|']
scenes = sorted(set(s for m in models.values() for s in m['ситуації']))
for scene in scenes:
    cells = []
    for model in models.values():
        item = model['ситуації'].get(scene)
        cells.append(f'{item["слів_лягло"]} / {item["слів_пропущено"]} · {item["розбіжностей"]}' if item else 'ще не запускали')
    lines.append(f'| `{scene}` | ' + ' | '.join(cells) + ' |')
lines += ['', '| дані основних проходів | Flash | Hydrogen |', '|---|---:|---:|']
for key, label in [('викликів', 'викликів'), ('знімків', 'знімків 390×844'), ('введено', 'реплік введено'), ('пропущено', 'реплік пропущено'), ('роздуми', 'токенів роздумів')]:
    lines.append(f'| {label} | ' + ' | '.join(str(m[key]) for m in models.values()) + ' |')
for status in ['200', '403']:
    lines.append(f'| attico.ua: відповіді {status} | ' + ' | '.join(str(m['attico'].get(status, 0)) for m in models.values()) + ' |')
lines += ['', 'Статуси викликів моста: ' + '; '.join(
    name + ': ' + json.dumps(m['статуси_моста'], ensure_ascii=False)
    for name, m in models.items()) + '. Відмови й сирі відповіді, якщо були, перелічені в перевірці даних.']
lines += ['', 'Сирі входи й виходи — `<модель>/стенд/записи/*.json.gz`; фото з SHA256 — там само. '
          'Кожна ситуація має `хід.md`, знімки й `підсумок.json`; кожна модель — `руки.md`, '
          '`розбіжності.md`, `зведення.json`. Продукт — лише рука 1; мапи містять позиції й правила поломки руки 2. '
          'Повторний показ старих карток позначений за ідентифікатором прогону.', '',
          '[Перевірка Hydrogen](продовження_6/gemini-4-hydrogen/перевірка_даних.json) '
          'звіряє дослівність, порядок реплік, два проходи, знімки, сирі входи, архів фото, SHA256 '
          'і успішне читання доступних фото моделлю. '
          'Незмінені дані Flash перевірені [раніше](спроба_6/gemini-3.8-flash/перевірка_даних.json). '
          'Позиції 1–4 і перестановка рук перевірені для кожної групи; помилок повноти немає. '
          'Усі завершені інструментальні виклики agy — `read_file`.', '',
          'Збої з рядками консолі та сирими відповідями: '
          '[Flash](спроба_6/gemini-3.8-flash/збої.md), '
          '[Hydrogen](продовження_6/gemini-4-hydrogen/збої.md). '
          'Сторож worker лишився на 300 с. Без внутрішньої траси кроку `запити` причину мовчання '
          'до наступного HTTP не встановлено. Відсутній показ карток не зараховано як нове збирання.', '',
          '[agy models](спроба_6/відновлення_2_моделі.stdout.txt): продовжено `gemini-4-hydrogen-low`, '
          'найнижче зусилля тієї самої моделі, як у с1–с4. Еквівалентність CLI Low налаштуванню API не встановлена. '
          'Транспорт — підписка agy без платного ключа й моста власника: текст дослівно між маркерами, '
          'фото файлами `NN.ext` і посиланнями `@NN.ext`; модель читає їх через `read_file`. '
          'agy додає власний системний контекст та інструменти, адаптер — доручення. '
          'Стелі — 660 с зовні, 630 с CLI; `max_tokens` сторінки записується, але не обмежує CLI. '
          'Дозволи оболонки не розширено.', '',
          'Використано ту саму CI-сторінку серії: джерела збірки '
          '`8dafc1113ba09cdc5459cead2c0878fbc14b2b37`, main '
          '`855d862368d2ad8e120fd7b083ec5b854c8728e8`, SHA256 '
          '`890864aa7b59a89da48560a83f50f4123ad8131031b0acbf156bce2909b2ca94`. '
          'Перед запуском сторінку відновлено й звірено за SHA256; новішої збірки не підмішували. '
          'Main цього доручення — `c3da34578ee9ab30373c5e9fda506895c71ed1d8`; '
          'голова гілки на старті — у [метаданих](продовження_6/початок.json). '
          'Порти й час кожного нового запуску — у `спроба_6/gemini-4-hydrogen/<ситуація>/запуск.json`.', '',
          '[Середовище продовження](продовження_6/середовище.json): agy 1.5.9, Node v22.23.5, '
          'Python 3.12.10, Playwright 1.64.1; телефон 390×844, Chromium headless. '
          'Моделей GPU для наряду не завантажували. Власні процеси стенда й завершення — '
          'у [квитанції](продовження_6/завершення.json).', '',
          'Код продукту, прилади коренів, правила, `.github/` й адаптер обгортки не змінені. '
          'Нових вад поза мірилом не встановлено; оцінювання образів — окремим судом. '
          'Історія попередніх спроб і перерваного допоміжного с5 — у попередньому звіті.', '']
(BASE / 'README.md').write_text('\n'.join(lines), encoding='utf-8')
print(json.dumps({'пар': total, 'додано': len(added), 'лишилось': state['лишилось'], 'квота': q}, ensure_ascii=False))
