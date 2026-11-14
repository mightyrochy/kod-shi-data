"""Запускає штатне приймання баз і фіксує кінцевий стан локального сервера."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
os.environ.update(NODE_PATH=r'C:\Users\gemini\kod-shi-test-node\node_modules', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
command = ['node', str(ROOT / 'аудит/проби/нова_база.js'), str(OUT)]
with (OUT / 'нова_база_лог.txt').open('w', encoding='utf-8') as log:
    rc = subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT).returncode
with urllib.request.urlopen('http://127.0.0.1:1234/api/v1/models', timeout=30) as response:
    models = json.load(response)
(OUT / 'моделі_після.json').write_text(json.dumps(models, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
record = dict(команда=command, rc=rc, час=datetime.now(timezone.utc).isoformat(),
              завантажені=[m['key'] for m in models['models'] if m['loaded_instances']])
(OUT / 'завершення.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(record, ensure_ascii=False), flush=True)
subprocess.run([sys.executable, str(OUT / 'підсумувати.py')], cwd=ROOT, check=True)
