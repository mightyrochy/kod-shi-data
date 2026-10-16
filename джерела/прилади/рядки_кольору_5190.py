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
import журнал_рядків_5190 as Ж


КОРІНЬ = Path(__file__).resolve().parents[2]
ДАНІ = Path(__file__).with_name('рядки_5190')
МОДЕЛЬ = 'mamaylm-gemma-3-12b-it-v2.0'
ПРОКСІ = 'http://127.0.0.1:1235/v1/chat/completions'
ПРОТОКОЛ = '5190-rows-v3'
ПРОТОКОЛ_ПРОКСІ = '5190-once-v1'
ПАРАМЕТРИ = {'temperature': 0, 'max_tokens': 4096, 'stream': False}
ПОЛЯ = ('Колір', '~Колір')  # Імена полів транспорту, не словник їхніх значень.
# Коди пілота понад чинний перелік продукту: шавлія (рядок 6423). Вікно коду — за вжитком
# (п.9, наряд ВІКНА-5663); до каталогу код іде лише кроком підключення 5190.
ДОДАНІ_КОДИ = ('sage',)


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
    форми = схема['properties']['rows']['items']['oneOf']
    переліки = [ф['properties']['variants']['items']['properties']['colors']['items']['properties']['code']['enum']
                for ф in форми if ф['properties']['status']['const'] == 'known']
    коди = переліки[0]
    if any(п != коди for п in переліки):
        raise ValueError('Кодові переліки форм схеми розійшлися')
    чинна = читати_json((КОРІНЬ / 'джерела/внутрішня_мова.schema.json').read_bytes())
    продукт = [к for к in чинна['$defs']['thing']['properties']['color_name']['enum'] if к != 'unknown']
    if [к for к in коди if к not in ДОДАНІ_КОДИ] != продукт or not set(ДОДАНІ_КОДИ) <= set(коди):
        raise ValueError('Перелік кодів змінився; потрібна явна ревізія схеми пілота')
    версія = {'protocol': ПРОТОКОЛ, 'model': МОДЕЛЬ, 'schema_sha256': відбиток(схема_байти),
              'prompt_sha256': відбиток(промпт_байти), 'generation': ПАРАМЕТРИ}
    return схема, промпт_байти.decode('utf-8'), версія, set(коди)


def попередні_спроби():
    """Відновлює відомі фактичні спроби з точних артефактів ноутбука."""
    індекс = читати_json((ДАНІ / 'попередні_спроби.json').read_bytes())
    рядки = {}
    for доказ in індекс['records']:
        байти = (ДАНІ / доказ['file']).read_bytes()
        if відбиток(байти) != доказ['sha256']:
            raise ValueError('Змінено артефакт попереднього фактичного виклику')
        запис = читати_json(байти)
        if відбиток(байти_json(запис['request'])) != доказ['request_sha256']:
            raise ValueError('Хибний відбиток запиту історичної спроби')
        for рядок in читати_json(запис['request']['messages'][1]['content'])['rows']:
            if рядок['row_id'] != відбиток(рядок['raw'].encode('utf-8')):
                raise ValueError('Хибний row_id історичної спроби')
            дані = рядки.setdefault(рядок['row_id'], dict(рядок, attempts=[]))
            дані['attempts'].append({'request_sha256': доказ['request_sha256'], 'identity': запис['identity'],
                'artifact_sha256': доказ['sha256'],
                'source_ref': доказ.get('source_commit', індекс['source_commit']) + ':' + доказ['source_path']})
    return list(рядки.values())


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


def _позиції(цитати, сирий):
    """Дає кожній цитаті власне незайняте входження в тексті; байти UTF-8.

    Два варіанти не ділять один фрагмент, два коди — одну цитату (рядок 6420).
    Це перевірка транспорту цитат, не відповідності коду змістові.
    """
    зайняті, позиції = [], []
    for цитата in цитати:
        _текст(цитата)
        початок = сирий.find(цитата)
        if початок < 0:
            raise ValueError('Цитати немає в точному вхідному рядку')
        while початок >= 0 and any(початок < кінець and перший < початок + len(цитата) for перший, кінець in зайняті):
            початок = сирий.find(цитата, початок + 1)
        if початок < 0:
            raise ValueError('Цитата повторює вже зайнятий фрагмент')
        зайняті.append((початок, початок + len(цитата)))
        байт = len(сирий[:початок].encode('utf-8'))
        позиції.append([байт, байт + len(цитата.encode('utf-8'))])
    return позиції


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
            коди_цитат = {}
            for група in групи:
                _поля(група, ('quote', 'colors'))
                if not isinstance(група['colors'], list) or not група['colors']:
                    raise ValueError('Варіант без кольорів')
                if (рядок['relation'] == 'single' and len(група['colors']) != 1) or (рядок['relation'] == 'combination' and len(група['colors']) < 2):
                    raise ValueError('Кількість кольорів не відповідає relation')
                for колір in група['colors']:
                    _поля(колір, ('code', 'quote'))
                    if not isinstance(колір['code'], str) or колір['code'] not in коди:
                        raise ValueError('Код кольору поза схемою')
                    if коди_цитат.setdefault(колір['quote'], колір['code']) != колір['code']:
                        raise ValueError('Та сама цитата отримала різні коди в одному рядку')
        else:
            raise ValueError('Невідомий status')
        групи_позицій = _позиції([г['quote'] for г in рядок['variants']], за_ід[ід])
        позиції = [[[п[0] + межа for межа in м] for м in _позиції([к['quote'] for к in г['colors']], г['quote'])]
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
    # Не використовуємо HTTP_PROXY середовища для місцевого стенда.
    клієнт = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    адреса = ПРОКСІ.removesuffix('/v1/chat/completions') + '/.well-known/lyusterko-5190'
    with клієнт.open(urllib.request.Request(адреса), timeout=10) as відповідь:
        можливість = читати_json(відповідь.read())
    if можливість != {'protocol': ПРОТОКОЛ_ПРОКСІ, 'post_retries': 0}:
        raise ValueError('Проксі не підтвердив заборону повторів; POST не надіслано')
    звернення = urllib.request.Request(ПРОКСІ, data=байти_json(тіло),
                 headers={'Content-Type': 'application/json', 'X-Lyusterko-Once': ПРОТОКОЛ_ПРОКСІ})
    with клієнт.open(звернення, timeout=900) as відповідь:
        return читати_json(відповідь.read())


def відповідь_пакета(відповідь, рядки, коди):
    """Перевіряє конверт, потім кожний рядок незалежно, без ремонту змісту."""
    if not isinstance(відповідь, dict) or відповідь.get('model') != МОДЕЛЬ or len(відповідь.get('choices', [])) != 1 or відповідь['choices'][0].get('finish_reason') != 'stop':
        raise ValueError('Чужа модель, неповна або обірвана відповідь')
    дані = читати_json(відповідь['choices'][0]['message']['content'])
    _поля(дані, ('rows',))
    if not isinstance(дані['rows'], list):
        raise ValueError('Пакет rows не є масивом')
    очікувані = {р['row_id']: р for р in рядки}
    згруповані, чужі = {}, []
    for запис in дані['rows']:
        ід = запис.get('row_id') if isinstance(запис, dict) else None
        if not isinstance(ід, str) or ід not in очікувані:
            чужі.append(запис)
        else:
            згруповані.setdefault(ід, []).append(запис)
    валідні, відхилені = {}, {}
    for ід, вхід in очікувані.items():
        записи = згруповані.get(ід, [])
        try:
            if len(записи) != 1:
                raise ValueError('Очікується рівно один рядок цього row_id, отримано ' + str(len(записи)))
            валідні.update(перевірити_відповідь({'rows': записи}, [вхід], коди))
        except (ValueError, TypeError, KeyError) as помилка:
            відхилені[ід] = {'row_id': ід, 'error': str(помилка), 'actual': записи,
                'expected': 'unknown:0 variants; single:1 variant/1 color; combination:1 variant/2+ colors; alternatives:2+ variants'}
    return {'valid': валідні, 'rejected': відхилені, 'unexpected_rows': чужі}


def перевірити_кеш(кеш, рядок, версія, тека, коди, схема, промпт):
    """Звіряє кеш із точними байтами збереженого запиту й відповіді."""
    if кеш['identity'] != версія or кеш['raw'] != рядок['raw'] or кеш['row_id'] != рядок['row_id']:
        raise ValueError('Застарілий або чужий кеш')
    запис = читати_json((Path(тека) / 'requests' / кеш['request_file']).read_bytes())
    if запис['identity'] != версія or запис['state'] not in ('validated', 'partial') or відбиток(байти_json(запис['request'])) != кеш['request_sha256']:
        raise ValueError('Немає точного походження кешу')
    запитані = читати_json(запис['request']['messages'][1]['content'])['rows']
    if рядок not in запитані or запис['request'] != запит(запитані, схема, промпт):
        raise ValueError('Рядка не було в збереженому запиті')
    for запитаний in запитані:
        _поля(запитаний, ('row_id', 'raw'))
        if запитаний['row_id'] != відбиток(запитаний['raw'].encode('utf-8')):
            raise ValueError('Пошкоджений відбиток рядка запиту')
    перевірене = відповідь_пакета(запис['response'], запитані, коди)['valid'][рядок['row_id']]
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


def виконати(маніфест, тека, пакет=2, транспорт=надіслати, лише_переклад=False, дозвіл=None):
    """Перекладає тільки нові рядки; журнал спроб спільний для всіх тек.

    Повтор потребує окремого наряду з точною історією та новою identity.
    Помилка одного рядка не губить валідних сусідів і не ремонтується кодом.
    """
    if type(пакет) is not int or not 1 <= пакет <= 2:
        raise ValueError('Пакет має містити один або два рядки')
    if not лише_переклад and any(в['admission'] != 'admitted' for в in маніфест['occurrences']):
        raise ValueError('Походження не доведене: дозволений лише явний --лише-переклад')
    if дозвіл and not лише_переклад:
        raise ValueError('Поточний наряд повтору стосується лише мовного виміру')
    if дозвіл and дозвіл.get('requires_all_provenance') and any(в['admission'] != 'admitted' for в in маніфест['occurrences']):
        raise ValueError('Наряд повтору вимагає спершу підтвердити походження всіх входжень')
    схема, промпт, версія, коди = контракт()
    тека = Path(тека)
    тека.mkdir(parents=True, exist_ok=True)
    with Ж.відкрити(попередні_спроби()) as журнал:
        результати, відхилені, нові = {}, {}, []
        виклики, час_пакетів, чужі = 0, 0.0, []
        try:
            зберегти(тека / 'звіт.json', {'state': 'started', 'identity': версія, 'once_ledger': str(журнал.шлях), 'runtime_applied': False})
            # Старі локальні requests також не можна обійти новою версією.
            for шлях in (тека / 'requests').glob('*.json'):
                запис = читати_json(шлях.read_bytes())
                ід_запиту = відбиток(байти_json(запис['request']))
                for рядок in читати_json(запис['request']['messages'][1]['content'])['rows']:
                    попередні = журнал.попередні(рядок)
                    if not any(с['request_sha256'] == ід_запиту for с in попередні):
                        дані = журнал.дані['rows'].setdefault(рядок['row_id'], {'raw': рядок['raw'], 'attempts': []})
                        дані['attempts'].append({'request_sha256': ід_запиту, 'identity': запис['identity'], 'state': 'legacy_needs_review', 'source_ref': str(шлях.resolve())})
            журнал.зберегти()
            for рядок in маніфест['rows']:
                попередні = журнал.попередні(рядок)
                остання = попередні[-1] if попередні else None
                if остання and остання['identity'] == версія and остання['state'] == 'validated':
                    джерело = Path(остання['output_dir'])
                    кеш = читати_json((джерело / 'cache' / (ключ_кешу(рядок, версія) + '.json')).read_bytes())
                    if кеш['request_file'] != остання['request_file'] or кеш['request_sha256'] != остання['request_sha256']:
                        raise ValueError('Кеш не належить останній зафіксованій спробі')
                    результати[рядок['row_id']] = dict(перевірити_кеш(кеш, рядок, версія, джерело, коди, схема, промпт), cache_origin=str(джерело))
                elif остання and остання['identity'] == версія and остання['state'] == 'rejected' and дозвіл is None:
                    запис = читати_json((Path(остання['output_dir']) / 'requests' / остання['request_file']).read_bytes())
                    вхід = читати_json(запис['request']['messages'][1]['content'])['rows']
                    if запис['identity'] != версія or відбиток(байти_json(запис['request'])) != остання['request_sha256'] or запис['request'] != запит(вхід, схема, промпт) or рядок not in вхід:
                        raise ValueError('Втрачено точне походження відхиленого рядка')
                    відхилені[рядок['row_id']] = відповідь_пакета(запис['response'], вхід, коди)['rejected'][рядок['row_id']]
                else:
                    журнал.перевірити_повтор(рядок, версія, дозвіл)
                    нові.append(рядок)
            зберегти(тека / 'маніфест.json', маніфест)
            for початок in range(0, len(нові), пакет):
                рядки = нові[початок:початок + пакет]
                тіло = запит(рядки, схема, промпт)
                ід_запиту = відбиток(байти_json(тіло))
                файл_запиту = ід_запиту + '-' + str(time.time_ns()) + '.json'
                слід = тека / 'requests' / файл_запиту
                запис = {'identity': версія, 'request': тіло, 'input_source': маніфест['source'],
                         'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'state': 'started',
                         'once_ledger': str(журнал.шлях), 'authorization': дозвіл}
                журнал.почати(рядки, версія, ід_запиту, файл_запиту, тека, дозвіл)
                зберегти(слід, запис)
                старт = time.monotonic()
                try:
                    виклики += 1
                    відповідь = транспорт(тіло)
                    час = time.monotonic() - старт
                    запис.update(response=відповідь, batch_elapsed_s=час)
                    перевірені = відповідь_пакета(відповідь, рядки, коди)
                    час_пакетів += час
                    запис.update(state='partial' if перевірені['rejected'] or перевірені['unexpected_rows'] else 'validated', validation=перевірені)
                    зберегти(слід, запис)
                except Exception as помилка:
                    запис.update(state='failed', error=str(помилка), batch_elapsed_s=time.monotonic() - старт)
                    зберегти(слід, запис)
                    журнал.завершити(рядки, {р['row_id']: 'ambiguous' for р in рядки})
                    raise
                for рядок in рядки:
                    ід = рядок['row_id']
                    if ід not in перевірені['valid']:
                        відхилені[ід] = перевірені['rejected'][ід]
                        continue
                    кеш = {**перевірені['valid'][ід], 'row_id': ід, 'raw': рядок['raw'],
                           'identity': версія, 'request_sha256': ід_запиту, 'request_file': файл_запиту,
                           'input_source': маніфест['source'], 'batch_elapsed_s': час, 'batch_rows': len(рядки),
                           'amortized_s': час / len(рядки), 'timing_kind': 'batch_wall_equal_share', 'created_utc': запис['started_utc']}
                    зберегти(тека / 'cache' / (ключ_кешу(рядок, версія) + '.json'), кеш)
                    результати[ід] = dict(кеш, cache_hit=False, cache_origin=str(тека.resolve()))
                журнал.завершити(рядки, {р['row_id']: 'validated' if р['row_id'] in перевірені['valid'] else 'rejected' for р in рядки})
                чужі.extend(перевірені['unexpected_rows'])
                зберегти(тека / 'переклади.json', list(результати.values()))
                зберегти(тека / 'відхилені.json', відхилені)
            звіт = {'state': 'partial' if відхилені or чужі else 'completed',
                    'mode': 'translation_only' if лише_переклад else 'provenance_checked_translation',
                    'identity': версія, 'once_ledger': str(журнал.шлях), 'raw_rows': len(маніфест['rows']),
                    'raw_occurrences': len(маніфест['occurrences']), 'validated_rows': len(результати),
                    'rejected_rows': len(відхилені), 'unexpected_rows': len(чужі),
                    'admitted_occurrences': sum(в['admission'] == 'admitted' for в in маніфест['occurrences']),
                    'unknown_provenance': sum(в['admission'] != 'admitted' for в in маніфест['occurrences']),
                    'requests_this_run': виклики, 'batch_wall_s_this_run': час_пакетів,
                    'cache_hits': sum(р['cache_hit'] for р in результати.values()),
                    'known_rows': sum(р['answer']['status'] == 'known' for р in результати.values()),
                    'model_unknown_rows': sum(р['answer']['status'] == 'unknown' for р in результати.values()),
                    'semantic_review': 'pending', 'photo_review': 'not_performed', 'runtime_applied': False}
            зберегти(тека / 'переклади.json', list(результати.values()))
            зберегти(тека / 'відхилені.json', відхилені)
            зберегти(тека / 'входження.json', приєднати(маніфест, результати))
            зберегти(тека / 'звіт.json', звіт)
            return звіт
        except Exception as помилка:
            зберегти(тека / 'звіт.json', {'state': 'failed', 'error': str(помилка), 'identity': версія,
                     'requests_this_run': виклики, 'validated_rows': len(результати), 'rejected_rows': len(відхилені),
                     'once_ledger': str(журнал.шлях), 'runtime_applied': False})
            raise


def головна():
    """Готує файли або явно запускає пілот на місцевому проксі ноутбука."""
    парсер = argparse.ArgumentParser(description=__doc__)
    парсер.add_argument('--вихід', type=Path, required=True)
    парсер.add_argument('--походження', type=Path)
    парсер.add_argument('--пакет', type=int, default=2)
    парсер.add_argument('--повтор-за', type=Path)
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
            дозвіл = читати_json(арг.повтор_за.read_bytes()) if арг.повтор_за else None
            звіт = виконати(маніфест, арг.вихід, арг.пакет, лише_переклад=арг.лише_переклад, дозвіл=дозвіл)
        else:
            if (Ж.тека_журналу() / '.lock').exists():
                raise ValueError('У цій теці вже працює пілот')
            зберегти(арг.вихід / 'маніфест.json', маніфест)
            зберегти(арг.вихід / 'звіт_підготовки.json', звіт)
        print(json.dumps(звіт, ensure_ascii=False, indent=2))
        return 1 if звіт.get('state') == 'partial' else 0
    except (ValueError, OSError, KeyError, TypeError) as помилка:
        print('ЗБІЙ ПІЛОТА 5190: ' + str(помилка))
        return 1


if __name__ == '__main__':
    raise SystemExit(головна())
