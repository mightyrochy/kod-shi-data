"""Знімок ваги кожної знахідки принтів; аргументи: корінь дерева (ДО чи ПІСЛЯ), вихід .json.gz."""
import collections, gzip, json, pathlib, sys


def main():
    """Записати сиру й обмежену вагу й опору (ГГ-1) на тих самих входах; набори — з дерева цієї проби."""
    дерево = pathlib.Path(sys.argv[1]).resolve() / 'джерела'
    sys.path[:0] = [str(дерево), str(pathlib.Path(__file__).resolve().parent)]
    import колір_принти as К, палітра_принт as П
    from реєстр_сила import обмежити_вагу, опора
    from е3_принти_набори import набори
    assert pathlib.Path(К.__file__).resolve().parent == дерево, К.__file__
    функції = dict(принти=К.принти, принт_придатність=П.принт_придатність)
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори():
        рез = функції[функція](*args, **kwargs)
        for з in (рез['знахідки'] if isinstance(рез, dict) else рез):
            еф = обмежити_вагу([dict(з)])[0]
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('блокує'), з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою')), опора(з)])
            підсумок[з['правило'], з.get('сила')] += 1
    with gzip.open(sys.argv[2], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), sorted(підсумок.items()))


if __name__ == '__main__':
    main()
