from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

out = Path('аудит/проби/Е1-нічний-живий-20261113')
os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'
os.environ['NODE_PATH'] = r'C:\Users\gemini\kod-shi-test-node\node_modules'
os.environ['TEKA_FOTO_SCENY'] = str(Path('../tmp/фото_сцен').resolve())
sys.path.insert(0, str(Path('аудит/проби').resolve()))
from записати_план import команди_плану

plan_bytes = (out / 'ПЛАН.json').read_bytes()
plan = json.loads(plan_bytes)
commands, refusals, question_refusals = команди_плану(plan, Path('../tmp/build'), Path(r'C:\Users\gemini\pyodide'), out)
selected = []
for command in commands:
    scene = command[command.index('--сцена') + 1]
    folder = out / scene
    if (folder / 'результат.json').exists():
        continue
    if folder.exists() and any(folder.iterdir()):
        raise RuntimeError('Є незавершені дані, їх не перезаписуємо: ' + scene)
    selected.append(command)
if len(selected) != 11:
    raise RuntimeError('Очікували 9 відмов до старту та 2 фото-сцени, отримали ' + str(len(selected)))

meta = {'початок': datetime.now(timezone.utc).isoformat(), 'стан': 'триває', 'pid': os.getpid(),
        'план_sha256': hashlib.sha256(plan_bytes).hexdigest(),
        'команди': selected, 'причина': '9 відмов до старту через зайнятий сервер і 2 початкові відмови через відсутні фото; жодну записану сцену не повторюємо',
        'TEKA_FOTO_SCENY': os.environ['TEKA_FOTO_SCENY']}

def save():
    target = out / 'дозапуск.json'
    temporary = out / 'дозапуск.tmp'
    assert target.parent.resolve() == out.resolve()
    temporary.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(target)

def wait_free(log):
    previous = None
    while True:
        try:
            with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=10) as response:
                models = json.load(response)
            loaded = [(m['key'], i['id']) for m in models['models'] for i in m['loaded_instances']]
            state = json.dumps(loaded, ensure_ascii=False)
            if state != previous:
                event = {'час': datetime.now(timezone.utc).isoformat(), 'сцена': meta['сцена'], 'завантажені': loaded}
                log.write('СТАН СЕРВЕРА ' + json.dumps(event, ensure_ascii=False) + '\n')
                log.flush()
                print('Очікування моделей: ' + state, flush=True)
                previous = state
            if not loaded:
                return
        except Exception as error:
            message = str(error)
            if message != previous:
                log.write('ОЧІКУВАННЯ СЕРВЕРА ' + message + '\n'); log.flush()
                previous = message
        time.sleep(10)

save()
code = 0
with (out / 'done.txt').open('a', encoding='utf-8') as done, (out / 'дозапуск_лог.txt').open('w', encoding='utf-8') as log:
    for command in selected:
        scene = command[command.index('--сцена') + 1]
        meta['сцена'] = scene; save()
        print('Черга першого запису: ' + scene, flush=True)
        wait_free(log)
        folder = out / scene
        if folder.exists():
            assert folder.resolve().parent == out.resolve()
            assert not any(folder.iterdir())
            folder.rmdir()  # Лише порожній результат відмови до старту, жодного запису тут не було.
        record = {'початок': datetime.now(timezone.utc).isoformat(), 'команда': command,
                  'відновлення': 'Перший живий запис після відмови до старту; початкові rc та логи збережено',
                  'TEKA_FOTO_SCENY': os.environ['TEKA_FOTO_SCENY']}
        log.write('КОМАНДА ' + json.dumps(record, ensure_ascii=False) + '\n'); log.flush()
        record['rc'] = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT).returncode
        record['кінець'] = datetime.now(timezone.utc).isoformat()
        done.write(json.dumps(record, ensure_ascii=False) + '\n'); done.flush()
        code = max(code, record['rc'])
        print('Кінець першого запису ' + scene + ': rc=' + str(record['rc']), flush=True)
meta.update(стан='завершено', кінець=datetime.now(timezone.utc).isoformat(), rc=code)
save()
raise SystemExit(code)
