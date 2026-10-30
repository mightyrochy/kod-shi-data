import os, pathlib, subprocess, sys, time, json
root = pathlib.Path(__file__).parent / 'pr2386'
out = pathlib.Path(__file__).parent / 'evidence2386'
out.mkdir(exist_ok=True)
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['PYTHONUTF8'] = '1'
source = root / 'джерела'
commands = [(root, [sys.executable, 'джерела/прилади/схема_записів_5624.py', '--фід']),
            (root, [sys.executable, 'аудит/жнива_5_3/вимір_5624.py', 'cc92707d4']),
            (root, [sys.executable, 'джерела/прилади/згорнути_дошку.py', '--лише-перевірити'])]
commands += [(source, [sys.executable, name]) for name in ['стенд_знімок.py --дим', 'тест_живого_шляху.py', 'тест_протоколу.py', 'прилади/розділи_гейтів.py', 'audit_contracts.py']]
commands[3] = (source, [sys.executable, 'стенд_знімок.py', '--дим'])
commands += [(source, ['node', 'тест_показу.js'])]
commands += [(source, [sys.executable, str(p.relative_to(source))]) for p in sorted((source/'проби').glob('каталог_*.py'))]
results = []
for i, (cwd, cmd) in enumerate(commands):
    path = out / f'{i:03d}.txt'
    start = time.monotonic()
    with path.open('w', encoding='utf-8') as f:
        f.write('Команда: ' + ' '.join(cmd) + '\nТека: ' + str(cwd) + '\n'); f.flush()
        try:
            r = subprocess.run(cmd, cwd=cwd, stdout=f, stderr=subprocess.STDOUT, timeout=1800)
            code = r.returncode
        except subprocess.TimeoutExpired:
            code = 'TIMEOUT'
        f.write(f'\nКод: {code}\n')
    item = {'команда': ' '.join(cmd[1:]), 'код':code, 'секунд':round(time.monotonic()-start,1), 'файл':path.name}
    results.append(item)
    (out/'results.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(item, ensure_ascii=False), flush=True)
print('Завершено:', len(results), 'невдалих:', sum(r['код'] != 0 for r in results), flush=True)
