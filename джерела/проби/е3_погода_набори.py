"""Повний каталог і граничні входи погодних гілок для порівняння ваги."""
import gzip, json, os, pathlib


def набори():
    """Віддати ті самі входи без моделі: кожна річ × кожна погодна смуга."""
    import feed as Ф
    import outfit as О
    import сценарій as С
    import trace as Т
    тека = pathlib.Path(__file__).resolve().parent
    for випадок in json.loads((тека / 'дані/е3_погода.json').read_text(encoding='utf-8')):
        yield випадок['назва'], випадок['функція'], випадок['args'], випадок.get('kwargs', {})
    кеш = pathlib.Path(os.environ['TMP']) / 'е3_каталог.json.gz'
    if not кеш.exists():
        каталог = Ф.база_прогону(Ф.каталог_на_диску('каталог_повний.xml'), ліміт_фото=0)['каталог']
        with gzip.open(кеш, 'wt', encoding='utf-8') as ф:
            json.dump(каталог, ф, ensure_ascii=False)
    else:
        with gzip.open(кеш, 'rt', encoding='utf-8') as ф:
            каталог = json.load(ф)
    print('каталог', len(каталог), flush=True)
    for р in каталог:
        Е = О.елементи([р], стан='надворі')
        for смуга in С.СМУГИ_ПОГОДИ:
            назва = str(р['id']) + '@' + смуга
            yield назва, 'сезон_і_погода', [[р]], dict(смуга_погоди=смуга, опади='дощ', реагенти=True)
            yield назва, 'погода', [Е], dict(речі=[р], смуга_погоди=смуга, опади='дощ',
                                          сонце=True, смуга_вітру='strong', стан='надворі')
            yield назва, 'теплові_знахідки', [[р]], dict(смуга_погоди=смуга)
            Т.ЗАПИСИ.clear()
