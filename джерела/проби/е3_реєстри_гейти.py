"""Ваги знахідок шару реєстрів на гейтах і пробах: вихід, дерево, скрипти з його `джерела/`."""
import functools, gzip, json, os, pathlib, runpy, sys, traceback
ДЕРЕВО = pathlib.Path(sys.argv[2]).resolve()
ДЖ = ДЕРЕВО / 'джерела'
ВИХІД, СКРИПТИ = sys.argv[1], sys.argv[3:]


def main():
    """Обгорнути `реєстри.перевірити` записом і прогнати названі скрипти до кінця."""
    sys.path[:0] = [str(ДЖ)]
    import реєстри as Р
    from реєстр_сила import обмежити_вагу
    assert Р.__file__.startswith(str(ДЕРЕВО)), Р.__file__
    записи, коди, мітка, оригінал = [], {}, [''], Р.перевірити
    @functools.wraps(оригінал)
    def перевірити(*а, **к):
        знахідки, о = оригінал(*а, **к)
        for з in знахідки:
            еф = обмежити_вагу([dict(з)])[0]
            записи.append([мітка[0], '', з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                           з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою'))])
        return знахідки, о
    Р.перевірити = перевірити
    for скрипт in СКРИПТИ:
        мітка[0], шлях, sys.argv[:] = скрипт, ДЖ / скрипт, [str(ДЖ / скрипт)]
        os.chdir(ДЖ); sys.path.insert(0, str(шлях.parent)); код = 0
        try:
            runpy.run_path(str(шлях), run_name='__main__')
        except SystemExit as е:
            код = е.code or 0
        except BaseException:
            код = 1; traceback.print_exc()
        sys.path.remove(str(шлях.parent)); коди[скрипт] = str(код)[:200]
        print('КІНЕЦЬ', скрипт, 'код', код, 'записів', len(записи), file=sys.__stderr__, flush=True)
    with gzip.open(ВИХІД, 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, коди=коди), ф, ensure_ascii=False)


if __name__ == '__main__':
    main()
