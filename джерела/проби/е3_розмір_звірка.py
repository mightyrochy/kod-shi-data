"""Звірити знахідки воріт розміру з двох знімків (`е3_розмір_знімок` чи `е3_розмір_гейти`)."""
import collections, gzip, json, sys


def main():
    """Склад і сила тотожні; друк сирих і ефективних змін ваги за правилом."""
    def читати(шлях):
        with gzip.open(шлях, 'rt', encoding='utf-8') as ф:
            д = json.load(ф)
        return д['записи'] if isinstance(д, dict) else д
    до, після = map(читати, sys.argv[1:3])
    assert len(до) == len(після), (len(до), len(після))
    сирі, ефективні = collections.Counter(), collections.Counter()
    for д, п in zip(до, після):
        assert д[:-2] == п[:-2], (д, п)
        правило = next(x for x in д if isinstance(x, str) and x.startswith('K-'))
        if д[-2] != п[-2]:
            сирі[правило, д[-2], п[-2]] += 1
        if д[-1] != п[-1]:
            ефективні[правило, д[-1], п[-1]] += 1
    print('знахідок', len(до), '— склад, сила, блокує й відсів тотожні; сирих змін', sum(сирі.values()),
          'ефективних', sum(ефективні.values()))
    for назва, т in (('сирі', сирі), ('ефективні', ефективні)):
        print('%s: | правило | ДО | ПІСЛЯ | кількість |' % назва)
        for (правило, було, стало), к in sorted(т.items(), key=str):
            print('| %s | %s | %s | %s |' % (правило, було, стало, к))


if __name__ == '__main__':
    main()
