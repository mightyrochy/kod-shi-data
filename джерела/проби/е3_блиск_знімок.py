"""Знімок кожної ваги блиску й металів на повному каталозі; другий аргумент — корінь дерева коду (ДО)."""
import collections, gzip, json, pathlib, sys
ПРОБИ = pathlib.Path(__file__).resolve().parent
КОД = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ПРОБИ.parents[1]
sys.path[:0] = [str(КОД / 'джерела'), str(ПРОБИ)]


def main():
    """Записати сиру й обмежену вагу кожної знахідки та покриття рядків емісії."""
    import суд_блиск as СБ
    from е3_блиск_набори import набори
    from реєстр_сила import обмежити_вагу
    assert pathlib.Path(СБ.__file__).resolve().parents[1] == КОД, СБ.__file__
    покриття, справжній = collections.Counter(), СБ._зн

    def емітент(*args, **kwargs):
        покриття[str(sys._getframe(1).f_lineno)] += 1
        return справжній(*args, **kwargs)
    СБ._зн = емітент
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори():
        for з in getattr(СБ, функція)(*args, **kwargs):
            еф = обмежити_вагу([dict(з)])[0]
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою')), bool(з.get('блокує'))])
            підсумок[з['правило'], з.get('сила')] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'покрито рядків емісії', len(покриття))
    print(sorted(підсумок.items(), key=str))
    pathlib.Path(sys.argv[1] + '.покриття.json').write_text(json.dumps(покриття), encoding='utf-8')


if __name__ == '__main__':
    main()
