"""Реальний невдалий запит сторінки через виправлений міст; власний процес закривається."""
from pathlib import Path
import gzip
import json
import os
import socket
import subprocess
import sys
import time
import urllib.request

old = Path(sys.argv[1])
out = Path(sys.argv[2]).resolve()
out.mkdir(parents=True, exist_ok=True)
record = json.loads(gzip.decompress((old / 'стенд/записи/0016.json.gz').read_bytes()))
prompt = json.loads(record['stdin'])['message']['content'][0]['text']
body = None
for path in old.glob('стенд/службове/*/обміни.jsonl'):
    for line in path.read_text(encoding='utf-8').splitlines():
        candidate = json.loads(json.loads(line)['запит'])
        blocks = [b for m in candidate['messages'] for b in m['content']]
        images = [b for b in blocks if b.get('type') == 'image']
        if len(images) == len(record['фото']) and all(b['text'] in prompt for b in blocks if b.get('type') == 'text'):
            body = candidate
            break
assert body is not None, 'Не знайдено первісного запиту сторінки'
(out / 'запит_сторінки.json').write_text(json.dumps(body, ensure_ascii=False, indent=2), encoding='utf-8')
port = 8791
while True:
    with socket.socket() as probe:
        try:
            probe.bind(('127.0.0.1', port))
            break
        except OSError:
            port += 1
with (out / 'міст.log').open('wb') as log:
    bridge = subprocess.Popen([sys.executable, str(Path(__file__).with_name('міст_agy.py')), str(port),
                               str(out / 'журнал.jsonl'), str(out / 'записи'), 'gemini-3.8-flash-low'],
                              stdout=log, stderr=log, env=dict(os.environ, PYTHONUTF8='1'))
    try:
        while True:
            if bridge.poll() is not None:
                raise RuntimeError('Міст завершився')
            try:
                with socket.create_connection(('127.0.0.1', port), timeout=1):
                    break
            except ConnectionRefusedError:
                time.sleep(.1)
        request = urllib.request.Request(f'http://127.0.0.1:{port}/',
            data=json.dumps(body, ensure_ascii=False).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-prohid': 'kontrol-alias'})
        with urllib.request.urlopen(request, timeout=960) as response:
            data = response.read()
        (out / 'відповідь_сторінці.json').write_bytes(data)
        print((out / 'журнал.jsonl').read_text(encoding='utf-8'))
    finally:
        bridge.terminate()
        bridge.wait(timeout=30)
