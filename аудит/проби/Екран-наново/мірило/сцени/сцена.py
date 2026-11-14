"""сцена.py <до|після> <id> <режим> <мітка> [ЗМІННА=значення…] — стенд рв6 зі змінними приладу записати_сцену.py.
Відповіді моделей — записані (replay_сцени.py з аудит/проби/нічні/20261107/<id>), коли запис є; «функція» — заглушка стенда."""
import json, os, re, shlex, subprocess, sys, time
ч, ід, режим, мітка, *дод = sys.argv[1:]
РЕПО = '/home/user/kod-shi-data'
к, зб = ('/tmp/до', '/tmp/zb_do') if ч == 'до' else (РЕПО, '/tmp/zb_pislia')
вихід = f'/tmp/м/сцени/{мітка}_{ч}'
subprocess.run(['rm', '-rf', вихід]); os.makedirs(вихід)
if режим == 'функція':   # прилад запису відмовляє: «код без моделі в Chromium» — вхід сцени з реєстру, модель — заглушка стенда
    x = [l.split('|') for l in open(к + '/аудит/проби/живі_сцени.txt', encoding='utf8').read().splitlines() if l.startswith(ід + '|')][0]
    з = {'SCENA': x[0], 'ZHINKA': к + '/аудит/проби/жінки/' + x[1] + '.json', 'CHAT_TEXT': x[2]}
    з.update(dict(ш.split('=', 1) for ш in x[3].split() if '=' in ш))
else:
    з = json.loads(subprocess.check_output(['python3', 'аудит/проби/записати_сцену.py', '--лише-змінні', '--сцена', ід, '--режим', режим], cwd=к, text=True))
з.update(dict(п.split('=', 1) for п in дод))
env = dict(os.environ, **{a: str(b) for a, b in з.items()})
запис = f'{РЕПО}/аудит/проби/нічні/20261107/{ід}'
повтор = None
if режим != 'функція' and os.path.isdir(запис + '/VIDPOVIDI'):
    лог = open(вихід + '/replay.txt', 'w')
    повтор = subprocess.Popen(['python3', '-u', 'replay_сцени.py', запис, '0'], cwd=РЕПО + '/аудит/проби', stdout=лог, stderr=subprocess.STDOUT)
    for _ in range(150):
        т = open(вихід + '/replay.txt').read()
        м = re.search(r'REPLAY_READY.*?(http://127\.0\.0\.1:\d+\S*)', т)
        if м: break
        time.sleep(0.2)
    env['MODEL_URL'] = м.group(1); модель = 'повтор запису 07.11'
else:
    env.pop('MODEL', None); env.pop('MODEL_MOVA', None); модель = 'заглушка стенда'
env.update(ZNIMKY=вихід + '/знімки', ZVIT_OUT=вихід + '/вердикти.txt', CHROMIUM='/opt/pw-browsers/chromium', NODE_PATH=РЕПО + '/джерела/node_modules')
json.dump({a: з[a] for a in з}, open(вихід + '/змінні.json', 'w'), ensure_ascii=False, indent=1)
try:
    rc = subprocess.run(['node', 'аудит/проби/рв6_стенд.js', 'http://127.0.0.1:8765', зб, '/tmp/pyodide', '3'], cwd=к, env=env,
                        stdout=open(вихід + '/лог.txt', 'w'), stderr=subprocess.STDOUT, timeout=1500).returncode
except subprocess.TimeoutExpired:
    rc = 'таймаут'
if повтор: повтор.kill()
зв = [re.sub(r'\s*\([0-9.,]+ ?(с|мс)[^)]*\)\s*$', '', р.strip()) for р in open(вихід + '/лог.txt', encoding='utf8', errors='replace') if re.match(r'\s*[✔✗]', р)]
open(вихід + '/звірки.txt', 'w').write('\n'.join(зв) + '\n')
зн = len([ф for ф in os.listdir(вихід + '/знімки')]) if os.path.isdir(вихід + '/знімки') else 0
print(f"{мітка} {ч}: rc={rc} ✔ {sum(р.startswith('✔') for р in зв)} ✗ {sum(р.startswith('✗') for р in зв)} файлів знімків {зн} · {модель}", flush=True)
