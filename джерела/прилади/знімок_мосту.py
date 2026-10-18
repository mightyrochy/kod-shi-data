"""Знімок мосту: відтворити записані входи `bridge.виклик` / `виклик_а` у CPython або в Pyodide 0.26.4 під Node
і порівняти результати по викликах (крок 0.2-А; корінь К-6 «мірило не те»: проби міряють CPython, а продукт біжить у Pyodide).

  # 1. входи: стенд пише кожен виклик `містП` рядком JSON
  ZAPYS_VYKLYKIV=/tmp/входи.jsonl node аудит/проби/рв6_стенд.js <база> <корінь зі index.html> <pyodide> <сід>
  gzip -9 /tmp/входи.jsonl
  # (записані входи сід 3, повний каталог, `main` 0d9b1b97: `аудит/проби/знімок_входи_сід3.jsonl.gz` — типове значення --входи)
  # 2. відтворення: тіло сторінки (МОДУЛІ_ПОКАЗУ) беремо з тієї самої зібраної index.html, що й сторінка
  python3.12 джерела/прилади/знімок_мосту.py cpython  --сторінка index.html --входи входи.jsonl.gz --вихід cpy.jsonl
  python3    джерела/прилади/знімок_мосту.py pyodide  --сторінка index.html --входи входи.jsonl.gz --вихід pyo.jsonl \\
                                                      --pyodide /tmp/pyodide        # кеш: аудит/проби/стенд_pyodide_кеш.sh
  # 3. різниця по викликах
  python3 джерела/прилади/знімок_мосту.py --діф pyo.jsonl cpy.jsonl

Знімок — рядки JSON: перший про входи (sha256), далі по рядку на виклик `{н, ім, результат | помилка}`, результат — канонічний
JSON (сортовані ключі, float через `repr`, без пробілів), тож два однакові знімки збігаються байт у байт (`cmp`). Час, версія
й середовище лежать окремо (`<вихід>.час.json`) — вони різні в кожному прогоні. Той самий файл виконується і в CPython, і в Pyodide
(тільки stdlib), тому розбіжність у знімку — розбіжність середовищ, а не приладу."""
import argparse, asyncio, signal, gzip, hashlib, io, json, math, os, re, subprocess, sys, tempfile, time, base64, zipfile

ФОРМАТ = 1
ВХОДИ_ТИПОВІ = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'аудит', 'проби', 'знімок_входи_сід3.jsonl.gz')


def канон(о):
    """Канонічний JSON: сортовані ключі, без пробілів; float — `repr` (так друкує його `json`)."""
    return json.dumps(о, ensure_ascii=False, sort_keys=True, separators=(',', ':'), default=repr)


def прочитати(шлях):
    відкрити = gzip.open if шлях.endswith('.gz') else open
    with відкрити(шлях, 'rt', encoding='utf-8') as ф:
        return ф.read()


def модулі_зі_сторінки(шлях):
    """Байти zip `МОДУЛІ_ПОКАЗУ` зі зібраної `index.html` — ті самі, що сторінка розпаковує в Pyodide."""
    м = re.search(r'МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"', прочитати(шлях))
    if not м:
        sys.exit('у %s нема МОДУЛІ_ПОКАЗУ' % шлях)
    return base64.b64decode(м.group(1))


def підготувати(тека):
    """Те саме, що `підняти_міст_показу`: модулі в `тека`, вона в `sys.path` і поточна."""
    sys.dont_write_bytecode = True
    if тека not in sys.path:
        sys.path.insert(0, тека)
    os.chdir(тека)


async def прогнати(входи_текст, лише=None):
    """Входи (JSONL) → (текст знімка, час). Виклики йдуть по одному в порядку запису."""
    import bridge
    рядки = [json.loads(р) for р in входи_текст.splitlines() if р.strip()]
    if лише:
        рядки = рядки[:лише]
    знімок = [канон({'формат': ФОРМАТ, 'входи_sha256': hashlib.sha256(входи_текст.encode('utf-8')).hexdigest(),
                     'викликів': len(рядки)})]
    час, самозвіт = [], {}
    t_усе = time.perf_counter()
    for н, в in enumerate(рядки):
        вхід = json.loads(в['вхід'])
        t0 = time.perf_counter()
        запис = {'н': н, 'ім': в['ім']}
        try:
            р = await bridge.виклик_а(в['ім'], вхід) if в.get('async') else bridge.виклик(в['ім'], вхід)
            if isinstance(р, str):
                try: р = json.loads(р)
                except ValueError: pass
            if isinstance(р, dict) and isinstance(р.get('мс'), (int, float)):
                самозвіт[н] = р.pop('мс')    # власний замір виклику (`оцінка`) — час, а не результат: у знімок не йде
            запис['результат'] = р
        except Exception as e:
            запис['помилка'] = repr(e)[:300]
        час.append([н, в['ім'], round((time.perf_counter() - t0) * 1000, 2)])
        знімок.append(канон(запис))
    return '\n'.join(знімок) + '\n', {'мс_разом': round((time.perf_counter() - t_усе) * 1000, 1), 'виклики': час, 'самозвіт_мс': самозвіт}


def в_cpython(арг):
    тека = tempfile.mkdtemp(prefix='знімок_показ_')
    zipfile.ZipFile(io.BytesIO(модулі_зі_сторінки(арг.сторінка))).extractall(тека)
    підготувати(тека)
    знімок, час = asyncio.run(прогнати(прочитати(арг.входи), арг.лише))
    час.update({'середовище': 'cpython', 'версія': sys.version, 'hashseed': os.environ.get('PYTHONHASHSEED')})
    return знімок, час


def в_pyodide(арг):
    """Pyodide живе в Node: `знімок_мосту_pyodide.js` піднімає його з локального кешу й виконує цей самий файл."""
    вихід = tempfile.mkdtemp(prefix='знімок_пд_')
    команда = ['node', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'знімок_мосту_pyodide.js'),
               арг.сторінка, арг.pyodide, арг.входи, вихід, str(арг.лише or 0)]
    п = subprocess.run(команда, text=True, capture_output=True)
    if п.returncode:
        sys.exit('Pyodide: rc %d\n%s%s' % (п.returncode, п.stdout[-1500:], п.stderr[-1500:]))
    return open(os.path.join(вихід, 'знімок.jsonl'), encoding='utf-8').read(), json.load(open(os.path.join(вихід, 'час.json')))


def обрізати(з, н=90):
    з = канон(з) if not isinstance(з, str) else repr(з)
    return з if len(з) <= н else з[:н] + '…(%d)' % len(з)


def різниця(а, б, шлях='', вихід=None, ліміт=40):
    """Перші відмінні поля двох значень: (шлях, опис)."""
    вихід = [] if вихід is None else вихід
    if len(вихід) >= ліміт:
        return вихід
    if isinstance(а, dict) and isinstance(б, dict):
        for к in sorted(set(а) | set(б)):
            if к not in а or к not in б:
                вихід.append((шлях + '.' + к, 'є лише в %s' % ('першому' if к in а else 'другому')))
            else:
                різниця(а[к], б[к], шлях + '.' + к, вихід, ліміт)
    elif isinstance(а, list) and isinstance(б, list):
        if len(а) != len(б):
            вихід.append((шлях, 'довжина %d ≠ %d' % (len(а), len(б))))
        for i, (x, y) in enumerate(zip(а, б)):
            різниця(x, y, '%s[%d]' % (шлях, i), вихід, ліміт)
    elif isinstance(а, float) and isinstance(б, float) and а != б and math.isfinite(а) and math.isfinite(б):
        вихід.append((шлях, 'float %r ≠ %r (%.0f ulp)' % (а, б, abs(а - б) / math.ulp(max(abs(а), abs(б))))))
    elif isinstance(а, str) and isinstance(б, str) and а != б:
        i = next((k for k in range(min(len(а), len(б))) if а[k] != б[k]), min(len(а), len(б)))
        вихід.append((шлях, 'рядок з позиції %d: %r ≠ %r' % (i, а[max(0, i - 15):i + 25], б[max(0, i - 15):i + 25])))
    elif а != б or type(а) is not type(б):
        вихід.append((шлях, '%s ≠ %s' % (обрізати(а), обрізати(б))))
    return вихід


def діф(шлях_а, шлях_б):
    """Друкує різницю двох знімків по викликах; повертає кількість різних викликів, а непорівнювані знімки
    (інші входи чи кількість викликів) рахує за помилку (+1), щоб код виходу не підтверджував порівняння, якого не було."""
    ра, рб = [open(ш, encoding='utf-8').read().splitlines() for ш in (шлях_а, шлях_б)]
    ша, шб = json.loads(ра[0]), json.loads(рб[0])
    непорівнювані = ша['входи_sha256'] != шб['входи_sha256'] or len(ра) != len(рб)
    if ша['входи_sha256'] != шб['входи_sha256']:
        print('УВАГА: входи різні (%s… ≠ %s…) — знімки непорівнювані' % (ша['входи_sha256'][:10], шб['входи_sha256'][:10]))
    різні = []
    for н, (ла, лб) in enumerate(zip(ра[1:], рб[1:])):
        if ла != лб:
            різні.append((н, json.loads(ла), json.loads(лб)))
    разом = min(len(ра), len(рб)) - 1
    if len(ра) != len(рб):
        print('УВАГА: викликів %d ≠ %d — знімки непорівнювані' % (len(ра) - 1, len(рб) - 1))
    print('викликів %d · різних %d%s' % (разом, len(різні), ' · знімки тотожні' if not різні and not непорівнювані else ''))
    за_іменем = {}
    for н, а, б in різні:
        за_іменем[а['ім']] = за_іменем.get(а['ім'], 0) + 1
    if за_іменем:
        print('за викликом: ' + ', '.join('%s %d' % (к, v) for к, v in sorted(за_іменем.items())))
    for н, а, б in різні:
        print('  #%d %s' % (н, а['ім']))
        if ('помилка' in а) != ('помилка' in б) or 'помилка' in а:
            print('     помилка: %s ≠ %s' % (а.get('помилка', 'нема'), б.get('помилка', 'нема')))
            continue
        for п, о in різниця(а['результат'], б['результат']):
            print('     %s: %s' % (п or '/', о))
    return len(різні) + (1 if непорівнювані else 0)


def main():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)    # `| head` не друкує трасу
    р = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    р.add_argument('середовище', nargs='?', choices=('cpython', 'pyodide'))
    р.add_argument('--діф', nargs=2, metavar=('А', 'Б'), help='різниця двох знімків по викликах')
    р.add_argument('--сторінка', help='зібрана index.html (з МОДУЛІ_ПОКАЗУ)')
    р.add_argument('--входи', default=ВХОДИ_ТИПОВІ, help='входи мосту, JSONL (можна .gz); типово — записані у репозиторії')
    р.add_argument('--вихід', help='файл знімка (поруч <вихід>.час.json)')
    р.add_argument('--pyodide', default='/tmp/pyodide', help='кеш Pyodide 0.26.4 (середовище pyodide)')
    р.add_argument('--лише', type=int, help='лише перші N викликів')
    арг = р.parse_args()
    if арг.діф:
        sys.exit(1 if діф(*арг.діф) else 0)
    if not (арг.середовище and арг.сторінка and арг.вихід):
        р.error('потрібні середовище, --сторінка, --вихід (або --діф А Б)')
    арг.сторінка, арг.входи, арг.вихід = (os.path.abspath(x) for x in (арг.сторінка, арг.входи, арг.вихід))
    знімок, час = (в_cpython if арг.середовище == 'cpython' else в_pyodide)(арг)
    open(арг.вихід, 'w', encoding='utf-8').write(знімок)
    json.dump(час, open(арг.вихід + '.час.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print('%s: %d викликів за %.1f с · %s' % (арг.середовище, знімок.count('\n') - 1, час['мс_разом'] / 1000,
                                             час['версія'].split('\n')[0]))


if __name__ == '__main__':
    main()
