"""Е3-сила-правила, п.1б–в, крок 2: батарея й проби місць кроку одним запуском, до кінця.

python3 аудит/проби/е3_сила_правила/вибір_людини_перевірки.py [<дерево>] [--з N]
<дерево> — корінь робочого дерева (типово — це). `--з N` — лише кроки від N, паралельно (фонове завдання
сесії живе 30 хв, а вся батарея довша); їхні коди дописуються до вже записаних кроків 0…N−1. Коди й хвости — у вибір_людини_перевірки.json поруч
(для іншого дерева — у /tmp). Повні журнали — у /tmp/вибір_людини_NN.log.
"""
import json, os, pathlib, subprocess, sys, time

тут = pathlib.Path(__file__).resolve()
арг = sys.argv[1:]
з_кроку = int(арг[арг.index('--з') + 1]) if '--з' in арг else None
арг = [a for i, a in enumerate(арг) if a != '--з' and (i == 0 or арг[i - 1] != '--з')]
root = pathlib.Path(арг[0]).resolve() if арг else тут.parents[3]
src = root / 'джерела'
out = (тут.parent if root == тут.parents[3] else pathlib.Path('/tmp')) / 'вибір_людини_перевірки.json'
env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1', NODE_PATH=str(src / 'node_modules'))
steps = [
    [sys.executable, '-c', "import чистка_каталогу as ч, feed as Ф; print(ч.забезпечити_чистим('каталог_повний.xml')); print(Ф.каталог_на_диску('каталог_brief.xml'))"],
    [sys.executable, 'стенд_знімок.py', '--дим'],
    [sys.executable, 'тест_живого_шляху.py'],
    [sys.executable, 'тест_протоколу.py'],
    [sys.executable, 'прилади/розділи_гейтів.py'],
    [sys.executable, 'audit_contracts.py'],
    ['node', 'тест_показу.js'],
]
family = ['оцінка_нема_на_фото_5284.py', 'повнота_вибір_прийняття.py', 'склад1_її_річ_у_ремонті.py',
          'склад2_її_гейт_у_ранжуванні.py', 'схема_960_гейт.py']
family += [p.name for p in sorted((src / 'проби').glob('сила_*.py'))]
steps += [[sys.executable, 'проби/' + p] for p in family]
def крок(i):
    command = steps[i]
    begin = time.monotonic()
    p = subprocess.run(command, cwd=src, env=env, capture_output=True)
    log = (p.stdout + p.stderr).decode('utf-8', errors='replace')
    pathlib.Path('/tmp/вибір_людини_%02d.log' % i).write_text(log, encoding='utf-8')
    print(i, command[-1][:60], 'код', p.returncode, flush=True)
    return dict(команда=command[1:] if command[0] == sys.executable else command, код=p.returncode,
                секунд=round(time.monotonic() - begin, 2), хвіст=log.splitlines()[-6:])


if з_кроку is None:
    results = []
    for i in range(len(steps)):
        results.append(крок(i))
        out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
else:
    from concurrent.futures import ThreadPoolExecutor
    results = json.loads(out.read_text(encoding='utf-8'))[:з_кроку]
    with ThreadPoolExecutor(4) as пул:
        results += list(пул.map(крок, range(з_кроку, len(steps))))
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('ФАКТ · кроків', len(results), 'пройшло', sum(x['код'] == 0 for x in results))
sys.exit(any(x['код'] for x in results))
