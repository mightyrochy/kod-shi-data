"""Команди та вимір середовища нічного прогону 16.11.2026; реалізацію продукту не змінює."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT.parent / 'tmp' / 'Е1-збірка'
CACHE = Path(r'C:\Users\gemini\pyodide')
os.environ.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
                  NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules')
events = []


def save():
    (OUT / 'середовище.json').write_text(json.dumps(events, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')


def api(path='', body=None):
    request = urllib.request.Request('http://127.0.0.1:1234/api/v1/models' + path,
        data=None if body is None else json.dumps(body).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
        events.append({'час': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                       'шлях': request.full_url, 'запит': body, 'status': response.status, 'відповідь': data})
        save()
        return data


def command(args, name):
    print('КОМАНДА:', ' '.join(map(str, args)), flush=True)
    with (OUT / name).open('w', encoding='utf-8') as log:
        result = subprocess.run(list(map(str, args)), cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
    events.append({'команда': list(map(str, args)), 'rc': result.returncode, 'лог': name,
                   'час': datetime.datetime.now(datetime.timezone.utc).isoformat()})
    save()
    print(name, 'rc=', result.returncode, flush=True)
    return result.returncode


def main():
    command(['git', 'merge-base', '--is-ancestor', 'a5b43f390488140e7041348ce47673fff458f250', 'origin/main'], 'предок.txt')
    command(['git', '-C', BUILD, 'rev-parse', 'HEAD'], 'дерево.txt')
    command(['nvidia-smi', '--query-gpu=name,memory.used,memory.total', '--format=csv,noheader'], 'gpu_до.txt')
    original = api()
    if any(model['loaded_instances'] for model in original['models']):
        raise RuntimeError('Чужа модель: потрібне очікування до звільнення')
    for model, context in [('qwen/qwen3.5-9b', 57344), ('mamaylm-gemma-3-12b-it-v2.0', 16384)]:
        instance = None
        try:
            loaded = api('/load', {'model': model, 'context_length': context, 'parallel': 1, 'echo_load_config': True})
            instance = loaded.get('instance_id')
            if not instance:
                raise RuntimeError('Сервер не повернув instance_id')
            actual = next(i for m in api()['models'] for i in m['loaded_instances'] if i['id'] == instance)
            if actual['config']['context_length'] != context or actual['config']['parallel'] != 1:
                raise RuntimeError('Сервер не підтвердив контекст та parallel=1')
            print('ПІДТВЕРДЖЕНО:', model, actual['config'], flush=True)
        finally:
            if instance:
                api('/unload', {'instance_id': instance})
    check = command([sys.executable, ROOT / 'аудит/проби/записати_план.py', OUT / 'ПЛАН.json', BUILD, CACHE, OUT,
                     '--лише-змінні'], 'змінні.txt')
    if check:
        raise RuntimeError('Відмова перевірки змінних: див. змінні.txt')
    result = command([sys.executable, ROOT / 'аудит/проби/записати_план.py', OUT / 'ПЛАН.json', BUILD, CACHE, OUT], 'план_лог.txt')
    command(['node', ROOT / 'аудит/проби/нова_база.js', OUT], 'база_лог.txt')
    api()
    return result


if __name__ == '__main__':
    try:
        sys.exit(main())
    finally:
        save()
