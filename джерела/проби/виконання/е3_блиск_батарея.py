"""Батарея й запис кожної ваги блиску й металів; запуск з кореня дерева коду (ДО — робоче дерево бази).

`python3 <цей файл> <префікс>` — записати; `python3 <цей файл> звірити <ДО.json.gz> <ПІСЛЯ.json.gz>` — звірити
мультимножини (ключ знахідки → ефективна вага, підлога, блокує) за кожною перевіркою."""
import collections, functools, gzip, inspect, json, os, pathlib, runpy, subprocess, sys, time, traceback

ПРОБИ = ('mat_K-MAT-04.py', 'cra_K-CRA-07.py', 'clr_K-CLR-05.py', 'метал_нп_256.py', 'prykrasy_nema_2243.py',
         'pasport_prykrasy_108.py', 'prykrasy_riad_120.py', 'vyniatky_103b.py', 'cond_K-COND-04.py',
         'е3_місце_блиск_нейтраль.py', 'заміна_судді_ч_в.py')


def ключ(р):
    """Ідентичність знахідки без порядку речей."""
    return json.dumps(р[:4] + [sorted(map(str, р[4] or [])), р[5]], ensure_ascii=False)


def звірити(до_шлях, після_шлях):
    """Друк таблиці «перевірка · ДО · ПІСЛЯ · сирих змін · ефективних відмінностей»; відмінність — код 1."""
    def читати(ш):
        with gzip.open(ш, 'rt', encoding='utf-8') as ф:
            return json.load(ф)
    до, після = читати(до_шлях), читати(після_шлях)
    print('Провали ДО:', до['провали'], 'ПІСЛЯ:', після['провали'])
    print('| Перевірка | ДО | ПІСЛЯ | Сирих змін | Ефективних відмінностей |\n|---|---|---|---|---|')
    вади = []
    for назва in sorted({р[0] for р in до['записи'] + після['записи']}):
        д, п = ([р for р in x['записи'] if р[0] == назва] for x in (до, після))
        сирі = [collections.Counter((ключ(р), р[6]) for р in x) for x in (д, п)]
        еф = [collections.Counter((ключ(р), tuple(р[7:])) for р in x) for x in (д, п)]
        розб = sum(((еф[0] - еф[1]) + (еф[1] - еф[0])).values())
        print('| %s | %d | %d | %d | %d |' % (назва, len(д), len(п), sum((сирі[0] - сирі[1]).values()), розб))
        if розб or len(д) != len(п): вади.append(назва)
    print('записів', len(до['записи']), '→', len(після['записи']), '· відмінності:', вади)
    return 1 if вади or до['провали'] != після['провали'] else 0


def main():
    """Обгорнути `блиск_бюджет` і `метали` скрізь, де на них посилаються, і виконати гейти, дим і проби сім'ї."""
    префікс = os.path.abspath(sys.argv[1])
    корінь = pathlib.Path.cwd(); джерела = корінь / 'джерела'; sys.path[:0] = [str(джерела), str(джерела / 'проби')]
    import суд_блиск as СБ
    from реєстр_сила import обмежити_вагу
    assert pathlib.Path(СБ.__file__).resolve().parents[1] == корінь.resolve(), СБ.__file__
    записи, мітка = [], ['самоперевірка']

    def обгорнути(ф):
        @functools.wraps(ф)
        def виклик(*а, **к):
            результат = ф(*а, **к)
            for з in результат if isinstance(результат, list) else []:
                if isinstance(з, dict) and 'правило' in з:
                    еф = обмежити_вагу([dict(з)])[0]
                    записи.append([мітка[0], ф.__name__, з['правило'], з.get('суть'), з.get('речі'), з.get('сила'),
                                   з.get('сила_нп'), еф.get('сила_нп'), bool(еф.get('під_підлогою')), bool(з.get('блокує'))])
            return результат
        return виклик
    for ім, ф in list(vars(СБ).items()):
        if inspect.isfunction(ф) and ф.__module__ == СБ.__name__ and ім in ('блиск_бюджет', 'метали'):
            о = обгорнути(ф)
            for м in list(sys.modules.values()):
                for к, з in list(getattr(м, '__dict__', {}).items()):
                    if з is ф: setattr(м, к, о)
    СБ.метали([], {}, прикраси='золото')
    assert записи, 'записник не бачить знахідок блиску й металів'
    перевірки = [(джерела / 'стенд_знімок.py', ['--дим']), (джерела / 'тест_живого_шляху.py', []),
                 (джерела / 'тест_протоколу.py', []), (джерела / 'прилади/розділи_гейтів.py', []),
                 (джерела / 'audit_contracts.py', [])] + [(джерела / 'проби' / п, []) for п in ПРОБИ]
    провали = []
    with open(префікс + '.log', 'w', encoding='utf-8', buffering=1) as журнал:
        for шлях, арг in перевірки:
            мітка[0] = шлях.name; sys.argv[1:] = арг; os.chdir(джерела); шляхи = list(sys.path)
            sys.argv[0] = str(шлях); sys.path.insert(0, str(шлях.parent)); код = 0; поч = time.monotonic()
            вих, пом = sys.stdout, sys.stderr; sys.stdout = sys.stderr = журнал
            try: runpy.run_path(str(шлях), run_name='__main__')
            except SystemExit as з: код = з.code or 0
            except BaseException: код = 1; traceback.print_exc()
            finally: sys.stdout, sys.stderr = вих, пом; sys.path[:] = шляхи
            if код: провали.append([мітка[0], str(код)])
            print('КІНЕЦЬ', мітка[0], 'код', код, 'секунд', round(time.monotonic() - поч), flush=True)
        п = subprocess.run(['node', 'тест_показу.js'], cwd=джерела, stdout=журнал, stderr=журнал,
                           env=dict(os.environ, NODE_PATH='node_modules'))
        if п.returncode: провали.append(['тест_показу.js', str(п.returncode)])
        print('КІНЕЦЬ тест_показу.js код', п.returncode, flush=True)
    with gzip.open(префікс + '.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, провали=провали), ф, ensure_ascii=False)
    print('ГОТОВО', len(записи), 'знахідок; провали', провали, flush=True)


if __name__ == '__main__':
    if sys.argv[1] == 'звірити':
        sys.exit(звірити(*sys.argv[2:4]))
    main()
