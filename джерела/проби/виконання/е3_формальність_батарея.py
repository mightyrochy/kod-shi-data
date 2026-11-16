"""Батарея з записом ваги кожної знахідки функцій `формальність.py`; аргументи: префікс, коміт ДО."""
def main():
    """Виконати дим, шлях, протокол, гейти, контракти й проби ошатності; зберегти ваги на базі або голові."""
    import gzip, json, os, pathlib, runpy, sys, time, traceback, functools, inspect
    корінь = pathlib.Path(__file__).resolve().parents[3]; джерела = корінь / 'джерела'
    sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    префікс = os.path.abspath(sys.argv[1]); база = sys.argv[2] if len(sys.argv) > 2 else None
    if база:
        from виконання.е3_база import встановити
        встановити(база, ('формальність',))
    import формальність as F
    from реєстр_сила import обмежити_вагу
    записи = []; стан = dict(мітка='')
    def обгорнути(функція):
        @functools.wraps(функція)
        def виклик(*а, **п):
            результат = функція(*а, **п)
            for з in результат if isinstance(результат, list) else []:
                if isinstance(з, dict) and 'правило' in з:
                    записи.append([стан['мітка'], функція.__name__, з.get('правило'), з.get('суть'), з.get('речі'),
                                   з.get('сила'), з.get('сила_нп'), обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return результат
        return виклик
    for ім, функція in list(vars(F).items()):
        if inspect.isfunction(функція) and функція.__module__ == F.__name__:
            обгортка, ід = обгорнути(функція), id(функція)
            for модуль in list(sys.modules.values()):
                for ключ, значення in list(getattr(модуль, '__dict__', {}).items()):
                    if id(значення) == ід: setattr(модуль, ключ, обгортка)
    стан['мітка'] = 'самоперевірка записника'
    F.вимоги_коду([dict(річ='x', слот='взуття', тип='кросівки')], 'cocktail')
    assert записи, 'записник не бачить знахідок формальності'
    перевірки = [джерела / 'стенд_знімок.py', джерела / 'тест_живого_шляху.py', джерела / 'тест_протоколу.py',
                 джерела / 'прилади/розділи_гейтів.py', джерела / 'audit_contracts.py']
    перевірки += sorted(ш for ш in (джерела / 'проби').glob('*.py')
                        if ш.name.split('_')[0] in ('koh', 'occ', 'traur', 'oshatnist', 'formalnist', 'vzuttia'))
    провали = []
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях in перевірки:
            стан['мітка'] = шлях.name; вихід, помилки = sys.stdout, sys.stderr
            sys.argv = [str(шлях)] + (['--дим'] if шлях.name == 'стенд_знімок.py' else []); os.chdir(джерела)
            попередні = list(sys.path); sys.path.insert(0, str(шлях.parent))
            print('СТАРТ', шлях.name, flush=True); початок = time.monotonic(); sys.stdout = sys.stderr = журнал; код = 0
            try: runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as збій: код = збій.code or 0
            except BaseException: код = 1; traceback.print_exc()
            finally: sys.stdout, sys.stderr = вихід, помилки; sys.path[:] = попередні
            if код: провали.append([шлях.name, код])
            print('КІНЕЦЬ', шлях.name, 'код', код, 'секунд', round(time.monotonic() - початок), flush=True)
    with gzip.open(префікс + '.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, провали=провали), ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    main()
