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

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
REPORT = HERE.parent / 'ПІСЛЯ-Е3.md'
NODE = r'C:\Users\gemini\tools\node-v24.22.1-win-x64\node.exe'
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
    rows = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(HERE.glob('*/результат.json'))]
    counts = collections.Counter(name for row in rows for name in set(row['звірки']))
    cards = sum(row['карток'] > 0 for row in rows)
    clean = sum(row['карток'] > 0 and not row['звірки'] and row['rc'] == 0 for row in rows)
    text = [f'SHA `main` на старті: {SHA}', '', '# Е3 наживо — серія 2 ПІСЛЯ', '',
            f'Завершено {len(rows)}/30 запитів. Картки: ДО 26/30 → ПІСЛЯ {cards}/{len(rows)}; '
            f'без жодної `✗`: ДО 1/30 → ПІСЛЯ {clean}/{len(rows)}. До завершення 30 запитів підсумок проміжний.', '',
            f'Стилістка `{MODEL}` (57344), мовна `{MOVA}` (16384), `parallel=1`, '
            'почерговий проксі :1236, LM Studio :1234; сід 3, повне, `OTSINKA=0`, `FOTO=0`, '
            '`ODNOCHASNO=1`, телефон 390×844. Збірка повного каталогу зі свіжого main; '
            'команда й вхід кожної сцени — `запуск.json`, усі виклики — `VIDPOVIDI/`, знімки — `знімки/`.', '',
            'Порівняння профілю у вході моделі з ДО — `профіль-ДО-ПІСЛЯ.json` кожної сцени. '
            'Жінки — репозиторні `аудит/проби/жінки/ж<N>.json`; ДО не змінюється. '
            'Порівнюються доступні поля профілю у справжньому вході моделі; сирі мірки й HEX, '
            'яких цей вхід не містить, не оголошуються виміряними.', '',
            '| № | запит | rc | с | карток | звірок ВПАЛО | запис | стан |',
            '|---|---|---|---|---|---|---|---|']
    for row in rows:
        status = 'виміряно' if row['карток'] else 'НЕ ВИМІРЯНО: ' + row['причина']
        text.append(f"| {row['номер']:02} | {row['сцена']} | {row['rc']} | {row['секунди']} | {row['карток']} | {row['впало']} | `{row['запис']}/` | {status} |")
    text += ['', '## Звірки → кількість запитів', '']
    text += [f'- {name}: **{n}**.' for name, n in counts.most_common()] or ['Невдалих звірок у завершених сценах немає.']
    for row in rows:
        text += ['', f"### {row['номер']:02} · {row['сцена']}", '']
        text += ['- ' + name for name in row['звірки']] or ['Жодної `✗`.']
        text += [f"Профіль ДО = ПІСЛЯ: **{row['профіль-збігається']}**."]
    text += ['', 'Образи не оцінювалися. Продукт і звірки не змінено; незалежного приймання немає.', '']
    REPORT.write_text('\n'.join(text), encoding='utf-8')
    return rows


def main():
    source = (ROOT / 'аудит/проби/б1_доречність.md').read_text(encoding='utf-8-sig')
    scenes = [line.split('|') for line in source.splitlines() if line.startswith('б1_')]
    assert len(scenes) == 30
    html = (STAND / 'index.html').read_text(encoding='utf-8')
    build_sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"', html)[1]
    source_diff = subprocess.check_output(['git', 'diff', SHA, build_sha, '--', 'джерела', 'аудит/проби/рв6_стенд.js', 'аудит/ноутбук_стенд_2/проксі_почергове.js'], cwd=ROOT)
    assert not source_diff, 'Збірка чи прилади відрізняються від main'
    write_json(HERE / 'збірка.json', {'sha-main': SHA, 'sha-збірки': build_sha, 'диф-продукту-й-приладів': source_diff.decode('utf-8')})
    assert subprocess.check_output(['git', 'branch', '--show-current'], cwd=ROOT, text=True, encoding='utf-8').strip() == 'gemini/Е3-наживо'
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
        env = dict(os.environ, NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules',
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
                   str(STAND), r'C:\Users\gemini\pyodide', '3']
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
                while stand.poll() is None:
                    try:
                        stand.wait(timeout=30)
                    except subprocess.TimeoutExpired:
                        lines = (folder / 'лог.txt').read_text(encoding='utf-8').splitlines()
                        print(f'{now()} {number:02}/30 {int(time.monotonic()-start)}с PID={stand.pid}: {lines[-1][:180] if lines else "очікування"}', flush=True)
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
        elapsed = round(time.monotonic() - start)
        text = (folder / 'лог.txt').read_text(encoding='utf-8')
        failures = re.findall(r'^\s*✗ (.+?)(?:  →|$)', text, re.M)
        totals = re.findall(r'^ВПАЛО (\d+)', text, re.M)
        cards = len(list((folder / 'знімки').glob('kartka_poz*_ruka*_seed3.png')))
        old = ROOT / f'аудит/проби/б1/ДО-2710/{number:02}_{scene}/VIDPOVIDI'
        old_profile, new_profile = prompt_profile(old), prompt_profile(folder / 'VIDPOVIDI')
        same = old_profile == new_profile if old_profile is not None and new_profile is not None else 'не виміряно'
        write_json(folder / 'профіль-ДО-ПІСЛЯ.json', {'ДО': old_profile, 'ПІСЛЯ': new_profile, 'збігаються': same,
                   'жінка': json.loads(Path(env['ZHINKA']).read_text(encoding='utf-8-sig'))})
        reason = '' if cards else 'див. лог.txt; номер дошки має призначити диспетчер'
        result = {'номер': number, 'сцена': scene, 'rc': rc, 'секунди': elapsed, 'карток': cards,
                  'впало': int(totals[-1]) if totals else len(failures), 'звірки': failures,
                  'запис': folder.relative_to(ROOT).as_posix(), 'причина': reason, 'профіль-збігається': same}
        write_json(folder / 'результат.json', result)
        with (HERE / 'done.txt').open('a', encoding='utf-8') as done:
            done.write(f'{now()} {scene} rc={rc} с={elapsed} карток={cards}\n')
        update_report()
        subprocess.run(['git', 'add', '--', str(HERE.relative_to(ROOT)), str(REPORT.relative_to(ROOT))], cwd=ROOT, check=True)
        subprocess.run(['git', 'commit', '-m', f'Е3 наживо: запис {number:02}/30 — {scene}'], cwd=ROOT, check=True)
        print(f'{now()} ГОТОВО {number:02}/30 rc={rc} карток={cards} впало={result["впало"]}', flush=True)
        if rc >= 2 and not cards:
            print('Потрібен розбір збою перед продовженням; автоматичного повтору немає.', flush=True)
            return rc
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
