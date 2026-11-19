"""Офлайн ДО/ПІСЛЯ: повний каталог, сітка входів і знахідки в батареї; без моделей і мережі."""
import collections
import functools
import gzip
import hashlib
import json
import os
import pathlib
import runpy
import subprocess
import sys
import traceback

КОРІНЬ = pathlib.Path(__file__).resolve().parents[3]
ДЖЕРЕЛА = КОРІНЬ / 'джерела'
ТУТ = pathlib.Path(__file__).resolve().parent
ФАЙЛИ = ('палітра_принт', 'палітра_запити', 'колір_принти', 'реєстр_константи')
БАЗА = '0f7835a6d302'


def записати(шлях, дані):
    """Записати дані виміру в UTF-8."""
    шлях.write_text(json.dumps(дані, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def підготувати(стан):
    """Вибрати код ДО чи ПІСЛЯ; лише чотири файли ДО відновлюються в TMP задачі."""
    sys.path[:0] = [str(ДЖЕРЕЛА), str(ДЖЕРЕЛА / 'проби')]
    if стан == 'до':
        тека = pathlib.Path(os.environ['TMP']) / 'е3-колір-принт-до'
        тека.mkdir(exist_ok=True)
        for ім in ФАЙЛИ:
            дані = subprocess.check_output(['git', 'show', БАЗА + ':джерела/' + ім + '.py'], cwd=КОРІНЬ)
            (тека / (ім + '.py')).write_bytes(дані)
        sys.path.insert(0, str(тека))
    os.chdir(ДЖЕРЕЛА)


def каталог():
    """Прочитати весь каталог через продукт без завантаження фото й записати один вхід обох знімків."""
    import feed
    шлях = pathlib.Path(feed.каталог_на_диску('каталог_повний.xml'))
    д = feed.база_прогону(str(шлях), ліміт_фото=0)['каталог']
    with gzip.open(pathlib.Path(os.environ['TMP']) / 'е3_каталог.json.gz', 'wt', encoding='utf-8') as ф:
        json.dump(д, ф, ensure_ascii=False)
    факт = dict(речей=len(д), принтованих=sum(р.get('візерунок') not in (None, 'solid') for р in д),
                sha256_xml=hashlib.sha256(шлях.read_bytes()).hexdigest(), база=БАЗА)
    записати(ТУТ / 'каталог.json', факт)
    print(факт, flush=True)


def додаткові_входи():
    """Перевірити кожну річ каталогу з фактичними мірами, а макіяж — на всіх елементах і межі ΔE00."""
    import colorspace as cs
    import outfit
    with gzip.open(pathlib.Path(os.environ['TMP']) / 'е3_каталог.json.gz', 'rt', encoding='utf-8') as ф:
        д = json.load(ф)
    профіль = cs.features(cs.hx('#deb295'), cs.hx('#2b1d14'), cs.hx('#759087'))
    for р in д:
        yield 'каталог|' + р['id'], 'принт_придатність', [р], dict(
            F=профіль, масштаб_особи=0.5, зона_камуфляж=р.get('слот'), слот_принту=р.get('слот'), річ_ід=р['id'])
    елементи = outfit.елементи(д)
    for колір in ('#d23947', '#bd7183', '#9d644e'):
        yield 'макіяж|' + колір, 'макіяж_тон_у_тон', [елементи, dict(
            губи=dict(рід='обрана', hex=колір, зона='губи'))], {}
    for зміна in (0, 0.01, 0.1, 1, 4, 5, 6, 10):
        yield 'макіяж_межа|' + str(зміна), 'макіяж_тон_у_тон', [[dict(
            річ='межа', слот='верх', lab=cs.hx('#d23947'))], dict(
                губи=dict(рід='обрана', hex=cs.hex_з_lab((cs.hx('#d23947')[0] + зміна,
                                                      *cs.hx('#d23947')[1:])), зона='губи'))], {}


def знімок(стан):
    """Зберегти вагу кожної знахідки каталогу й граничної сітки на обраному коді."""
    import itertools
    import колір_принти as К
    import палітра_принт as П
    import палітра_запити as З
    from е3_принти_набори import набори
    функції = dict(принти=К.принти, принт_придатність=П.принт_придатність, макіяж_тон_у_тон=З.макіяж_тон_у_тон)
    лічба, входів = collections.Counter(), 0
    with gzip.open(ТУТ / (стан + '.jsonl.gz'), 'wt', encoding='utf-8') as ф:
        for назва, ім, args, kwargs in itertools.chain(набори(), додаткові_входи()):
            входів += 1
            рез = функції[ім](*args, **kwargs)
            for з in (рез['знахідки'] if isinstance(рез, dict) else рез):
                рядок = [назва, ім, з['правило'], з.get('речі'), з.get('суть'), з.get('сила'),
                         з.get('сила_нп'), з.get('блокує'), з.get('регістр'), з.get('полярність')]
                ф.write(json.dumps(рядок, ensure_ascii=False) + '\n')
                лічба[з['правило']] += 1
    print(стан, 'входів', входів, 'знахідок', sum(лічба.values()), sorted(лічба.items()), flush=True)


def звірити():
    """Перевірити кожну пару знахідок: склад, сила й вага лишилися тотожними."""
    import itertools
    лічба, зміни, зразки = collections.Counter(), collections.Counter(), {}
    with gzip.open(ТУТ / 'до.jsonl.gz', 'rt', encoding='utf-8') as а, gzip.open(
            ТУТ / 'після.jsonl.gz', 'rt', encoding='utf-8') as б:
        for д, п in itertools.zip_longest(а, б):
            assert д is not None and п is not None, 'різна кількість знахідок'
            д, п = json.loads(д), json.loads(п)
            assert д[:5] == п[:5] and д[7:] == п[7:], (д, п)
            лічба[д[2]] += 1
            assert д[5:7] == п[5:7], (д, п)
    факт = dict(знахідок=sum(лічба.values()), правила=dict(лічба),
                зміни=[dict(правило=k[0], сила_до=k[1], сила_після=k[2], до=k[3], після=k[4], кількість=v)
                        for k, v in sorted(зміни.items())], зразки=зразки)
    записати(ТУТ / 'звірка.json', факт)
    print(json.dumps(факт, ensure_ascii=False), flush=True)


def батарея(стан):
    """Виконати батарею й сім'ї pal/col/принтів до кінця, записати знахідки та всі коди виходу."""
    import колір_принти as К
    import палітра_принт as П
    import палітра_запити as З
    import palette
    import колір_образу
    мета, записи, результати = dict(скрипт=''), [], []
    def обгорнути(функція):
        """Зібрати вагу кожної знахідки з усіх трьох модулів частини."""
        @functools.wraps(функція)
        def виклик(*args, **kwargs):
            рез = функція(*args, **kwargs)
            for з in (рез.get('знахідки', []) if isinstance(рез, dict) else рез):
                записи.append([мета['скрипт'], функція.__name__, з.get('правило'), з.get('сила'), з.get('сила_нп')])
            return рез
        return виклик
    for модуль, ім in ((К, 'принти'), (П, 'принт_придатність'), (З, 'макіяж_тон_у_тон')):
        оригінал = getattr(модуль, ім)
        обгортка = обгорнути(оригінал)
        for м in list(sys.modules.values()):
            for ключ, значення in list(getattr(м, '__dict__', {}).items()):
                if значення is оригінал:
                    setattr(м, ключ, обгортка)
    скрипти = ['стенд_знімок.py', 'тест_живого_шляху.py', 'тест_протоколу.py',
               'прилади/розділи_гейтів.py', 'audit_contracts.py']
    for префікс in ('pal_', 'col_', 'принти_'):
        скрипти += [str(п.relative_to(ДЖЕРЕЛА)) for п in sorted((ДЖЕРЕЛА / 'проби').glob(префікс + '*.py'))
                    if п.stem not in ('pal_вердикт', 'pal_вимір')]
    for скрипт in скрипти:
        мета['скрипт'] = скрипт
        код, вихід, помилки, argv, шляхи = 0, sys.stdout, sys.stderr, sys.argv, list(sys.path)
        with (ТУТ / (стан + '-батарея.log')).open('a', encoding='utf-8') as ф:
            print('СТАРТ', скрипт, flush=True)
            try:
                sys.stdout = sys.stderr = ф
                sys.argv = [str(ДЖЕРЕЛА / скрипт)] + (['--дим'] if скрипт == 'стенд_знімок.py' else [])
                sys.path.insert(0, str((ДЖЕРЕЛА / скрипт).parent))
                runpy.run_path(str(ДЖЕРЕЛА / скрипт), run_name='__main__')
            except SystemExit as з:
                код = з.code or 0
            except Exception:
                код = 1
                traceback.print_exc()
            finally:
                sys.stdout, sys.stderr, sys.argv = вихід, помилки, argv
                sys.path[:] = шляхи
                os.chdir(ДЖЕРЕЛА)
        результати.append([скрипт, код])
        print('КІНЕЦЬ', скрипт, код, flush=True)
    записати(ТУТ / (стан + '-батарея.json'), dict(результати=результати, записи=записи))
    провали = [р for р in результати if р[1]]
    print('провали', провали, flush=True)
    return 1 if провали else 0


if __name__ == '__main__':
    режим = sys.argv[1]
    стан = sys.argv[2] if len(sys.argv) > 2 else 'після'
    підготувати(стан)
    sys.exit(dict(каталог=каталог, знімок=lambda: знімок(стан), звірити=звірити, батарея=lambda: батарея(стан))[режим]())
