"""Власний режим концерту з плану: фото та справжнє вікно рушія 52000.

Питання #2937 просить FOTO=0, #2954 — FOTO=1 для тієї самої сцени.
Спільний запис використовує FOTO=1; це обмеження порівняння зазначається у звіті.
Код продукту, стенда й проксі береться без змін із призначеного дерева.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
BUILD = ROOT.parent / 'tmp' / 'збірка'
SPEC = importlib.util.spec_from_file_location('recorder', BUILD / 'аудит/проби/записати_сцену.py')
REC = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(REC)


def main():
    scene = REC.сцена_реєстру('б1_концерт_стримано')
    dest = OUT / scene['назва']
    dest.mkdir(exist_ok=False)
    env = dict(os.environ)
    for key in list(env):
        if key.startswith('REPLAY_'):
            del env[key]
    env.update(scene['змінні'])
    env.update(FOTO='1', OTSINKA='0', ODNOCHASNO='1', LMS_MODE='http', PORT='1235',
               CTX=json.dumps({env['MODEL']: 52000, env['MODEL_MOVA']: 16384}),
               MODEL_CTX='52000', MODEL_URL='http://127.0.0.1:1235/v1',
               VIDPOVIDI=str(dest / 'VIDPOVIDI'), ZNIMKY=str(dest / 'знімки'),
               ZVIT_OUT=str(dest / 'вердикти.txt'))
    if any(model['loaded_instances'] for model in REC.api()['models']):
        raise RuntimeError('Сервер тримає чужу модель')
    sha = re.search(r'const ЗБІРКА_ПОКАЗУ = "([0-9a-f]{40})"',
                    (BUILD / 'index.html').read_text(encoding='utf-8'))[1]
    (dest / 'код.txt').write_text(f"{sha} {scene['назва']} ПІСЛЯ {env['MODEL']}+{env['MODEL_MOVA']}\n", encoding='utf-8')
    command = ['node', str(BUILD / 'аудит/проби/рв6_стенд.js'),
               'http://127.0.0.1:8765', str(BUILD), r'C:\Users\gemini\pyodide', '3']
    proxy_code = (BUILD / 'аудит/ноутбук_стенд_2/проксі_почергове.js').read_bytes()
    result = {'початок': datetime.now(timezone.utc).isoformat(), 'sha': sha,
              'сцена': scene['назва'], 'команда': command,
              'проксі_sha256': hashlib.sha256(proxy_code).hexdigest(),
              'змінні': {key: env[key] for key in (*scene['змінні'], 'LMS_MODE', 'PORT',
                        'CTX', 'MODEL_CTX', 'MODEL_URL', 'ODNOCHASNO')}}
    result['змінні'].update(FOTO='1', OTSINKA='0')
    started = time.monotonic()
    proxy = stand = None
    with tempfile.TemporaryDirectory(prefix='концерт-проксі-') as temp:
        proxy_file = Path(temp) / 'проксі.js'
        proxy_file.write_bytes(proxy_code)
        try:
            with (dest / 'проксі.txt').open('w', encoding='utf-8') as proxy_log:
                proxy = subprocess.Popen(['node', str(proxy_file)], cwd=BUILD, env=env,
                                         stdout=proxy_log, stderr=subprocess.STDOUT,
                                         creationflags=subprocess.CREATE_NO_WINDOW)
                for _ in range(50):
                    if proxy.poll() is not None:
                        raise RuntimeError('Проксі завершився до старту стенда')
                    try:
                        with REC.socket.create_connection(('127.0.0.1', 1235), timeout=0.2):
                            break
                    except OSError:
                        time.sleep(0.1)
                else:
                    raise RuntimeError('Проксі не відкрив порт')
                with (dest / 'лог.txt').open('w', encoding='utf-8') as log:
                    stand = subprocess.Popen(command, cwd=BUILD, env=env, stdout=log,
                                             stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
                    result['rc'] = stand.wait(timeout=1800)
        finally:
            for process in (stand, proxy):
                if process and process.poll() is None:
                    process.terminate()
                    process.wait(timeout=30)
            log = (dest / 'проксі.txt').read_text(encoding='utf-8') if (dest / 'проксі.txt').exists() else ''
            owned = set(re.findall(r'HTTP власний екземпляр (.+)', log))
            result['вивантажено'] = [REC.api('/unload', {'instance_id': inst['id']})
                for model in REC.api()['models'] for inst in model['loaded_instances'] if inst['id'] in owned]
            result['моделі_після'] = [{'key': model['key'], 'loaded_instances': model['loaded_instances']}
                                     for model in REC.api()['models']]
            result['кінець'] = datetime.now(timezone.utc).isoformat()
            result['секунд'] = round(time.monotonic() - started, 1)
            (dest / 'результат.json').write_text(json.dumps(result, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    return result['rc']


if __name__ == '__main__':
    raise SystemExit(main())
