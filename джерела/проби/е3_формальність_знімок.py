"""Знімок кожної ваги емітентів `формальність.py` на повному каталозі; другий аргумент — коміт ДО."""
import collections, gzip, json, pathlib, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби')]


def main():
    """Записати склад, силу, регістр, блок, сиру й обмежену вагу кожної знахідки."""
    if len(sys.argv) > 2:
        from виконання.е3_база import встановити
        встановити(sys.argv[2], ('формальність',))
    import формальність as F
    from е3_формальність_набори import набори
    from реєстр_сила import обмежити_вагу
    покриття, оригінал = collections.Counter(), F._зн
    def _зн(*args, **kwargs):
        покриття[str(sys._getframe(1).f_lineno)] += 1
        return оригінал(*args, **kwargs)
    F._зн = _зн
    вих, підсумок = [], collections.Counter()
    for назва, функція, args, kwargs in набори():
        for з in getattr(F, функція)(*args, **kwargs):
            еф = обмежити_вагу([dict(з)])[0]
            вих.append([назва, функція, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                        з.get('регістр'), bool(з.get('блокує')), з.get('сила_нп'), еф.get('сила_нп'),
                        bool(еф.get('під_підлогою'))])
            підсумок[з['правило'], з.get('сила')] += 1
    with gzip.open(sys.argv[1], 'wt', encoding='utf-8') as ф:
        json.dump(вих, ф, ensure_ascii=False)
    print('знахідок', len(вих), 'правил', sorted(підсумок.items()))
    pathlib.Path(sys.argv[1] + '.покриття.json').write_text(json.dumps(покриття, sort_keys=True), encoding='utf-8')


if __name__ == '__main__':
    main()
