"""Пілот 5190: точні рядки → MamayLM → коди з цитатами, поза продуктом.

Без --виконати лише готує 81 контроль (frozen40 усередині), 97 рядків і
119 входжень. Мережа дозволена лише явним запуском через місцевий проксі.
Невідоме походження не дає прив'язки до речі; --лише-переклад дозволяє
виміряти тільки мовний розбір. Вікна, фото й каталоги прилад не змінює.
"""
import argparse
import datetime
import gzip
import hashlib
import json
import math
from pathlib import Path
import tempfile
import time
import urllib.request
import xml.etree.ElementTree as XML


КОРІНЬ = Path(__file__).resolve().parents[2]
ДАНІ = Path(__file__).with_name('рядки_5190')
МОДЕЛЬ = 'mamaylm-gemma-3-12b-it-v2.0'
ПРОКСІ = 'http://127.0.0.1:1235/v1/chat/completions'
ПРОТОКОЛ = '5190-rows-v1'
ПАРАМЕТРИ = {'temperature': 0, 'max_tokens': 4096, 'stream': False}
ПОЛЯ = ('Колір', '~Колір')  # Імена полів транспорту, не словник їхніх значень.


def відбиток(байти):
    """Повертає SHA256 точних байтів без нормалізації тексту."""
    return hashlib.sha256(байти).hexdigest()


def байти_json(дані):
    """Кодує стабільний JSON для відбитків та переносних артефактів."""
    return (json.dumps(дані, ensure_ascii=False, indent=2, allow_nan=False) + '\n').encode('utf-8')


def _пари(пари):
    """Відхиляє повторні ключі JSON замість мовчазного перезапису."""
    словник = {}
    for ключ, значення in пари:
        if ключ in словник:
            raise ValueError('Повторний ключ JSON: ' + ключ)
        словник[ключ] = значення
    return словник


def читати_json(текст):
    """Читає лише строгий JSON, без Markdown, NaN та повторних ключів."""
    def хибна_стала(значення):
        """Відхиляє нестандартну числову сталу."""
        raise ValueError('Не JSON-число: ' + значення)
    return json.loads(текст, object_pairs_hook=_пари, parse_constant=хибна_стала)


def зберегти(шлях, дані):
    """Атомарно зберігає артефакт, зокрема на Windows ноутбука."""
    шлях = Path(шлях)
    шлях.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=шлях.parent, delete=False) as файл:
        тимчасовий = Path(файл.name)
        файл.write(байти_json(дані))
    тимчасовий.replace(шлях)


def _поля(структура, ключі):
    """Вимагає точний набір полів об'єкта протоколу."""
    if not isinstance(структура, dict) or set(структура) != set(ключі):
        raise ValueError('Неочікувані або відсутні поля: ' + repr(ключі))


def _текст(значення):
    """Вимагає непорожній текст; його зміст код не тлумачить."""
    if not isinstance(значення, str) or not значення:
        raise ValueError('Потрібний непорожній рядок')


def контракт():
    """Читає версії промпту, схеми та чинний кодовий перелік."""
    схема_байти = (ДАНІ / 'відповідь.schema.json').read_bytes()
    промпт_байти = (ДАНІ / 'промпт.txt').read_bytes()
    схема = читати_json(схема_байти)
    коди = схема['properties']['rows']['items']['oneOf'][0]['properties']['variants']['items']['properties']['colors']['items']['properties']['code']['enum']
    чинна = читати_json((КОРІНЬ / 'джерела/внутрішня_мова.schema.json').read_bytes())
    if коди != [к for к in чинна['$defs']['thing']['properties']['color_name']['enum'] if к != 'unknown']:
        raise ValueError('Перелік кодів змінився; потрібна явна ревізія схеми пілота')
    версія = {'protocol': ПРОТОКОЛ, 'model': МОДЕЛЬ, 'schema_sha256': відбиток(схема_байти),
              'prompt_sha256': відбиток(промпт_байти), 'generation': ПАРАМЕТРИ}
    return схема, промпт_байти.decode('utf-8'), версія, set(коди)


def підготувати(корінь=КОРІНЬ):
    """Витягує лише фіксовані контроли; не розбирає значення кольорів."""
    джерело = читати_json((ДАНІ / 'контролі.json').read_bytes())
    контролі, заморожені = джерело['controls81'], джерело['frozen40']
    if len(set(контролі)) != len(контролі) or len(контролі) != 81 or len(заморожені) != 40 or len(set(заморожені)) != 40 or not set(заморожені) <= set(контролі):
        raise ValueError('Змінена вибірка 81/frozen40')
    сирі = (Path(корінь) / джерело['raw_path']).read_bytes()
    if відбиток(сирі) != джерело['raw_sha256']:
        raise ValueError('Raw-каталог не той, що зафіксовано для пілота')
    входження, знайдені = [], set()
    for річ in XML.fromstring(gzip.decompress(сирі)).iter('offer'):
        параметри = list(річ.findall('param'))
        крамниця = next((''.join(п.itertext()).strip().lower() for п in параметри
                        if п.get('name') in ('магазин', 'Магазин')), '')
        ід = річ.get('id') + '@' + крамниця
        if ід not in контролі:
            continue
        if ід in знайдені:
            raise ValueError('Повторний id контролю: ' + ід)
        знайдені.add(ід)
        for номер, параметр in enumerate(параметри):
            сирий = ''.join(параметр.itertext())
            if параметр.get('name') not in ПОЛЯ or not сирий.strip():
                continue
            входження.append({'occurrence_id': ід + '#' + str(номер), 'offer_id': ід,
                'product_url': річ.findtext('url'),
                'param_index': номер, 'field': параметр.get('name'), 'raw': сирий,
                'row_id': відбиток(сирий.encode('utf-8')), 'param_attributes': dict(параметр.attrib),
                'frozen40': ід in заморожені, 'source_kind': 'unknown',
                'source_object_id': None, 'evidence_ref': None,
                'admission': 'unknown', 'reason': 'missing_structural_provenance'})
    рядки = sorted({в['raw'] for в in входження})
    if знайдені != set(контролі) or len(входження) != джерело['expected_occurrences'] or len(рядки) != джерело['expected_raw_rows'] or відбиток(байти_json(рядки)) != джерело['rows_sha256']:
        raise ValueError('Склад 81 контролю / 119 входжень / 97 рядків змінився')
    return {'source': джерело, 'rows': [{'row_id': відбиток(р.encode('utf-8')), 'raw': р} for р in рядки],
            'occurrences': входження}


def допустити(входження, запис, посилання):
    """Судить структурні коди походження конкретного входження.

    Запис походить із окремо перевіреного адаптера/артефакту; цитата чи
    мітка «картка» не створює такого доказу. Код тут не перевіряє семантику
    адаптера, а вимагає точні id, значення та тип джерела.
    """
    _поля(запис, ('object_id', 'subject_id', 'kind', 'value', 'variant_id'))
    _текст(запис['object_id'])
    if запис['kind'] not in ('product_attribute', 'variant_attribute', 'review', 'recommendation', 'unknown'):
        raise ValueError('Невідомий код джерела')
    if запис['value'] != входження['raw'] or запис['subject_id'] != входження['offer_id']:
        raise ValueError('Доказ не належить цьому значенню або id речі')
    if запис['kind'] == 'variant_attribute':
        _текст(запис['variant_id'])
    elif запис['variant_id'] is not None:
        raise ValueError('Неочікуваний id варіанта')
    дозволено = запис['kind'] in ('product_attribute', 'variant_attribute')
    return dict(входження, source_kind=запис['kind'], source_object_id=запис['object_id'],
                evidence_ref=посилання, admission='admitted' if дозволено else 'unknown',
                reason='verified_structural_source' if дозволено else 'non_product_source')


def вузол(джерело, покажчик):
    """Переходить за JSON Pointer у збереженому структурному джерелі."""
    if покажчик == '':
        return джерело
    if not isinstance(покажчик, str) or not покажчик.startswith('/'):
        raise ValueError('Некоректний JSON Pointer джерела')
    for частина in покажчик[1:].split('/'):
        ключ = частина.replace('~1', '/').replace('~0', '~')
        джерело = джерело[int(ключ)] if isinstance(джерело, list) else джерело[ключ]
    return джерело


def походження(маніфест, шлях):
    """Під'єднує лише перевірені локальні докази; відсутнє лишає невідомим."""
    if шлях is None:
        return маніфест
    шлях = Path(шлях)
    журнал = читати_json(шлях.read_bytes())
    _поля(журнал, ('version', 'raw_sha256', 'entries'))
    if журнал['version'] != '5190-provenance-v1' or журнал['raw_sha256'] != маніфест['source']['raw_sha256']:
        raise ValueError('Докази від іншої версії або raw-каталогу')
    за_ід = {в['occurrence_id']: в for в in маніфест['occurrences']}
    бачені = set()
    for доказ in журнал['entries']:
        _поля(доказ, ('occurrence_id', 'row_id', 'artifact', 'artifact_sha256', 'object_id', 'review_ref'))
        ід = доказ['occurrence_id']
        if ід in бачені or ід not in за_ід or доказ['row_id'] != за_ід[ід]['row_id']:
            raise ValueError('Дубль, чужий id або застарілий рядок у доказах')
        бачені.add(ід)
        _текст(доказ['review_ref'])
        байти = (шлях.parent / доказ['artifact']).read_bytes()
        if відбиток(байти) != доказ['artifact_sha256']:
            raise ValueError('Змінився перевірений артефакт походження')
        артефакт = читати_json(байти)
        _поля(артефакт, ('version', 'source_ref', 'capture', 'records'))
        if артефакт['version'] != '5190-source-objects-v1':
            raise ValueError('Невідома схема структурного артефакту')
        _текст(артефакт['source_ref'])
        записи = [з for з in артефакт['records'] if з.get('object_id') == доказ['object_id']]
        if len(записи) != 1:
            raise ValueError('Не знайдено єдиний об’єкт джерела')
        запис = dict(записи[0])
        збережений = вузол(артефакт['capture'], запис.pop('capture_pointer'))
        if запис['kind'] in ('product_attribute', 'variant_attribute'):
            # Вузький структурний адаптер JSON-LD Product: пряма властивість
            # color того самого id/URL. Довільна мітка product не є доказом.
            if not isinstance(збережений, dict) or збережений.get('@type') != 'Product' or збережений.get('@id') != запис['object_id'] or збережений.get('url') != за_ід[ід]['product_url'] or збережений.get('color') != за_ід[ід]['raw'] or артефакт['source_ref'] != за_ід[ід]['product_url']:
                raise ValueError('Немає прямої властивості того самого Product/id/URL у збереженому джерелі')
            if запис['kind'] == 'variant_attribute' and запис['variant_id'] != збережений['@id']:
                raise ValueError('Id варіанта не збігається з об’єктом джерела')
        за_ід[ід] = допустити(за_ід[ід], запис, dict(доказ, source_ref=артефакт['source_ref']))
    return dict(маніфест, occurrences=list(за_ід.values()))


def _цитата(цитата, сирий):
    """Перевіряє дослівний збіг і повертає байтову позицію UTF-8.

    Це перевірка транспорту цитати, не відповідності коду змістові.
    """
    _текст(цитата)
    початок = сирий.find(цитата)
    if початок < 0:
        raise ValueError('Цитати немає в точному вхідному рядку')
    початок = len(сирий[:початок].encode('utf-8'))
    return [початок, початок + len(цитата.encode('utf-8'))]


def перевірити_відповідь(відповідь, рядки, коди):
    """Відхиляє чужі id, коди, форму, вигадані цитати й неповні пакети."""
    _поля(відповідь, ('rows',))
    if not isinstance(відповідь['rows'], list) or len(відповідь['rows']) != len(рядки):
        raise ValueError('Повернуто не весь пакет')
    за_ід = {р['row_id']: р['raw'] for р in рядки}
    бачені, результат = set(), {}
    for рядок in відповідь['rows']:
        _поля(рядок, ('row_id', 'status', 'relation', 'variants', 'unknown_reason'))
        ід = рядок['row_id']
        if not isinstance(ід, str) or ід not in за_ід or ід in бачені:
            raise ValueError('Чужий або повторний row_id')
        бачені.add(ід)
        if not isinstance(рядок['variants'], list):
            raise ValueError('Варіанти мають бути масивом')
        if рядок['status'] == 'unknown':
            if рядок['relation'] != 'unknown' or рядок['variants'] or рядок['unknown_reason'] not in ('ambiguous', 'no_colour', 'insufficient_context'):
                raise ValueError('Некоректна форма unknown')
        elif рядок['status'] == 'known':
            if рядок['unknown_reason'] != 'none' or рядок['relation'] not in ('single', 'combination', 'alternatives'):
                raise ValueError('Некоректна форма known')
            групи = рядок['variants']
            if not групи or (рядок['relation'] == 'alternatives' and len(групи) < 2) or (рядок['relation'] != 'alternatives' and len(групи) != 1):
                raise ValueError('Кількість варіантів не відповідає relation')
            for група in групи:
                _поля(група, ('quote', 'colors'))
                _цитата(група['quote'], за_ід[ід])
                if not isinstance(група['colors'], list) or not група['colors']:
                    raise ValueError('Варіант без кольорів')
                if (рядок['relation'] == 'single' and len(група['colors']) != 1) or (рядок['relation'] == 'combination' and len(група['colors']) < 2):
                    raise ValueError('Кількість кольорів не відповідає relation')
                for колір in група['colors']:
                    _поля(колір, ('code', 'quote'))
                    if not isinstance(колір['code'], str) or колір['code'] not in коди:
                        raise ValueError('Код кольору поза схемою')
                    _цитата(колір['quote'], група['quote'])
        else:
            raise ValueError('Невідомий status')
        групи_позицій = [_цитата(г['quote'], за_ід[ід]) for г in рядок['variants']]
        позиції = [[[п[0] + межа for межа in _цитата(к['quote'], г['quote'])] for к in г['colors']]
                   for г, п in zip(рядок['variants'], групи_позицій)]
        результат[ід] = {'answer': рядок, 'quote_utf8_spans': позиції, 'variant_utf8_spans': групи_позицій}
    return результат


def ключ_кешу(рядок, версія):
    """Версіонує переклад рядка незалежно від довіри до його входжень."""
    return відбиток(байти_json({'row_id': рядок['row_id'], **версія}))


def запит(рядки, схема, промпт):
    """Будує пакет точних рядків без читання вільних слів кодом."""
    схема_пакета = читати_json(байти_json(схема))
    перелік = схема_пакета['properties']['rows']
    перелік.update(minItems=len(рядки), maxItems=len(рядки))
    for форма in перелік['items']['oneOf']:
        форма['properties']['row_id'] = {'type': 'string', 'enum': [р['row_id'] for р in рядки]}
    return {'model': МОДЕЛЬ, **ПАРАМЕТРИ,
            'messages': [{'role': 'system', 'content': промпт},
                         {'role': 'user', 'content': json.dumps({'rows': рядки}, ensure_ascii=False)}],
            'response_format': {'type': 'json_schema', 'json_schema':
                               {'name': 'colour_rows_5190', 'strict': True, 'schema': схема_пакета}}}


def надіслати(тіло):
    """Викликає послідовний місцевий проксі тільки з явного живого шляху."""
    звернення = urllib.request.Request(ПРОКСІ, data=байти_json(тіло), headers={'Content-Type': 'application/json'})
    # Не використовуємо HTTP_PROXY середовища для місцевого стенда.
    клієнт = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with клієнт.open(звернення, timeout=900) as відповідь:
        return читати_json(відповідь.read())


def відповідь_пакета(відповідь, рядки, коди):
    """Перевіряє модель, кінець генерації й увесь повернутий пакет."""
    if not isinstance(відповідь, dict) or відповідь.get('model') != МОДЕЛЬ or len(відповідь.get('choices', [])) != 1 or відповідь['choices'][0].get('finish_reason') != 'stop':
        raise ValueError('Чужа модель, неповна або обірвана відповідь')
    return перевірити_відповідь(читати_json(відповідь['choices'][0]['message']['content']), рядки, коди)


def перевірити_кеш(кеш, рядок, версія, тека, коди, схема, промпт):
    """Звіряє кеш із точними байтами збереженого запиту й відповіді."""
    if кеш['identity'] != версія or кеш['raw'] != рядок['raw'] or кеш['row_id'] != рядок['row_id']:
        raise ValueError('Застарілий або чужий кеш')
    запис = читати_json((Path(тека) / 'requests' / (кеш['request_sha256'] + '.json')).read_bytes())
    if запис['identity'] != версія or запис['state'] != 'validated' or відбиток(байти_json(запис['request'])) != кеш['request_sha256']:
        raise ValueError('Немає точного походження кешу')
    запитані = читати_json(запис['request']['messages'][1]['content'])['rows']
    if рядок not in запитані or запис['request'] != запит(запитані, схема, промпт):
        raise ValueError('Рядка не було в збереженому запиті')
    for запитаний in запитані:
        _поля(запитаний, ('row_id', 'raw'))
        if запитаний['row_id'] != відбиток(запитаний['raw'].encode('utf-8')):
            raise ValueError('Пошкоджений відбиток рядка запиту')
    перевірене = відповідь_пакета(запис['response'], запитані, коди)[рядок['row_id']]
    if кеш['answer'] != перевірене['answer'] or кеш['quote_utf8_spans'] != перевірене['quote_utf8_spans'] or кеш['variant_utf8_spans'] != перевірене['variant_utf8_spans']:
        raise ValueError('Кеш не тотожний перевіреній відповіді')
    if type(кеш['batch_rows']) is not int or кеш['batch_rows'] != len(запитані) or not math.isfinite(кеш['batch_elapsed_s']) or кеш['batch_elapsed_s'] < 0 or кеш['batch_elapsed_s'] != запис['batch_elapsed_s'] or кеш['amortized_s'] != кеш['batch_elapsed_s'] / кеш['batch_rows'] or кеш['timing_kind'] != 'batch_wall_equal_share':
        raise ValueError('Пошкоджений час кешу')
    return dict(кеш, cache_hit=True)


def приєднати(маніфест, переклади):
    """Повертає кандидати лише для доведених входжень; варіант не обирає."""
    результат = []
    for входження in маніфест['occurrences']:
        переклад = переклади.get(входження['row_id'])
        відомо = переклад is not None and переклад['answer']['status'] == 'known'
        допустиме = входження['admission'] == 'admitted' and відомо
        результат.append({'occurrence_id': входження['occurrence_id'], 'row_id': входження['row_id'],
            'admission': входження['admission'], 'source': входження['evidence_ref'],
            'state': 'candidate' if допустиме else 'unknown',
            'reason': 'requires_semantic_and_photo_review' if допустиме else входження['reason'] if not входження['admission'] == 'admitted' else 'translation_unknown',
            'variants': переклад['answer']['variants'] if допустиме else []})
    return результат


def виконати(маніфест, тека, пакет=4, транспорт=надіслати, лише_переклад=False):
    """Послідовно перекладає нові рядки; збій зупиняє прогін без повтору.

    Час рядка — явно позначена рівна частка wall-time пакета, не окрема
    затримка моделі. Кеш зберігає сирий запит/відповідь, версії та джерело.
    """
    if type(пакет) is not int or not 1 <= пакет <= 8:
        raise ValueError('Пакет має містити від 1 до 8 рядків')
    if not лише_переклад and any(в['admission'] != 'admitted' for в in маніфест['occurrences']):
        raise ValueError('Походження не доведене: дозволений лише явний --лише-переклад')
    схема, промпт, версія, коди = контракт()
    тека = Path(тека)
    тека.mkdir(parents=True, exist_ok=True)
    замок = тека / '.5190.lock'
    # Власник знімає залишений після аварії замок лише після перевірки процесу.
    with замок.open('x', encoding='utf-8') as файл:
        файл.write(datetime.datetime.now(datetime.timezone.utc).isoformat())
    результати, нові, виклики, час_пакетів = {}, [], 0, 0.0
    try:
        зберегти(тека / 'звіт.json', {'state': 'started', 'identity': версія, 'runtime_applied': False})
        for рядок in маніфест['rows']:
            шлях = тека / 'cache' / (ключ_кешу(рядок, версія) + '.json')
            if not шлях.exists():
                нові.append(рядок)
                continue
            кеш = читати_json(шлях.read_bytes())
            результати[рядок['row_id']] = перевірити_кеш(кеш, рядок, версія, тека, коди, схема, промпт)
        нові_ід = {р['row_id'] for р in нові}
        for шлях in (тека / 'requests').glob('*.json'):
            спроба = читати_json(шлях.read_bytes())
            if спроба['identity'] == версія:
                попередні = читати_json(спроба['request']['messages'][1]['content'])['rows']
                if any(р['row_id'] in нові_ід for р in попередні):
                    raise ValueError('Рядок уже мав спробу без повного кешу; потрібен розбір збою, не автоматичний повтор')
        зберегти(тека / 'маніфест.json', маніфест)
        for початок in range(0, len(нові), пакет):
            рядки = нові[початок:початок + пакет]
            тіло = запит(рядки, схема, промпт)
            ід_запиту = відбиток(байти_json(тіло))
            слід = тека / 'requests' / (ід_запиту + '.json')
            if слід.exists():
                raise ValueError('Пакет уже мав спробу без повного кешу; потрібен розбір збереженого збою')
            запис = {'identity': версія, 'request': тіло, 'input_source': маніфест['source'],
                     'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': 'started'}
            зберегти(слід, запис)
            старт = time.monotonic()
            try:
                виклики += 1
                відповідь = транспорт(тіло)
                час = time.monotonic() - старт
                запис.update(response=відповідь, batch_elapsed_s=час)
                перевірені = відповідь_пакета(відповідь, рядки, коди)
                час_пакетів += час
                запис['state'] = 'validated'
                зберегти(слід, запис)
            except Exception as помилка:
                запис.update(state='failed', error=str(помилка), batch_elapsed_s=time.monotonic() - старт)
                зберегти(слід, запис)
                raise
            for рядок in рядки:
                кеш = {**перевірені[рядок['row_id']], 'row_id': рядок['row_id'], 'raw': рядок['raw'],
                       'identity': версія, 'request_sha256': ід_запиту, 'input_source': маніфест['source'],
                       'batch_elapsed_s': час, 'batch_rows': len(рядки), 'amortized_s': час / len(рядки),
                       'timing_kind': 'batch_wall_equal_share', 'created_utc': запис['started_utc']}
                зберегти(тека / 'cache' / (ключ_кешу(рядок, версія) + '.json'), кеш)
                результати[рядок['row_id']] = dict(кеш, cache_hit=False)
            зберегти(тека / 'переклади.json', list(результати.values()))
        звіт = {'state': 'completed', 'mode': 'translation_only' if лише_переклад else 'provenance_checked_translation',
                'identity': версія, 'raw_rows': len(маніфест['rows']), 'raw_occurrences': len(маніфест['occurrences']),
                'admitted_occurrences': sum(в['admission'] == 'admitted' for в in маніфест['occurrences']),
                'unknown_provenance': sum(в['admission'] != 'admitted' for в in маніфест['occurrences']),
                'requests_this_run': виклики, 'batch_wall_s_this_run': час_пакетів,
                'cache_hits': sum(р['cache_hit'] for р in результати.values()),
                'known_rows': sum(р['answer']['status'] == 'known' for р in результати.values()),
                'unknown_rows': sum(р['answer']['status'] == 'unknown' for р in результати.values()),
                'semantic_review': 'pending', 'photo_review': 'not_performed', 'runtime_applied': False}
        зберегти(тека / 'переклади.json', list(результати.values()))
        зберегти(тека / 'входження.json', приєднати(маніфест, результати))
        зберегти(тека / 'звіт.json', звіт)
        return звіт
    except Exception as помилка:
        зберегти(тека / 'звіт.json', {'state': 'failed', 'error': str(помилка), 'identity': версія,
                 'requests_this_run': виклики, 'validated_rows': len(результати), 'runtime_applied': False})
        raise
    finally:
        замок.unlink()


def головна():
    """Готує файли або явно запускає пілот на місцевому проксі ноутбука."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--вихід', type=Path, required=True)
    парсер.add_argument('--походження', type=Path)
    парсер.add_argument('--пакет', type=int, default=4)
    парсер.add_argument('--виконати', action='store_true')
    парсер.add_argument('--лише-переклад', action='store_true')
    арг = парсер.parse_args()
    try:
        маніфест = походження(підготувати(), арг.походження)
        контракт()
        звіт = {'mode': 'prepared', 'controls': len(маніфест['source']['controls81']),
                'frozen_subset': len(маніфест['source']['frozen40']), 'raw_rows': len(маніфест['rows']),
                'raw_occurrences': len(маніфест['occurrences']),
                'admitted_occurrences': sum(в['admission'] == 'admitted' for в in маніфест['occurrences']),
                'unknown_provenance': sum(в['admission'] != 'admitted' for в in маніфест['occurrences']),
                'requests_this_run': 0, 'runtime_applied': False}
        if арг.виконати:
            звіт = виконати(маніфест, арг.вихід, арг.пакет, лише_переклад=арг.лише_переклад)
        else:
            if (арг.вихід / '.5190.lock').exists():
                raise ValueError('У цій теці вже працює пілот')
            зберегти(арг.вихід / 'маніфест.json', маніфест)
            зберегти(арг.вихід / 'звіт_підготовки.json', звіт)
        print(json.dumps(звіт, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as помилка:
        print('ЗБІЙ ПІЛОТА 5190: ' + str(помилка))
        return 1


if __name__ == '__main__':
    raise SystemExit(головна())
