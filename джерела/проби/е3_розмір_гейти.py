"""Ваги воріт розміру аксесуарів на повному прогоні гейтів; аргументи: вихід.json.gz [коміт ДО]."""
import functools, gzip, inspect, json, os, pathlib, runpy, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
sys.path[:0] = [str(КОРІНЬ / 'джерела'), str(КОРІНЬ / 'джерела/проби'), str(КОРІНЬ / 'джерела/прилади')]


def main():
    """Обгорнути емітентів модуля записом знахідок і виконати `розділи_гейтів.py` до кінця."""
    if len(sys.argv) > 2:
        from виконання.е3_база import встановити
        встановити(sys.argv[2], ('аксесуари_розмір',))
    import аксесуари_розмір as А
    from реєстр_сила import обмежити_вагу
    записи, вихід = [], sys.argv[1]

    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*а, **к):
            р = ф(*а, **к)
            for з in (р if isinstance(р, list) else [р[1]] if isinstance(р, tuple) else []):
                if isinstance(з, dict) and 'правило' in з:
                    записи.append([ф.__name__, з['правило'], з.get('суть'), з.get('сила'), з.get('блокує'),
                                   з.get('сила_нп'), обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return р
        return виклик
    for ім in ('ворота_однієї', 'ширина_й_розмір'):
        старий = getattr(А, ім); новий = обгорнути(старий)
        for м in list(sys.modules.values()):
            for к, з in list(vars(м).items() if hasattr(м, '__dict__') else []):
                if з is старий: setattr(м, к, новий)
    os.chdir(КОРІНЬ / 'джерела'); sys.argv = ['прилади/розділи_гейтів.py']; код = 0
    try: runpy.run_path('прилади/розділи_гейтів.py', run_name='__main__')
    except SystemExit as е: код = е.code or 0
    with gzip.open(вихід, 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, код=код), ф, ensure_ascii=False)
    print('гейти: код', код, 'знахідок воріт розміру', len(записи), file=sys.__stdout__)


if __name__ == '__main__':
    main()
