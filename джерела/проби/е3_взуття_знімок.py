"""Знімок кожної ваги чотирьох суддів `аксесуари_взуття` на повному каталозі; аргументи: вихід.json.gz [корінь дерева]."""
import collections, gzip, hashlib, json, pathlib, sys
ТУТ, ВАГА = pathlib.Path(__file__).resolve().parent, ('сила_нп', 'сила_нп_джерело', 'під_підлогою')
sys.path.insert(0, str(ТУТ))
sys.path.insert(0, str(pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else ТУТ.parents[1]).resolve() / 'джерела'))


def main():
    """Сира й обмежена (`обмежити_вагу`) вага, мітка підлоги й відбиток решти полів кожної знахідки."""
    import аксесуари_взуття as A
    from реєстр_сила import обмежити_вагу
    from е3_взуття_набори import набори
    print('дерево', A.__file__, flush=True)
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори():
        for з in getattr(A, функція)(*args, **kwargs):
            еф = обмежити_вагу([dict(з)])[0]
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою')),
                        hashlib.md5(json.dumps({к: в for к, в in з.items() if к not in ВАГА}, ensure_ascii=False,
                                               sort_keys=True, default=str).encode()).hexdigest()[:12]])
            підсумок[з['правило'], з.get('сила')] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), sorted(підсумок.items(), key=str))


if __name__ == '__main__':
    main()
