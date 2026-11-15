"""Зіставлення ваг силуету образу й регістру уваги в гейтах і пробах ДО/ПІСЛЯ (`виконання/е3_ваги_модулів.py`)."""
import collections, gzip, json, pathlib, sys
from е3_силует_увага_звірка import ДОЗВОЛЕНІ


def читати(префікс):
    """Записи (jsonl.gz) і коди завершення перевірок одного дерева."""
    with gzip.open(префікс + '.jsonl.gz', 'rt', encoding='utf-8') as ф:
        рядки = [json.loads(р) for р in ф]
    return рядки, json.loads(pathlib.Path(префікс + '.провали.json').read_text(encoding='utf-8'))


def main():
    """Склад тотожний; ефективна вага змінюється лише на названих літералах K-SIL-10; коди ті самі."""
    (до, збої_до), (після, збої_після) = map(читати, sys.argv[1:3])
    ключ = lambda р: json.dumps(р[:6], ensure_ascii=False, sort_keys=True)
    print('Провали ДО:', збої_до, 'ПІСЛЯ:', збої_після)
    print('| Перевірка | ДО | ПІСЛЯ | Сирих змін | Ефективних змін | Поза дозволеними |\n|---|---|---|---|---|---|')
    вади = []
    for назва in sorted({р[0] for р in до + після}):
        д, п = ([р for р in дані if р[0] == назва] for дані in (до, після))
        assert collections.Counter(map(ключ, д)) == collections.Counter(map(ключ, п)), назва
        пари = list(zip(sorted(д, key=ключ), sorted(п, key=ключ)))
        сирі = sum(а[6] != б[6] for а, б in пари)
        еф = [(а[2], а[5], а[7], б[7]) for а, б in пари if а[7] != б[7] or а[8] != б[8]]
        чужі = [е for е in еф if е not in ДОЗВОЛЕНІ]
        print('| %s | %d | %d | %d | %d | %d |' % (назва, len(д), len(п), сирі, len(еф), len(чужі)))
        if чужі: вади.append((назва, чужі[:3]))
    print('записів', len(до), '→', len(після), 'вади:', вади)
    assert not вади and збої_до == збої_після, (вади, збої_до, збої_після)


if __name__ == '__main__':
    main()
