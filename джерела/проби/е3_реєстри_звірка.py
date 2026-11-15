"""Звірити кожну знахідку шару реєстрів у двох знімках; таблиця «правило · ДО · ПІСЛЯ»."""
import collections, gzip, json, statistics, sys


def main():
    """Склад і сила — тотожні; ефективна вага й підлога — зведено за правилом і силою."""
    def читати(шлях):
        with gzip.open(шлях, 'rt', encoding='utf-8') as ф:
            дані = json.load(ф)
        return дані['записи'] if isinstance(дані, dict) else дані
    до, після = map(читати, sys.argv[1:3])
    assert len(до) == len(після), (len(до), len(після))
    групи = collections.defaultdict(list)
    for д, п in zip(до, після):
        assert д[:6] == п[:6], (д, п)
        групи[д[2], д[5]].append((д[7], п[7], д[8], п[8]))
    змін = sum(1 for в in групи.values() for x in в if x[0] != x[1])
    print('знахідок', len(до), '; склад і сила тотожні; ефективних змін ваги', змін)
    print('| правило · сила | знахідок | ДО (еф.) | ПІСЛЯ (еф.): мін / медіана / макс | змінилось | під підлогою ДО → ПІСЛЯ |')
    print('|---|---|---|---|---|---|')
    for (правило, сила), в in sorted(групи.items(), key=str):
        пі = [x[1] for x in в]
        print('| %s · %s | %d | %s | %s / %s / %s | %d | %d → %d |' % (
            правило, сила, len(в), ', '.join(map(str, sorted(set(x[0] for x in в)))), min(пі),
            statistics.median(пі), max(пі), sum(1 for x in в if x[0] != x[1]),
            sum(1 for x in в if x[2]), sum(1 for x in в if x[3])))


if __name__ == '__main__':
    main()
