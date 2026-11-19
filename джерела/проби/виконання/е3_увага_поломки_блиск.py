"""Запис ваг частини на каталозі й батареї; база підставляється імпортом із коміту.

Запуск з кореня: <каталог|батарея|точково> <вихід.json.gz> [коміт ДО]; звірити <ДО> <ПІСЛЯ>.
Звірка місць: місця <прилад-ДО.txt> <прилад-ПІСЛЯ.txt> <коміт ДО>.
Моделей і мережі не використовує. Повні журнали лежать поряд із результатом.
"""
import collections
import gzip
import hashlib
import itertools
import json
import os
import pathlib
import runpy
import shutil
import subprocess
import sys
import traceback

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
ДЖЕРЕЛА = КОРІНЬ / 'джерела'
sys.path[:0] = [str(ДЖЕРЕЛА), str(ДЖЕРЕЛА / 'проби')]
МОДУЛІ = ('регістр_уваги', 'поломки', 'суд_блиск', 'реєстр_константи')
ПРОБИ = ('mat_K-MAT-04', 'cra_K-CRA-07', 'clr_K-CLR-05', 'метал_нп_256',
         'prykrasy_nema_2243', 'pasport_prykrasy_108', 'prykrasy_riad_120',
         'vyniatky_103b', 'cond_K-COND-04', 'е3_місце_блиск_нейтраль',
         'заміна_судді_ч_в', 'е3_місце_увага', 'увага_заяви',
         'мета_уваги_суд', 'мета_уваги_пул', 'рука2_хибні_суд',
         'рука2_хибні_контекст', 'рука2_регістр', 'рука2_регістр_тінь',
         'руки_т11', 'vzuttia_руки', 'сила_частка', 'сила_підлога_емісії',
         'сила_стани_входу', 'поділ_суд_ast', 'поділ_реєстр_правил_ast')


def читати(шлях):
    """Прочитати стиснений запис виміру."""
    with gzip.open(шлях, 'rt', encoding='utf-8') as ф:
        return json.load(ф)


def звірити_місця(до, після, база):
    """Звірити мультимножини файл · пункт · функція, залишок частини назвати явно."""
    from е3_місця import місця
    д = місця(pathlib.Path(до).read_text(encoding='utf-8-sig'), база)
    п = місця(pathlib.Path(після).read_text(encoding='utf-8-sig'))
    файли = {'джерела/' + м + '.py' for м in МОДУЛІ[:3]}
    частина = lambda м: sum(н for к, н in м.items() if к[0] in файли)
    print('частина:', частина(д), '→', частина(п), '; нових:', sum((п-д).values()))
    for к, н in sorted((д-п).items()):
        print('знято:', ' · '.join(к), н)
    for к, н in sorted(п.items()):
        if к[0] in файли:
            print('лишилось:', ' · '.join(к), н)
    assert not (п-д), 'додано місця кореня'
    assert {к: н for к, н in д.items() if к[0] not in файли} == {
        к: н for к, н in п.items() if к[0] not in файли}, 'зміни поза частиною'


def звірити(до, після):
    """Звірити кожну знахідку та надрукувати переходи ваг за правилом."""
    д, п = читати(до), читати(після)
    print('записів:', len(д['записи']), '→', len(п['записи']))
    def групи(записи):
        вих = collections.defaultdict(collections.Counter)
        for р in записи:
            ключ = json.dumps(р[:2] + [sorted(map(str, р[2] or []))], ensure_ascii=False)
            вих[ключ][tuple(р[3:])] += 1
        return вих
    гд, гп = групи(д['записи']), групи(п['записи'])
    зміни, порушення = collections.Counter(), 0
    разом = collections.Counter(р[1] for р in д['записи'])
    for ключ in гд.keys() | гп.keys():
        а, б = гд.get(ключ, collections.Counter()), гп.get(ключ, collections.Counter())
        if sum(а.values()) != sum(б.values()):
            порушення += 1
        if а != б:
            зміни[json.loads(ключ)[1], str(dict(а-б)), str(dict(б-а))] += 1
    print('змін складу:', порушення, '; змін ваги/сили:', sum(зміни.values()))
    print('| Правило | ДО (сила, сира/ефективна вага, гейт) | ПІСЛЯ | Кількість |')
    print('|---|---|---|---|')
    for правило, н in sorted(разом.items()):
        if not any(к[0] == правило for к in зміни):
            print('| %s | без змін | без змін | %d |' % (правило, н))
    for (правило, а, б), н in sorted(зміни.items()):
        print('| %s | %s | %s | %d |' % (правило, а, б, н))
    print('провали ДО:', д.get('провали', []))
    print('провали ПІСЛЯ:', п.get('провали', []))
    assert not порушення, 'змінився склад знахідок'
    assert not зміни, 'змінились ваги знахідок; потрібна оцінка переходів'


def каталог(запис):
    """Кожна річ каталогу для уваги, усі набори металів і поломки каблука."""
    import feed as Ф
    import outfit as О
    import регістр_уваги as У
    import суд_блиск as Б
    import поломки as П
    from е3_блиск_набори import набори
    кеш = pathlib.Path(os.environ['TMP']) / 'каталог.json.gz'
    if not кеш.exists():
        архів = кеш.parent / 'каталог_повний.xml.gz'
        shutil.copyfile(КОРІНЬ / архів.name, архів)
        речі = Ф.база_прогону(Ф.каталог_на_диску('каталог_повний.xml', тека=str(кеш.parent)),
                            ліміт_фото=0)['каталог']
        with gzip.open(кеш, 'wt', encoding='utf-8') as ф:
            json.dump(речі, ф, ensure_ascii=False)
    речі = читати(кеш)
    print('каталог:', len(речі), 'речей', flush=True)
    for р in речі:
        Е = О.елементи([р])
        for мета, зони in itertools.product(('приховати', 'експресія'), (None, ['живіт'], ['ноги'])):
            for з in У.знахідка_уваги(Е, [р], мета, зони_мети=зони):
                запис(str(р['id']) + '@' + мета + str(зони), з)
        h = р.get('каблук_см')
        if р.get('слот') == 'взуття' and isinstance(h, (float, int)):
            for год, коеф in itertools.product((0.5, 4.0, 9.0), (1.0, 1.5)):
                for з in П._каблук_вищий([], р, h, год, коеф):
                    запис(str(р['id']) + '@каблук' + str((год, коеф)), з)
    for назва, функція, а, к in набори():
        for з in getattr(Б, функція)(*а, **к):
            запис(назва + '@' + функція, з)
    # Межі всіх змінених формул, включно з рукою 2 й відсутньою площею.
    for h, год, коеф in itertools.product((0, 2, 4, 5.9, 6, 9), (0, 0.5, 4, 8, 16), (1, 1.5)):
        for з in П._каблук_вищий([], dict(id='межа', слот='взуття'), h, год, коеф):
            запис('межа-каблук' + str((h, год, коеф)), з)
    for near in (0, 0.1, 0.25, 0.5, 1):
        р = dict(id='метал-межа', річ='метал-межа', метал='золото',
                 місце_речі=dict(джерело='вимір', видно=1, біля_обличчя=near))
        for з in П._метал_навпаки([], 0, р, 'теплий', lambda: 1):
            запис('межа-метал' + str(near), з)
    return dict(каталог=len(речі), sha256=hashlib.sha256((КОРІНЬ / 'каталог_повний.xml.gz').read_bytes()).hexdigest())


def точково(запис):
    """Межі прийнятих правок уваги й металу без побудови повного каталогу."""
    import регістр_уваги as У
    import місце_речі as М
    import поломки as П
    for L, C, площа, мета in itertools.product((30., 50., 90.), (5., 50., 80.),
                                               (None, 0., .02, .25, .4), ('приховати', 'експресія')):
        р = dict(id='увага', слот='верх', lab=[L, C, 0.])
        е = dict(р, річ=р['id'], площа=площа,
                 місце_речі=dict(М.записати(р), видно=1., видно_джерело='стилістка'))
        for з in У.знахідка_уваги([е], [р], мета):
            запис('увага' + str((L, C, площа, мета)), з)
    for near in (0, .1, .25, .5, 1):
        р = dict(id='метал', річ='метал', метал='золото',
                 місце_речі=dict(джерело='вимір', видно=1., біля_обличчя=near))
        for з in П._метал_навпаки([], 0, р, 'теплий', lambda: 1):
            запис('метал' + str(near), з)
    return dict(сцен='90 комбінацій уваги та 5 положень металу')


def батарея(запис, журнал):
    """Дим, шлях, протокол, гейти, контракти та проби сім'ї до кінця."""
    import реєстр_сила as С
    import фід_каталог as Ф
    фіди = pathlib.Path(os.environ['TMP']) / 'фіди'
    фіди.mkdir(exist_ok=True)
    for ім in ('каталог_повний.xml.gz', 'каталог_brief.xml.gz'):
        джерело = next(к / ім for к in (КОРІНЬ, ДЖЕРЕЛА) if (к / ім).exists())
        shutil.copyfile(джерело, фіди / ім)
    каталог_на_диску = Ф.каталог_на_диску
    def окремий_каталог(перевага=None, тека=None):
        return каталог_на_диску(перевага, тека=тека or str(фіди))
    for м in list(sys.modules.values()):
        for ім, з in list(getattr(м, '__dict__', {}).items()):
            if з is каталог_на_диску:
                setattr(м, ім, окремий_каталог)
    ориг, мітка = С.зн, ['початок']
    def емітент(*а, **к):
        з = ориг(*а, **к)
        запис(мітка[0], з)
        return з
    for м in list(sys.modules.values()):
        for ім, з in list(getattr(м, '__dict__', {}).items()):
            if з is ориг:
                setattr(м, ім, емітент)
    перевірки = [('стенд_знімок.py', ['--дим']), ('тест_живого_шляху.py', []),
                 ('тест_протоколу.py', []), ('прилади/розділи_гейтів.py', []), ('audit_contracts.py', [])]
    перевірки += [('проби/' + ім + '.py', []) for ім in ПРОБИ]
    провали = []
    with open(журнал, 'w', encoding='utf-8') as ф:
        for ім, арг in перевірки:
            вих, пом, шляхи = sys.stdout, sys.stderr, list(sys.path)
            os.chdir(ДЖЕРЕЛА)
            sys.argv[:] = [str(ДЖЕРЕЛА / ім)] + арг
            sys.path.insert(0, str((ДЖЕРЕЛА / ім).parent))
            мітка[0] = ім
            sys.stdout = sys.stderr = ф
            код = 0
            try:
                runpy.run_path(str(ДЖЕРЕЛА / ім), run_name='__main__')
            except SystemExit as п:
                код = п.code or 0
            except Exception:
                код = 1
                traceback.print_exc()
            finally:
                sys.stdout, sys.stderr, sys.path[:] = вих, пом, шляхи
                ф.flush()
            if код:
                провали.append([ім, str(код)])
            print('КІНЕЦЬ', ім, 'код', код, flush=True)
        п = subprocess.run(['node', 'тест_показу.js'], cwd=ДЖЕРЕЛА, stdout=ф, stderr=ф,
                           env=dict(os.environ, NODE_PATH='node_modules'))
        if п.returncode:
            провали.append(['тест_показу.js', str(п.returncode)])
    return dict(провали=провали)


def main():
    """Зберегти відтворювані дані одного дерева або звірити пару."""
    режим, вихід = sys.argv[1:3]
    if режим == 'звірити':
        return звірити(вихід, sys.argv[3])
    if режим == 'місця':
        return звірити_місця(вихід, sys.argv[3], sys.argv[4])
    шлях = pathlib.Path(вихід).resolve()
    тимчасова = pathlib.Path(str(шлях) + '.tmp')
    тимчасова.mkdir(parents=True, exist_ok=True)
    os.environ['TMP'] = os.environ['TEMP'] = str(тимчасова)
    if len(sys.argv) > 3:
        from виконання.е3_база import встановити
        встановити(sys.argv[3], МОДУЛІ)
    from реєстр_сила import обмежити_вагу
    записи = []
    def запис(назва, з):
        еф = обмежити_вагу([dict(з)])[0]
        записи.append([назва, з['правило'], з.get('речі'), з.get('сила'),
                       з.get('сила_нп'), еф.get('сила_нп'), bool(з.get('блокує'))])
    if режим == 'каталог':
        мета = каталог(запис)
    elif режим == 'точково':
        мета = точково(запис)
    else:
        мета = батарея(запис, str(шлях) + '.log')
    with gzip.open(шлях, 'wt', encoding='utf-8') as ф:
        json.dump(dict(записи=записи, **мета), ф, ensure_ascii=False)
    print('ГОТОВО:', len(записи), 'знахідок;', мета, flush=True)


if __name__ == '__main__':
    main()
