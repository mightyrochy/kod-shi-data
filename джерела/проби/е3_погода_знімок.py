"""Знімок кожної ваги на погодних пробах і гейтах; другий аргумент — коміт ДО."""
import collections, gzip, json, pathlib, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(КОРІНЬ / 'джерела'))
sys.path.insert(0, str(КОРІНЬ / 'джерела/проби'))

def main():
    """Записати сирі й обмежені ваги без моделі, для кожного вхідного випадку."""
    if len(sys.argv) > 2:
        from виконання.е3_база import встановити
        встановити(sys.argv[2])
    import суд_погода as П
    from е3_погода_набори import набори
    from реєстр_сила import обмежити_вагу
    покриття = collections.Counter()
    def емітент(функція):
        def виклик(*args, **kwargs):
            кадр = sys._getframe(1)
            покриття[str(кадр.f_lineno)] += 1
            return функція(*args, **kwargs)
        return виклик
    for ім in ('_зн', '_зн_акс', '_зн_верх'):
        setattr(П, ім, емітент(getattr(П, ім)))
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори():
        знахідки = getattr(П, функція)(*args, **kwargs)
        for з in знахідки:
            вага = з.get('сила_нп')
            еф = обмежити_вагу([dict(з)])[0].get('сила_нп')
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'),
                        з.get('сила'), вага, еф])
            підсумок[з['правило']] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'правил', dict(підсумок))
    pathlib.Path(sys.argv[1] + '.покриття.json').write_text(json.dumps(покриття), encoding='utf-8')


if __name__ == '__main__':
    main()
