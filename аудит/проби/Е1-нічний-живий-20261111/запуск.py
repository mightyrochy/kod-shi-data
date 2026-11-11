"""Послідовний запуск призначеного плану; службові фото лишаються в TEMP."""
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
BUILD = ROOT.parent / 'tmp/збірка'
CACHE = Path(r'C:\Users\gemini\pyodide')
os.environ.update(NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules',
                  PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
PHOTOS = ROOT.parent / 'tmp/фото_сцен'
PHOTOS.mkdir(exist_ok=True)
os.environ['TEKA_FOTO_SCENY'] = str(PHOTOS)
sources = []
with gzip.open(BUILD / 'каталог_повний.xml.gz', 'rb') as stream:
    for _, offer in ET.iterparse(stream, events=['end']):
        if offer.tag != 'offer':
            continue
        item_id = offer.attrib.get('id')
        if item_id in ('ж-02799', 'ж-09444'):
            filename = 'bluza.jpg' if item_id == 'ж-02799' else 'її_річ.jpg'
            url = offer.findtext('picture')
            try:
                request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(request, timeout=45) as response:
                    data = response.read()
                    status = response.status
                from PIL import Image
                Image.open(io.BytesIO(data)).convert('RGB').save(PHOTOS / filename, format='JPEG')
                sources.append(dict(id=item_id, файл=filename, url=url, HTTP=status,
                                    sha256=hashlib.sha256((PHOTOS / filename).read_bytes()).hexdigest()))
            except Exception as exc:
                sources.append(dict(id=item_id, файл=filename, url=url, помилка=str(exc)))
        offer.clear()
(OUT / 'джерела_фото.json').write_text(json.dumps(sources, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(sources, ensure_ascii=False), flush=True)
command = [sys.executable, str(ROOT / 'аудит/проби/записати_план.py'),
           str(OUT / 'ПЛАН.json'), str(BUILD), str(CACHE), str(OUT)]
record = dict(початок=datetime.now(timezone.utc).isoformat(), команда=command,
              NODE_PATH=os.environ['NODE_PATH'], TEKA_FOTO_SCENY=str(PHOTOS),
              NODE_OPTIONS=os.environ.get('NODE_OPTIONS'), PYTHONPATH=os.environ.get('PYTHONPATH'))
with (OUT / 'перевірка_змінних.txt').open('w', encoding='utf-8') as log:
    record['перевірка_змінних_rc'] = subprocess.run(command + ['--лише-змінні'], cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
with (OUT / 'план-лог.txt').open('w', encoding='utf-8') as log:
    record['rc'] = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
record['кінець'] = datetime.now(timezone.utc).isoformat()
(OUT / 'запуск.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False), flush=True)
sys.exit(record['rc'])
