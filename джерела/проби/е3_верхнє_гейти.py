"""Ваги знахідок `верхнє_суд` / `верхнє_догляд` під повним прогоном `розділи_гейтів.py`.

Аргументи: вихідний .json.gz, [коміт ДО]. Обгортає кожну функцію двох модулів у всіх
модулях, що тримають на неї посилання (фасад `outer` реекспортує імена), і пише сиру й
обмежену вагу кожної поверненої знахідки з міткою функції."""
import functools, gzip, inspect, json, os, pathlib, runpy, sys
КОРІНЬ = pathlib.Path(__file__).resolve().parents[2]
ДЖ = КОРІНЬ / 'джерела'
sys.path[:0] = [str(ДЖ), str(ДЖ / 'проби')]


def main():
    """Обгорнути, прогнати гейти, зберегти записи й код виходу."""
    if len(sys.argv) > 2:
        from е3_верхнє_знімок import база
        база(sys.argv[2])
    import верхнє_суд as ВС, верхнє_догляд as ВД, outer  # noqa: F401 — фасад до обгортання
    from реєстр_сила import обмежити_вагу
    записи = []

    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **kw):
            р = ф(*a, **kw)
            for з in р if isinstance(р, list) else []:
                if isinstance(з, dict) and 'правило' in з:
                    записи.append([ф.__module__, ф.__name__, з.get('правило'), з.get('суть'), з.get('речі'),
                                   з.get('сила'), з.get('блокує'), з.get('сила_нп'),
                                   обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return р
        return виклик
    for М in (ВС, ВД):
        for ім, ф in list(vars(М).items()):
            if inspect.isfunction(ф) and ф.__module__ == М.__name__:
                о, ід = обгорнути(ф), id(ф)
                for м in list(sys.modules.values()):
                    for к, з in list(getattr(м, '__dict__', {}).items()):
                        if id(з) == ід:
                            setattr(м, к, о)
    ВД.догляд([dict(id='с', слот='верхній_шар', матеріал='вовна')], реагенти=True)
    assert записи, 'записник не бачить знахідок'
    записи.clear()
    os.chdir(ДЖ)
    sys.argv = [str(ДЖ / 'прилади/розділи_гейтів.py')]
    sys.path.insert(0, str(ДЖ / 'прилади'))
    код = 0
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except SystemExit as е:
        код = е.code or 0
    with gzip.open(ВИХІД, 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, код=код), ф, ensure_ascii=False)
    print('ЗАПИСАНО', len(записи), 'знахідок; код гейтів', код, file=sys.__stdout__, flush=True)


if __name__ == '__main__':
    ВИХІД = str(pathlib.Path(sys.argv[1]).resolve())
    main()
