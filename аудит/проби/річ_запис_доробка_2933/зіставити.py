"""Звіряє всі поля та відбитки незмінних 144 входів доробки #2933."""
import gzip
import hashlib
import json
from pathlib import Path


def main():
    """Друкує зміни текстів і перевіряє відповідність доказів остаточному коду."""
    тека = Path(__file__).resolve().parent
    корінь = тека.parents[2]
    with gzip.open(тека / 'поля-до.json.gz', 'rt', encoding='utf8') as файл:
        до = json.load(файл)
    with gzip.open(тека / 'поля-після.json.gz', 'rt', encoding='utf8') as файл:
        після = json.load(файл)
    assert len(до['сторінки']) == len(після['сторінки']) == 144
    зміни = []
    for а, б in zip(до['сторінки'], після['сторінки']):
        assert а['url'] == б['url'] and а['sha256'] == б['sha256']
        вхід = корінь / 'аудит/проби/річ_запис_каталог_2026_10_30' / б['файл']
        assert hashlib.sha256(вхід.read_bytes()).hexdigest() == б['sha256']
        for поле in ('назва', 'опис', 'межа'):
            if а[поле] != б[поле]:
                зміни.append(dict(url=а['url'], поле=поле, до=а[поле], після=б[поле]))
    for шлях, відбиток in після['джерела_sha256'].items():
        assert hashlib.sha256((корінь / шлях).read_bytes()).hexdigest() == відбиток
    звіт = dict(сторінок=144, змін=зміни, до=до['лічба'], після=після['лічба'], відбитки_збігаються=True)
    (тека / 'зіставлення.json').write_text(json.dumps(звіт, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(звіт, ensure_ascii=False))
    return int(bool(зміни))


if __name__ == '__main__':
    raise SystemExit(main())
