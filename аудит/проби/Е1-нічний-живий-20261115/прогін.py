"""Підготовка середовища та послідовний запуск призначеного плану Е1."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT.parent / 'tmp' / 'збірка'
CACHE = Path('C:/Users/gemini/pyodide')
MODELS = {'qwen/qwen3.5-9b': 57344, 'mamaylm-gemma-3-12b-it-v2.0': 16384}
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                  NODE_PATH='C:/Users/gemini/kod-shi-test-node/node_modules')


def now():
    return datetime.now(timezone.utc).isoformat()


def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def api(suffix='', body=None):
    req = urllib.request.Request('http://127.0.0.1:1234/api/v1/models' + suffix,
        data=None if body is None else json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=300) as response:
        return {'status': response.status, 'body': json.load(response)}


def run(args, name):
    started = now()
    with (OUT / name).open('w', encoding='utf-8') as log:
        result = subprocess.run(args, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    entry = {'початок': started, 'кінець': now(), 'команда': args, 'rc': result.returncode, 'лог': name}
    with (OUT / 'запуск.jsonl').open('a', encoding='utf-8') as log:
        log.write(json.dumps(entry, ensure_ascii=False) + '\n')
    print(json.dumps(entry, ensure_ascii=False), flush=True)
    return result.returncode


def main():
    state = {'час': now(), 'збірка': str(BUILD), 'кеш': str(CACHE),
             'змінні': {k: os.environ.get(k) for k in ('NODE_OPTIONS', 'PYTHONPATH', 'NODE_PATH', 'TEKA_FOTO_SCENY')}}
    for args in (['git', 'rev-parse', 'HEAD', 'origin/main'],
                 ['git', 'merge-base', '--is-ancestor', '1369eaf7988e8a2e06724f3aa40e017ebda42728', 'origin/main'],
                 ['git', '-C', str(BUILD), 'rev-parse', 'HEAD'],
                 ['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader']):
        p = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
        state[' '.join(args)] = {'rc': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr}
    save('середовище.json', state)
    before = api()
    save('моделі_до.json', before)
    with (OUT / 'очікування.jsonl').open('a', encoding='utf-8') as log:
        while True:
            current = api()
            instances = [{'key': m['key'], 'instance': i} for m in current['body']['models'] for i in m['loaded_instances']]
            if not instances:
                break
            entry = {'час': now(), 'чужі_екземпляри': instances}
            log.write(json.dumps(entry, ensure_ascii=False) + '\n')
            log.flush()
            print('Очікування чужих моделей: ' + ', '.join(i['key'] for i in instances), flush=True)
            time.sleep(45)
    available = {m['key'] for m in current['body']['models']}
    if not set(MODELS) <= available:
        raise RuntimeError('Нема моделей наряду: ' + str(set(MODELS) - available))
    checks = []
    for model, context in MODELS.items():
        loaded = api('/load', {'model': model, 'context_length': context, 'parallel': 1, 'echo_load_config': True})
        instance = loaded['body'].get('instance_id')
        try:
            actual = api()
            matches = [i for m in actual['body']['models'] if m['key'] == model for i in m['loaded_instances'] if i['id'] == instance]
            checks.append({'модель': model, 'завантаження': loaded, 'фактичні_екземпляри': matches})
            save('моделі_перевірка.json', checks)
            if not matches or matches[0]['config']['context_length'] != context or matches[0]['config']['parallel'] != 1:
                raise RuntimeError('Не підтверджено контекст та parallel=1: ' + model)
        finally:
            if instance:
                checks[-1]['вивантаження'] = api('/unload', {'instance_id': instance})
                save('моделі_перевірка.json', checks)
    browser = "const {chromium}=require('playwright'); (async()=>{const b=await chromium.launch({headless:true}); console.log(b.version()); await b.close();})().catch(e=>{console.error(e);process.exitCode=1})"
    if run(['node', '-e', browser], 'браузер.txt'):
        raise RuntimeError('Chromium не запустився')
    command = [sys.executable, str(ROOT / 'аудит/проби/записати_план.py'), str(OUT / 'ПЛАН.json'), str(BUILD), str(CACHE), str(OUT)]
    run(command + ['--лише-змінні'], 'змінні_плану.txt')
    rc = run(command, 'план_лог.txt')
    save('моделі_після.json', api())
    print('План завершено, rc=' + str(rc), flush=True)
    return rc


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as error:
        save('збій_запуску.json', {'час': now(), 'тип': type(error).__name__, 'помилка': str(error)})
        raise
