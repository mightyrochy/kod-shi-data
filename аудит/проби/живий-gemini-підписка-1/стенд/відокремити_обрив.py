"""Відокремити неповний запуск від основних даних перед новим повтором.

python відокремити_обрив.py <тека_моделі> <ситуація> <тека_архіву>
Усі переміщення перевіряються в межах теки проби, нічого не видаляється.
"""
from pathlib import Path
import json
import re
import shutil
import sys

model, scene, archive = Path(sys.argv[1]).resolve(), sys.argv[2], Path(sys.argv[3]).resolve()
base = Path(__file__).resolve().parent.parent
assert model.is_relative_to(base) and archive.is_relative_to(base)
assert not archive.exists(), 'Архів уже існує'
assert not (model / scene / 'підсумок.json').exists(), 'Завершену ситуацію не переміщуємо'
journal = model / 'стенд/журнал_моделі_продукту.jsonl'
rows = [json.loads(s) for s in journal.read_text(encoding='utf-8').splitlines()]
failed = [r for r in rows if r['прохід'].startswith(scene + ' · ')]
moves = [(model / scene, archive / scene),
         (model / 'стенд/службове' / scene, archive / 'стенд/службове' / scene),
         (model / 'стенд' / (scene + '.log'), archive / 'стенд' / (scene + '.log')),
         (base / 'спроба_6' / model.name / scene, archive / 'метадані')]
for row in failed:
    num = f'{row["н"]:04d}'
    moves.extend([(model / 'стенд/записи' / (num + '.json.gz'), archive / 'стенд/записи' / (num + '.json.gz')),
                  (model / 'стенд/записи/фото' / num, archive / 'стенд/записи/фото' / num)])
# Перевірка всіх кінцевих абсолютних адрес до першого переміщення.
for src, dst in moves:
    assert src.resolve().is_relative_to(base) and dst.resolve().is_relative_to(base), (src, dst)
    assert not dst.exists(), dst
archive.mkdir(parents=True)
for src, dst in moves:
    if src.exists():
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))
(archive / 'стенд/журнал_моделі_продукту.jsonl').write_text(
    ''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in failed), encoding='utf-8')
journal.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows if r not in failed), encoding='utf-8')
diffs = model / 'розбіжності.md'
if diffs.exists():
    shutil.copy2(diffs, archive / 'розбіжності_первісні.md')
    kept, skip = [], False
    for line in diffs.read_text(encoding='utf-8').splitlines(keepends=True):
        if re.match(r'^- с[1-8]_', line):
            skip = line.startswith('- ' + scene + ' · ')
        if not skip:
            kept.append(line)
    diffs.write_text(''.join(kept), encoding='utf-8')
(archive / 'ПРИМІТКА.md').write_text(
    '# Перерваний запуск с5\n\nПерший прохід завершив показ образів, другий перервано стендом: '
    '`page.screenshot: Timeout 15000ms exceeded`. Стек — у `с5_весілля_сестри/збій.txt`; '
    'усі знімки, слова, обміни, фото й сирі відповіді залишені тут без підміни. '
    'Це допоміжні дані, вони не входять до основної пари с5.\n\n'
    'Єдина правка стенда — timeout:0 у спільній функції знімка. Код продукту й стелі '
    'його worker не змінено. Основну пару повторено з початку на тому самому вході. '
    'Завершені с1, с2, с3 та с4 повторно не запускаються.\n', encoding='utf-8')
print('Відокремлено викликів:', len(failed), '; архів:', archive)
