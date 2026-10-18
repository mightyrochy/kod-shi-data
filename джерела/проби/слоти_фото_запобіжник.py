"""Ф2/2.6: невідомий тип кадру не пропускає метал та вставки (7483)."""
import gzip, json, os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import фід_збагачення as З


def main():
    """Справжні п'ять раніше відсіяних кадрів і живий позитивний вхід."""
    шлях = Path(З.__file__).parent / 'каталог_збагачення.json.gz'
    with gzip.open(шлях, 'rt') as ф:
        записи = json.load(ф)
    іди = ('ж-07551@honchstudio.com', 'ж-07570@likeangel.com.ua',
           'ж-07624@likeangel.com.ua', 'ж-07632@honchstudio.com',
           'ж-11795@theoriginals.com.ua')
    for ід in іди:
        зб = записи[ід]
        for слот in (None, 'верх', 'пояс', 'невідомий'):
            assert З.частка_металу(зб, 'прикраси', 'золото', слот) is None, ід
            assert З.колір_вставки(зб, 'прикраси', 'золото', слот) is None, ід
        # Позитивний шлях не заглушено: підтверджений jewelry-код приймається.
        assert З.частка_металу(зб, 'прикраси', 'золото', 'прикраси') is not None, ід
        assert З.колір_вставки(зб, 'прикраси', 'золото', 'прикраси') is not None, ід
    print('ПРОЙДЕНО: 5 справжніх кадрів, unknown/чужий слот утримано, кодовий вхід живий')


if __name__ == '__main__':
    main()
