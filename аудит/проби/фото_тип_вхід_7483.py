"""Відтворюваний добір пілота 7483 зі збережених даних, без мережі й gold.

Старі слоти, каталог і хеші — лише стратифікація, не спостереження кадру.
Службові URL — кандидати негативної групи; їхній клас встановлюють очі.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit


СТРАТИ = (('collision_metadata', 30), ('catalog_photo_disagreement', 20),
          ('multiobject_catalog_hint', 20), ('oldconfirmed_metadata', 30))
КІЛЬКІСТЬ = {'real': 100, 'negative': 20, 'calibration_real': 33,
             'calibration_negative': 7}


def хеш(значення):
    """Повертає стабільний SHA256 байтів або тексту."""
    дані = значення.encode('utf-8') if isinstance(значення, str) else значення
    return hashlib.sha256(дані).hexdigest()


def читати(шлях):
    """Читає збережений JSON, повертаючи також хеш вхідних байтів."""
    дані = Path(шлях).read_bytes()
    вміст = gzip.decompress(дані) if дані[:2] == b'\x1f\x8b' else дані
    return json.loads(вміст), хеш(дані)


def вебадреса(значення):
    """Перевіряє точну адресу, не виправляючи й не відвідуючи її."""
    if not isinstance(значення, str):
        return False
    адреса = urlsplit(значення)
    return адреса.scheme in ('http', 'https') and bool(адреса.netloc)


def перевірити(корпус, каталог, джерело):
    """Відхиляє незіставні входи замість вигадування SKU чи URL."""
    if not re.fullmatch(r'[0-9a-f]{40}', джерело):
        raise ValueError('source-sha має бути повним 40-символьним SHA')
    if not isinstance(корпус, list) or not isinstance(каталог, list):
        raise ValueError('Корпус і каталог мають бути списками')
    іди = [рядок['id'] for рядок in корпус]
    if len(set(іди)) != len(іди):
        raise ValueError('Повтор SKU у корпусі')
    індекс = {рядок['id']: рядок for рядок in каталог}
    if len(індекс) != len(каталог):
        raise ValueError('Повтор SKU у каталозі')
    for рядок in корпус:
        if рядок['id'] not in індекс or not вебадреса(рядок.get('форма_URL')):
            raise ValueError('Нема точного каталожного join або URL кадру')
        if not вебадреса(індекс[рядок['id']].get('url')):
            raise ValueError('Нема точної сторінки SKU')
    return індекс


def ознаки(корпус, каталог):
    """Будує підказки добору, які не є класами зображень."""
    адреси = collections.Counter(рядок['форма_URL'] for рядок in корпус)
    хеші = collections.Counter((рядок.get('маніфест') or {}).get('sha256')
                               for рядок in корпус)
    вихід = {}
    for рядок in корпус:
        запис = каталог[рядок['id']]
        відбиток = (рядок.get('маніфест') or {}).get('sha256')
        вихід[рядок['id']] = {
            'collision_metadata': адреси[рядок['форма_URL']] > 1 or
                bool(відбиток and хеші[відбиток] > 1),
            'catalog_photo_disagreement': запис.get('слот') != рядок['old_photo_slot'],
            'multiobject_catalog_hint': запис.get('слот') == 'комплект' or
                bool(запис.get('набір')),
            'oldconfirmed_metadata': рядок['oldconfirmed'] is True,
        }
    return вихід


def порядок(рядок, зерно, страта):
    """Задає незалежний від порядку файлів детермінований порядок."""
    return хеш(f"{зерно}\n{страта}\n{рядок['id']}\n{рядок['форма_URL']}")


def добрати(корпус, підказки, зерно):
    """Вибирає 100 різних кадрів, виключаючи відомі дублікати байтів."""
    вибрані, адреси, хеші = [], set(), set()
    for страта, кількість in СТРАТИ:
        кандидати = (р for р in корпус if підказки[р['id']][страта])
        взято = 0
        for рядок in sorted(кандидати, key=lambda р: порядок(р, зерно, страта)):
            адреса = рядок['форма_URL']
            відбиток = (рядок.get('маніфест') or {}).get('sha256')
            if адреса in адреси or відбиток and відбиток in хеші:
                continue
            вибрані.append((рядок, страта))
            адреси.add(адреса)
            if відбиток:
                хеші.add(відбиток)
            взято += 1
            if взято == кількість:
                break
        if взято != кількість:
            raise ValueError(f'Страта {страта}: доступно {взято}, потрібно {кількість}')
    return вибрані


def основа(ід, роль, джерело):
    """Створює стан кандидата без призначення класу чи очного висновку."""
    return {'id': ід, 'sample_id': ід, 'role': роль, 'kind': роль,
            'source_sha': джерело, 'sku': None, 'source_url': None,
            'item_page_url': None, 'image_url': None, 'image_sha256': None,
            'frame_target': 'form',
            'target_binding': {'kind': 'full_frame', 'crop': None},
            'groundtruth_status': 'pending_eye', 'eye_status': 'pending',
            'calibration': False, 'ready_for_download': False}


def кандидат(рядок, страта, запис, підказки, джерело):
    """Зберігає точну прив'язку кадру й окремо непідтверджені старі дані."""
    ід = '7483-real-' + хеш(рядок['id'] + '\n' + рядок['форма_URL'])[:16]
    вихід = основа(ід, 'real', джерело)
    вихід.update(sku=рядок['id'], source_kind='product', source_id=рядок['id'],
                 source_url=запис['url'],
                 item_page_url=запис['url'], image_url=рядок['форма_URL'],
                 stratum=страта, ready_for_download=True)
    вихід['known_old_metadata'] = {
        'usage': 'stratification_only_not_gold_not_model_input',
        'oldconfirmed': рядок['oldconfirmed'],
        'old_photo_slot': рядок['old_photo_slot'],
        'catalog_slot': запис.get('слот'), 'catalog_type_legacy': запис.get('тип'),
        'catalog_set_legacy': запис.get('набір'), 'stratum_hints': підказки,
        'historical_frame_metadata': рядок.get('маніфест'),
        'historical_color_frame_url': рядок.get('top_URL'),
    }
    return вихід


def контролі(службові, рядки, джерело, зерно):
    """Бере точні службові URL без припущення про видимий зміст кадру."""
    зайняті = {р['image_url'] for р in рядки}
    записи = []
    for домен, адреси in службові.items():
        for адреса, лічба in адреси.items():
            if вебадреса(адреса) and адреса not in зайняті:
                записи.append((домен, адреса, лічба))
    записи.sort(key=lambda з: хеш(f'{зерно}\nservice_control\n{з[0]}\n{з[1]}'))
    вихід = []
    for домен, адреса, лічба in записи:
        if адреса in зайняті:
            continue
        зайняті.add(адреса)
        ід = '7483-control-' + хеш(домен + '\n' + адреса)[:16]
        рядок = основа(ід, 'negative', джерело)
        екранувати = lambda текст: текст.replace('~', '~0').replace('/', '~1')
        рядок.update(source_kind='service_control', source_id=ід,
                     source_url=адреса, image_url=адреса,
                     frame_target='service_candidate', stratum='service_control_candidate',
                     ready_for_download=True,
                     source_record_pointer='/' + екранувати(домен) + '/' + екранувати(адреса),
                     known_old_metadata={'usage': 'stratification_only_not_gold_not_model_input',
                                         'service_domain': домен, 'service_occurrences': лічба})
        вихід.append(рядок)
        if len(вихід) == КІЛЬКІСТЬ['negative']:
            return вихід
    raise ValueError(f'Службових URL лише {len(вихід)}, потрібно20')


def калібрування(рядки, зерно):
    """Позначає 40 місць як підмножину 120, без повторного кадру."""
    for роль in ('real', 'negative'):
        група = [рядок for рядок in рядки if рядок['role'] == роль]
        група.sort(key=lambda р: хеш(f"{зерно}\ncalibration\n{р['sample_id']}"))
        for рядок in група[:КІЛЬКІСТЬ['calibration_' + роль]]:
            рядок['calibration'] = True


def зібрати(корпус, каталог, службові, джерело, зерно):
    """Повертає 100 товарних і 20 службових кадрів без призначення gold."""
    індекс = перевірити(корпус, каталог, джерело)
    підказки = ознаки(корпус, індекс)
    рядки = [кандидат(р, с, індекс[р['id']], підказки[р['id']], джерело)
             for р, с in добрати(корпус, підказки, зерно)]
    рядки.extend(контролі(службові, рядки, джерело, зерно))
    калібрування(рядки, зерно)
    return рядки, підказки


def зведення(рядки, підказки, походження):
    """Рахує URL, не видаючи службове походження за підтверджений клас."""
    реальні = [р for р in рядки if р['role'] == 'real']
    відомі = [(р['known_old_metadata']['historical_frame_metadata'] or {}).get('sha256')
              for р in реальні]
    return {'provenance': походження, 'candidate_slots': len(рядки),
            'real_candidates': len(реальні), 'negative_candidate_urls': КІЛЬКІСТЬ['negative'],
            'negative_gold_verified': 0, 'infer_ready': False,
            'strata': dict(collections.Counter(р['stratum'] for р in рядки)),
            'available_hints': {с: sum(п[с] for п in підказки.values()) for с, _ in СТРАТИ},
            'unique_real_urls': len({р['image_url'] for р in реальні}),
            'unique_all_urls': len({р['image_url'] for р in рядки}),
            'known_historical_hashes': sum(bool(х) for х in відомі),
            'unique_known_historical_hashes': len({х for х in відомі if х}),
            'actual_pixels_verified': 0, 'gold_assigned': 0,
            'calibration_ids': [р['sample_id'] for р in рядки if р['calibration']],
            'remaining_ids': [р['sample_id'] for р in рядки if not р['calibration']]}


def main():
    """Пише JSONL та коротке зведення, не завантажуючи жодного зображення."""
    парсер = argparse.ArgumentParser(description=__doc__)
    for назва in ('corpus', 'catalog', 'service', 'source-sha', 'output', 'summary'):
        парсер.add_argument('--' + назва, required=True)
    парсер.add_argument('--seed', default='7483-120-v1')
    арг = парсер.parse_args()
    корпус, хешкорпусу = читати(арг.corpus)
    каталог, хешкаталогу = читати(арг.catalog)
    службові, хешслужбових = читати(арг.service)
    рядки, підказки = зібрати(корпус, каталог, службові, арг.source_sha, арг.seed)
    походження = {'source_sha': арг.source_sha, 'corpus_sha256': хешкорпусу,
                  'catalog_sha256': хешкаталогу, 'seed': арг.seed,
                  'service_manifest_sha256': хешслужбових,
                  'selector_sha256': хеш(Path(__file__).read_bytes())}
    for рядок in рядки:
        рядок['selection_provenance'] = походження
        if рядок['source_kind'] == 'service_control':
            рядок['source_file'] = 'джерела/каталог_службові_кадри.json.gz'
            рядок['source_file_sha256'] = хешслужбових
    текст = ''.join(json.dumps(р, ensure_ascii=False, sort_keys=True) + '\n' for р in рядки)
    Path(арг.output).write_text(текст, encoding='utf-8')
    звіт = зведення(рядки, підказки, походження)
    звіт['manifest_sha256'] = хеш(текст)
    Path(арг.summary).write_text(json.dumps(звіт, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({к: звіт[к] for к in ('candidate_slots', 'real_candidates',
          'negative_candidate_urls', 'infer_ready', 'manifest_sha256')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
