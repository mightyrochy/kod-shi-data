"""Серія 2: послідовні живі запити, записи та коміт після кожного результату."""
import collections
import datetime as dt
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import time
import urllib.request
import urllib.error

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = HERE.parent / 'ПІСЛЯ-1211.md'
NODE = r'C:\Program Files\nodejs\node.exe'
MODEL = 'qwen/qwen3.5-9b'
MOVA = 'mamaylm-gemma-3-12b-it-v2.0'
SHA = (HERE / 'код-main.txt').read_text().strip()
STAND = ROOT.parent / 'tmp/стенд'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')


def api(tail='', body=None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request('http://127.0.0.1:1234/api/v1/models' + tail,
                                 data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as response:
        return json.load(response)


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prompt_profile(folder):
    files = sorted(folder.glob('*хід_розмови.txt'))
    if files:
        text = files[0].read_text(encoding='utf-8-sig')
    else:
        names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', '-z', 'HEAD', '--', folder.relative_to(ROOT).as_posix()], cwd=ROOT).decode('utf-8').split('\0')
        names = sorted(name for name in names if name.endswith('хід_розмови.txt'))
        if not names:
            return None
        text = subprocess.check_output(['git', 'show', 'HEAD:' + names[0]], cwd=ROOT).decode('utf-8-sig')
    obj = json.JSONDecoder().raw_decode(text[text.index('{'):])[0]
    return obj.get('profile')


def update_report():
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(HERE.glob('*/результат.json'))]


def main():
    source = (ROOT / 'аудит/проби/б1_доречність.md').read_text(encoding='utf-8-sig')
    scenes = [line.split('|') for line in source.splitlines() if line.startswith('б1_')]
    assert len(scenes) == 30
    html = (STAND / 'index.html').read_text(encoding='utf-8')
    build_sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    source_diff = subprocess.check_output(['git', 'diff', SHA, build_sha, '--', 'джерела', 'аудит/проби/рв6_стенд.js', 'аудит/ноутбук_стенд_2/проксі_почергове.js'], cwd=ROOT)
    assert not source_diff, 'Збірка чи прилади відрізняються від main'
    write_json(HERE / 'збірка.json', {'sha-main': SHA, 'sha-збірки': build_sha, 'диф-продукту-й-приладів': source_diff.decode('utf-8')})
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True, encoding='utf-8').strip() == 'claude/Б.1-серія-2-повтор-1211'
    for number, (scene, woman, chat, extra) in enumerate(scenes, 1):
        folder = HERE / f'{number:02}_{scene}'
        if (folder / 'результат.json').exists():
            continue
        folder.mkdir(exist_ok=True)
        before = api()
        write_json(folder / 'моделі-до.json', before)
        if any(m['loaded_instances'] for m in before['models']):
            raise RuntimeError('LM Studio тримає не завантажені цією сесією моделі: ' + json.dumps(before, ensure_ascii=False))
        gpu = subprocess.check_output(['nvidia-smi', '--query-gpu=name,memory.used,utilization.gpu', '--format=csv,noheader'], text=True)
        (folder / 'gpu-до.txt').write_text(gpu, encoding='utf-8')
        with socket.socket() as check:
            check.bind(('127.0.0.1', 1236))
        env = dict(os.environ, NODE_PATH=r'C:\Users\Admin\kod-shi-test-node\node_modules',
                   LMS_MODE='http', PORT='1236', MODEL=MODEL, MODEL_MOVA=MOVA,
                   MODEL_URL='http://127.0.0.1:1236/v1', CTX=json.dumps({MODEL: 57344, MOVA: 16384}),
                   OTSINKA='0', FOTO='0', ODNOCHASNO='1', CHAT_TEXT=chat,
                   ZHINKA=str(ROOT / f'аудит/проби/жінки/{woman}.json'),
                   ZNIMKY=str(folder / 'знімки'), VIDPOVIDI=str(folder / 'VIDPOVIDI'),
                   ZVIT_OUT=str(folder / 'вердикти.txt'), NODE_USE_SYSTEM_CA='1',
                   PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        for key in ('DO', 'SCENA', 'CHROMIUM', 'PASPORT', 'ZHYVA', 'REPLAY_EXCHANGE', 'REPLAY_RECORDINGS'):
            env.pop(key, None)
        command = [NODE, str(ROOT / 'аудит/проби/рв6_стенд.js'), 'http://127.0.0.1:8765',
                   str(STAND), r'C:\Users\Admin\stend-nout\pyodide', '3']
        write_json(folder / 'запуск.json', {'sha-main': SHA, 'команда': command,
                   'змінні': {key: env[key] for key in ('MODEL','MODEL_MOVA','MODEL_URL','LMS_MODE','CTX','OTSINKA','FOTO','ODNOCHASNO','CHAT_TEXT','ZHINKA')}})
        (folder / 'код.txt').write_text(f'{build_sha} {scene} ПІСЛЯ {MODEL}+{MOVA}\n', encoding='utf-8')
        start = time.monotonic()
        proxy = stand = None
        try:
            with (folder / 'проксі.txt').open('w', encoding='utf-8') as proxylog, (folder / 'лог.txt').open('w', encoding='utf-8') as log:
                proxy = subprocess.Popen([NODE, str(ROOT / 'аудит/ноутбук_стенд_2/проксі_почергове.js')], cwd=ROOT, env=env, stdout=proxylog, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
                for _ in range(50):
                    if proxy.poll() is not None:
                        raise RuntimeError('Проксі завершився до початку: ' + (folder / 'проксі.txt').read_text(encoding='utf-8'))
                    try:
                        with socket.create_connection(('127.0.0.1', 1236), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Проксі не відкрив порт')
                print(f'{now()} СТАРТ {number:02}/30 {scene}; проксі PID={proxy.pid}', flush=True)
                stand = subprocess.Popen(command, cwd=ROOT, env=env, stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
                blocked = False
                previous_models = before
                previous_time = now()
                last_status = time.monotonic()
                while stand.poll() is None:
                    try:
                        stand.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        lines = (folder / 'лог.txt').read_text(encoding='utf-8').splitlines()
                        proxy_text = (folder / 'проксі.txt').read_text(encoding='utf-8')
                        try:
                            current_models = api()
                        except urllib.error.HTTPError as error:
                            current_models = {'помилка-GET': error.code, 'відповідь': error.read().decode('utf-8', errors='replace')}
                        except (OSError, TimeoutError) as error:
                            current_models = {'помилка-GET': str(error)}
                        with (folder / 'спостереження-моделей.jsonl').open('a', encoding='utf-8') as observations:
                            observations.write(json.dumps({'час': now(), 'models': current_models}, ensure_ascii=False) + '\n')
                        if re.search(r'(?:HTTP\s+503\b|POST /v1/chat/completions:\s*503\b)', proxy_text + '\n' + '\n'.join(lines)):
                            write_json(folder / 'відмова-діагностика.json', {
                                'до-час': previous_time, 'до': previous_models,
                                'після-час': now(), 'після': current_models,
                                'проксі': proxy_text, 'стенд-PID': stand.pid, 'проксі-PID': proxy.pid})
                            gpu_processes = subprocess.run(['nvidia-smi', '--query-compute-apps=pid,process_name,used_memory', '--format=csv'], capture_output=True, text=True)
                            (folder / 'gpu-відмова.txt').write_text(gpu_processes.stdout + gpu_processes.stderr, encoding='utf-8')
                            write_json(HERE / 'повторний-блокер.json', {'номер': number, 'сцена': scene, 'час': now(), 'запис': folder.relative_to(ROOT).as_posix(), 'секунди': round(time.monotonic()-start)})
                            blocked = True
                            print(f'{now()} ЗАБЛОКОВАНО {number:02}: повторна HTTP 503; діагностику збережено, повтору немає.', flush=True)
                            break
                        previous_models, previous_time = current_models, now()
                        if time.monotonic() - last_status >= 30:
                            print(f'{now()} {number:02}/30 {int(time.monotonic()-start)}с PID={stand.pid}: {lines[-1][:180] if lines else "очікування"}', flush=True)
                            last_status = time.monotonic()
                rc = stand.returncode
        finally:
            for child in (stand, proxy):
                if child and child.poll() is None:
                    child.terminate()
                    child.wait(timeout=30)
            own = set(re.findall(r'HTTP власний екземпляр (.+)', (folder / 'проксі.txt').read_text(encoding='utf-8')))
            unloaded = []
            for model in api()['models']:
                for instance in model['loaded_instances']:
                    if instance['id'] in own:
                        unloaded.append(api('/unload', {'instance_id': instance['id']}))
            write_json(folder / 'прибирання.json', {'вивантажено': unloaded, 'моделі-після': api()})
        if blocked:
            return 3
        elapsed = round(time.monotonic() - start)
        text = (folder / 'лог.txt').read_text(encoding='utf-8')
        failures = re.findall(r'^ {2}✗ (.+?)(?:  →|$)', text, re.M)
        totals = re.findall(r'^ВПАЛО (\d+)', text, re.M)
        hands = [json.loads(value) for value in re.findall(r'^\s+рука [1-4] (\{.*\})$', text, re.M)]
        hands = [hand for hand in hands if 'речей' in hand and 'збій' in hand]
        cards = sum(hand['речей'] > 0 and not hand['збій'] for hand in hands)
        same = 'не міряно'
        reason = '' if cards == 4 else 'див. лог.txt; номер дошки має призначити диспетчер'
        result = {'номер': number, 'сцена': scene, 'rc': rc, 'секунди': elapsed, 'карток': cards,
                  'впало': int(totals[-1]) if totals else len(failures), 'звірки': failures,
                  'запис': folder.relative_to(ROOT).as_posix(), 'причина': reason, 'профіль-збігається': same}
        write_json(folder / 'результат.json', result)
        with (HERE / 'done.txt').open('a', encoding='utf-8') as done:
            done.write(f'{now()} {scene} rc={rc} с={elapsed} карток={cards}\n')
        subprocess.run(['git', 'add', '--', str(HERE.relative_to(ROOT))], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', f'Б.1 повтор 1211: запис {number:02}/30 — {scene}'], cwd=ROOT, check=True)
        subprocess.run(['git', 'push', '--no-thin', 'origin', 'HEAD'], cwd=ROOT)
        print(f'{now()} ГОТОВО {number:02}/30 rc={rc} карток={cards} впало={result["впало"]}', flush=True)
        if rc >= 2 and not cards:
            print('Потрібен розбір збою перед продовженням; автоматичного повтору немає.', flush=True)
            return rc
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
