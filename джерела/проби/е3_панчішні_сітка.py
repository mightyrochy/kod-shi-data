"""Вага K-HOS-02 (`суд_погода.панчішні`) на сітці трійок світлот колготки/низ/взуття; перший аргумент — корінь
дерева (ДО чи ПІСЛЯ), другий — файл виходу json. Порівняння — `е3_панчішні_сітка.py --звірити ДО.json ПІСЛЯ.json`."""
import collections, itertools, json, pathlib, sys


def головна():
    """Записати (колготки, низ, взуття) → сила й вага знахідки K-HOS-02 для всієї сітки."""
    sys.path.insert(0, str(pathlib.Path(sys.argv[1]).resolve() / 'джерела'))
    import суд_погода as П
    крок = list(range(0, 101, 5))
    вих = {}
    for к, н, в in itertools.product(крок, крок, крок):
        речі = [dict(id='к', назва='Колготки', слот='колготи', L=к),
                dict(id='н', назва='Спідниця', слот='низ', L=н),
                dict(id='в', назва='Черевики', слот='взуття', L=в)]
        з = [x for x in П.панчішні(речі) if x['правило'] == 'K-HOS-02']
        вих['%s/%s/%s' % (к, н, в)] = [з[0]['сила'], з[0]['сила_нп']] if з else None
    pathlib.Path(sys.argv[2]).write_text(json.dumps(вих), encoding='utf-8')
    print('трійок', len(вих), 'із знахідкою', sum(1 for v in вих.values() if v))


def звірити():
    """Таблиця змін: за різницею |Δвз − Δниз| — скільки трійок і яка вага ДО → ПІСЛЯ."""
    до, після = (json.loads(pathlib.Path(p).read_text(encoding='utf-8')) for p in sys.argv[2:4])
    рядки = collections.Counter()
    зсього = змін = 0
    for к, v in до.items():
        w = після[к]
        зсього += 1
        if v != w:
            змін += 1
            рядки[(tuple(v) if v else None, tuple(w) if w else None)] += 1
    print('трійок', зсього, 'змінилась вага чи сила', змін)
    for (a, b), n in sorted(рядки.items(), key=str)[:60]:
        print(n, a, '→', b)


if __name__ == '__main__':
    звірити() if sys.argv[1] == '--звірити' else головна()
