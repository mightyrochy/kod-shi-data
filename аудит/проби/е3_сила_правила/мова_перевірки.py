"""Батарея й сім’я мовного гейта одним запуском, до кінця.

python аудит/проби/е3_сила_правила/мова_перевірки.py
Повні журнали — у TEMP; коди й хвости — у крок1_мова_перевірки.json поруч.
"""
import json, os, pathlib, subprocess, sys, time

root = pathlib.Path(__file__).resolve().parents[3]
src = root / 'джерела'
out = root / 'аудит/проби/е3_сила_правила/крок1_мова_перевірки.json'
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', NODE_PATH=str(src / 'node_modules'))
steps = [
    [sys.executable, '-c', "import чистка_каталогу as ч, feed as Ф; print(ч.забезпечити_чистим('каталог_повний.xml')); print(Ф.каталог_на_диску('каталог_brief.xml'))"],
    [sys.executable, 'стенд_знімок.py', '--дим'],
    [sys.executable, 'тест_живого_шляху.py'],
    [sys.executable, 'тест_протоколу.py'],
    [sys.executable, 'прилади/розділи_гейтів.py'],
    [sys.executable, 'audit_contracts.py'],
    ['node', 'тест_показу.js'],
    [sys.executable, 'language_gate.py'],
]
family = ['col_K-COL-07.py', 'lang_lyshe_slid.py', 'sig_K-SIG-01.py',
    'мовний_гейт_коду_доїжджає.py', 'фг2_мова_тіла.py', 'мова_046.py']
family += [p.name for p in sorted((src / 'проби').glob('сила_*.py'))]
steps += [[sys.executable, 'проби/' + p] for p in family]
results = []
for i, command in enumerate(steps):
    begin = time.monotonic()
    p = subprocess.run(command, cwd=src, env=env, capture_output=True)
    log = (p.stdout + p.stderr).decode('utf-8', errors='replace')
    (pathlib.Path(os.environ['TEMP']) / ('мова_перевірка_%02d.log' % i)).write_text(log, encoding='utf-8')
    results.append(dict(команда=command, код=p.returncode, секунд=round(time.monotonic()-begin, 2),
                        хвіст=log.splitlines()[-10:]))
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print(i, command[-1], 'код', p.returncode, flush=True)
print('ФАКТ · кроків', len(results), 'пройшло', sum(x['код']==0 for x in results))
sys.exit(any(x['код'] for x in results))
