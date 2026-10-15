"""5191: лічить джерела типу; збіг enum не означає доведений тип моделі."""
import gzip, hashlib, json, sys, xml.etree.ElementTree as E
from collections import Counter
from pathlib import Path

def main():
    """Друкує факти незмінних raw і збагачення без модельних викликів."""
    корінь = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(корінь / 'джерела'))
    from внутрішня_мова import ТАБЛИЦЯ
    raw = (корінь / 'каталог_повний.xml.gz').read_bytes()
    речі = E.fromstring(gzip.decompress(raw)).findall('.//offer')
    значення = [''.join(п.itertext()) for р in речі for п in р.findall('param') if п.get('name') == 'тип']
    рядки = (json.dumps(sorted(set(значення)), ensure_ascii=False, indent=2) + '\n').encode()
    зб = json.loads(gzip.decompress((корінь / 'джерела/каталог_збагачення.json.gz').read_bytes()))
    def ключі(в):
        """Обходить і вкладені записи, не тлумачачи їхніх значень."""
        if isinstance(в, dict):
            for к, з in в.items():
                yield к
                yield from ключі(з)
        elif isinstance(в, list):
            for з in в:
                yield from ключі(з)
    поля = Counter(ключі(зб))
    print('raw', len(речі), 'тип_входжень', len(значення), 'тип_рядків', len(set(значення)))
    print('точний_enum_метаданих', sum(з in ТАБЛИЦЯ['item_type'].values() for з in значення))
    print('збагачення_записів', len(зб), 'ключі_типу', {к: поля[к] for к in ('тип', 'item_type')})
    print('raw_sha256', hashlib.sha256(raw).hexdigest())
    print('рядки_байтів', len(рядки), 'рядки_sha256', hashlib.sha256(рядки).hexdigest())

if __name__ == '__main__':
    main()
