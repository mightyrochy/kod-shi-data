"""Запис кожної ваги знахідок названих модулів у гейтах і пробах; аргументи: префікс, модулі через кому,
файл переліку проб (рядок — ім'я в `проби/` і аргументи), [коміт ДО]."""
def main():
    """Обгорнути функції модулів записом, прогнати гейти й проби, зберегти ваги й коди завершення."""
    import gzip, json, pathlib, runpy, sys, time, traceback, functools, inspect, importlib, os, resource
    корінь = pathlib.Path.cwd(); джерела = корінь / 'джерела'; sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    префікс, модулі, перелік = sys.argv[1], tuple(sys.argv[2].split(',')), sys.argv[3]
    if len(sys.argv) > 4:
        from виконання.е3_база import встановити
        встановити(sys.argv[4], модулі)
    from реєстр_сила import обмежити_вагу
    записи = gzip.open(префікс + '.jsonl.gz', 'wt', encoding='utf-8'); мітка = ['']; лічба = [0]
    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*a, **k):
            р = ф(*a, **k)
            for з in р if isinstance(р, list) else []:
                if isinstance(з, dict) and 'правило' in з:
                    еф = обмежити_вагу([dict(з)])[0]
                    записи.write(json.dumps([мітка[0], ф.__name__, з.get('правило'), з.get('суть'), з.get('речі'),
                                 з.get('сила'), з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою'))],
                                 ensure_ascii=False) + '\n'); лічба[0] += 1
            return р
        return виклик
    for ім in модулі:
        м = importlib.import_module(ім)
        for н, ф in list(vars(м).items()):
            if inspect.isfunction(ф) and ф.__module__ == ім:
                о, і = обгорнути(ф), id(ф)
                for мод in list(sys.modules.values()):
                    for ключ, знач in list(vars(мод).items()) if hasattr(мод, '__dict__') else []:
                        if id(знач) == і: setattr(мод, ключ, о)
    перевірки = [(джерела / 'прилади/розділи_гейтів.py', [])] + [
        (джерела / 'проби' / р.split()[0], р.split()[1:]) for р in pathlib.Path(перелік).read_text(encoding='utf-8').split('\n') if р.strip()]
    провали = []
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях, арг in перевірки:
            мітка[0] = шлях.name; вих, пом = sys.stdout, sys.stderr; sys.argv = [str(шлях), *арг]; os.chdir(джерела)
            шляхи = list(sys.path); sys.path.insert(0, str(шлях.parent)); п = time.monotonic(); код = 0
            sys.stdout = sys.stderr = журнал
            try: runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as з: код = з.code or 0
            except BaseException: код = 1; traceback.print_exc()
            finally: sys.stdout, sys.stderr = вих, пом; sys.path[:] = шляхи
            if код: провали.append([мітка[0], код])
            print('КІНЕЦЬ', мітка[0], 'код', код, 'секунд', round(time.monotonic() - п),
                  'пам МБ', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024, flush=True)
    записи.close()
    pathlib.Path(префікс + '.провали.json').write_text(json.dumps(провали, ensure_ascii=False), encoding='utf-8')
    print('ГОТОВО', лічба[0], 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    main()
