"""Гейти й проби принтів із записом ваги кожної знахідки принтів; аргументи: корінь дерева, вихід .json.gz."""


def main():
    """Виконати `розділи_гейтів.py` і проби принтів дерева; зберегти сиру й обмежену вагу, опору (ГГ-1) та коди виходу."""
    import functools, gzip, json, os, pathlib, runpy, sys, time, traceback
    джерела = pathlib.Path(sys.argv[1]).resolve() / 'джерела'
    sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    os.chdir(джерела)
    import колір_принти as К, палітра_принт as П
    from реєстр_сила import обмежити_вагу, опора
    assert pathlib.Path(К.__file__).resolve().parent == джерела, К.__file__
    записи, стан = [], dict(мітка='')

    def обгорнути(функція):
        """Записати кожну знахідку, яку повертає функція принтів."""
        @functools.wraps(функція)
        def виклик(*аргументи, **параметри):
            рез = функція(*аргументи, **параметри)
            for з in (рез.get('знахідки', []) if isinstance(рез, dict) else рез if isinstance(рез, list) else []):
                if isinstance(з, dict) and 'правило' in з:
                    еф = обмежити_вагу([dict(з)])[0]
                    записи.append([стан['мітка'], функція.__name__, з['правило'], з.get('суть'), з.get('речі'),
                                   з.get('сила'), з.get('блокує'), з.get('сила_нп'), еф.get('сила_нп'), опора(з)])
            return рез
        return виклик
    for модуль_ф, ім in ((К, 'принти'), (П, 'принт_придатність')):
        оригінал = getattr(модуль_ф, ім); обгортка = обгорнути(оригінал)
        for модуль in list(sys.modules.values()):
            for ключ, значення in list(getattr(модуль, '__dict__', {}).items()):
                if значення is оригінал:
                    setattr(модуль, ключ, обгортка)
    стан['мітка'] = 'самоперевірка'
    К.принти([dict(id='a', візерунок='камуфляж')], [dict(річ='a', сім_я=None)])
    assert записи, 'записувач не бачить знахідок принтів'
    скрипти = ['прилади/розділи_гейтів.py'] + ['проби/%s.py' % п for п in (
        'col_K-COL-10', 'pal_K-PAL-07', 'vyniatky_103c', 'заміна_діагнози', 'заміна_пояснення_чб',
        'принти_вхід', 'принти_невідома_різниця_світлоти', 'фізика_дрібні_краї')]
    провали = []
    with open(sys.argv[2] + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for скрипт in скрипти:
            стан['мітка'] = скрипт; шлях = джерела / скрипт
            вихід, помилки, argv, шляхи = sys.stdout, sys.stderr, sys.argv, list(sys.path)
            sys.argv = [str(шлях)]; sys.path.insert(0, str(шлях.parent)); код = 0
            print('СТАРТ', скрипт, flush=True); початок = time.monotonic()
            sys.stdout = sys.stderr = журнал
            try:
                runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as збій:
                код = збій.code or 0
            except BaseException:
                код = 1; traceback.print_exc()
            finally:
                sys.stdout, sys.stderr, sys.argv = вихід, помилки, argv; sys.path[:] = шляхи; os.chdir(джерела)
            if код:
                провали.append([скрипт, код])
            print('КІНЕЦЬ', скрипт, 'код', код, 'секунд', round(time.monotonic() - початок), flush=True)
    with gzip.open(sys.argv[2], 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, провали=провали), ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    main()
