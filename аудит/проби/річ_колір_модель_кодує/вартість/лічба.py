"""Лічить каталог зафіксованого main та зводить виміри без модельних викликів."""
import argparse
from collections import Counter
import contextlib
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import statistics as ст
import subprocess
import sys

ТУТ = Path(__file__).resolve().parent
КОРІНЬ = ТУТ.parents[3]
MAIN = '8238cb365a24c8ab053d19b67fb7a595127a4476'


def записати(імʼя, дані):
    """Зберігає відтворювані числа в UTF-8."""
    (ТУТ / імʼя).write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def каталог():
    """Рахує галереї всіх оферів штатним читачем main після його чистки й показу."""
    тмп = КОРІНЬ.parent / 'tmp' / 'вартість' / 'каталог'
    тмп.mkdir(parents=True, exist_ok=True)
    джерело = 'каталог_повний.xml.gz'
    архів = subprocess.check_output(['git', 'show', MAIN + ':' + джерело], cwd=КОРІНЬ)
    шлях = тмп / 'каталог_повний.xml'
    gz = шлях.with_suffix('.xml.gz')
    if not gz.exists() or gz.read_bytes() != архів:
        gz.write_bytes(архів)
        шлях.write_bytes(gzip.decompress(архів))
    файли = ['джерела/фід_розбір.py', 'джерела/фід_слот.py', 'джерела/фід_фото.py', 'джерела/чистка_каталогу.py',
             'джерела/фід_каталог.py']
    for імʼя in файли:
        if (КОРІНЬ / імʼя).read_bytes() != subprocess.check_output(['git', 'show', MAIN + ':' + імʼя], cwd=КОРІНЬ):
            raise ValueError(f'Код читача не збігається з main: {імʼя}')
    sys.path.insert(0, str(КОРІНЬ / 'джерела'))
    from фід_каталог import каталог_на_диску
    from фід_розбір import читати_yml, побудувати_запис_речі
    from фід_слот import розкласти_по_слотах
    cwd = os.getcwd()
    try:
        os.chdir(КОРІНЬ / 'джерела')
        with contextlib.redirect_stdout(io.StringIO()):
            офери, _ = читати_yml(каталог_на_диску(str(шлях)))
    finally:
        os.chdir(cwd)
    for офер in офери:
        офер['запис_речі'] = побудувати_запис_речі(офер)
    слоти, _ = розкласти_по_слотах(офери)
    варіанти = [о for група in слоти.values() for о in група]
    кадри = [len(о.get('фото') or []) for о in варіанти]
    дані = {'main': MAIN, 'джерело': джерело, 'git_blob': subprocess.check_output(
        ['git', 'rev-parse', MAIN + ':' + джерело], cwd=КОРІНЬ, text=True).strip(),
        'sha256_архіву': hashlib.sha256(архів).hexdigest(),
        'одиниця': 'офер (варіант) після штатної чистки, накладання показу й розкладання за слотами',
        'оферів_до_розкладання':len(офери),
        'варіантів_усього': len(кадри), 'варіантів_з_галереєю': sum(к > 0 for к in кадри),
        'кадрів_усього': sum(кадри), 'кадрів_до_трьох': sum(min(3, к) for к in кадри),
        'гістограма_кадрів': dict(sorted(Counter(кадри).items()))}
    дані['середнє_кадрів_з_галереєю'] = дані['кадрів_усього'] / дані['варіантів_з_галереєю']
    записати('каталог.json', дані)
    print(json.dumps(дані, ensure_ascii=False))


def звести():
    """Зводить 53 незалежні читання та арифметичні оцінки повної й скороченої галерей."""
    рядки = sorted((json.loads(п.read_text(encoding='utf-8')) for п in (ТУТ / 'сирі').glob('*.json')),
                    key=lambda р: (р['набір'] != 'sproba2', р['номер']))
    очікувані = {('sproba2', н) for н in range(1, 41)} | {('приймання13', н) for н in
                     [1, 4, 5, 8, 11, 13, 17, 23, 24, 31, 32, 33, 40]}
    вхід = {(р['набір'], р['номер']): р for р in json.loads((ТУТ / 'вхід.json').read_text(encoding='utf-8'))['речі']}
    if {(р['набір'], р['номер']) for р in рядки} != очікувані or len(рядки) != 53:
        raise ValueError('Потрібно рівно 40 + 13 вимірів')
    for р in рядки:
        if р['контекст_рушія'] != {'model': 'gpt-6.1-sol', 'effort': 'high'}:
            raise ValueError('Модель чи режим не відповідають наряду')
        if р['кадрів'] != len(вхід[р['набір'], р['номер']]['кадри']):
            raise ValueError('Лічба кадрів розійшлася з входом')
        if р['код_виходу'] or not р['лічильник_CLI'] or р['виклики_інструментів']:
            raise ValueError(f'Невдале чи неізольоване читання: {р["набір"]} {р["номер"]}')
        п = р['події_лічильника'][-1]['payload']['info']['total_token_usage']
        if any(п[к] != р['лічильник_CLI'][к] for к in р['лічильник_CLI']):
            raise ValueError('Лічильники JSONL і turn.completed не збігаються')
    with (ТУТ / 'назви_сильної_моделі.tsv').open('w', encoding='utf-8', newline='') as ф:
        п = csv.writer(ф, delimiter='\t', lineterminator='\n')
        п.writerow(['набір', 'номер', 'назва', 'принт'])
        п.writerows((р['набір'], р['номер'], р['відповідь']['назва'], р['відповідь']['принт'] or '') for р in рядки)
    with (ТУТ / 'виміри.tsv').open('w', encoding='utf-8', newline='') as ф:
        п = csv.writer(ф, delimiter='\t', lineterminator='\n')
        п.writerow(['набір', 'номер', 'кадрів', 'вхід', 'кешований_вхід', 'вихід_разом_з_міркуванням', 'міркування', 'секунд'])
        п.writerows((р['набір'], р['номер'], р['кадрів'], р['лічильник_CLI']['input_tokens'],
           р['лічильник_CLI']['cached_input_tokens'], р['лічильник_CLI']['output_tokens'],
           р['лічильник_CLI']['reasoning_output_tokens'], р['секунд']) for р in рядки)
    x = [р['кадрів'] for р in рядки]
    y = [р['лічильник_CLI']['input_tokens'] for р in рядки]
    вихід = [р['лічильник_CLI']['output_tokens'] for р in рядки]
    b = sum((к - ст.mean(x)) * (т - ст.mean(y)) for к, т in zip(x, y)) / sum((к - ст.mean(x)) ** 2 for к in x)
    a = ст.mean(y) - b * ст.mean(x)
    cat = json.loads((ТУТ / 'каталог.json').read_text(encoding='utf-8'))
    n = cat['варіантів_з_галереєю']
    оцінки = {}
    for назва, кадрів in [('повна_галерея', cat['кадрів_усього']), ('до_трьох_кадрів', cat['кадрів_до_трьох'])]:
        оцінки[назва] = {'варіантів': n, 'кадрів': кадрів, 'вхідних_токенів': a*n + b*кадрів,
                         'вихідних_токенів': ст.mean(вихід)*n,
                         'токенів_разом': (a+ст.mean(вихід))*n + b*кадрів,
                         'тижневих_квот': None, 'календарних_діб_за_квотою': None}
    квоти = [п['payload']['rate_limits']['primary'] for р in рядки for п in р['події_лічильника']]
    знімок = json.loads((ТУТ / 'квота.json').read_text(encoding='utf-8'))
    знімок['після_останнього_завершеного_читання'] = max(рядки, key=lambda р: р['кінець_unix'])['події_лічильника'][-1]
    знімок['завершено_речей'] = len(рядки)
    записати('квота.json', знімок)
    дані = {'речей':len(рядки), 'кадрів':sum(x), 'вхідних_токенів':sum(y), 'вихідних_токенів':sum(вихід),
        'вхід_медіана':ст.median(y), 'вхід_максимум':max(y), 'вихід_медіана':ст.median(вихід),
        'вихід_максимум':max(вихід), 'разом_медіана':ст.median(а+б for а,б in zip(y,вихід)),
        'разом_максимум':max(а+б for а,б in zip(y,вихід)),
        'секунд_сума':sum(р['секунд'] for р in рядки), 'секунд_медіана':ст.median(р['секунд'] for р in рядки),
        'кешованих_вхідних_токенів':sum(р['лічильник_CLI']['cached_input_tokens'] for р in рядки),
        'секунд_від_першого_початку_до_останнього_кінця':max(р['кінець_unix'] for р in рядки)-min(р['початок_unix'] for р in рядки),
        'квота_використано_перше':квоти[0]['used_percent'], 'квота_використано_останнє':квоти[-1]['used_percent'],
        'квота_період_хвилин':квоти[0]['window_minutes'], 'квота_скидання_unix':квоти[0]['resets_at'],
        'квота_на_річ': None, 'квота_обмеження':'Різниця показів не перевищує крок показу; це не нуль витрат. Лічильник спільний для акаунта.',
        'арифметика':{'вхід_a':a,'вхід_b_на_кадр':b,'вихід_середній':ст.mean(вихід),
                       'вхід_MAE':ст.mean(abs(т-a-b*к) for к,т in zip(x,y)),
                       'R2':1-sum((т-a-b*к)**2 for к,т in zip(x,y))/sum((т-ст.mean(y))**2 for т in y)}, 'каталог':оцінки}
    записати('підсумок.json', дані)
    print(json.dumps(дані, ensure_ascii=False))


def головна():
    """Виконує явно обрану лічбу без повторного читання фото моделлю."""
    п = argparse.ArgumentParser(description=__doc__)
    п.add_argument('--каталог', action='store_true')
    а = п.parse_args()
    каталог() if а.каталог else звести()


if __name__ == '__main__':
    головна()
