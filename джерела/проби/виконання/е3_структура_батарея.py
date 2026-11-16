"""Гейти й проби acc_/cra_ із записом кожної знахідки `аксесуари_структура`; аргументи: префікс, коміт ДО."""
def main():
    """Виконати гейти й проби, зберегти сиру й обмежену вагу знахідок восьми емітентів файлу."""
    import gzip, json, os, pathlib, runpy, sys, time, traceback, functools, inspect
    корінь = pathlib.Path.cwd(); джерела = корінь / 'джерела'; sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    префікс = sys.argv[1]; база = sys.argv[2] if len(sys.argv) > 2 else None
    if база:
        from виконання.е3_база import встановити
        встановити(база, ('аксесуари_структура',))
    import аксесуари_структура as А
    from реєстр_сила import обмежити_вагу
    записи, мітка = [], ['']
    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **k):
            р = ф(*a, **k)
            for з in (р[1] if ф.__name__ == 'рятівник_приобличчя' else р) or []:
                if isinstance(з, dict) and 'правило' in з:
                    записи.append([мітка[0], ф.__name__, з.get('правило'), з.get('суть'), з.get('речі'), з.get('сила'),
                                   з.get('блокує'), з.get('сила_нп'), обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return р
        return виклик
    for ім in ('аксесуар_як_структура', 'передумови_пояса', 'масштаб_аксесуара', 'асиметрія_інтересу',
               'рятівник_приобличчя', 'місце_не_обране', 'віднімання', 'формат_хустки'):
        ориг = getattr(А, ім); обг = обгорнути(ориг)
        for м in list(sys.modules.values()):
            for к, v in list(getattr(м, '__dict__', {}).items()):
                if v is ориг: setattr(м, к, обг)
    А.масштаб_аксесуара([{'слот': 'сумка', 'формат': 'великий', 'id': 'x'}])
    assert записи, 'записник не бачить знахідок'; записи.clear()
    перевірки = [джерела / 'прилади/розділи_гейтів.py'] + sorted((джерела / 'проби').glob('acc_*.py')) \
        + sorted((джерела / 'проби').glob('cra_*.py'))
    провали = []
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях in перевірки:
            мітка[0] = шлях.name; о, е = sys.stdout, sys.stderr; sys.argv = [str(шлях)]; os.chdir(джерела)
            шляхи = list(sys.path); sys.path.insert(0, str(шлях.parent)); п = time.monotonic(); код = 0
            sys.stdout = sys.stderr = журнал
            try: runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as з: код = з.code or 0
            except BaseException: код = 1; traceback.print_exc()
            finally: sys.stdout, sys.stderr = о, е; sys.path[:] = шляхи
            if код: провали.append([мітка[0], str(код)])
            print('КІНЕЦЬ', мітка[0], 'код', код, 'с', round(time.monotonic() - п), flush=True)
    with gzip.open(префікс + '.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, провали=провали), ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    main()
