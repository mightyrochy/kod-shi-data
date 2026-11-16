"""Ваги чотирьох суддів `аксесуари_взуття` на повному прогоні `розділи_гейтів.py`; з кореня дерева: вихід.json.gz."""
import functools, gzip, json, os, pathlib, runpy, sys


def main():
    """Обгорнути суддів записом ваги, прогнати гейти дерева з поточної теки, зберегти записи й код."""
    дж = pathlib.Path.cwd() / 'джерела'
    sys.path[:0] = [str(дж / 'прилади'), str(дж)]
    import аксесуари_взуття as A
    from реєстр_сила import обмежити_вагу
    записи, вихід = [], pathlib.Path(sys.argv[1]).resolve()
    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*а, **к):
            р = ф(*а, **к)
            for з in (з for з in (р if isinstance(р, list) else []) if isinstance(з, dict) and 'правило' in з):
                еф = обмежити_вагу([dict(з)])[0]
                записи.append([ф.__name__, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                               з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою'))])
            return р
        return виклик
    for ім in ('халява_і_поділ', 'лінія_ноги', 'взуття_і_поділ', 'видимість_краю'):
        ориг, обг = getattr(A, ім), обгорнути(getattr(A, ім))
        for м in [м for м in list(sys.modules.values()) if м is not None and getattr(м, ім, None) is ориг]:
            setattr(м, ім, обг)
    os.chdir(дж); sys.argv = [str(дж / 'прилади/розділи_гейтів.py')]; код = 0
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except SystemExit as е:
        код = е.code or 0
    with gzip.open(вихід, 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, код=код), ф, ensure_ascii=False)
    print('ЗАПИСАНО', len(записи), 'знахідок; код гейтів', код, file=sys.stderr)


if __name__ == '__main__':
    main()
