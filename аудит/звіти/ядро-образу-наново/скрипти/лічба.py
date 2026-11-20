"""Лічба переліку вад за джерелом і відром: python3 -I аудит/звіти/ядро-образу-наново/скрипти/лічба.py"""
import collections, os, sys
ф = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'вади-перелік.tsv')
рядки = [р.rstrip('\n').split('\t') for р in open(ф, encoding='utf-8')][1:]
ВІДРА = ('ЯДРО', 'ЗНАННЯ', 'ПОЗА', 'ВІДКИНУТО')
л = collections.Counter((р[1], р[2]) for р in рядки)
print('| джерело | переглянуто | ядро | знання | поза ядром | відкинуто |')
print('|---|---|---|---|---|---|')
for д in sorted(set(р[1] for р in рядки), key=lambda д: -sum(л[(д, в)] for в in ВІДРА)):
    print(f'| {д} | {sum(л[(д, в)] for в in ВІДРА)} | ' + ' | '.join(str(л[(д, в)]) for в in ВІДРА) + ' |')
в = collections.Counter(р[2] for р in рядки)
print(f'| **разом** | **{len(рядки)}** | ' + ' | '.join(f'**{в[x]}**' for x in ВІДРА) + ' |')
if '--класи' in sys.argv:
    print()
    for к, n in collections.Counter(р[3] for р in рядки if р[2] == 'ЯДРО').most_common():
        print(f'{к}\t{n}')
    print()
    for к, n in collections.Counter(р[4] for р in рядки if р[2] in ('ЗНАННЯ', 'ПОЗА')).most_common():
        print(f'{к}\t{n}')
    print()
    for к, n in collections.Counter(р[8] for р in рядки if р[2] == 'ВІДКИНУТО').most_common():
        print(f'{к}\t{n}')
