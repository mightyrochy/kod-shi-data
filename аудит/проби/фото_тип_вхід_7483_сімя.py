"""Мала сім'я добору 7483: повтори, витік старих полів, чесний pending."""
import json
import фото_тип_вхід_7483 as В


def main():
    """Перевіряє добір без мережі, каталожного циклу й призначення gold."""
    корпус, каталог = [], []
    for номер in range(300):
        ід = f'реальний-{номер}'
        корпус.append({'id': ід, 'форма_URL': f'https://example.org/{номер}.jpg',
                       'oldconfirmed': True, 'old_photo_slot': 'верх',
                       'маніфест': {'sha256': f'{номер // 2:064x}'}})
        каталог.append({'id': ід, 'url': f'https://example.org/sku/{номер}',
                        'слот': 'низ', 'тип': 'штани', 'набір': ['верх', 'низ'],
                        'назва': 'СЕКРЕТ НАЗВИ', 'опис': 'СЕКРЕТ ОПИСУ'})
    рядки, підказки = В.зібрати(корпус, каталог, 'a' * 40, 'сімя')
    інші, _ = В.зібрати(корпус[::-1], каталог[::-1], 'a' * 40, 'сімя')
    assert рядки == інші and len(рядки) == len({р['sample_id'] for р in рядки}) == 120
    реальні = [р for р in рядки if р['role'] == 'real']
    негативи = [р for р in рядки if р['role'] == 'negative']
    assert len(реальні) == len({р['image_url'] for р in реальні}) == 100
    assert len({р['known_old_metadata']['historical_frame_metadata']['sha256'] for р in реальні}) == 100
    assert len(негативи) == 20 and all(р['sku'] is р['image_url'] is None for р in негативи)
    assert all(not р['ready_for_download'] for р in негативи)
    assert sum(р['calibration'] for р in рядки) == 40
    assert all(р['image_sha256'] is None and р['groundtruth_status'] == 'pending_eye' for р in рядки)
    assert 'СЕКРЕТ' not in json.dumps(рядки, ensure_ascii=False)
    звіт = В.зведення(рядки, підказки, {})
    assert not звіт['infer_ready'] and звіт['gold_assigned'] == 0
    for поганий in (корпус + корпус[:1], [dict(корпус[0], форма_URL='одяг.jpg')]):
        try:
            В.зібрати(поганий, каталог, 'a' * 40, 'сімя')
        except ValueError:
            continue
        raise AssertionError('Хибний вхід прийнято')
    print('ПРОЙДЕНО 7483: 100/20 pending, 40 subset, сталість, без повторів/gold/описів')

if __name__ == '__main__':
    main()
