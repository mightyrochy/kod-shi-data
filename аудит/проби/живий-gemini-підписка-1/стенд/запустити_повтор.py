"""Передній план: міст + браузерні повтори; на виході власний міст зупиняється.
python запустити_повтор.py <тека_виходу> <модель_agy> <модель_сторінки> <ситуації...>
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import shutil
import socket
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve()
MODEL, PAGE_MODEL = sys.argv[2:4]
ENV = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", PRODUCT_MODEL=PAGE_MODEL)
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'стенд').mkdir(exist_ok=True)
PORT = 8791
(OUT / 'запуск.json').write_text(json.dumps({
    'початок_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'модель_agy': MODEL, 'модель_сторінки': PAGE_MODEL, 'ситуації': sys.argv[4:],
    'голова_гілки': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
    'main_наряду': 'a6b373f405422d09afe6a562671317c1900b7ba8',
    'сторінка_sha256': hashlib.sha256((Path(ENV['STOR']) / 'index.html').read_bytes()).hexdigest(),
    'жінка': 'скрипт зі словами й діями першого прогону', 'телефон': [390, 844],
    'стеля_моста_с': int(ENV.get('AGY_СТЕЛЯ_С', 660)),
}, ensure_ascii=False, indent=2), encoding='utf-8')


def quota(name):
    work = Path(os.environ['TEMP']) / 'agy-прогін-4'
    work.mkdir(exist_ok=True)
    result = subprocess.run(['agy', '-p', '/usage'], cwd=work, capture_output=True, timeout=120)
    (OUT / (name + '.stdout.txt')).write_bytes(result.stdout)
    (OUT / (name + '.stderr.txt')).write_bytes(result.stderr)
    (OUT / (name + '.json')).write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'код': result.returncode}, ensure_ascii=False), encoding='utf-8')
    print(name, result.stdout.decode('utf-8', 'replace'), flush=True)


try:
    with socket.create_connection(('127.0.0.1', PORT), timeout=1):
        raise SystemExit('ЗАБЛОКОВАНО: порт 8791 уже зайнято; чужого процесу не змінено')
except (ConnectionRefusedError, TimeoutError):
    pass

quota('квота_до')
with (OUT / 'стенд/міст.log').open('wb') as log:
    bridge = subprocess.Popen([sys.executable, str(HERE / 'міст_agy.py'), str(PORT),
                               str(OUT / 'стенд/журнал_моделі_продукту.jsonl'),
                               str(OUT / 'стенд/записи'), MODEL], env=ENV, stdout=log, stderr=log)
    try:
        while True:
            if bridge.poll() is not None:
                raise RuntimeError('Міст завершився до відкриття порту')
            try:
                with socket.create_connection(('127.0.0.1', PORT), timeout=1):
                    break
            except (ConnectionRefusedError, TimeoutError):
                time.sleep(.25)
        for scene in sys.argv[4:]:
            print('ПОЧАТОК', MODEL, scene, datetime.datetime.now(datetime.timezone.utc).isoformat(), flush=True)
            with (OUT / 'стенд' / (scene + '.log')).open('wb') as scene_log:
                result = subprocess.run(['node', str(HERE / 'повтор.js'), scene, str(OUT), str(PORT)], env=ENV, stdout=scene_log, stderr=scene_log)
            print('КІНЕЦЬ', scene, result.returncode, flush=True)
            if result.returncode:
                raise RuntimeError('Браузерний повтор не завершився: ' + scene)
    finally:
        bridge.terminate()
        bridge.wait(timeout=30)
        quota('квота_після')
