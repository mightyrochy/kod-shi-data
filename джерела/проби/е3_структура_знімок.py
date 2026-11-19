"""Знімок кожної ваги восьми емісій `аксесуари_структура` на повному каталозі; другий аргумент — коміт ДО."""
import collections, gzip, json, pathlib, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
sys.path.insert(0, str(КОРІНЬ / 'джерела/проби'))


def main():
    """Записати сиру й обмежену вагу кожної знахідки без моделі."""
    if len(sys.argv) > 2:
        from виконання.е3_база import встановити
        встановити(sys.argv[2], ('аксесуари_структура',))
    import аксесуари_структура as А
    import trace as Т
    from е3_структура_набори import набори
    from реєстр_сила import обмежити_вагу
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори(А):
        знахідки = getattr(А, функція)(*args, **kwargs)
        if функція == 'рятівник_приобличчя':
            знахідки = знахідки[1]
        for з in знахідки:
            еф = обмежити_вагу([dict(з)])[0].get('сила_нп')
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('блокує'), з.get('сила_нп'), еф])
            підсумок[з['правило'], з.get('сила')] += 1
        Т.ЗАПИСИ.clear()
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), {'%s/%s' % к: v for к, v in sorted(підсумок.items())})


if __name__ == '__main__':
    main()
