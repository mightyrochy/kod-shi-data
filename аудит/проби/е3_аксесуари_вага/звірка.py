"""Зіставити кожну знахідку ДО/ПІСЛЯ; аргументи — дві теки вимірів та файл звіту."""
from collections import Counter, defaultdict
import gzip
from itertools import zip_longest
import json
from pathlib import Path
import sys


def main():
    """Відокремити дозволені зміни ваги від змін складу, сили й діагностики."""
    до, після, звіт = map(Path, sys.argv[1:])
    групи, помилки, n = defaultdict(Counter), [], 0
    дозволені = {'сила_нп', 'сила_нп_джерело', 'під_підлогою'}
    with gzip.open(до / 'знахідки.jsonl.gz', 'rt', encoding='utf-8') as а, gzip.open(
            після / 'знахідки.jsonl.gz', 'rt', encoding='utf-8') as б:
        for n, пара in enumerate(zip_longest(а, б), 1):
            if None in пара:
                помилки.append([n, 'різна кількість знахідок'])
                break
            д, п = map(json.loads, пара)
            if д[:4] != п[:4]:
                помилки.append([n, 'змінився ключ', д[:4], п[:4]])
                continue
            різні = {к for к in д[4].keys() | п[4].keys() if д[4].get(к) != п[4].get(к)}
            if різні - дозволені:
                помилки.append([n, sorted(різні - дозволені)])
            ключ = ' · '.join(д[1:4])
            групи[ключ][д[4].get('сила_нп'), п[4].get('сила_нп')] += 1
    вих = ['| модуль · функція · правило | знахідок | зі зміненою вагою | ДО → ПІСЛЯ (кількість) |',
           '|---|---:|---:|---|']
    деталі = {}
    for ключ, пари in sorted(групи.items()):
        змін = sum(к for (д, п), к in пари.items() if д != п)
        текст = '; '.join('%s → %s (%s)' % (*пара, к) for пара, к in sorted(пари.items()))
        деталі[ключ] = текст
        if len(текст) > 350:
            текст = ('без змін; діапазон %s…%s' % (min(д for д, _ in пари), max(д for д, _ in пари)) if not змін
                else 'ДО %s…%s → ПІСЛЯ %s; усі пари — `%s`' % (
                    min(д for д, _ in пари), max(д for д, _ in пари), sorted({п for _, п in пари}), звіт.with_suffix('.json').name))
        вих.append('| %s | %s | %s | %s |' % (ключ, sum(пари.values()), змін, текст))
    вих += ['', 'Знахідок: %s. Змін поза вагою та її походженням: %s.' % (n, len(помилки))]
    звіт.write_text('\n'.join(вих) + '\n', encoding='utf-8')
    звіт.with_suffix('.json').write_text(json.dumps(dict(ваги=деталі, помилки=помилки), ensure_ascii=False, indent=2), encoding='utf-8')
    print('зіставлено:', n, 'помилок:', len(помилки))
    return bool(помилки)


if __name__ == '__main__':
    sys.exit(main())
