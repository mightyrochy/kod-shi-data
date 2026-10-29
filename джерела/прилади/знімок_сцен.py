"""Знімок мосту на багатьох сценах (крок 0.2-Б): запис входів стенда й один запуск усіх сцен у Pyodide та CPython.

Сцени — `аудит/проби/знімок_сцени.json` (ім'я, сід, змінні стенда, навіщо). Входи кожної сцени лежать стиснутими в
`аудит/проби/знімок_входи/<ім>.jsonl.gz`; сцена `сід3` — наявний файл 0.2-А. Відтворює їх `знімок_мосту.py`.

  # 1. записати входи (стенд із заглушкою моделі, повний каталог; ~2–4 хв на сцену, -j сцен одночасно)
  LYUSTERKO_CATALOG=повний python3 джерела/build_артефакт.py джерела /tmp/стенд/index.html показ-повний   # з теки джерела
  python3 джерела/прилади/знімок_сцен.py записати --корінь /tmp/стенд --pyodide /tmp/pyodide -j 3
  # 2. один запуск усіх сцен: Pyodide двічі (байт у байт?), CPython раз; час, зміст, розбіжні виклики
  python3 джерела/прилади/знімок_сцен.py прогнати --сторінка /tmp/стенд/index.html --pyodide /tmp/pyodide \\
          --вихід /tmp/знімки -j 4 [--cpython python3.12] [--лише ім ...] [--дослід математика множини обидві]
  # повторний запуск у ту саму --вихід дописує лише нові знімки (--наново — перезаписати все)

Звіт, не гейт (ПРОДУКТ.md п.3): код виходу 0, коли прогін відбувся; тотожність і розбіжності — у таблиці `<вихід>/підсумок.md`.
Час у таблиці — з паралельних процесів (-j): годинна стіна однакова для Pyodide й CPython, але абсолютні мс залежать від -j."""
import argparse, concurrent.futures, gzip, hashlib, json, os, shutil, subprocess, sys, tempfile, time

ТЕКА = os.path.dirname(os.path.abspath(__file__))
КОРІНЬ_РЕПО = os.path.abspath(os.path.join(ТЕКА, '..', '..'))
СЦЕНИ = os.path.join(КОРІНЬ_РЕПО, 'аудит', 'проби', 'знімок_сцени.json')
ТЕКА_ВХОДІВ = os.path.join(КОРІНЬ_РЕПО, 'аудит', 'проби', 'знімок_входи')
СТЕНД = os.path.join(КОРІНЬ_РЕПО, 'аудит', 'проби', 'рв6_стенд.js')
ЗНІМОК = os.path.join(ТЕКА, 'знімок_мосту.py')


def сцени(лише=None):
    список = json.load(open(СЦЕНИ, encoding='utf-8'))['сцени']
    if лише:
        невідомі = set(лише) - {с['ім'] for с in список}
        if невідомі:
            sys.exit('нема сцен: ' + ', '.join(sorted(невідомі)))
        список = [с for с in список if с['ім'] in лише]
    return список


def файл_входів(сцена):
    return os.path.join(КОРІНЬ_РЕПО, сцена['файл']) if 'файл' in сцена else os.path.join(ТЕКА_ВХОДІВ, сцена['ім'] + '.jsonl.gz')


def записати_сцену(сцена, арг):
    """Стенд із `ZAPYS_VYKLYKIV`: входи мосту → gz. Стенд може кінчити червоним (rc 1) — входи вже записано, rc іде в підсумок."""
    сирий = tempfile.mktemp(prefix='входи_%s_' % сцена['ім'], suffix='.jsonl')
    середовище = dict(os.environ, ZAPYS_VYKLYKIV=сирий, LYUSTERKO_CATALOG='повний', CHROMIUM=арг.chromium, NODE_PATH=арг.node_path)
    середовище.update(сцена['оточення'])
    t0 = time.time()
    п = subprocess.run(['node', СТЕНД, 'http://127.0.0.1:8765', арг.корінь, арг.pyodide, str(сцена['сід'])], env=середовище,
                       cwd=КОРІНЬ_РЕПО, text=True, capture_output=True)
    вхід = open(сирий, 'rb').read() if os.path.exists(сирий) else b''
    if os.path.exists(сирий):
        os.remove(сирий)
    ціль = файл_входів(сцена)
    with gzip.GzipFile(ціль, 'wb', compresslevel=9, mtime=0) as ф:    # mtime=0: той самий вміст — той самий файл
        ф.write(вхід)
    return {'ім': сцена['ім'], 'rc': п.returncode, 'викликів': вхід.count(b'\n'), 'байт_gz': os.path.getsize(ціль),
            'с': round(time.time() - t0, 1), 'червоних': п.stdout.count('  ✗ '),
            'хвіст': next((р for р in reversed(п.stdout.splitlines()) if 'СТЕНД' in р or 'ВПАЛО' in р or 'СЦЕНА' in р), '')[:120]}


def записати(арг):
    os.makedirs(ТЕКА_ВХОДІВ, exist_ok=True)
    список = [с for с in сцени(арг.лише) if 'файл' not in с]
    with concurrent.futures.ThreadPoolExecutor(арг.j) as пул:
        for р in пул.map(lambda с: записати_сцену(с, арг), список):
            print('%-18s rc %d · викликів %3d · %6d Б gz · %5.1f с · звірок ✗ %d · %s' % (
                р['ім'], р['rc'], р['викликів'], р['байт_gz'], р['с'], р['червоних'], р['хвіст']))
    разом = sum(os.path.getsize(файл_входів(с)) for с in сцени())
    print('разом входів (gz) %d Б' % разом)


def запустити(середовище, сцена, арг, вихід, підміна=None):
    """Один знімок сцени в одному середовищі; повертає (шлях знімка, час)."""
    команда = [арг.cpython if середовище == 'cpython' else sys.executable, ЗНІМОК, середовище, '--сторінка', арг.сторінка,
               '--входи', файл_входів(сцена), '--вихід', вихід]
    if середовище == 'pyodide':
        команда += ['--pyodide', арг.pyodide]
    if підміна:
        команда += ['--портативна', підміна]
    if os.path.exists(вихід) and os.path.exists(вихід + '.час.json') and not арг.наново:
        return вихід, json.load(open(вихід + '.час.json', encoding='utf-8'))    # знімок уже є: повторний запуск дописує лише нове
    t0 = time.perf_counter()
    п = subprocess.run(команда, text=True, capture_output=True)
    if п.returncode:
        raise RuntimeError('%s %s: rc %d\n%s' % (середовище, сцена['ім'], п.returncode, (п.stdout + п.stderr)[-800:]))
    час = json.load(open(вихід + '.час.json', encoding='utf-8'))
    час['стіна_с'] = round(time.perf_counter() - t0, 1)
    json.dump(час, open(вихід + '.час.json', 'w', encoding='utf-8'), ensure_ascii=False)
    return вихід, час


def прогнати_сцену(сцена, арг):
    ім = сцена['ім']
    запуски = [('pyodide_а', 'pyodide', None), ('pyodide_б', 'pyodide', None), ('cpython', 'cpython', None)]
    for підміна in арг.дослід or ():
        запуски += [('pyodide_' + підміна.replace(':', '_'), 'pyodide', підміна), ('cpython_' + підміна.replace(':', '_'), 'cpython', підміна)]
    шляхи = {к: os.path.join(арг.вихід, '%s.%s.jsonl' % (ім, к)) for к, _, _ in запуски}
    час = {}
    for ключ, середовище, підміна in запуски:
        _, час[ключ] = запустити(середовище, сцена, арг, шляхи[ключ], підміна)
    return ім, шляхи, час


def байти(шлях):
    return open(шлях, 'rb').read()


def розбіжні_виклики(шлях_а, шлях_б):
    """Номери й імена викликів, чий результат у двох знімках різний (порівняння рядків знімка)."""
    ра, рб = [open(ш, encoding='utf-8').read().splitlines()[1:] for ш in (шлях_а, шлях_б)]
    різні = [(i, json.loads(а)['ім']) for i, (а, б) in enumerate(zip(ра, рб)) if а != б]
    return різні, len(ра) == len(рб)


def змін_змісту(шлях_а, шлях_б):
    sys.path.insert(0, ТЕКА)
    import знімок_змісту as З
    зміни = З.діф_змісту(З.прочитати_зміст(шлях_а), З.прочитати_зміст(шлях_б))
    лічба = {}
    for розділ, тип, _, _ in зміни:
        лічба['%s/%s' % (розділ, тип)] = лічба.get('%s/%s' % (розділ, тип), 0) + 1
    return len(зміни), лічба


def прогнати(арг):
    os.makedirs(арг.вихід, exist_ok=True)
    список = сцени(арг.лише)
    результати = []
    with concurrent.futures.ThreadPoolExecutor(арг.j) as пул:
        for ім, шляхи, час in пул.map(lambda с: прогнати_сцену(с, арг), список):
            різні, порівнянні = розбіжні_виклики(шляхи['pyodide_а'], шляхи['cpython'])
            змін, лічба = змін_змісту(шляхи['pyodide_а'], шляхи['cpython'])
            ім_лічба = {}
            for _, назва in різні:
                ім_лічба[назва] = ім_лічба.get(назва, 0) + 1
            дослід = {п: len(розбіжні_виклики(шляхи['pyodide_' + п.replace(':', '_')], шляхи['cpython_' + п.replace(':', '_')])[0]) for п in арг.дослід or ()}
            результати.append({
                'розбіжних_дослід': дослід,
                'ім': ім, 'викликів': час['cpython']['виклики'][-1][0] + 1,
                'pyodide_тотожні': байти(шляхи['pyodide_а']) == байти(шляхи['pyodide_б']),
                'розбіжних': len(різні), 'порівнянні': порівнянні, 'розбіжні_за_іменем': ім_лічба, 'розбіжні_н': [н for н, _ in різні],
                'змін_змісту': змін, 'зміни_змісту_за_типом': лічба,
                'мс': {к: час[к]['мс_разом'] for к in час}, 'підйом_pyodide_мс': час['pyodide_а'].get('підйом_мс'),
                'стіна_с': {к: час[к].get('стіна_с') for к in час}})
            р = результати[-1]
            print('%-18s викликів %3d · Pyodide≡Pyodide %s · розбіжних %2d · змін змісту %2d · мс P/P/C %.0f/%.0f/%.0f' % (
                ім, р['викликів'], 'так' if р['pyodide_тотожні'] else 'НІ', р['розбіжних'], змін, р['мс']['pyodide_а'],
                р['мс']['pyodide_б'], р['мс']['cpython']), flush=True)
    json.dump(результати, open(os.path.join(арг.вихід, 'підсумок.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(арг.вихід, 'підсумок.md'), 'w', encoding='utf-8').write(таблиця(результати, арг.j))
    print(таблиця(результати, арг.j))


def таблиця(результати, j):
    р = ['| сцена | викликів | Pyodide≡Pyodide (байт) | мс Pyodide А / Б | мс CPython | Pyodide÷CPython | розбіжних CPython↔Pyodide | змін змісту |',
         '|---|---:|:---:|---:|---:|---:|---:|---:|']
    for с in результати:
        м = с['мс']
        розб = ', '.join('%s %d' % (к, v) for к, v in sorted(с['розбіжні_за_іменем'].items())) or '—'
        р.append('| %s | %d | %s | %.0f / %.0f | %.0f | %.1f× | %d (%s) | %d |' % (
            с['ім'], с['викликів'], 'так' if с['pyodide_тотожні'] else '**ні**', м['pyodide_а'], м['pyodide_б'], м['cpython'],
            (м['pyodide_а'] + м['pyodide_б']) / 2 / м['cpython'], с['розбіжних'], розб, с['змін_змісту']))
    р.append('| **разом** | %d | %d з %d | %.0f | %.0f | %.1f× | %d | %d |' % (
        sum(с['викликів'] for с in результати), sum(с['pyodide_тотожні'] for с in результати), len(результати),
        sum(с['мс']['pyodide_а'] for с in результати), sum(с['мс']['cpython'] for с in результати),
        sum(с['мс']['pyodide_а'] for с in результати) / sum(с['мс']['cpython'] for с in результати),
        sum(с['розбіжних'] for с in результати), sum(с['змін_змісту'] for с in результати)))
    підміни = sorted({п for с in результати for п in с['розбіжних_дослід']})
    if підміни:
        р.append('\nДослід причини (однакова підміна в обох середовищах) — розбіжних викликів CPython↔Pyodide:\n')
        р.append('| сцена | без підміни | ' + ' | '.join(підміни) + ' |')
        р.append('|---|---:|' + '---:|' * len(підміни))
        for с in результати:
            р.append('| %s | %d | %s |' % (с['ім'], с['розбіжних'], ' | '.join(str(с['розбіжних_дослід'].get(п, '—')) for п in підміни)))
        р.append('| **разом** | %d | %s |' % (sum(с['розбіжних'] for с in результати),
                 ' | '.join(str(sum(с['розбіжних_дослід'].get(п, 0) for с in результати)) for п in підміни)))
    р.append('\nмс — власний замір виклику в самому середовищі (без підйому Pyodide), `-j %d` процесів одночасно.' % j)
    return '\n'.join(р)


def main():
    р = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    п = р.add_subparsers(dest='дія', required=True)
    з = п.add_parser('записати', help='записати входи сцен стендом')
    з.add_argument('--корінь', required=True, help='теки зі зібраною index.html (повний каталог)')
    з.add_argument('--pyodide', default='/tmp/pyodide')
    з.add_argument('--chromium', default=os.environ.get('CHROMIUM', '/opt/pw-browsers/chromium'))
    з.add_argument('--node-path', default=os.environ.get('NODE_PATH', '/opt/node-tools/node_modules'))
    з.add_argument('-j', type=int, default=3)
    з.add_argument('--лише', nargs='+')
    в = п.add_parser('прогнати', help='усі сцени: Pyodide двічі, CPython раз')
    в.add_argument('--сторінка', required=True)
    в.add_argument('--pyodide', default='/tmp/pyodide')
    в.add_argument('--cpython', default='python3.12')
    в.add_argument('--вихід', required=True)
    в.add_argument('-j', type=int, default=4)
    в.add_argument('--лише', nargs='+')
    в.add_argument('--дослід', nargs='+',
                   help='додатково: CPython і Pyodide з однаковою підміною (libm, порядок множин чи обидві) — що саме дає розбіжність')
    в.add_argument('--наново', action='store_true', help='перезаписати знімки, що вже лежать у --вихід (типово лишаються)')
    арг = р.parse_args()
    {'записати': записати, 'прогнати': прогнати}[арг.дія](арг)


if __name__ == '__main__':
    main()
