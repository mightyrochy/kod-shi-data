import gzip, io, json, os, pathlib, subprocess, sys, tarfile, time

ROOT = pathlib.Path(os.environ.get('KOD_SHI_REVIEW_ROOT', pathlib.Path(__file__).parent))
TREE = ROOT / 'review-2106'
BEFORE = ROOT / 'before-2106'
LOGS = ROOT / 'review-logs'
LOGS.mkdir(exist_ok=True)
os.environ['PYTHONUTF8'] = '1'
os.environ['NODE_PATH'] = 'C:/Users/gemini/kod-shi-data/джерела/node_modules'

def run(name, command, cwd):
    start = time.perf_counter()
    result = subprocess.run(command, cwd=cwd, capture_output=True, encoding='utf8', errors='replace')
    output = result.stdout + result.stderr
    (LOGS / (name + '.txt')).write_text(output, encoding='utf8')
    record = dict(назва=name, команда=command, тека=str(cwd), код=result.returncode,
                  секунд=round(time.perf_counter()-start, 3), вивід=output[-3500:])
    print(name, result.returncode, record['секунд'], output[-400:], flush=True)
    return record

if sys.argv[1] in ('prepare', 'preparebase'):
    if sys.argv[1] == 'preparebase':
        BEFORE = ROOT / 'prbase-2106'
    BEFORE.mkdir(exist_ok=True)
    base_sha = '7561309d7644bff3600a3cc1b07704661a85150f' if sys.argv[1] == 'preparebase' else 'bd628bb29a90637ae18833c92eceb8230bd9b995'
    archive = subprocess.check_output(['git', 'archive', base_sha, 'джерела'], cwd=TREE)
    with tarfile.open(fileobj=io.BytesIO(archive)) as bundle:
        bundle.extractall(BEFORE, filter='data')
    catalog = gzip.decompress((TREE / 'каталог_повний.xml.gz').read_bytes())
    for folder in (TREE, BEFORE):
        (folder / 'джерела/каталог_повний.xml').write_bytes(catalog)
    print('ДО й ПІСЛЯ підготовлено; каталог', len(catalog), flush=True)
elif sys.argv[1] == 'summarize':
    results = json.loads((LOGS / 'батарея.json').read_text(encoding='utf8'))
    prefixes = ('ПРОЙДЕНО ', 'ВИКОНАНО ЗВІРОК:', 'ПОКАЗ:', 'тест_протоколу:', 'КОНТРАКТИ', 'файлів ', 'ФАКТ')
    for record in results:
        output = (LOGS / (record['назва'] + '.txt')).read_text(encoding='utf8')
        summary = '\n'.join(line for line in output.splitlines() if line.startswith(prefixes))
        record['вивід'] = summary if summary else output[-1400:]
    (LOGS / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print('Команд:', len(results), '; успішних:', sum(r['код'] == 0 for r in results))
    assert len(results) == 12 and all(r['код'] == 0 for r in results)
elif sys.argv[1] == 'battery':
    commands = [([sys.executable, '-X', 'utf8', file, *args], file) for file, args in (
        ('стенд_знімок.py', ['--дим']), ('тест_живого_шляху.py', []),
        ('тест_протоколу.py', []), ('прилади/розділи_гейтів.py', []), ('audit_contracts.py', []))]
    commands += [(['node', 'тест_показу.js'], 'тест_показу.js')]
    results = [run('батарея-' + str(i), command, TREE / 'джерела')
               for i, (command, _) in enumerate(commands, 1)]
    probes = ['ремонт_понад_просили', 'ремонт_порядок_5511', 'повнота_до_вибору_ходи',
              'повнота_після_вибору_ходи', 'повнота_вибір_прийняття']
    results += [run(name, [sys.executable, '-X', 'utf8', 'проби/' + name + '.py'], TREE / 'джерела')
                for name in probes]
    results += [run('дошка', [sys.executable, '-X', 'utf8', 'джерела/прилади/згорнути_дошку.py', '--лише-перевірити'], TREE)]
    (LOGS / 'батарея.json').write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    sys.exit(any(r['код'] for r in results))
