"""Гейти й проби сімей з записом ваги чотирьох аксесуарних файлів; аргументи: префікс [коміт ДО]."""
def main():
    """Виконати перевірки й зберегти кожну знахідку, яку повернула функція цих файлів."""
    import gzip, hashlib, inspect, json, os, pathlib, runpy, sys, time, traceback, functools
    корінь = pathlib.Path.cwd(); джерела = корінь / 'джерела'; sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    префікс = sys.argv[1]
    if len(sys.argv) > 2:
        from виконання.е3_акс_база import встановити
        встановити(sys.argv[2])
    from виконання.е3_акс_база import МОДУЛІ
    import importlib
    from реєстр_сила import обмежити_вагу
    записи, мітка = [], ['']
    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **kw):
            р = ф(*a, **kw)
            for з in р if isinstance(р, list) else []:
                if isinstance(з, dict) and 'правило' in з:
                    відбиток = hashlib.md5(json.dumps([з.get('суть'), з.get('речі'), з.get('блокує')], ensure_ascii=False,
                                                      sort_keys=True, default=str).encode()).hexdigest()[:12]
                    записи.append([мітка[0], ф.__name__, з['правило'], відбиток, з.get('сила'), з.get('сила_нп'),
                                   обмежити_вагу([dict(з)])[0].get('сила_нп')])
            return р
        return виклик
    for ім in МОДУЛІ:
        М = importlib.import_module(ім)
        for ф in [ф for ф in vars(М).values() if inspect.isfunction(ф) and ф.__module__ == ім]:
            о, і = обгорнути(ф), id(ф)
            for м in list(sys.modules.values()):
                for к, з in list(getattr(м, '__dict__', {}).items()):
                    if id(з) == і: setattr(м, к, о)
    перевірки = [джерела / 'прилади/розділи_гейтів.py'] + sorted(p for п in ('acc_', 'sho_', 'tsina_') for p in (джерела / 'проби').glob(п + '*.py'))
    провали = []
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях in перевірки:
            мітка[0] = шлях.name; вих, пом = sys.stdout, sys.stderr; sys.argv = [str(шлях)]; os.chdir(джерела)
            шляхи = list(sys.path); sys.path.insert(0, str(шлях.parent)); початок = time.monotonic(); код = 0
            sys.stdout = sys.stderr = журнал
            try: runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as з: код = з.code or 0
            except BaseException: код = 1; traceback.print_exc()
            finally: sys.stdout, sys.stderr = вих, пом; sys.path[:] = шляхи
            if код: провали.append([мітка[0], str(код)])
            print('КІНЕЦЬ', мітка[0], 'код', код, 'с', round(time.monotonic() - початок), flush=True)
    with gzip.open(префікс + '.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(записи, ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    main()
