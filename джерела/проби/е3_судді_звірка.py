"""Звірка двох знімків записувача суддів: склад, сила, блокування й ефективна вага; таблиця сирих змін."""
import collections, gzip, json, sys


def main():
    def читати(ш):
        return [[json.dumps(р[:7], ensure_ascii=False, sort_keys=True), р[7], р[8]]
                for р in json.load(gzip.open(ш, 'rt', encoding='utf-8'))['записи']]
    до, після = читати(sys.argv[1]), читати(sys.argv[2])
    ск = [collections.Counter(к for к, _, _ in д) for д in (до, після)]
    еф = [collections.Counter((к, е) for к, _, е in д) for д in (до, після)]
    сирі = collections.Counter()
    for (к, с0, е0), (_, с1, е1) in zip(sorted(до), sorted(після)):
        if с0 != с1:
            сирі[json.loads(к)[2], json.loads(к)[5], с0, с1, е0] += 1
    розб = sum(((еф[0] - еф[1]) + (еф[1] - еф[0])).values())
    print('записів %d → %d; склад однаковий: %s; ефективних відмінностей %d; сирих змін %d'
          % (len(до), len(після), ск[0] == ск[1], розб, sum(сирі.values())))
    print('| правило | сила | ДО | ПІСЛЯ | ефективна | кількість |')
    print('|---|---|---|---|---|---|')
    for (п, с, а, б, е), н in sorted(сирі.items(), key=str):
        print('| %s | %s | %s | %s | %s | %d |' % (п, с, а, б, е, н))
    print('за правилом і силою:', dict(collections.Counter((json.loads(к)[2], json.loads(к)[5]) for к, _, _ in після)))
    assert ск[0] == ск[1] and not розб


if __name__ == '__main__':
    main()
