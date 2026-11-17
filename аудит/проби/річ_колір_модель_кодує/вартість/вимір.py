"""Готує незмінні кадри й вимірює окреме читання галереї Codex за підпискою.

Не читає назв людей, ключів, свотчів і попередніх відповідей моделей.
"""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import urllib.request

ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[3]
ПРОБА = ТУТ.parent
ТИМЧАСОВА = КОРІНЬ.parent / 'tmp' / 'вартість'
МОДЕЛЬ = 'gpt-6.1-sol'
ДАНІ_ПРИЙМАННЯ = 'c7b37862c5195f823e0ef211cd8ecd718b498f95'
ТИПИ = {1: 'светр', 4: 'штани', 5: 'штани', 8: 'куртка', 11: 'сукня',
        13: 'штани', 17: 'сукня', 23: 'штани', 24: 'сукня', 31: 'сукня',
        32: 'джемпер', 33: 'сорочка', 40: 'пальто'}
ПРОХАННЯ = ('На всіх доданих кадрах галереї опиши колір цільової речі: {тип}. '
              'Назви відтінок і принт своїми словами українською, як для людини; '
              'у двоколірної речі назви обидва кольори. Відділяй тканину від тла, '
              'шкіри, інших речей, тіней, блиску та освітлення. Без словника, '
              'переліків, кодів і hex. Відповідь — лише JSON з полями '
              '"назва" та "принт" (null, коли принту немає). '
              'Працюй лише з доданими зображеннями, без інструментів, файлів та мережі.')


def записати(шлях, дані):
    """Зберігає JSON без BOM і без втрати українських літер."""
    шлях.parent.mkdir(parents=True, exist_ok=True)
    шлях.write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def підготувати():
    """Збирає лише номери, типи та кадри з дозволених джерел входу."""
    from PIL import Image
    вхід = json.loads((ПРОБА / 'наступний_вхід.json').read_text(encoding='utf-8'))
    речі = [dict(р, набір='sproba2') for р in вхід['речі']]
    with (КОРІНЬ / 'аудит/проби/річ_колір_приймання_1511/вибірка.tsv').open(encoding='utf-8') as ф:
        рядки = list(csv.DictReader(ф, delimiter='\t'))
    for номер, тип in ТИПИ.items():
        кадри = [{'файл': 'аудит/проби/річ_колір_перезбір_0411/' + р['фото'],
                   'sha256': р['sha256']} for р in рядки if int(р['номер']) == номер]
        речі.append({'набір': 'приймання13', 'номер': номер, 'тип': тип, 'кадри': кадри})
    відсутні = []
    for річ in речі:
        for і, кадр in enumerate(річ['кадри'], 1):
            ціль = ТИМЧАСОВА / f"{річ['набір']}-{річ['номер']:02d}-{і:02d}.jpg"
            if ціль.exists():
                кадр['підготовлений_sha256'] = hashlib.sha256(ціль.read_bytes()).hexdigest()
                continue
            if 'файл' in кадр:
                шлях = КОРІНЬ / кадр['файл']
                if not шлях.exists():
                    обʼєкт = subprocess.run(['git', 'show', ДАНІ_ПРИЙМАННЯ + ':' + кадр['файл']],
                                           cwd=КОРІНЬ, capture_output=True)
                    if обʼєкт.returncode:
                        відсутні.append(кадр['файл'])
                        continue
                    байти = обʼєкт.stdout
                    кадр['джерело_git'] = ДАНІ_ПРИЙМАННЯ
                else:
                    байти = шлях.read_bytes()
                if hashlib.sha256(байти).hexdigest() != кадр['sha256']:
                    raise ValueError(f'Змінився кадр {шлях}')
            else:
                with urllib.request.urlopen(urllib.request.Request(кадр['url'], headers={'User-Agent': 'Mozilla/5.0'}), timeout=60) as ф:
                    байти = ф.read()
                кадр['отриманий_sha256'] = hashlib.sha256(байти).hexdigest()
            ціль.parent.mkdir(parents=True, exist_ok=True)
            with Image.open(io.BytesIO(байти)) as з:
                з = з.convert('RGB')
                з.thumbnail((640, 640), Image.Resampling.LANCZOS)
                з.save(ціль, format='JPEG', quality=85)
            кадр['підготовлений_sha256'] = hashlib.sha256(ціль.read_bytes()).hexdigest()
    записати(ТУТ / 'вхід.json', {'речі': речі, 'відсутні': відсутні})
    print(f'Речей {len(речі)}, кадрів {sum(len(р["кадри"]) for р in речі)}, відсутніх {len(відсутні)}')


def прогнати(набір, номер):
    """Запускає послідовно окреме читання однієї галереї з точним лічильником CLI."""
    річ = next(р for р in json.loads((ТУТ / 'вхід.json').read_text(encoding='utf-8'))['речі']
               if р['набір'] == набір and р['номер'] == номер)
    ід = f'{набір}-{номер:02d}'
    вихід = ТУТ / 'сирі' / f'{ід}.json'
    if вихід.exists():
        raise ValueError(f'Вимір уже існує: {ід}')
    команда = [shutil.which('codex'), 'exec', '--ignore-user-config', '--skip-git-repo-check',
               '-C', str(ТИМЧАСОВА), '-s', 'read-only', '-m', МОДЕЛЬ,
               '-c', 'model_reasoning_effort="high"', '--json', '-o', str(ТИМЧАСОВА / f'{ід}.json')]
    for і, кадр in enumerate(річ['кадри'], 1):
        шлях = ТИМЧАСОВА / f'{набір}-{номер:02d}-{і:02d}.jpg'
        if not шлях.exists() or hashlib.sha256(шлях.read_bytes()).hexdigest() != кадр['підготовлений_sha256']:
            raise ValueError(f'Нема точного кадру {шлях}')
        команда.extend(['-i', str(шлях)])
    команда.append('-')
    початок = time.time()
    процес = subprocess.run(команда, input=ПРОХАННЯ.format(тип=річ['тип']), capture_output=True, text=True, encoding='utf-8')
    кінець = time.time()
    (ТИМЧАСОВА / f'{ід}.stdout.jsonl').write_text(процес.stdout, encoding='utf-8')
    (ТИМЧАСОВА / f'{ід}.stderr.txt').write_text(процес.stderr, encoding='utf-8')
    події = [json.loads(р) for р in процес.stdout.splitlines() if р.startswith('{')]
    потік = next((п['thread_id'] for п in події if п.get('type') == 'thread.started'), None)
    лічба = next((п.get('usage') for п in події if п.get('type') == 'turn.completed'), None)
    результат = {'набір': набір, 'номер': номер, 'модель': МОДЕЛЬ, 'режим': 'high',
                 'кадрів': len(річ['кадри']), 'початок_unix': початок, 'кінець_unix': кінець,
                 'секунд': кінець - початок, 'код_виходу': процес.returncode, 'потік': потік,
                 'лічильник_CLI': лічба, 'прохання': ПРОХАННЯ.format(тип=річ['тип'])}
    if процес.returncode == 0:
        результат['відповідь'] = json.loads((ТИМЧАСОВА / f'{ід}.json').read_text(encoding='utf-8'))
    else:
        результат['помилка'] = процес.stderr[-2500:]
    if потік:
        сесії = Path.home() / '.codex' / 'sessions'
        for файл in сесії.rglob(f'*{потік}*.jsonl'):
            події_рушія = [json.loads(р) for р in файл.read_text(encoding='utf-8').splitlines()]
            результат['події_лічильника'] = [п for п in події_рушія if п.get('type') == 'event_msg'
                 and п['payload'].get('type') == 'token_count']
    результат['виклики_інструментів'] = [п for п in події if п.get('item', {}).get('type')
                                        in ('command_execution', 'mcp_tool_call', 'web_search')]
    записати(вихід, результат)
    print(json.dumps({к: результат[к] for к in ['набір', 'номер', 'кадрів', 'секунд', 'лічильник_CLI', 'код_виходу']}, ensure_ascii=False), flush=True)
    if процес.returncode:
        raise SystemExit(процес.returncode)


def головна():
    """Вибирає підготовку кадрів або один вимір без неявного повторного прогону."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--підготувати', action='store_true')
    парсер.add_argument('--набір', choices=['sproba2', 'приймання13'])
    парсер.add_argument('--номер', type=int)
    парсер.add_argument('--усі', action='store_true')
    а = парсер.parse_args()
    if а.підготувати:
        підготувати()
    elif а.усі:
        вхід = json.loads((ТУТ / 'вхід.json').read_text(encoding='utf-8'))
        if вхід['відсутні']:
            raise ValueError('Пачка неповна: є відсутні кадри')
        for річ in вхід['речі']:
            if not (ТУТ / 'сирі' / f"{річ['набір']}-{річ['номер']:02d}.json").exists():
                прогнати(річ['набір'], річ['номер'])
    elif а.набір and а.номер:
        прогнати(а.набір, а.номер)
    else:
        парсер.error('Вкажіть --підготувати або --набір і --номер')


if __name__ == '__main__':
    головна()
